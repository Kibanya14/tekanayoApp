"""
Fonctions utilitaires pour TekanayoApp
Extrait de apps.py pour alléger le fichier principal
"""

import os
import re
import secrets
from datetime import datetime
from functools import wraps

from flask import current_app, flash, redirect, request, session, url_for
from flask_login import current_user, login_required
from flask_mail import Message
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from sqlalchemy import or_
from werkzeug.utils import secure_filename

from backend.models import (
    PlatformActivityLog,
    PlatformSettings,
    PortalCustomer,
    SellerAdmin,
    SellerCustomer,
    SellerDeliverer,
    SellerOrder,
    SellerProduct,
    SellerShop,
    db,
)
from backend.config_data import ALLOWED_UPLOAD_EXTENSIONS

# ============================================================================
# FONCTIONS UTILITAIRES GÉNÉRALES
# ============================================================================


def _slugify(value: str) -> str:
    """Convertit une chaîne en slug URL-friendly."""
    value = re.sub(r"[^a-zA-Z0-9]+", "-", (value or "").strip().lower()).strip("-")
    return value or f"shop-{secrets.token_hex(2)}"


def _unique_slug(base: str) -> str:
    """Génère un slug unique en ajoutant un suffixe numérique si nécessaire."""
    slug = base
    i = 2
    while SellerShop.query.filter_by(slug=slug).first():
        slug = f"{base}-{i}"
        i += 1
    return slug


def _safe_float(value, default=0.0):
    """Convertit une valeur en float de manière sécurisée."""
    try:
        return float(value)
    except Exception:
        return float(default)


def _generate_temp_password(length: int = 10) -> str:
    """Génère un mot de passe temporaire sécurisé."""
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789"
    return "".join(secrets.choice(alphabet) for _ in range(max(8, length)))


# ============================================================================
# FONCTIONS EMAIL
# ============================================================================


def _email_shell(title: str, body_html: str, brand: str, accent: str = "#0f766e"):
    """Génère un template HTML d'email avec mise en page."""
    return f"""
    <div style="font-family:Arial,sans-serif;background:#f4f6fb;padding:24px;color:#0f172a;">
      <div style="max-width:680px;margin:auto;background:#fff;border:1px solid #e2e8f0;border-radius:14px;overflow:hidden;">
        <div style="padding:20px 24px;background:linear-gradient(135deg,{accent},#0f172a);color:#fff;">
          <h2 style="margin:0;font-size:22px;">{title}</h2>
          <p style="margin:6px 0 0;opacity:.9">{brand}</p>
        </div>
        <div style="padding:20px 24px;line-height:1.7;">{body_html}</div>
        <div style="padding:14px 24px;background:#f8fafc;color:#64748b;font-size:12px;text-align:center;">
          © {datetime.utcnow().year} {brand} - Propulsé par Esperdigi
        </div>
      </div>
    </div>
    """


def _send_email(to: str, subject: str, body: str, html_body: str | None = None):
    """Envoie un email via Flask-Mail."""
    from backend.apps import mail
    try:
        msg = Message(subject=subject, sender=os.getenv("MAIL_DEFAULT_SENDER"), recipients=[to])
        msg.body = body
        msg.html = html_body or _email_shell(subject, body.replace("\n", "<br>"), "Tekanayo App")
        mail.send(msg)
        return True
    except Exception:
        return False


# ============================================================================
# FONCTIONS DE FICHIERS
# ============================================================================


def _save_uploaded_image(file_storage, bucket: str) -> str | None:
    """Sauvegarde une image uploadée dans Supabase Storage."""
    if not file_storage or not getattr(file_storage, "filename", None):
        return None
    
    filename = secure_filename(file_storage.filename or "")
    if not filename or "." not in filename:
        return None
    
    ext = filename.rsplit(".", 1)[1].lower()
    if ext not in ALLOWED_UPLOAD_EXTENSIONS:
        return None
    
    try:
        # Utiliser Supabase Storage à la place du stockage local
        from backend.supabase_storage import storage_client
        
        # Construire le chemin Supabase : bucket/YYYYMMDDHHMMSS_token.ext
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        token = secrets.token_hex(8)
        supabase_path = f"{bucket}/{timestamp}_{token}.{ext}"
        
        # Upload vers Supabase
        response = storage_client.client.storage.from_('uploads').upload(
            path=supabase_path,
            file=file_storage.stream.read(),
            file_options={"content-type": file_storage.content_type or "application/octet-stream"}
        )
        
        # Retourner le chemin pour stocker en BD
        if response.status_code == 200:
            return supabase_path
        else:
            current_app.logger.error(f"Supabase upload failed: {response.json()}")
            return None
    except Exception as e:
        current_app.logger.error(f"Upload error: {str(e)}")
        # Fallback au stockage local en cas d'erreur
        try:
            folder = os.path.join(current_app.config["UPLOAD_ROOT"], bucket)
            os.makedirs(folder, exist_ok=True)
            final_name = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{secrets.token_hex(4)}.{ext}"
            abs_path = os.path.join(folder, final_name)
            file_storage.save(abs_path)
            return f"/uploads/{bucket}/{final_name}"
        except Exception as fallback_error:
            current_app.logger.error(f"Fallback upload failed: {str(fallback_error)}")
            return None


# ============================================================================
# FONCTIONS DE GÉOCODAGE
# ============================================================================


def _geocode_address(address: str):
    """Géocode une adresse via Nominatim (OpenStreetMap)."""
    if not address:
        return None, None, None
    try:
        import requests
        resp = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": address, "format": "json", "limit": 1},
            headers={"User-Agent": "TekanayoApp/1.0"},
            timeout=5,
        )
        data = resp.json()
        if isinstance(data, list) and data:
            item = data[0]
            return _safe_float(item.get("lat"), None), _safe_float(item.get("lon"), None), item.get("display_name")
    except Exception:
        return None, None, None
    return None, None, None


# ============================================================================
# FONCTIONS DE RÉSOLUTION DE BOUTIQUES
# ============================================================================


def _resolve_shop_identifier(identifier: str):
    """Résout un identifiant de boutique (slug, id, custom_domain)."""
    raw = (identifier or "").strip()
    if not raw:
        return None
    if raw.isdigit():
        return SellerShop.query.filter_by(id=int(raw), is_active=True).first()
    clean = raw.lower()
    direct = (
        SellerShop.query
        .filter(
            SellerShop.is_active.is_(True),
            or_(
                SellerShop.slug == clean,
                SellerShop.custom_domain == clean,
            ),
        )
        .first()
    )
    if direct:
        return direct
    # Accept dev access key format: <slug>-<id>
    m = re.match(r"^(.*)-(\d+)$", clean)
    if m:
        slug_part, id_part = m.group(1), m.group(2)
        try:
            sid = int(id_part)
        except Exception:
            return None
        shop = SellerShop.query.filter_by(id=sid, is_active=True).first()
        if shop and (shop.slug or "").lower() == slug_part:
            return shop
    # Backward compatibility: <slug><id>
    m2 = re.match(r"^(.*?)(\d+)$", clean)
    if m2:
        slug_part, id_part = m2.group(1), m2.group(2)
        try:
            sid = int(id_part)
        except Exception:
            return None
        shop = SellerShop.query.filter_by(id=sid, is_active=True).first()
        if shop and (shop.slug or "").lower() == slug_part:
            return shop
    return None


def _shop_access_key(shop: SellerShop) -> str:
    """Génère la clé d'accès publique d'une boutique."""
    if not shop:
        return ""
    custom = (shop.custom_domain or "").strip().lower()
    if custom:
        return custom
    return f"{shop.slug}-{shop.id}"


def _resolve_shop_access_key(access_key: str):
    """Résout une clé d'accès en objet boutique."""
    key = (access_key or "").strip().lower()
    if not key:
        return None
    by_domain = SellerShop.query.filter_by(custom_domain=key, is_active=True).first()
    if by_domain:
        return by_domain
    by_slug = SellerShop.query.filter_by(slug=key, is_active=True).first()
    if by_slug:
        return by_slug
    m = re.match(r"^(.*)-(\d+)$", key)
    if m:
        slug_part, id_part = m.group(1), m.group(2)
    else:
        # Backward compatibility: old format slug+id (without "-")
        m2 = re.match(r"^(.*?)(\d+)$", key)
        if not m2:
            return None
        slug_part, id_part = m2.group(1), m2.group(2)
    if not slug_part:
        return None
    try:
        sid = int(id_part)
    except Exception:
        return None
    shop = SellerShop.query.filter_by(id=sid, is_active=True).first()
    if shop and (shop.slug or "").lower() == slug_part:
        return shop
    return None


# ============================================================================
# FONCTIONS DE GESTION DU PANIER
# ============================================================================


def _shop_cart_key(shop_id: int) -> str:
    return f"seller_cart_{int(shop_id)}"


def _get_shop_cart(shop_id: int):
    """Récupère le panier d'une boutique depuis la session."""
    data = session.get(_shop_cart_key(shop_id), [])
    if not isinstance(data, list):
        return []
    cleaned = []
    for entry in data:
        try:
            pid = int(entry.get("product_id"))
            qty = int(entry.get("quantity", 1))
        except Exception:
            continue
        if qty <= 0:
            continue
        cleaned.append({"product_id": pid, "quantity": qty})
    return cleaned


def _set_shop_cart(shop_id: int, items):
    """Sauvegarde le panier d'une boutique dans la session."""
    session[_shop_cart_key(shop_id)] = items
    session.modified = True


def _get_shop_customer(shop_id: int):
    """Récupère le client connecté d'une boutique."""
    data = session.get("shop_customer_sessions", {})
    if isinstance(data, dict):
        cid = data.get(str(shop_id))
        if cid:
            try:
                return SellerCustomer.query.filter_by(id=int(cid), shop_id=shop_id).first()
            except Exception:
                pass
    if current_user.is_authenticated and hasattr(current_user, '_sa_instance_state'):
        if isinstance(current_user, PortalCustomer):
            return current_user
    return None


def _set_shop_customer(shop_id: int, customer_id: int | None):
    """Définit le client connecté pour une boutique."""
    data = session.get("shop_customer_sessions", {})
    if not isinstance(data, dict):
        data = {}
    key = str(shop_id)
    if customer_id is None:
        data.pop(key, None)
    else:
        data[key] = int(customer_id)
    session["shop_customer_sessions"] = data
    session.modified = True


# ============================================================================
# FONCTIONS DE CONTEXTE BOUTIQUE
# ============================================================================


def _build_shop_page_context(shop, selected_category=None, search_term=None, selected_product_id=None):
    """Construit le contexte complet pour l'affichage d'une boutique."""
    selected_category = (selected_category or "").strip()
    search_term = (search_term or "").strip()

    products_q = SellerProduct.query.filter_by(shop_id=shop.id, is_active=True)
    if selected_category:
        products_q = products_q.filter(SellerProduct.category == selected_category)
    if search_term:
        like = f"%{search_term}%"
        products_q = products_q.filter(or_(SellerProduct.name.ilike(like), SellerProduct.description.ilike(like)))

    products = products_q.order_by(SellerProduct.is_promoted.desc(), SellerProduct.created_at.desc()).all()

    featured_products = (
        SellerProduct.query
        .filter_by(shop_id=shop.id, is_active=True)
        .order_by(SellerProduct.is_promoted.desc(), SellerProduct.quantity.desc(), SellerProduct.created_at.desc())
        .limit(8)
        .all()
    )

    selected_product = None
    if selected_product_id:
        try:
            selected_product = SellerProduct.query.filter_by(
                id=int(selected_product_id), shop_id=shop.id, is_active=True
            ).first()
        except Exception:
            selected_product = None

    if not selected_product and featured_products:
        selected_product = featured_products[0]

    categories = [
        row[0]
        for row in (
            db.session.query(SellerProduct.category)
            .filter_by(shop_id=shop.id, is_active=True)
            .distinct()
            .order_by(SellerProduct.category.asc())
            .all()
        )
        if row and row[0]
    ]

    cart_entries = _get_shop_cart(shop.id)
    cart_ids = [item["product_id"] for item in cart_entries]
    cart_products = {}
    if cart_ids:
        rows = SellerProduct.query.filter(
            SellerProduct.shop_id == shop.id,
            SellerProduct.id.in_(cart_ids),
            SellerProduct.is_active.is_(True),
        ).all()
        cart_products = {p.id: p for p in rows}

    cart_items = []
    cart_total = 0.0
    total_qty = 0
    clean_cart = []
    for item in cart_entries:
        product = cart_products.get(item["product_id"])
        if not product:
            continue
        qty = max(1, min(item["quantity"], max(product.quantity, 1)))
        line = float(product.price or 0.0) * qty
        cart_total += line
        total_qty += qty
        clean_cart.append({"product_id": product.id, "quantity": qty})
        cart_items.append(
            {
                "product": product,
                "quantity": qty,
                "line_total": line,
            }
        )

    if clean_cart != cart_entries:
        _set_shop_cart(shop.id, clean_cart)

    customer = _get_shop_customer(shop.id)
    customer_orders = []
    if customer:
        customer_orders = (
            SellerOrder.query
            .filter_by(shop_id=shop.id, customer_id=customer.id)
            .order_by(SellerOrder.created_at.desc())
            .limit(15)
            .all()
        )

    return {
        "products": products,
        "featured_products": featured_products,
        "categories": categories,
        "selected_category": selected_category,
        "search_term": search_term,
        "selected_product": selected_product,
        "cart_items": cart_items,
        "cart_total": cart_total,
        "cart_count": total_qty,
        "shop_customer": customer,
        "customer_orders": customer_orders,
        "shop_settings": {
            "shop_name": shop.name,
            "shop_logo": shop.logo_url,
            "shop_email": shop.support_email or shop.owner_email,
            "shop_phone": shop.support_phone,
            "shop_address": shop.address,
            "facebook_url": shop.facebook_url,
            "whatsapp_number": shop.whatsapp_number,
            "whatsapp_group_url": shop.whatsapp_group_url,
            "telegram_username": shop.telegram_username,
            "telegram_url": shop.telegram_url,
            "about_page_content": shop.about_page_content,
            "legal_page_content": shop.legal_page_content,
            "terms_page_content": shop.terms_page_content,
            "returns_page_content": shop.returns_page_content,
            "privacy_page_content": shop.privacy_page_content,
        },
    }


# ============================================================================
# FONCTIONS D'AUTHENTIFICATION ET DÉCORATEURS
# ============================================================================


def _serializer(app):
    return URLSafeTimedSerializer(app.config["SECRET_KEY"])


def _generate_reset_token(app, role: str, record_id: int):
    return _serializer(app).dumps({"role": role, "id": int(record_id)}, salt="tekanayo-reset")


def _verify_reset_token(app, token: str, max_age: int = 3600):
    try:
        payload = _serializer(app).loads(token, salt="tekanayo-reset", max_age=max_age)
        if isinstance(payload, dict):
            return payload
        return None
    except (SignatureExpired, BadSignature):
        return None


def admin_required(permission=None):
    """Décorateur pour restreindre l'accès aux admins avec permission optionnelle."""
    def deco(view):
        @wraps(view)
        @login_required
        def wrapped(*args, **kwargs):
            if not current_user.is_active:
                flash("Compte admin inactif.", "error")
                return redirect(url_for("admin_login_page"))
            if permission and not current_user.has_permission(permission):
                flash("Permission insuffisante.", "error")
                return redirect(url_for("tekanayo_admin_panel"))
            return view(*args, **kwargs)
        return wrapped
    return deco


def record_activity(action: str, actor=None, extra: str | None = None):
    """Enregistre une activité dans le journal."""
    try:
        actor = actor or (current_user if current_user.is_authenticated else None)
        entry = PlatformActivityLog(
            action=action,
            actor_id=getattr(actor, "id", None),
            actor_email=getattr(actor, "email", None),
            actor_name=f"{getattr(actor, 'first_name', '')} {getattr(actor, 'last_name', '')}".strip() if actor else None,
            actor_phone=getattr(actor, "phone", None),
            extra=extra,
        )
        db.session.add(entry)
        db.session.commit()
    except Exception:
        db.session.rollback()


def seller_session_required(view):
    """Décorateur pour restreindre l'accès aux vendeurs connectés."""
    @wraps(view)
    def wrapped(slug, *args, **kwargs):
        sid = session.get("seller_admin_id")
        admin = SellerAdmin.query.filter_by(id=sid, is_active=True).first() if sid else None
        shop = SellerShop.query.filter_by(slug=slug).first_or_404()
        if not admin or admin.shop_id != shop.id:
            flash("Connectez-vous à votre espace vendeur.", "error")
            return redirect(url_for("seller_entry_for_shop_key", shop_key=_shop_access_key(shop)))
        return view(slug, *args, **kwargs)
    return wrapped


def deliverer_session_required(view):
    """Décorateur pour restreindre l'accès aux livreurs connectés."""
    @wraps(view)
    def wrapped(slug, *args, **kwargs):
        did = session.get("seller_deliverer_id")
        deliverer = SellerDeliverer.query.filter_by(id=did, is_active=True).first() if did else None
        shop = SellerShop.query.filter_by(slug=slug).first_or_404()
        if not deliverer or deliverer.shop_id != shop.id:
            flash("Connectez-vous à votre espace livreur.", "error")
            return redirect(url_for("deliverer_entry_for_shop_key", shop_key=_shop_access_key(shop)))
        return view(slug, *args, **kwargs)
    return wrapped


# ============================================================================
# FONCTIONS DE PARAMÈTRES PLATEFORME
# ============================================================================


def _get_platform_settings():
    """Récupère ou crée les paramètres de la plateforme."""
    settings = PlatformSettings.query.first()
    if settings:
        return settings
    settings = PlatformSettings(
        exchange_rate_usd_cdf=_safe_float(os.getenv("EXCHANGE_RATE_USD_CDF"), 2800.0),
    )
    db.session.add(settings)
    db.session.commit()
    return settings

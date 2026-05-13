"""
Routes du portail public Tekanayo
Extrait de apps.py pour alléger le fichier principal
"""

from datetime import datetime

from flask import (
    Blueprint, flash, jsonify, redirect, render_template, request,
    session, url_for, current_app
)
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import or_

from backend.models import (
    PlatformAdmin, PlatformAnnouncement, PlatformSettings,
    PortalCustomer, SellerAdmin, SellerCustomer, SellerDeliverer,
    SellerOrder, SellerProduct, SellerShop, db,
)
from backend.helpers import (
    _slugify, _shop_access_key, _build_shop_page_context,
    _get_shop_cart, _set_shop_cart, _get_shop_customer, _set_shop_customer,
    _get_platform_settings, _send_email, _email_shell, _generate_temp_password,
    _save_uploaded_image, record_activity, _safe_float,
)
from backend.config_data import CATEGORY_NICHES, INVOICE_THEMES, ADMIN_PERMISSION_LABELS, NICHE_CHOICES

portal_bp = Blueprint("portal", __name__, url_prefix="")


# ============================================================================
# FONCTIONS INTERNES DU BLUEPRINT
# ============================================================================


def _portal_shop():
    return SellerShop.query.filter_by(is_active=True).first() or SellerShop.query.first()


def _portal_shop_context():
    platform_settings = _get_platform_settings()
    shop = _portal_shop()
    if not shop:
        return None, {
            "products": [],
            "featured_products": [],
            "categories": [],
            "selected_category": "",
            "search_term": "",
            "selected_product": None,
            "cart_items": [],
            "cart_total": 0.0,
            "cart_count": 0,
            "shop_customer": None,
            "customer_orders": [],
            "shop_settings": {},
            "seller_promotions": [],
            "announcements": [],
            "platform_settings": platform_settings,
        }
    view = _build_shop_page_context(shop)
    announcements = PlatformAnnouncement.query.order_by(PlatformAnnouncement.created_at.desc()).all()
    promoted = (
        db.session.query(SellerProduct, SellerShop)
        .join(SellerShop, SellerProduct.shop_id == SellerShop.id)
        .filter(SellerProduct.is_promoted.is_(True), SellerProduct.is_active.is_(True), SellerShop.is_active.is_(True))
        .order_by(SellerProduct.created_at.desc())
        .limit(16)
        .all()
    )
    seller_promotions = []
    for product, seller_shop in promoted:
        seller_promotions.append(
            {
                "product": product,
                "shop": seller_shop,
                "shop_url": url_for("shop_public_entry", shop_key=_shop_access_key(seller_shop)),
                "product_url": url_for("seller_shop_product_detail", slug=_shop_access_key(seller_shop), product_id=product.id),
            }
        )
    view["seller_promotions"] = seller_promotions
    view["announcements"] = announcements
    view["platform_settings"] = platform_settings
    return shop, view


# ============================================================================
# ROUTES PRINCIPALES DU PORTAIL
# ============================================================================


@portal_bp.route("/")
@portal_bp.route("/portal")
def tekanayo_portal():
    shop, view = _portal_shop_context()
    return render_template("portal/portal.html", shop=shop, **view)


@portal_bp.route("/about")
@portal_bp.route("/portal/about")
def about():
    shop, view = _portal_shop_context()
    return render_template("portal/about.html", shop=shop, **(view or {}))


@portal_bp.route("/portal/categories")
def tekanayo_portal_categories():
    shop, view = _portal_shop_context()
    return render_template("portal/categories.html", shop=shop, **view)


@portal_bp.route("/portal/products")
def tekanayo_portal_products():
    shop, view = _portal_shop_context()
    return render_template("portal/products.html", shop=shop, **view)


@portal_bp.route("/portal/legal")
def tekanayo_portal_legal():
    shop, view = _portal_shop_context()
    return render_template("portal/legal.html", shop=shop, **view)


@portal_bp.route("/portal/terms")
def tekanayo_portal_terms():
    shop, view = _portal_shop_context()
    return render_template("portal/terms.html", shop=shop, **view)


@portal_bp.route("/portal/returns")
def tekanayo_portal_returns():
    shop, view = _portal_shop_context()
    return render_template("portal/returns.html", shop=shop, **view)


@portal_bp.route("/portal/privacy")
def tekanayo_portal_privacy():
    shop, view = _portal_shop_context()
    return render_template("portal/privacy.html", shop=shop, **view)


@portal_bp.route("/portal/<page>")
def tekanayo_portal_page(page):
    template_map = {
        "about": "portal/about.html",
        "categories": "portal/categories.html",
        "products": "portal/products.html",
        "legal": "portal/legal.html",
        "terms": "portal/terms.html",
        "returns": "portal/returns.html",
        "privacy": "portal/privacy.html",
        "cart": "portal/cart.html",
        "checkout": "portal/checkout.html",
        "login": "portal/login.html",
        "register": "portal/register.html",
        "profile": "portal/profile.html",
        "orders": "portal/orders.html",
        "forum": "portal/forum.html",
        "reset_request": "portal/reset_request.html",
        "reset_password": "portal/reset_password.html",
        "order_confirmation": "portal/order_confirmation.html",
        "order_detail": "portal/order_detail.html",
        "product_detail": "portal/product_detail.html",
    }
    tpl = template_map.get((page or "").strip().lower())
    if not tpl:
        return redirect(url_for("portal.tekanayo_portal"))
    shop, view = _portal_shop_context()
    return render_template(tpl, shop=shop, **view)


@portal_bp.route("/set-currency", methods=["POST"])
def set_currency():
    code = (request.form.get("currency") or "").strip().upper()
    if code in {"USD", "CDF"}:
        session["selected_currency"] = code
    return redirect(request.referrer or url_for("portal.tekanayo_portal"))


# ============================================================================
# API ROUTES (vérifications)
# ============================================================================


@portal_bp.route("/api/check-email")
def check_email_availability():
    email = request.args.get("email", "").strip().lower()
    if not email:
        return jsonify({"available": False, "error": "Email requis"})

    existing_owner_email = SellerShop.query.filter_by(owner_email=email).first()
    existing_support_email = SellerShop.query.filter_by(support_email=email).first()
    existing_seller_admin = SellerAdmin.query.filter_by(email=email).first()
    existing_platform_admin = PlatformAdmin.query.filter_by(email=email).first()
    existing_portal_customer = PortalCustomer.query.filter_by(email=email).first()
    existing_deliverer = SellerDeliverer.query.filter_by(email=email).first()
    existing_customer = SellerCustomer.query.filter_by(email=email).first()

    available = not any([
        existing_owner_email,
        existing_support_email,
        existing_seller_admin,
        existing_platform_admin,
        existing_portal_customer,
        existing_deliverer,
        existing_customer,
    ])
    return jsonify({"available": available})


@portal_bp.route("/api/check-shop-name")
def check_shop_name_availability():
    name = request.args.get("name", "").strip()
    if not name:
        return jsonify({"available": False, "error": "Nom de boutique requis"})

    existing_shop = SellerShop.query.filter(
        SellerShop.name.ilike(name) | SellerShop.slug.ilike(_slugify(name))
    ).first()

    available = existing_shop is None
    return jsonify({"available": available})


@portal_bp.route("/api/check-custom-domain")
def check_custom_domain_availability():
    domain = (request.args.get("domain") or "").strip().lower()
    if not domain:
        return jsonify({"available": True})

    existing_domain = SellerShop.query.filter_by(custom_domain=domain).first()
    return jsonify({"available": existing_domain is None})


# ============================================================================
# ROUTES D'INSCRIPTION VENDEUR
# ============================================================================


@portal_bp.route("/portal/sellerregister", methods=["GET"])
def seller_register_page():
    return render_template(
        "portal/seller_register.html",
        now=datetime.now(),
        niches=NICHE_CHOICES
    )


@portal_bp.route("/devenir-vendeur", methods=["POST"])
@portal_bp.route("/portal/sellerregister", methods=["POST"])
def become_seller():
    print("\n=== DÉBUT ENREGISTREMENT VENDEUR ===")
    print("=== DONNÉES REÇUES DU FORMULAIRE ===")
    print(f"Form keys: {list(request.form.keys())}")
    print(f"Files keys: {list(request.files.keys())}")
    for key in request.form:
        print(f"  {key}: {request.form.get(key)[:50] if len(request.form.get(key)) > 50 else request.form.get(key)}")
    print("=== FIN DONNÉES FORMULAIRE ===\n")

    # Récupération des données du formulaire
    shop_name = (request.form.get("shop_name") or "").strip()
    first_name = (request.form.get("first_name") or "").strip()
    last_name = (request.form.get("last_name") or "").strip()
    email = (request.form.get("email") or "").strip().lower()
    password = (request.form.get("password") or "").strip()
    confirm_password = (request.form.get("confirm_password") or "").strip()

    # Phone input component fields
    country_code = (request.form.get("country_code") or "").strip().upper() or None
    phone_number = (request.form.get("phone_number") or "").strip() or None

    # Legacy fields (for backward compatibility)
    legacy_country = (request.form.get("country") or "").strip().upper()
    legacy_phone = (request.form.get("phone") or "").strip()

    # Use new fields first, fallback to legacy
    if not country_code:
        country_code = legacy_country
    if not phone_number:
        phone_number = legacy_phone

    address = (request.form.get("address") or "").strip()
    category_niche = (request.form.get("category_niche") or "").strip()
    shop_description = (request.form.get("shop_description") or "").strip()
    website = (request.form.get("website") or "").strip()
    custom_domain = (request.form.get("custom_domain") or "").strip().lower()
    terms = request.form.get("terms")
    data_processing = request.form.get("data_processing")

    print(f"Shop name: {shop_name}")
    print(f"Email: {email}")
    print(f"Phone number: {phone_number}")

    # Validation
    errors = []
    if not shop_name:
        errors.append("Le nom de la boutique est requis.")
    if not first_name:
        errors.append("Le prénom est requis.")
    if not last_name:
        errors.append("Le nom est requis.")
    if not email:
        errors.append("L'email est requis.")
    if not password:
        errors.append("Le mot de passe est requis.")
    elif len(password) < 6:
        errors.append("Le mot de passe doit contenir au moins 6 caractères.")
    if password != confirm_password:
        errors.append("Les mots de passe ne correspondent pas.")
    if not phone_number:
        errors.append("Le numéro de téléphone est requis.")
    if not terms:
        errors.append("Vous devez accepter les conditions d'utilisation.")
    if not data_processing:
        errors.append("Vous devez accepter le traitement des données.")

    # Vérifier unicité email
    existing = SellerShop.query.filter(
        or_(SellerShop.owner_email == email, SellerShop.support_email == email)
    ).first()
    if existing:
        errors.append("Cet email est déjà utilisé par une autre boutique.")

    existing_admin = SellerAdmin.query.filter_by(email=email).first()
    if existing_admin:
        errors.append("Cet email est déjà utilisé par un administrateur de boutique.")

    existing_platform_admin = PlatformAdmin.query.filter_by(email=email).first()
    if existing_platform_admin:
        errors.append("Cet email est déjà utilisé par un administrateur de la plateforme.")

    existing_portal_customer = PortalCustomer.query.filter_by(email=email).first()
    if existing_portal_customer:
        errors.append("Cet email est déjà utilisé par un client.")

    if errors:
        for err in errors:
            flash(err, "error")
        return redirect(url_for("portal.seller_register_page"))

    # Création de la boutique
    from werkzeug.security import generate_password_hash

    slug = _slugify(shop_name)
    # Vérifier unicité du slug
    existing_slug = SellerShop.query.filter_by(slug=slug).first()
    if existing_slug:
        i = 2
        while SellerShop.query.filter_by(slug=f"{slug}-{i}").first():
            i += 1
        slug = f"{slug}-{i}"

    shop = SellerShop(
        name=shop_name,
        slug=slug,
        owner_first_name=first_name,
        owner_last_name=last_name,
        owner_email=email,
        owner_password=generate_password_hash(password),
        country_code=country_code,
        phone_number=phone_number,
        address=address,
        category_niche=category_niche,
        description=shop_description,
        website=website,
        custom_domain=custom_domain,
        is_active=False,
        subscription_status="pending",
    )

    # Upload des documents
    id_file = request.files.get("id_document")
    address_file = request.files.get("address_proof")

    if id_file and id_file.filename:
        id_path = _save_uploaded_image(id_file, "seller_documents/id", seller_id=shop.seller_id)
        if id_path:
            shop.id_document_path = id_path

    if address_file and address_file.filename:
        address_path = _save_uploaded_image(address_file, "seller_documents/address", seller_id=shop.seller_id)
        if address_path:
            shop.address_document_path = address_path

    # Upload du logo
    logo_file = request.files.get("shop_logo")
    if logo_file and logo_file.filename:
        logo_path = _save_uploaded_image(logo_file, "seller/logos", seller_id=shop.seller_id)
        if logo_path:
            shop.logo_url = logo_path

    db.session.add(shop)
    db.session.commit()

    # Créer l'admin vendeur principal
    seller_admin = SellerAdmin(
        shop_id=shop.id,
        email=email,
        password=generate_password_hash(password),
        first_name=first_name,
        last_name=last_name,
        phone=phone_number,
        is_active=True,
        is_owner=True,
        permissions=",".join([
            "view_dashboard", "manage_products", "manage_orders",
            "manage_deliverers", "manage_clients", "manage_categories",
            "view_tasks", "manage_admins", "manage_settings", "view_about",
            "manage_access_requests",
        ]),
    )
    db.session.add(seller_admin)
    db.session.commit()

    record_activity(
        f"Nouvelle boutique créée: {shop_name} (slug: {slug})",
        extra=f"Email: {email}, Niches: {category_niche}"
    )

    # Envoyer email de confirmation
    try:
        body_html = f"""
        <p>Bonjour {first_name} {last_name},</p>
        <p>Votre demande d'inscription pour la boutique <strong>{shop_name}</strong> a bien été reçue.</p>
        <p>Notre équipe va examiner vos documents et valider votre inscription dans les plus brefs délais.</p>
        <p>Vous recevrez un email dès que votre boutique sera activée.</p>
        <p>Numéro de dossier: #{shop.id}</p>
        <p>Email de contact: {email}</p>
        """
        _send_email(
            to=email,
            subject="Confirmation d'inscription - Tekanayo",
            body=f"Votre inscription pour la boutique {shop_name} a bien été reçue.",
            html_body=_email_shell("Inscription reçue ✓", body_html, "Tekanayo App"),
        )
    except Exception:
        pass

    print(f"\n=== BOUTIQUE CRÉÉE AVEC SUCCÈS: ID={shop.id}, slug={slug} ===\n")
    return redirect(url_for("portal.seller_confirmation"))


@portal_bp.route("/portal/sellerconfirmation")
def seller_confirmation():
    return render_template("portal/seller_confirmation.html")


# ============================================================================
# ROUTES D'INSCRIPTION CLIENT PORTAIL
# ============================================================================


@portal_bp.route("/portal/register", methods=["GET"])
def portal_register_page():
    return render_template("portal/register.html", now=datetime.now())


@portal_bp.route("/portal/register/confirmation", methods=["GET"])
def portal_register_confirmation():
    return render_template("portal/portal_confirmation.html")


@portal_bp.route("/portal/register", methods=["POST"])
def portal_register():
    first_name = (request.form.get("first_name") or "").strip()
    last_name = (request.form.get("last_name") or "").strip()
    email = (request.form.get("email") or "").strip().lower()
    password = (request.form.get("password") or "").strip()
    confirm_password = (request.form.get("confirm_password") or "").strip()
    phone = (request.form.get("phone") or "").strip()
    country_code = (request.form.get("country_code") or "").strip().upper() or None
    phone_number = (request.form.get("phone_number") or "").strip() or None
    terms = request.form.get("terms")

    # Use new phone fields first, fallback to legacy
    if not phone_number:
        phone_number = phone

    errors = []
    if not first_name:
        errors.append("Le prénom est requis.")
    if not last_name:
        errors.append("Le nom est requis.")
    if not email:
        errors.append("L'email est requis.")
    if not password:
        errors.append("Le mot de passe est requis.")
    elif len(password) < 6:
        errors.append("Le mot de passe doit contenir au moins 6 caractères.")
    if password != confirm_password:
        errors.append("Les mots de passe ne correspondent pas.")
    if not terms:
        errors.append("Vous devez accepter les conditions d'utilisation.")

    existing = PortalCustomer.query.filter_by(email=email).first()
    if existing:
        errors.append("Cet email est déjà utilisé.")

    if errors:
        for err in errors:
            flash(err, "error")
        return redirect(url_for("portal.portal_register_page"))

    from werkzeug.security import generate_password_hash

    customer = PortalCustomer(
        first_name=first_name,
        last_name=last_name,
        email=email,
        password=generate_password_hash(password),
        phone=phone_number,
        country_code=country_code,
        is_active=True,
    )
    db.session.add(customer)
    db.session.commit()

    record_activity(
        f"Nouveau client portal: {first_name} {last_name} ({email})",
        extra=f"Téléphone: {phone_number}"
    )

    return redirect(url_for("portal.portal_register_confirmation"))


@portal_bp.route("/portal/confirmation")
def portal_confirmation():
    return render_template("portal/portal_confirmation.html")


# ============================================================================
# ROUTES DE CONNEXION / DÉCONNEXION PORTAIL
# ============================================================================


@portal_bp.route("/portal/login", methods=["POST"])
def portal_login():
    email = (request.form.get("email") or "").strip().lower()
    password = (request.form.get("password") or "").strip()

    if not email or not password:
        flash("Email et mot de passe requis.", "error")
        return redirect(url_for("portal.tekanayo_portal_page", page="login"))

    from werkzeug.security import check_password_hash

    customer = PortalCustomer.query.filter_by(email=email).first()
    if customer and customer.is_active and check_password_hash(customer.password, password):
        login_user(customer)
        session["portal_customer_id"] = customer.id
        record_activity(f"Connexion client portal: {email}")
        next_page = request.args.get("next") or url_for("portal.tekanayo_portal")
        return redirect(next_page)

    flash("Email ou mot de passe incorrect.", "error")
    return redirect(url_for("portal.tekanayo_portal_page", page="login"))


@portal_bp.route("/portal/logout")
def portal_logout():
    session.pop("portal_customer_id", None)
    logout_user()
    return redirect(url_for("portal.tekanayo_portal"))


# ============================================================================
# ROUTES PROFIL CLIENT PORTAIL
# ============================================================================


@portal_bp.route("/portal/profile", methods=["GET", "POST"])
@login_required
def portal_profile():
    if not isinstance(current_user, PortalCustomer):
        flash("Accès réservé aux clients.", "error")
        return redirect(url_for("portal.tekanayo_portal"))

    if request.method == "POST":
        first_name = (request.form.get("first_name") or "").strip()
        last_name = (request.form.get("last_name") or "").strip()
        phone = (request.form.get("phone") or "").strip()
        address = (request.form.get("address") or "").strip()

        if first_name:
            current_user.first_name = first_name
        if last_name:
            current_user.last_name = last_name
        if phone:
            current_user.phone = phone
        if address:
            current_user.address = address

        db.session.commit()
        flash("Profil mis à jour.", "success")
        return redirect(url_for("portal.portal_profile"))

    shop, view = _portal_shop_context()
    return render_template("portal/profile.html", shop=shop, **view)


# ============================================================================
# ROUTES PANIER PORTAIL
# ============================================================================


@portal_bp.route("/portal/cart/add", methods=["POST"])
def portal_cart_add():
    shop = _portal_shop()
    if not shop:
        flash("Aucune boutique active.", "error")
        return redirect(url_for("portal.tekanayo_portal"))

    product_id = request.form.get("product_id")
    quantity = request.form.get("quantity", 1)

    try:
        product_id = int(product_id)
        quantity = int(quantity)
    except (TypeError, ValueError):
        flash("Produit invalide.", "error")
        return redirect(request.referrer or url_for("portal.tekanayo_portal"))

    product = SellerProduct.query.filter_by(id=product_id, shop_id=shop.id, is_active=True).first()
    if not product:
        flash("Produit introuvable.", "error")
        return redirect(request.referrer or url_for("portal.tekanayo_portal"))

    cart = _get_shop_cart(shop.id)
    found = False
    for item in cart:
        if item["product_id"] == product_id:
            item["quantity"] = min(item["quantity"] + quantity, max(product.quantity, 1))
            found = True
            break
    if not found:
        cart.append({"product_id": product_id, "quantity": min(quantity, max(product.quantity, 1))})

    _set_shop_cart(shop.id, cart)
    flash(f"{product.name} ajouté au panier.", "success")
    return redirect(request.referrer or url_for("portal.tekanayo_portal"))


@portal_bp.route("/portal/cart/update", methods=["POST"])
def portal_cart_update():
    shop = _portal_shop()
    if not shop:
        return redirect(url_for("portal.tekanayo_portal"))

    product_id = request.form.get("product_id")
    quantity = request.form.get("quantity", 1)

    try:
        product_id = int(product_id)
        quantity = int(quantity)
    except (TypeError, ValueError):
        return redirect(url_for("portal.tekanayo_portal_page", page="cart"))

    cart = _get_shop_cart(shop.id)
    for item in cart:
        if item["product_id"] == product_id:
            if quantity <= 0:
                cart = [i for i in cart if i["product_id"] != product_id]
            else:
                item["quantity"] = quantity
            break

    _set_shop_cart(shop.id, cart)
    return redirect(url_for("portal.tekanayo_portal_page", page="cart"))


@portal_bp.route("/portal/cart/remove", methods=["POST"])
def portal_cart_remove():
    shop = _portal_shop()
    if not shop:
        return redirect(url_for("portal.tekanayo_portal"))

    product_id = request.form.get("product_id")
    try:
        product_id = int(product_id)
    except (TypeError, ValueError):
        return redirect(url_for("portal.tekanayo_portal_page", page="cart"))

    cart = _get_shop_cart(shop.id)
    cart = [i for i in cart if i["product_id"] != product_id]
    _set_shop_cart(shop.id, cart)
    return redirect(url_for("portal.tekanayo_portal_page", page="cart"))


# ============================================================================
# ROUTES COMMANDES PORTAIL
# ============================================================================


@portal_bp.route("/portal/checkout", methods=["POST"])
def portal_checkout():
    shop = _portal_shop()
    if not shop:
        flash("Aucune boutique active.", "error")
        return redirect(url_for("portal.tekanayo_portal"))

    cart = _get_shop_cart(shop.id)
    if not cart:
        flash("Votre panier est vide.", "error")
        return redirect(url_for("portal.tekanayo_portal_page", page="cart"))

    # Récupérer ou créer le client
    customer_name = (request.form.get("customer_name") or "").strip()
    customer_email = (request.form.get("customer_email") or "").strip().lower()
    customer_phone = (request.form.get("customer_phone") or "").strip()
    customer_address = (request.form.get("customer_address") or "").strip()
    notes = (request.form.get("notes") or "").strip()

    if not customer_name or not customer_email:
        flash("Nom et email du client requis.", "error")
        return redirect(url_for("portal.tekanayo_portal_page", page="checkout"))

    # Chercher ou créer le client dans la boutique
    customer = SellerCustomer.query.filter_by(shop_id=shop.id, email=customer_email).first()
    if not customer:
        customer = SellerCustomer(
            shop_id=shop.id,
            name=customer_name,
            email=customer_email,
            phone=customer_phone,
            address=customer_address,
        )
        db.session.add(customer)
        db.session.commit()

    # Calculer le total
    total = 0.0
    product_ids = [item["product_id"] for item in cart]
    products = SellerProduct.query.filter(SellerProduct.id.in_(product_ids), SellerProduct.shop_id == shop.id).all()
    product_map = {p.id: p for p in products}

    for item in cart:
        product = product_map.get(item["product_id"])
        if product:
            total += float(product.price or 0.0) * item["quantity"]

    # Créer la commande
    order = SellerOrder(
        shop_id=shop.id,
        customer_id=customer.id,
        customer_name=customer_name,
        customer_email=customer_email,
        customer_phone=customer_phone,
        customer_address=customer_address,
        total_amount=total,
        status="pending",
        notes=notes,
    )
    db.session.add(order)
    db.session.commit()

    # Vider le panier
    _set_shop_cart(shop.id, [])

    record_activity(
        f"Nouvelle commande #{order.id} - {customer_name} ({customer_email})",
        extra=f"Montant: {total:.2f} USD, Boutique: {shop.name}"
    )

    return redirect(url_for("portal.tekanayo_portal_page", page="order_confirmation", order_id=order.id))


@portal_bp.route("/portal/orders")
@login_required
def portal_orders():
    if not isinstance(current_user, PortalCustomer):
        flash("Accès réservé aux clients.", "error")
        return redirect(url_for("portal.tekanayo_portal"))

    shop, view = _portal_shop_context()
    return render_template("portal/orders.html", shop=shop, **view)


@portal_bp.route("/portal/order/<int:order_id>")
@login_required
def portal_order_detail(order_id):
    if not isinstance(current_user, PortalCustomer):
        flash("Accès réservé aux clients.", "error")
        return redirect(url_for("portal.tekanayo_portal"))

    shop, view = _portal_shop_context()
    order = SellerOrder.query.filter_by(id=order_id, customer_email=current_user.email).first_or_404()
    view["selected_order"] = order
    return render_template("portal/order_detail.html", shop=shop, **view)


# ============================================================================
# ROUTES PRODUIT DÉTAIL PORTAIL
# ============================================================================


@portal_bp.route("/portal/product/<int:product_id>")
def portal_product_detail(product_id):
    shop, view = _portal_shop_context()
    product = SellerProduct.query.filter_by(id=product_id, is_active=True).first()
    if not product:
        flash("Produit introuvable.", "error")
        return redirect(url_for("portal.tekanayo_portal"))
    view["selected_product"] = product
    return render_template("portal/product_detail.html", shop=shop, **view)


# ============================================================================
# ROUTES FORUM PORTAIL
# ============================================================================


@portal_bp.route("/portal/forum")
def portal_forum():
    shop, view = _portal_shop_context()
    return render_template("portal/forum.html", shop=shop, **view)


# ============================================================================
# ROUTES RÉINITIALISATION MOT DE PASSE PORTAIL
# ============================================================================


@portal_bp.route("/portal/reset-request", methods=["GET", "POST"])
def portal_reset_request():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        if not email:
            flash("Email requis.", "error")
            return redirect(url_for("portal.portal_reset_request"))

        customer = PortalCustomer.query.filter_by(email=email).first()
        if customer:
            from backend.helpers import _generate_reset_token
            token = _generate_reset_token(current_app._get_current_object(), "portal_customer", customer.id)
            reset_url = url_for("portal.portal_reset_password", token=token, _external=True)
            try:
                body_html = f"""
                <p>Bonjour {customer.first_name},</p>
                <p>Vous avez demandé la réinitialisation de votre mot de passe.</p>
                <p><a href="{reset_url}" style="display:inline-block;padding:12px 24px;background:#0f766e;color:#fff;text-decoration:none;border-radius:6px;">Réinitialiser mon mot de passe</a></p>
                <p>Ce lien expire dans 1 heure.</p>
                """
                _send_email(
                    to=email,
                    subject="Réinitialisation mot de passe - Tekanayo",
                    body=f"Cliquez sur ce lien pour réinitialiser votre mot de passe: {reset_url}",
                    html_body=_email_shell("Réinitialisation mot de passe", body_html, "Tekanayo App"),
                )
            except Exception:
                pass

        flash("Si cet email existe, un lien de réinitialisation a été envoyé.", "success")
        return redirect(url_for("portal.tekanayo_portal_page", page="login"))

    shop, view = _portal_shop_context()
    return render_template("portal/reset_request.html", shop=shop, **view)


@portal_bp.route("/portal/reset-password/<token>", methods=["GET", "POST"])
def portal_reset_password(token):
    from backend.helpers import _verify_reset_token
    payload = _verify_reset_token(current_app._get_current_object(), token)
    if not payload or payload.get("role") != "portal_customer":
        flash("Lien invalide ou expiré.", "error")
        return redirect(url_for("portal.tekanayo_portal_page", page="login"))

    customer = PortalCustomer.query.get(payload["id"])
    if not customer:
        flash("Compte introuvable.", "error")
        return redirect(url_for("portal.tekanayo_portal_page", page="login"))

    if request.method == "POST":
        password = (request.form.get("password") or "").strip()
        confirm = (request.form.get("confirm_password") or "").strip()

        if not password or len(password) < 6:
            flash("Le mot de passe doit contenir au moins 6 caractères.", "error")
            return redirect(request.url)

        if password != confirm:
            flash("Les mots de passe ne correspondent pas.", "error")
            return redirect(request.url)

        from werkzeug.security import generate_password_hash
        customer.password = generate_password_hash(password)
        db.session.commit()
        flash("Mot de passe réinitialisé avec succès.", "success")
        return redirect(url_for("portal.tekanayo_portal_page", page="login"))

    shop, view = _portal_shop_context()
    return render_template("portal/reset_password.html", shop=shop, **view, token=token)

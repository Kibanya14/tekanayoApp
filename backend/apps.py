import os
import re
import secrets
from datetime import datetime, timedelta
from functools import wraps

from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for, send_file, send_from_directory
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from flask_mail import Mail, Message
from flask_migrate import Migrate
from sqlalchemy import or_
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from werkzeug.utils import secure_filename

from backend.models import (
    PlatformAccessRequest,
    PlatformAdmin,
    PlatformActivityLog,
    PlatformAnnouncement,
    PlatformDeliverer,
    PlatformSettings,
    PortalCustomer,
    SellerAdmin,
    SellerCustomer,
    SellerDeliverer,
    SellerOrder,
    SellerProduct,
    SellerShop,
    SellerSubscription,
    SellerPayment,
    SellerPaymentTask,
    AdminNotification,
    db,
)
from backend.utils.invoice_generator import generate_seller_invoice_pdf
from countries import Countries, FlaskCountries

# legacy/demo helper -- replaced by the main ``create_app`` below
# (kept only for reference; the real factory is defined later in this file).
# def create_app():
#     """Create and configure the Flask application"""
#     app = Flask(__name__)
#
#     # Configuration de base
#     app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
#     app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///tekanayo.db')
#     app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
#     app.config['UPLOAD_FOLDER'] = 'uploads'
#     app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
#
#     # Configuration email
#     app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
#     app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
#     app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
#     app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
#     app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
#     app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', app.config['MAIL_USERNAME'])
#
#     # Initialiser les extensions
#     db.init_app(app)
#     mail.init_app(app)
#     migrate = Migrate(app, db)
#
#     # Initialiser Flask Countries
#     countries_ext = FlaskCountries(app)
#
#     # Initialiser les routes Flask Countries
#     from backend.countries_routes import init_flask_countries_routes
#     init_flask_countries_routes(app)
#
#     return app
#

mail = Mail()

# ============================================================================
# CATÉGORIES ET NICHES DE BOUTIQUES
# Chaque niche a ses propres icônes FontAwesome pour les catégories de produits
# Le vendeur ne verra que les icônes de sa niche lors de l'ajout de produits
# ============================================================================

CATEGORY_NICHES = {
    # Boutique générale / Divers
    "shopdivers": [
        "fa-store", "fa-gift", "fa-basket-shopping", "fa-box-open", "fa-bag-shopping",
        "fa-cart-shopping", "fa-handshake", "fa-tags", "fa-shop", "fa-cart-plus",
        "fa-bag-shopping", "fa-barcode", "fa-receipt", "fa-wallet", "fa-credit-card"
    ],
    
    # Alimentation générale
    "allimentation": [
        "fa-apple-whole", "fa-carrot", "fa-bowl-food", "fa-fish", "fa-drumstick-bite",
        "fa-cheese", "fa-bacon", "fa-egg", "fa-lemon", "fa-pepper-hot",
        "fa-wheat-awn", "fa-jar", "fa-bottle-water", "fa-can-food", "fa-box-tissue"
    ],
    
    # Restaurant et restauration rapide
    "restaurant": [
        "fa-utensils", "fa-mug-hot", "fa-pizza-slice", "fa-burger", "fa-hotdog",
        "fa-ice-cream", "fa-cookie", "fa-wine-glass", "fa-martini-glass", "fa-beer-mug",
        "fa-fork-knife", "fa-blender", "fa-cake-candles", "fa-donut", "fa-sandwich"
    ],
    
    # Maison et habillement
    "maison_habillement": [
        "fa-shirt", "fa-vest", "fa-socks", "fa-person-dress", "fa-user-tie",
        "fa-hat-cowboy", "fa-glasses", "fa-ring", "fa-gem", "fa-crown",
        "fa-shirt", "fa-person-dress", "fa-person", "fa-vest-patches", "fa-scarf"
    ],
    
    # Pharmacie et soins
    "pharmacie_soin": [
        "fa-briefcase-medical", "fa-pills", "fa-heart-pulse", "fa-prescription-bottle-medical",
        "fa-syringe", "fa-vial", "fa-bandage", "fa-stethoscope", "fa-user-doctor",
        "fa-hospital", "fa-kit-medical", "fa-pump-medical", "fa-mortar-pestle", "fa-flask",
        "fa-jar", "fa-pump-soap", "fa-hands-bubbles", "fa-tooth", "fa-eye"
    ],
    
    # Boulangerie et pâtisserie
    "boulangerie": [
        "fa-bread-slice", "fa-cookie", "fa-cake-candles", "fa-mug-saucer", "fa-croissant",
        "fa-baguette", "fa-pie", "fa-candy-cane", "fa-ice-cream", "fa-donut",
        "fa-cookie-bite", "fa-cheese", "fa-egg", "fa-wheat-awn", "fa-jar"
    ],
    
    # Location de voitures
    "locations_voiture": [
        "fa-car", "fa-gas-pump", "fa-road", "fa-key", "fa-car-side",
        "fa-truck", "fa-motorcycle", "fa-bus", "fa-van-shuttle", "fa-plane",
        "fa-taxi", "fa-tractor", "fa-truck-pickup", "fa-shuttle-space", "fa-car-rear"
    ],
    
    # Location de chambres
    "location_chambre": [
        "fa-bed", "fa-door-open", "fa-key", "fa-hotel", "fa-suitcase",
        "fa-bell-concierge", "fa-elevator", "fa-person-booth", "fa-door-closed", "fa-couch",
        "fa-tv", "fa-wifi", "fa-snowflake", "fa-fan", "fa-bath"
    ],
    
    # Location de maisons
    "location_maison": [
        "fa-house", "fa-couch", "fa-shower", "fa-map-location-dot", "fa-kitchen-set",
        "fa-tv", "fa-wifi", "fa-snowflake", "fa-fan", "fa-bath",
        "fa-toilet", "fa-sink", "fa-chair", "fa-lightbulb", "fa-door-open"
    ],
    
    # Vente de maisons / Immobilier
    "vente_maison": [
        "fa-house-circle-check", "fa-city", "fa-building", "fa-handshake", "fa-house-chimney",
        "fa-building-columns", "fa-hotel", "fa-house-lock", "fa-house-flag", "fa-landmark",
        "fa-map-location", "fa-sign-hanging", "fa-key", "fa-file-contract", "fa-pen-ruler"
    ],
    
    # Livres et éducation
    "livres": [
        "fa-book", "fa-book-open", "fa-graduation-cap", "fa-pen", "fa-pencil",
        "fa-bookmark", "fa-library", "fa-chalkboard", "fa-ruler", "fa-calculator",
        "fa-laptop", "fa-book-journal-whills", "fa-scroll", "fa-feather", "fa-award"
    ],
    
    # Électronique et technologie
    "electronique": [
        "fa-laptop", "fa-mobile-screen", "fa-headphones", "fa-keyboard", "fa-mouse",
        "fa-tv", "fa-camera", "fa-watch", "fa-battery-full", "fa-plug",
        "fa-wifi", "fa-bluetooth", "fa-hard-drive", "fa-memory", "fa-microchip"
    ],
    
    # Mode et vêtements
    "mode": [
        "fa-shirt", "fa-person-dress", "fa-shoe-prints", "fa-hat-cowboy", "fa-glasses",
        "fa-ring", "fa-gem", "fa-crown", "fa-vest", "fa-socks",
        "fa-user-tie", "fa-person-dress", "fa-person", "fa-scarf", "fa-mitten"
    ],
    
    # Maison et jardin
    "maison": [
        "fa-couch", "fa-lightbulb", "fa-sink", "fa-toilet", "fa-shower",
        "fa-tree", "fa-leaf", "fa-seedling", "fa-faucet", "fa-broom",
        "fa-spray-can", "fa-plug", "fa-door-open", "fa-window-maximize", "fa-blender"
    ],
    
    # Sport et loisirs
    "sport": [
        "fa-futbol", "fa-basketball", "fa-volleyball", "fa-baseball-bat-ball", "fa-tennis-ball",
        "fa-bicycle", "fa-person-running", "fa-person-swimming", "fa-dumbbell", "fa-trophy",
        "fa-medal", "fa-whistle", "fa-stopwatch", "fa-person-skiing", "fa-person-snowboarding"
    ],
    
    # Beauté et santé
    "beaute": [
        "fa-spa", "fa-hands-bubbles", "fa-spray-can", "fa-scissors", "fa-brush",
        "fa-mirror", "fa-pump-soap", "fa-bath", "fa-jar", "fa-flask",
        "fa-heart-pulse", "fa-weight-scale", "fa-person-running", "fa-apple-whole", "fa-syringe"
    ],
    
    # Autres catégories
    "autres": [
        "fa-box-open", "fa-gift", "fa-tags", "fa-shop", "fa-cart-shopping",
        "fa-handshake", "fa-star", "fa-thumbs-up", "fa-check", "fa-plus",
        "fa-circle-question", "fa-circle-info", "fa-circle-exclamation", "fa-bell", "fa-envelope"
    ]
}

# Liste des niches pour le formulaire d'enregistrement
NICHE_CHOICES = [
    ("shopdivers", "Boutique générale / Divers"),
    ("allimentation", "Alimentation générale"),
    ("restaurant", "Restaurant / Restauration"),
    ("maison_habillement", "Maison / Habillement"),
    ("pharmacie_soin", "Pharmacie / Soins"),
    ("boulangerie", "Boulangerie / Pâtisserie"),
    ("locations_voiture", "Location de voitures"),
    ("location_chambre", "Location de chambres"),
    ("location_maison", "Location de maisons"),
    ("vente_maison", "Vente de maisons / Immobilier"),
    ("livres", "Livres / Éducation"),
    ("electronique", "Électronique / Technologie"),
    ("mode", "Mode / Vêtements"),
    ("maison", "Maison / Jardin"),
    ("sport", "Sport / Loisirs"),
    ("beaute", "Beauté / Santé"),
    ("autres", "Autres"),
]

INVOICE_THEMES = {
    "classic": "Classique pro",
    "modern": "Moderne",
    "minimal": "Minimal",
    "bold": "Bold business",
}

ADMIN_PERMISSION_LABELS = {
    "manage_products": "Gérer produits",
    "manage_orders": "Gérer commandes",
    "manage_deliverers": "Gérer livreurs",
    "manage_clients": "Gérer clients",
    "manage_categories": "Gérer catégories",
    "view_tasks": "Voir tâches",
    "manage_sellers": "Gérer vendeurs",
    "manage_subscriptions": "Gérer abonnements",
    "manage_announcements": "Gérer annonces",
    "manage_admins": "Gérer admins",
    "manage_settings": "Gérer paramètres",
}

SELLER_PERMISSION_LABELS = {
    "view_dashboard": "Voir tableau de bord",
    "manage_products": "Gérer produits",
    "manage_orders": "Gérer commandes",
    "manage_deliverers": "Gérer livreurs",
    "manage_clients": "Gérer clients",
    "manage_categories": "Gérer catégories",
    "view_tasks": "Voir tâches",
    "manage_admins": "Gérer administrateurs",
    "manage_settings": "Gérer paramètres",
    "view_about": "Voir à propos",
    "manage_access_requests": "Traiter demandes d'accès",
}


def _slugify(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "-", (value or "").strip().lower()).strip("-")
    return value or f"shop-{secrets.token_hex(2)}"


def _unique_slug(base: str) -> str:
    slug = base
    i = 2
    while SellerShop.query.filter_by(slug=slug).first():
        slug = f"{base}-{i}"
        i += 1
    return slug


def _email_shell(title: str, body_html: str, brand: str, accent: str = "#0f766e"):
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
    try:
        msg = Message(subject=subject, sender=os.getenv("MAIL_DEFAULT_SENDER"), recipients=[to])
        msg.body = body
        msg.html = html_body or _email_shell(subject, body.replace("\n", "<br>"), "Tekanayo App")
        mail.send(msg)
        return True
    except Exception:
        return False


def _safe_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return float(default)


def _generate_temp_password(length: int = 10) -> str:
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789"
    return "".join(secrets.choice(alphabet) for _ in range(max(8, length)))


def create_app():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app = Flask(
        __name__,
        template_folder=os.path.join(root, "frontend", "templates"),
        static_folder=os.path.join(root, "frontend", "static"),
        static_url_path="/static"
    )

    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "change-this-secret")
    db_path = os.path.join(root, "database.db")
    try:
        with open(db_path, "a", encoding="utf-8"):
            pass
    except Exception:
        pass
    database_url = os.getenv("DATABASE_URL")
    if database_url and database_url.startswith("sqlite:///") and not database_url.startswith("sqlite:////"):
        sqlite_target = database_url.replace("sqlite:///", "", 1)
        if sqlite_target and not os.path.isabs(sqlite_target):
            database_url = f"sqlite:///{os.path.join(root, sqlite_target)}"
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url or f"sqlite:///{db_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    app.config["MAIL_PORT"] = int(os.getenv("MAIL_PORT", "587"))
    app.config["MAIL_USE_TLS"] = os.getenv("MAIL_USE_TLS", "True").lower() == "true"
    app.config["MAIL_USE_SSL"] = os.getenv("MAIL_USE_SSL", "False").lower() == "true"
    app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
    app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
    app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_DEFAULT_SENDER", os.getenv("MAIL_USERNAME"))
    app.config["MAIL_SUPPRESS_SEND"] = os.getenv("MAIL_SUPPRESS_SEND", "False").lower() == "true"
    app.config["UPLOAD_ROOT"] = os.path.join(root, "uploads")

    db.init_app(app)
    mail.init_app(app)
    Migrate(app, db)

    from flask_wtf.csrf import CSRFProtect
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address

    csrf = CSRFProtect(app)
    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=["200 per day", "50 per hour"],
        storage_uri="memory://",
    )

    # ---- flask-countries support -----------------------------------------
    # register the extension so template globals (countries_for_select, etc.)
    countries_ext = FlaskCountries(app)

    os.makedirs(app.config["UPLOAD_ROOT"], exist_ok=True)

    ALLOWED_UPLOAD_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}

    def _save_uploaded_image(file_storage, bucket: str) -> str | None:
        if not file_storage or not getattr(file_storage, "filename", None):
            return None
        filename = secure_filename(file_storage.filename or "")
        if not filename or "." not in filename:
            return None
        ext = filename.rsplit(".", 1)[1].lower()
        if ext not in ALLOWED_UPLOAD_EXTENSIONS:
            return None
        folder = os.path.join(app.config["UPLOAD_ROOT"], bucket)
        os.makedirs(folder, exist_ok=True)
        final_name = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{secrets.token_hex(4)}.{ext}"
        abs_path = os.path.join(folder, final_name)
        file_storage.save(abs_path)
        return f"/uploads/{bucket}/{final_name}"


    # Schema changes are managed only through Flask-Migrate (Alembic).


    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "admin_login_page"

    @login_manager.user_loader
    def load_user(user_id):
        # Try PlatformAdmin first (for admin panel)
        admin = PlatformAdmin.query.get(int(user_id))
        if admin:
            return admin
        # Try PortalCustomer (for portal)
        return PortalCustomer.query.get(int(user_id))

    def _get_platform_settings():
        settings = PlatformSettings.query.first()
        if settings:
            return settings
        settings = PlatformSettings(
            exchange_rate_usd_cdf=_safe_float(os.getenv("EXCHANGE_RATE_USD_CDF"), 2800.0),
        )
        db.session.add(settings)
        db.session.commit()
        return settings

    def _geocode_address(address: str):
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

    def _resolve_shop_identifier(identifier: str):
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
        if not shop:
            return ""
        custom = (shop.custom_domain or "").strip().lower()
        if custom:
            return custom
        return f"{shop.slug}-{shop.id}"

    def _resolve_shop_access_key(access_key: str):
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

    @app.before_request
    def _canonical_shop_urls():
        # Keep universal entries (/vendeur, /livreur, /admin) as-is; canonicalize only legacy /boutique/<slug> GET links.
        if request.method != "GET":
            return None
        path = request.path or ""
        if not path.startswith("/boutique/"):
            return None
        tail = path[len("/boutique/"):]
        if not tail:
            return None
        slug = tail.split("/", 1)[0].strip()
        if not slug:
            return None
        shop = _resolve_shop_identifier(slug)
        if not shop:
            return None
        suffix = tail[len(slug):]  # "" or "/about", "/products", etc.
        target = f"/{_shop_access_key(shop)}{suffix}"
        qs = request.query_string.decode("utf-8", errors="ignore")
        if qs:
            target = f"{target}?{qs}"
        return redirect(target, code=302)

    def _shop_cart_key(shop_id: int) -> str:
        return f"seller_cart_{int(shop_id)}"

    def _get_shop_cart(shop_id: int):
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
        session[_shop_cart_key(shop_id)] = items
        session.modified = True

    def _get_shop_customer(shop_id: int):
        # First, check if there's a SellerCustomer logged in via shop session
        data = session.get("shop_customer_sessions", {})
        if isinstance(data, dict):
            cid = data.get(str(shop_id))
            if cid:
                try:
                    return SellerCustomer.query.filter_by(id=int(cid), shop_id=shop_id).first()
                except Exception:
                    pass
        # Fallback: if a PortalCustomer is logged in via Flask-Login, return it
        # so the navbar shows the connected state
        if current_user.is_authenticated and hasattr(current_user, '_sa_instance_state'):
            from backend.models import PortalCustomer
            if isinstance(current_user, PortalCustomer):
                return current_user
        return None

    def _set_shop_customer(shop_id: int, customer_id: int | None):
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

    def _build_shop_page_context(shop, selected_category=None, search_term=None, selected_product_id=None):
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

    def _serializer():
        return URLSafeTimedSerializer(app.config["SECRET_KEY"])

    @app.route("/uploads/<path:filename>")
    def uploaded_file(filename):
        """
        Serve files from Supabase Storage with proper access control.
        - Public files (public/*) : accessible to everyone
        - Semi-private files (semi_private/*) : accessible to authenticated users only
        - Private files (private/*) : accessible to admins only
        """
        try:
            from backend.supabase_storage import storage_client
            
            # Déterminer le type de fichier selon le chemin
            path_parts = filename.split('/')
            
            if not path_parts or not filename:
                return "File not found", 404
            
            # Cas 1 : Fichiers publics (public/*)
            if path_parts[0] == 'public':
                # Générer l'URL publique
                public_url = storage_client.get_public_url(filename)
                return redirect(public_url)
            
            # Cas 2 : Fichiers semi-privés (semi_private/*)
            elif path_parts[0] == 'semi_private':
                if not current_user.is_authenticated:
                    return "Unauthorized", 401
                signed_url = storage_client.get_signed_url(filename, expires_in=3600)
                return redirect(signed_url) if signed_url else ("Access denied", 403)
            
            # Cas 3 : Fichiers privés (private/*)
            elif path_parts[0] == 'private':
                # Vérifier que c'est un admin avec les bonnes permissions
                if not current_user.is_authenticated:
                    return "Unauthorized", 401
                
                admin = PlatformAdmin.query.filter_by(id=current_user.id).first()
                if not admin or 'manage_sellers' not in (admin.permissions or ''):
                    return "Forbidden", 403
                
                signed_url = storage_client.get_signed_url(filename, expires_in=3600)
                return redirect(signed_url) if signed_url else ("Access denied", 403)
            
            else:
                return "File not found", 404
        
        except Exception as e:
            app.logger.error(f"File serve error: {str(e)}")
            return "Server error", 500

    def _generate_reset_token(role: str, record_id: int):
        return _serializer().dumps({"role": role, "id": int(record_id)}, salt="tekanayo-reset")

    def _verify_reset_token(token: str, max_age: int = 3600):
        try:
            payload = _serializer().loads(token, salt="tekanayo-reset", max_age=max_age)
            if isinstance(payload, dict):
                return payload
            return None
        except (SignatureExpired, BadSignature):
            return None

    def admin_required(permission=None):
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

    @app.context_processor
    def inject_refs():
        settings = _get_platform_settings()
        digits = "".join(ch for ch in (settings.whatsapp_number or "") if ch.isdigit())
        whatsapp_link = settings.whatsapp_url or (f"https://wa.me/{digits}" if digits else None)
        telegram_link = settings.telegram_url
        if not telegram_link and settings.telegram_username:
            telegram_link = f"https://t.me/{settings.telegram_username.lstrip('@')}"

        selected_currency = (session.get("selected_currency") or settings.default_currency or "USD").upper()
        if selected_currency not in {"USD", "CDF"}:
            selected_currency = "USD"

        def convert_amount(amount, from_currency="USD", to_currency="CDF"):
            rate = _safe_float(settings.exchange_rate_usd_cdf, 2800.0) or 2800.0
            value = _safe_float(amount, 0.0)
            f = (from_currency or "USD").upper()
            t = (to_currency or "CDF").upper()
            if f == t:
                return value
            if f == "USD" and t == "CDF":
                return value * rate
            if f == "CDF" and t == "USD":
                return value / rate if rate else value
            return value

        def display_amount(amount, source_currency="USD"):
            converted = convert_amount(amount, source_currency, selected_currency)
            return converted, selected_currency

        def media_url(path: str | None):
            value = (path or "").strip()
            if not value:
                return url_for("uploaded_file", filename="default_logo.svg")
            if value.startswith("http://") or value.startswith("https://"):
                return value
            # Normalize stored upload paths like /uploads/... or uploads/...
            if value.startswith("/uploads/"):
                value = value[len("/uploads/"):]
            elif value.startswith("uploads/"):
                value = value[len("uploads/"):]
            return url_for("uploaded_file", filename=value.lstrip("/"))

        def convert_price(amount, from_currency="USD", to_currency=None):
            target_currency = (to_currency or selected_currency or "USD").upper()
            converted = convert_amount(amount, from_currency, target_currency)
            currency = target_currency
            symbol = "$" if currency == "USD" else "FC"
            return f"{symbol} {converted:,.2f}"

        def get_first_image_url(product):
            if not product:
                return ""
            candidate = ""
            for attr in ("image", "image_url", "photo"):
                value = getattr(product, attr, None)
                if isinstance(value, str) and value.strip():
                    candidate = value.strip()
                    break
            if not candidate:
                images = getattr(product, "images", None)
                if isinstance(images, list) and images:
                    candidate = str(images[0]).strip()
                elif isinstance(images, str) and images.strip():
                    candidate = images.split(",")[0].strip()
            if not candidate:
                return ""
            if candidate.startswith("http://") or candidate.startswith("https://"):
                return candidate
            cleaned = candidate.lstrip("/")
            if cleaned.startswith("uploads/"):
                return media_url(cleaned)
            return media_url(f"uploads/products/{cleaned}")

        def status_fr(status: str, kind: str = None) -> str:
            if not status:
                return ""
            value = str(status)
            common = {
                "pending": "En attente",
                "confirmed": "Confirmée",
                "shipped": "Expédiée",
                "delivered": "Livrée",
                "cancelled": "Annulée",
                "assigned": "Assignée",
                "in_progress": "En cours",
                "postponed": "Reportée",
                "busy": "Occupé",
                "available": "Disponible",
                "offline": "Hors ligne",
                "paid": "Payée",
                "failed": "Échouée",
            }
            mapping = common
            if kind == "assignment":
                mapping = {k: v for k, v in common.items() if k in {"assigned", "in_progress", "delivered", "postponed", "cancelled"}}
            elif kind == "deliverer":
                mapping = {k: v for k, v in common.items() if k in {"available", "busy", "offline"}}
            return mapping.get(value, value)

        return {
            "niches": CATEGORY_NICHES,
            "invoice_themes": INVOICE_THEMES,
            "admin_permission_labels": ADMIN_PERMISSION_LABELS,
            "platform_settings": settings,
            "whatsapp_link": whatsapp_link,
            "telegram_link": telegram_link,
            "convert_amount": convert_amount,
            "display_amount": display_amount,
            "selected_currency": selected_currency,
            "current_currency": selected_currency,
            "available_currencies": ["USD", "CDF"],
            "current_year": datetime.utcnow().year,
            "media_url": media_url,
            "base_currency": "USD",
            "convert_price": convert_price,
            "get_first_image_url": get_first_image_url,
            "status_fr": status_fr,
            "shop_ref": _shop_access_key,
        }

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

    @app.route("/")
    @app.route("/portal")
    def tekanayo_portal():
        shop, view = _portal_shop_context()
        return render_template("portal/portal.html", shop=shop, **view)

    @app.route("/about")
    @app.route("/portal/about")
    def about():
        # always render the about page; don't redirect when no shop is active
        shop, view = _portal_shop_context()
        # shop may be None, but templates expect view dict with defaults
        return render_template("portal/about.html", shop=shop, **(view or {}))

    @app.route("/portal/categories")
    def tekanayo_portal_categories():
        shop, view = _portal_shop_context()
        return render_template("portal/categories.html", shop=shop, **view)

    @app.route("/portal/products")
    def tekanayo_portal_products():
        shop, view = _portal_shop_context()
        return render_template("portal/products.html", shop=shop, **view)

    @app.route("/portal/legal")
    def tekanayo_portal_legal():
        shop, view = _portal_shop_context()
        return render_template("portal/legal.html", shop=shop, **view)

    @app.route("/portal/terms")
    def tekanayo_portal_terms():
        shop, view = _portal_shop_context()
        return render_template("portal/terms.html", shop=shop, **view)

    @app.route("/portal/returns")
    def tekanayo_portal_returns():
        shop, view = _portal_shop_context()
        return render_template("portal/returns.html", shop=shop, **view)

    @app.route("/portal/privacy")
    def tekanayo_portal_privacy():
        shop, view = _portal_shop_context()
        return render_template("portal/privacy.html", shop=shop, **view)

    @app.route("/portal/<page>")
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
            return redirect(url_for("tekanayo_portal"))
        shop, view = _portal_shop_context()
        return render_template(tpl, shop=shop, **view)

    @app.route("/set-currency", methods=["POST"])
    def set_currency():
        code = (request.form.get("currency") or "").strip().upper()
        if code in {"USD", "CDF"}:
            session["selected_currency"] = code
        return redirect(request.referrer or url_for("tekanayo_portal"))

    @app.route("/api/check-email")
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

    @app.route("/api/check-shop-name")
    def check_shop_name_availability():
        name = request.args.get("name", "").strip()
        if not name:
            return jsonify({"available": False, "error": "Nom de boutique requis"})

        existing_shop = SellerShop.query.filter(
            SellerShop.name.ilike(name) | SellerShop.slug.ilike(_slugify(name))
        ).first()

        available = existing_shop is None
        return jsonify({"available": available})

    @app.route("/api/check-custom-domain")
    def check_custom_domain_availability():
        domain = (request.args.get("domain") or "").strip().lower()
        if not domain:
            return jsonify({"available": True})

        existing_domain = SellerShop.query.filter_by(custom_domain=domain).first()
        return jsonify({"available": existing_domain is None})

    # ===== FLASK COUNTRIES DEMO ROUTES =====
    @app.route("/countries-demo")
    def countries_demo():
        """Demo page showing Flask Countries functionality"""
        return render_template("countries_example.html")

    @app.route("/register-with-country", methods=["GET", "POST"])
    def register_with_country():
        """Example registration form with country selection"""
        if request.method == "POST":
            name = request.form.get("name")
            email = request.form.get("email")
            country_code = request.form.get("country")
            phone = request.form.get("phone")

            # Import here to avoid circular imports
            from countries import Countries

            # Validate country
            country_name = Countries.get_country_name(country_code)
            dial_code = Countries.get_country_dial_code(country_code)

            if not country_name:
                flash("Pays invalide sélectionné.", "error")
                return redirect(request.url)

            flash(f"Inscription réussie! Pays: {country_name} ({dial_code}) - Téléphone: {phone}", "success")
            return redirect(url_for("countries_demo"))

        return render_template("register_example.html")

    @app.route("/api/countries")
    def api_countries():
        """API endpoint to get countries data"""
        from countries import Countries
        return jsonify({
            "countries": Countries.get_countries_with_dial_codes(),
            "african_countries": Countries.get_african_countries_with_dial_codes()
        })

    @app.route("/api/country/<code>")
    def api_country(code):
        """Get country info by ISO code"""
        from countries import Countries
        name = Countries.get_country_name(code.upper())
        dial_code = Countries.get_country_dial_code(code.upper())

        if not name:
            return jsonify({"error": "Country not found"}), 404

        return jsonify({
            "code": code.upper(),
            "name": name,
            "dial_code": dial_code
        })
    # ===== END FLASK COUNTRIES DEMO ROUTES =====

    @app.route("/portal/register", methods=["GET"])
    def portal_register_page():
        """Page d'inscription pour les clients Tekanayo"""
        return render_template(
            "portal/register.html",
            now=datetime.now()
        )

    @app.route("/portal/sellerregister", methods=["GET"])
    def seller_register_page():
        # Passe les niches disponibles au template
        return render_template(
            "portal/seller_register.html",
            now=datetime.now(),
            niches=NICHE_CHOICES
        )

    @app.route("/devenir-vendeur", methods=["POST"])
    @app.route("/portal/sellerregister", methods=["POST"])
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
        print(f"Country code: {country_code}")
        print(f"Category niche: {category_niche}")

        # Validation des champs requis
        required_fields = [shop_name, first_name, last_name, email, password, 
                          confirm_password, phone_number, category_niche, shop_description]
        
        if not all(required_fields):
            missing = []
            if not shop_name: missing.append("nom boutique")
            if not first_name: missing.append("prénom")
            if not last_name: missing.append("nom")
            if not email: missing.append("email")
            if not password: missing.append("mot de passe")
            if not confirm_password: missing.append("confirmation mot de passe")
            if not phone_number: missing.append("téléphone")
            if not category_niche: missing.append("niche")
            if not shop_description: missing.append("description")
            
            flash(f"Tous les champs obligatoires doivent être remplis. Manquants : {', '.join(missing)}", "error")
            return redirect(url_for("seller_register_page"))

        # Validation de la niche
        if category_niche and category_niche not in dict(NICHE_CHOICES):
            flash("Niche de boutique invalide.", "error")
            return redirect(url_for("seller_register_page"))

        # Validation du pays si fourni
        if country_code and not Countries.get_country_name(country_code):
            flash("Pays invalide.", "error")
            return redirect(url_for("seller_register_page"))

        # Validation du téléphone (doit être exactement 9 chiffres)
        if not phone_number or len(phone_number) != 9 or not phone_number.isdigit():
            flash("Le numéro de téléphone doit contenir exactement 9 chiffres.", "error")
            return redirect(url_for("seller_register_page"))

        # Validation de l'email
        import re
        if not re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", email):
            flash("Adresse email invalide.", "error")
            return redirect(url_for("seller_register_page"))

        # Validation du mot de passe
        if len(password) < 8:
            flash("Le mot de passe doit contenir au moins 8 caractères.", "error")
            return redirect(url_for("seller_register_page"))

        # Validation de la confirmation du mot de passe
        if password != confirm_password:
            flash("Les mots de passe ne correspondent pas.", "error")
            return redirect(url_for("seller_register_page"))

        # Validation des conditions d'utilisation
        if not terms or not data_processing:
            flash("Vous devez accepter les conditions d'utilisation et autoriser le traitement de vos données.", "error")
            return redirect(url_for("seller_register_page"))

        # Vérification de l'unicité de l'email dans TOUS les niveaux
        if (SellerAdmin.query.filter_by(email=email).first()
            or PlatformAdmin.query.filter_by(email=email).first()
            or PortalCustomer.query.filter_by(email=email).first()
            or SellerDeliverer.query.filter_by(email=email).first()
            or SellerCustomer.query.filter_by(email=email).first()):
            flash("Cette adresse email est déjà utilisée.", "error")
            return redirect(url_for("seller_register_page"))

        # Vérification de l'unicité du nom de boutique
        if SellerShop.query.filter(
            SellerShop.name.ilike(shop_name) | SellerShop.slug.ilike(_slugify(shop_name))
        ).first():
            flash("Ce nom de boutique est déjà utilisé.", "error")
            return redirect(url_for("seller_register_page"))

        if custom_domain:
            conflict_domain = SellerShop.query.filter_by(custom_domain=custom_domain).first()
            if conflict_domain:
                flash("Ce nom de domaine est déjà utilisé.", "error")
                return redirect(url_for("seller_register_page"))

        # ====================================================================
        # GESTION DES DOCUMENTS UPLOADÉS
        # ====================================================================
        import os
        from werkzeug.utils import secure_filename
        
        ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'pdf'}
        MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
        
        def allowed_file(filename):
            return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
        
        def save_uploaded_file_simple(file, folder):
            """Sauvegarde un fichier uploadé"""
            if not file or not file.filename:
                return None
            
            if not allowed_file(file.filename):
                flash(f"Type de fichier non autorisé pour {folder}. Formats acceptés : JPG, PNG, PDF", "error")
                return None
            
            # Vérifier la taille
            file.seek(0, 2)
            size = file.tell()
            file.seek(0)
            
            if size > MAX_FILE_SIZE:
                flash(f"Le fichier {file.filename} dépasse 5MB.", "error")
                return None
            
            # Créer le dossier
            upload_folder = os.path.join(app.config['UPLOAD_ROOT'], folder)
            os.makedirs(upload_folder, exist_ok=True)
            
            # Nom du fichier
            timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
            ext = file.filename.rsplit('.', 1)[1].lower()
            filename = f"{timestamp}_{secrets.token_hex(4)}.{ext}"
            
            # Sauvegarder
            filepath = os.path.join(upload_folder, filename)
            file.save(filepath)
            
            return f"/uploads/{folder}/{filename}"
        
        # Les documents ne sont plus requis lors de l'inscription.
        # Le vendeur pourra les uploader depuis son espace vendeur après inscription.
        id_document_path = None
        address_document_path = None

        # Get dial code for full phone number
        dial_code = Countries.get_country_dial_code(country_code) if country_code else '+243'
        # dial_code already contains '+' (e.g. '+243'), so no need to add another '+'
        full_phone = f"{dial_code}{phone_number}" if phone_number else None

        # Création de la boutique et du propriétaire
        slug = _unique_slug(_slugify(shop_name))
        shop = SellerShop(
            name=shop_name,
            slug=slug,
            owner_email=email,
            support_phone=full_phone,  # Legacy field
            address=address,
            description=shop_description,
            custom_domain=custom_domain or None,
            category_niche=category_niche,
            # Documents uploadés
            id_document_path=id_document_path,
            address_document_path=address_document_path,
            verification_status='pending',
            currency="USD",
            subscription_status="trial",
        )

        owner = SellerAdmin(
            shop=shop,
            first_name=first_name,
            last_name=last_name,
            email=email,
            is_owner=True,
            country_code=country_code,
            phone_number=phone_number  # Stocker sans le code pays
        )
        owner.set_password(password)

        db.session.add_all([shop, owner])
        db.session.flush()  # Obtenir les IDs sans commit final
        
        # Création de l'abonnement
        from datetime import timedelta
        trial_end = datetime.utcnow() + timedelta(days=60)  # 2 mois gratuits
        
        subscription = SellerSubscription(
            shop_id=shop.id,
            status="trial",
            trial_start_date=datetime.utcnow(),
            trial_end_date=trial_end,
            monthly_price=5.0,
            payment_method=None,
        )
        db.session.add(subscription)
        
        try:
            db.session.commit()
            print("=== VENDEUR CRÉÉ AVEC SUCCÈS ===")
        except Exception as e:
            db.session.rollback()
            print(f"=== ERREUR: {str(e)} ===")
            flash(f"Erreur lors de la création de la boutique : {str(e)}", "error")
            return redirect(url_for("seller_register_page"))

        # Envoi de l'email de bienvenue
        root_url = request.url_root.rstrip("/")
        shop_key = _shop_access_key(shop)
        seller_login_url = f"{root_url}/{shop_key}/vendeur"
        shop_public_url = f"{root_url}/{shop_key}"
        deliverer_login_url = f"{root_url}/{shop_key}/livreur"

        html = _email_shell(
            "Bienvenue sur Tekanayo App - Vos identifiants de connexion",
            (
                f"<div style='text-align:center;padding:20px 0;'>"
                f"<div style='font-size:48px;margin-bottom:10px;'>🎉</div>"
                f"<h1 style='color:#1e293b;margin:0;font-size:24px;'>Félicitations {first_name} !</h1>"
                f"</div>"
                f"<p style='font-size:16px;color:#475569;line-height:1.6;'>"
                f"Votre boutique <strong style='color:#7c3aed;'>{shop.name}</strong> a été créée avec succès sur <strong>Tekanayo App</strong> !"
                f"</p>"
                f"<div style='background:linear-gradient(135deg,#f5f3ff,#ede9fe);padding:20px;border-radius:12px;margin:20px 0;border:1px solid #c4b5fd;'>"
                f"<h3 style='margin:0 0 15px 0;color:#6d28d9;font-size:16px;'>🔐 Vos identifiants de connexion</h3>"
                f"<table style='width:100%;border-collapse:collapse;'>"
                f"<tr><td style='padding:8px 0;color:#6b7280;font-size:14px;'>📧 Email</td><td style='padding:8px 0;font-weight:bold;color:#1e293b;'>{email}</td></tr>"
                f"<tr><td style='padding:8px 0;color:#6b7280;font-size:14px;'>🔑 Mot de passe</td><td style='padding:8px 0;font-weight:bold;color:#1e293b;font-family:monospace;'>{password}</td></tr>"
                f"<tr><td style='padding:8px 0;color:#6b7280;font-size:14px;'>📞 Téléphone</td><td style='padding:8px 0;font-weight:bold;color:#1e293b;'>{full_phone}</td></tr>"
                f"</table>"
                f"</div>"
                f"<div style='background:#fefce8;padding:15px;border-radius:8px;margin:15px 0;border-left:4px solid #eab308;'>"
                f"<p style='margin:0;color:#854d0e;font-size:13px;'>"
                f"<strong>⚠️ Important :</strong> Changez votre mot de passe lors de votre première connexion."
                f"</p>"
                f"</div>"
                f"<h3 style='color:#1e293b;font-size:16px;margin:25px 0 15px 0;'>📍 Accès rapides</h3>"
                f"<table style='width:100%;border-collapse:collapse;'>"
                f"<tr>"
                f"<td style='padding:8px;'><a href='{seller_login_url}' style='display:block;background:#7c3aed;color:white;text-decoration:none;padding:12px 20px;border-radius:8px;text-align:center;font-weight:bold;font-size:14px;'>🛍️ Espace Vendeur</a></td>"
                f"</tr>"
                f"<tr>"
                f"<td style='padding:8px;'><a href='{shop_public_url}' style='display:block;background:#059669;color:white;text-decoration:none;padding:12px 20px;border-radius:8px;text-align:center;font-weight:bold;font-size:14px;'>🌐 Votre Boutique en Ligne</a></td>"
                f"</tr>"
                f"<tr>"
                f"<td style='padding:8px;'><a href='{deliverer_login_url}' style='display:block;background:#2563eb;color:white;text-decoration:none;padding:12px 20px;border-radius:8px;text-align:center;font-weight:bold;font-size:14px;'>🚚 Espace Livreur</a></td>"
                f"</tr>"
                f"</table>"
                f"<div style='background:#f0fdf4;padding:15px;border-radius:8px;margin:20px 0;border:1px solid #bbf7d0;'>"
                f"<h4 style='margin:0 0 8px 0;color:#16a34a;font-size:14px;'>💡 Prochaines étapes</h4>"
                f"<ol style='margin:0;padding-left:20px;color:#475569;font-size:13px;line-height:1.8;'>"
                f"<li>Connectez-vous à votre <strong>Espace Vendeur</strong></li>"
                f"<li>Ajoutez vos produits et catégories</li>"
                f"<li>Personnalisez votre boutique (logo, couleurs, description)</li>"
                f"<li>Invitez des livreurs à rejoindre votre équipe</li>"
                f"<li>Commencez à vendre !</li>"
                f"</ol>"
                f"</div>"
            ),
            "Tekanayo App",
            "#7c3aed",
        )

        _send_email(
            email,
            "Bienvenue sur Tekanayo App - Vos identifiants",
            f"Votre boutique {shop.name} est créée. Email: {email}, Mot de passe: {password}. URLs: {seller_login_url}",
            html,
        )

        # Connexion automatique du vendeur
        session["seller_admin_id"] = owner.id
        
        # Rediriger vers la page de confirmation
        return redirect(url_for("seller_confirmation_page",
            first_name=first_name,
            shop_name=shop.name,
            email=email,
            password=password,
            full_phone=full_phone,
            seller_login_url=seller_login_url,
            shop_public_url=shop_public_url,
            deliverer_login_url=deliverer_login_url
        ))

    @app.route("/portal/register/confirmation", methods=["GET"])
    def seller_confirmation_page():
        """Page de confirmation après inscription vendeur"""
        first_name = request.args.get("first_name", "Cher vendeur")
        shop_name = request.args.get("shop_name", "votre boutique")
        email = request.args.get("email", "")
        password = request.args.get("password", "")
        full_phone = request.args.get("full_phone", "")
        seller_login_url = request.args.get("seller_login_url", "#")
        shop_public_url = request.args.get("shop_public_url", "#")
        deliverer_login_url = request.args.get("deliverer_login_url", "#")
        
        return render_template(
            "portal/seller_confirmation.html",
            first_name=first_name,
            shop_name=shop_name,
            email=email,
            password=password,
            full_phone=full_phone,
            seller_login_url=seller_login_url,
            shop_public_url=shop_public_url,
            deliverer_login_url=deliverer_login_url,
            now=datetime.now()
        )

    # ============================================================================
    # AUTHENTIFICATION PORTAL CLIENT (Inscription / Connexion)
    # ============================================================================
    @app.route("/portal/register", methods=["POST"])
    def portal_register():
        """Inscription d'un client sur le portail Tekanayo"""
        first_name = (request.form.get("first_name") or "").strip()
        last_name = (request.form.get("last_name") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        password = (request.form.get("password") or "").strip()
        agree_terms = request.form.get("agree-terms")

        # Validation des champs requis
        if not all([first_name, last_name, email, password]):
            flash("Tous les champs obligatoires doivent être remplis.", "error")
            return redirect(url_for("tekanayo_portal_page", page="register"))

        # Validation email
        import re
        if not re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", email):
            flash("Adresse email invalide.", "error")
            return redirect(url_for("tekanayo_portal_page", page="register"))

        # Validation mot de passe
        if len(password) < 8:
            flash("Le mot de passe doit contenir au moins 8 caractères.", "error")
            return redirect(url_for("tekanayo_portal_page", page="register"))

        # Validation conditions d'utilisation
        if not agree_terms:
            flash("Vous devez accepter les conditions d'utilisation.", "error")
            return redirect(url_for("tekanayo_portal_page", page="register"))

        # Vérification unicité email dans TOUS les niveaux
        if (PortalCustomer.query.filter_by(email=email).first()
            or SellerAdmin.query.filter_by(email=email).first()
            or PlatformAdmin.query.filter_by(email=email).first()
            or SellerDeliverer.query.filter_by(email=email).first()
            or SellerCustomer.query.filter_by(email=email).first()):
            flash("Cette adresse email est déjà utilisée.", "error")
            return redirect(url_for("tekanayo_portal_page", page="register"))

        # Création du client
        customer = PortalCustomer(
            first_name=first_name,
            last_name=last_name,
            email=email,
        )
        customer.set_password(password)
        db.session.add(customer)
        db.session.commit()

        # Connexion automatique
        login_user(customer)

        # Email de bienvenue
        html = _email_shell(
            "Bienvenue sur Tekanayo - Votre compte client",
            (
                f"<div style='text-align:center;padding:20px 0;'>"
                f"<div style='font-size:48px;margin-bottom:10px;'>🎉</div>"
                f"<h1 style='color:#1e293b;margin:0;font-size:24px;'>Bienvenue {first_name} !</h1>"
                f"</div>"
                f"<p style='font-size:16px;color:#475569;line-height:1.6;'>"
                f"Votre compte client a été créé avec succès sur <strong>Tekanayo</strong>."
                f"</p>"
                f"<div style='background:linear-gradient(135deg,#f5f3ff,#ede9fe);padding:20px;border-radius:12px;margin:20px 0;border:1px solid #c4b5fd;'>"
                f"<h3 style='margin:0 0 15px 0;color:#6d28d9;font-size:16px;'>✅ Votre compte est prêt</h3>"
                f"<table style='width:100%;border-collapse:collapse;'>"
                f"<tr><td style='padding:8px 0;color:#6b7280;font-size:14px;'>👤 Nom</td><td style='padding:8px 0;font-weight:bold;color:#1e293b;'>{first_name} {last_name}</td></tr>"
                f"<tr><td style='padding:8px 0;color:#6b7280;font-size:14px;'>📧 Email</td><td style='padding:8px 0;font-weight:bold;color:#1e293b;'>{email}</td></tr>"
                f"</table>"
                f"</div>"
                f"<div style='background:#f0fdf4;padding:15px;border-radius:8px;margin:20px 0;border:1px solid #bbf7d0;'>"
                f"<h4 style='margin:0 0 8px 0;color:#16a34a;font-size:14px;'>💡 Ce que vous pouvez faire</h4>"
                f"<ul style='margin:0;padding-left:20px;color:#475569;font-size:13px;line-height:1.8;'>"
                f"<li>Parcourir les boutiques et produits</li>"
                f"<li>Passer des commandes</li>"
                f"<li>Suivre vos commandes</li>"
                f"<li>Gérer votre profil</li>"
                f"</ul>"
                f"</div>"
                f"<div style='text-align:center;margin:20px 0;'>"
                f"<a href='{request.url_root.rstrip('/')}' style='display:inline-block;background:#7c3aed;color:white;text-decoration:none;padding:14px 28px;border-radius:8px;font-weight:bold;font-size:15px;'>🛍️ Découvrir les boutiques</a>"
                f"</div>"
            ),
            "Tekanayo",
            "#7c3aed",
        )
        _send_email(
            email,
            "Bienvenue sur Tekanayo - Votre compte client",
            f"Votre compte client Tekanayo a été créé. Email: {email}",
            html,
        )

        return redirect(
            url_for(
                "portal_confirmation_page",
                first_name=first_name,
                email=email,
                password=password,
            )
        )

    @app.route("/portal/confirmation")
    def portal_confirmation_page():
        """Affiche la page de confirmation après inscription client"""
        first_name = request.args.get("first_name", "Client")
        email = request.args.get("email", "")
        password = request.args.get("password", "")

        shop, view = _portal_shop_context()
        return render_template(
            "portal/portal_confirmation.html",
            shop=shop,
            first_name=first_name,
            email=email,
            password=password,
            **view,
        )

    @app.route("/portal/login", methods=["POST"])
    @limiter.limit("5 per minute")
    def portal_login():
        """Connexion d'un client sur le portail Tekanayo"""
        email = (request.form.get("email") or "").strip().lower()
        password = (request.form.get("password") or "").strip()
        remember_me = request.form.get("remember_me") == "on"

        if not email or not password:
            flash("Veuillez remplir tous les champs.", "error")
            return redirect(url_for("tekanayo_portal_page", page="login"))

        customer = PortalCustomer.query.filter_by(email=email, is_active=True).first()
        if not customer or not customer.check_password(password):
            flash("Email ou mot de passe incorrect.", "error")
            return redirect(url_for("tekanayo_portal_page", page="login"))

        login_user(customer, remember=remember_me)
        flash("Connexion réussie !", "success")
        return redirect(url_for("tekanayo_portal"))

    @app.route("/portal/logout")
    @login_required
    def portal_logout():
        """Déconnexion d'un client du portail"""
        logout_user()
        flash("Vous avez été déconnecté.", "success")
        return redirect(url_for("tekanayo_portal"))

    @app.route("/admin", methods=["GET", "POST"])
    @app.route("/admin/", methods=["GET", "POST"])
    @app.route("/admin/entry", methods=["GET", "POST"])
    @limiter.limit("5 per minute")
    def admin_login_page():
        if request.method == "GET":
            if current_user.is_authenticated:
                return redirect(url_for("tekanayo_admin_panel"))
            return render_template("admin/admin_entry.html", login_mode=True, settings=_get_platform_settings())

        email = (request.form.get("email") or "").strip().lower()
        password = (request.form.get("password") or "").strip()
        admin = PlatformAdmin.query.filter_by(email=email, is_active=True).first()
        if not admin or not admin.check_password(password):
            flash("Identifiants admin invalides.", "error")
            return redirect(url_for("admin_login_page"))
        login_user(admin)
        return redirect(url_for("tekanayo_admin_panel"))

    @app.route("/admin/login", methods=["GET", "POST"])
    @app.route("/tekanayo-admin/login", methods=["GET", "POST"])
    def legacy_admin_login():
        if request.method == "POST":
            return redirect(url_for("admin_login_page"), code=307)
        return redirect(url_for("admin_login_page"), code=302)

    @app.route("/admin_entry", methods=["GET", "POST"])
    def admin_entry():
        if request.method == "POST":
            return redirect(url_for("admin_login_page"), code=307)
        return redirect(url_for("admin_login_page"), code=302)

    @app.route("/admin/reset_password", methods=["GET", "POST"])
    def admin_reset_request():
        if request.method == "GET":
            return render_template("reset_request.html", role="admin")
        email = (request.form.get("email") or "").strip().lower()
        admin = PlatformAdmin.query.filter_by(email=email, is_active=True).first()
        if admin:
            token = _generate_reset_token("admin", admin.id)
            reset_url = f"{request.url_root.rstrip('/')}{url_for('admin_reset_with_token', token=token)}"
            html = _email_shell(
                "Réinitialisation mot de passe",
                f"<p>Bonjour {admin.first_name},</p><p>Utilisez ce lien pour changer votre mot de passe:</p><p><a href='{reset_url}'>{reset_url}</a></p>",
                "Tekanayo App Administration",
                "#0f172a",
            )
            _send_email(admin.email, "Reset password - Admin Tekanayo", f"Lien reset: {reset_url}", html)
        flash("Si cet email existe, un lien a été envoyé.", "success")
        return redirect(url_for("admin_login_page"))

    @app.route("/admin/reset_password/<token>", methods=["GET", "POST"])
    def admin_reset_with_token(token):
        payload = _verify_reset_token(token)
        if not payload or payload.get("role") != "admin":
            flash("Lien invalide ou expiré.", "error")
            return redirect(url_for("admin_reset_request"))
        admin = PlatformAdmin.query.get(payload.get("id"))
        if not admin:
            flash("Compte introuvable.", "error")
            return redirect(url_for("admin_reset_request"))
        if request.method == "GET":
            return render_template("reset_form.html", role="admin", token=token)
        password = (request.form.get("password") or "").strip()
        confirm = (request.form.get("confirm_password") or "").strip()
        if len(password) < 6 or password != confirm:
            flash("Mot de passe invalide ou confirmation différente.", "error")
            return redirect(url_for("admin_reset_with_token", token=token))
        admin.set_password(password)
        db.session.commit()
        flash("Mot de passe admin mis à jour.", "success")
        return redirect(url_for("admin_login_page"))

    @app.route("/admin/logout")
    @login_required
    def tekanayo_admin_logout():
        logout_user()
        return redirect(url_for("admin_login_page"))

    @app.route("/tekanayo-admin/logout")
    @login_required
    def legacy_tekanayo_admin_logout():
        return redirect(url_for("tekanayo_admin_logout"), code=302)

    @app.route("/admin/dashboard")
    @admin_required()
    def tekanayo_admin_panel():
        return _render_tekanayo_admin_page("dashboard")

    def _render_tekanayo_admin_page(active_tab="dashboard", selected_admin=None, selected_deliverer=None):
        settings = _get_platform_settings()
        portal_shop = _portal_shop()
        sellers = SellerShop.query.order_by(SellerShop.created_at.desc()).all()
        admins = PlatformAdmin.query.order_by(PlatformAdmin.created_at.desc()).all()
        announcements = PlatformAnnouncement.query.order_by(PlatformAnnouncement.created_at.desc()).all()
        logs = PlatformActivityLog.query.order_by(PlatformActivityLog.created_at.desc()).limit(300).all()
        recent_orders = SellerOrder.query.order_by(SellerOrder.created_at.desc()).limit(10).all()
        products = []
        orders = []
        deliverers = []
        clients = []
        categories = []
        if portal_shop:
            products = SellerProduct.query.filter_by(shop_id=portal_shop.id).order_by(SellerProduct.created_at.desc()).all()
            orders = SellerOrder.query.filter_by(shop_id=portal_shop.id).order_by(SellerOrder.created_at.desc()).all()
            categories = sorted({(p.category or "").strip() for p in products if (p.category or "").strip()})
        # Platform deliverers are not tied to any specific shop
        deliverers = PlatformDeliverer.query.order_by(PlatformDeliverer.created_at.desc()).all()
        portal_customers = PortalCustomer.query.order_by(PortalCustomer.created_at.desc()).all()
        clients = portal_customers
        stats = {
            "total_orders": SellerOrder.query.count(),
            "total_products": SellerProduct.query.count(),
            "total_users": PortalCustomer.query.count(),
            "total_seller_customers": SellerCustomer.query.count(),
            "total_deliverers": PlatformDeliverer.query.count(),  # Platform deliverers only
            "total_seller_admins": SellerAdmin.query.count(),
            "total_platform_admins": PlatformAdmin.query.count(),
            "total_revenue": float(sum(float(o.total_amount or 0.0) for o in SellerOrder.query.all())),
            "total_sellers": len(sellers),
            "active_sellers": sum(1 for s in sellers if s.is_active),
            "suspended_sellers": sum(1 for s in sellers if not s.is_active or (s.subscription_status or "").lower() == "suspended"),
        }
        platform_events = []
        for item in logs[:120]:
            platform_events.append(
                {
                    "kind": "Log",
                    "label": item.action,
                    "by": item.actor_name or item.actor_email or "Système",
                    "extra": item.extra or "",
                    "created_at": item.created_at,
                }
            )
        for o in orders[:80]:
            platform_events.append(
                {
                    "kind": "Commande",
                    "label": o.order_number,
                    "by": o.customer_name or "Client",
                    "extra": f"Montant: {o.total_amount or 0} | Statut: {o.status}",
                    "created_at": o.created_at,
                }
            )
        for c in clients[:80]:
            platform_events.append(
                {
                    "kind": "Client",
                    "label": f"{c.first_name} {c.last_name}",
                    "by": c.email,
                    "extra": "Inscription client",
                    "created_at": c.created_at,
                }
            )
        for d in deliverers[:80]:
            platform_events.append(
                {
                    "kind": "Livreur",
                    "label": f"{d.first_name} {d.last_name}",
                    "by": d.email,
                    "extra": f"Statut: {d.status}",
                    "created_at": d.created_at,
                }
            )
        for s in sellers[:80]:
            platform_events.append(
                {
                    "kind": "Vendeur",
                    "label": s.name,
                    "by": s.owner_email,
                    "extra": f"Abonnement: {s.subscription_status}",
                    "created_at": s.created_at,
                }
            )
        platform_events.sort(key=lambda x: x.get("created_at") or datetime.min, reverse=True)
        platform_events = platform_events[:220]

        selected_admin_id = request.args.get("view_admin", type=int)
        selected_admin = PlatformAdmin.query.get(selected_admin_id) if selected_admin_id else None
        selected_admin_created_requests = []
        selected_admin_processed_requests = []
        if selected_admin:
            selected_admin_created_requests = (
                PlatformAccessRequest.query
                .filter_by(admin_id=selected_admin.id)
                .order_by(PlatformAccessRequest.created_at.desc())
                .all()
            )
            selected_admin_processed_requests = (
                PlatformAccessRequest.query
                .filter_by(processed_by=selected_admin.id)
                .order_by(PlatformAccessRequest.processed_at.desc())
                .all()
            )

        my_requests = (
            PlatformAccessRequest.query
            .filter_by(admin_id=current_user.id)
            .order_by(PlatformAccessRequest.created_at.desc())
            .all()
        )
        access_requests = []
        if current_user.role == "super_admin" or current_user.has_permission("manage_admins"):
            access_requests = PlatformAccessRequest.query.order_by(PlatformAccessRequest.created_at.desc()).all()
        access_request_count = PlatformAccessRequest.query.filter_by(status="pending").count()

        current_perms = {p.strip() for p in (current_user.permissions or "").split(",") if p.strip()}
        missing_permissions = [p for p in ADMIN_PERMISSION_LABELS.keys() if p not in current_perms]

        shop_settings = {
            "shop_name": settings.platform_name if settings and settings.platform_name else "Tekanayo App",
            "admin_logo": settings.admin_logo_url if settings else None,
            "shop_logo": settings.portal_logo_url if settings else None,
        }

        template_map = {
            "dashboard": "admin/tekanayo_admin.html",
            "products": "admin/products.html",
            "orders": "admin/orders.html",
            "deliverers": "admin/deliverers.html",
            "clients": "admin/clients.html",
            "categories": "admin/categories.html",
            "tasks": "admin/tasks.html",
            "sellers": "admin/vendeurs.html",
            "announcements": "admin/annonces.html",
            "admins": "admin/admins.html",
            "access_requests": "admin/access_requests.html",
            "settings": "admin/settings.html",
            "profile": "admin/profile.html",
            "about": "admin/about.html",
        }

        return render_template(
            template_map.get(active_tab, "admin/tekanayo_admin.html"),
            login_mode=False,
            active_tab=active_tab,
            active_page=active_tab,
            portal_shop=portal_shop,
            sellers=sellers,
            admins=admins,
            announcements=announcements,
            settings=settings,
            shop_settings=shop_settings,
            logs=logs,
            stats=stats,
            recent_orders=recent_orders,
            products=products,
            orders=orders,
            deliverers=deliverers,
            clients=clients,
            categories=categories,
            platform_events=platform_events,
            my_requests=my_requests,
            access_requests=access_requests,
            access_request_count=access_request_count,
            missing_permissions=missing_permissions,
            selected_admin=selected_admin,
            selected_admin_created_requests=selected_admin_created_requests,
            selected_admin_processed_requests=selected_admin_processed_requests,
            selected_deliverer=selected_deliverer,
            admin_permission_labels=ADMIN_PERMISSION_LABELS,
            countries=Countries,
        )

    @app.route("/admin/sellers")
    @admin_required("manage_sellers")
    def tekanayo_admin_sellers():
        return _render_tekanayo_admin_page("sellers")

    @app.route("/admin/products")
    @admin_required("manage_products")
    def tekanayo_admin_products():
        return _render_tekanayo_admin_page("products")

    @app.route("/admin/orders")
    @admin_required("manage_orders")
    def tekanayo_admin_orders():
        return _render_tekanayo_admin_page("orders")

    @app.route("/admin/deliverers")
    @admin_required("manage_deliverers")
    def tekanayo_admin_deliverers():
        return _render_tekanayo_admin_page("deliverers")

    @app.route("/admin/clients")
    @admin_required("manage_clients")
    def tekanayo_admin_clients():
        return _render_tekanayo_admin_page("clients")

    @app.route("/admin/categories")
    @admin_required("manage_categories")
    def tekanayo_admin_categories():
        return _render_tekanayo_admin_page("categories")

    @app.route("/admin/subscriptions")
    @admin_required()
    def tekanayo_admin_subscriptions():
        return _render_tekanayo_admin_page("subscriptions")

    @app.route("/admin/admins")
    @admin_required("manage_admins")
    def tekanayo_admin_admins():
        return _render_tekanayo_admin_page("admins")

    @app.route("/admin/admin_views")
    @admin_required()
    def tekanayo_admin_admin_views():
        return _render_tekanayo_admin_page("admin_views")

    @app.route("/admin/announcements")
    @admin_required("manage_announcements")
    def tekanayo_admin_announcements():
        return _render_tekanayo_admin_page("announcements")

    @app.route("/admin/settings")
    @admin_required("manage_settings")
    def tekanayo_admin_settings():
        return _render_tekanayo_admin_page("settings")

    @app.route("/admin/profile")
    @admin_required()
    def tekanayo_admin_profile():
        return _render_tekanayo_admin_page("profile")

    @app.route("/admin/access_requests")
    @admin_required("manage_admins")
    def tekanayo_admin_access_requests():
        return _render_tekanayo_admin_page("access_requests")

    @app.route("/admin/tasks")
    @admin_required("view_tasks")
    def tekanayo_admin_tasks():
        return _render_tekanayo_admin_page("tasks")

    # ========================================================================
    # ROUTES DE GESTION DES ABONNEMENTS ET NOTIFICATIONS
    # ========================================================================

    @app.route("/admin/api/notification-count")
    @admin_required()
    def admin_notification_count():
        """API: Retourne le nombre de notifications non lues et tâches en attente"""
        # Notifications non lues
        unread_notifications = AdminNotification.query.filter_by(
            admin_id=current_user.id,
            is_read=False
        ).count()
        
        # Tâches en attente
        pending_tasks = SellerPaymentTask.query.filter_by(status='pending').count()
        
        return jsonify({
            'unread_notifications': unread_notifications,
            'pending_tasks': pending_tasks,
            'total': unread_notifications + pending_tasks
        })

    @app.route("/admin/api/notifications/mark-all-read", methods=["POST"])
    @admin_required()
    def admin_mark_notifications_read():
        """API: Marquer toutes les notifications comme lues"""
        AdminNotification.query.filter_by(
            admin_id=current_user.id,
            is_read=False
        ).update({'is_read': True, 'read_at': datetime.utcnow()})
        db.session.commit()
        return jsonify({'success': True})

    @app.route("/admin/api/tasks/<int:task_id>/mark-viewed", methods=["POST"])
    @admin_required()
    def admin_mark_task_viewed(task_id):
        """API: Marquer une tâche comme vue"""
        task = SellerPaymentTask.query.get_or_404(task_id)
        if not task.is_viewed:
            task.is_viewed = True
            task.viewed_at = datetime.utcnow()
            task.viewed_by = current_user.id
            db.session.commit()
        return jsonify({'success': True})

    @app.route("/admin/subscriptions/list")
    @admin_required()
    def admin_subscriptions_list():
        """Liste de tous les abonnements avec filtres"""
        # Récupérer les filtres
        status_filter = request.args.get('status', '')
        search_query = request.args.get('search', '')
        
        # Requête de base
        query = SellerSubscription.query.join(SellerShop)
        
        # Appliquer les filtres
        if status_filter:
            query = query.filter(SellerSubscription.status == status_filter)
        if search_query:
            query = query.filter(
                db.or_(
                    SellerShop.name.ilike(f'%{search_query}%'),
                    SellerShop.owner_email.ilike(f'%{search_query}%')
                )
            )
        
        subscriptions = query.order_by(SellerSubscription.created_at.desc()).all()
        
        return jsonify([{
            'id': sub.id,
            'shop_id': sub.shop_id,
            'shop_name': sub.shop.name,
            'owner_email': sub.shop.owner_email,
            'status': sub.status,
            'monthly_price': sub.monthly_price,
            'total_paid': sub.total_paid,
            'trial_end_date': sub.trial_end_date.strftime('%d/%m/%Y') if sub.trial_end_date else None,
            'subscription_end_date': sub.subscription_end_date.strftime('%d/%m/%Y') if sub.subscription_end_date else None,
            'days_remaining': sub.days_remaining(),
            'payment_method': sub.payment_method,
            'pending_payment': sub.pending_payment
        } for sub in subscriptions])

    @app.route("/admin/subscriptions/<int:subscription_id>/activate", methods=["POST"])
    @admin_required("manage_sellers")
    def admin_activate_subscription(subscription_id):
        """Activer manuellement un abonnement (paiement hors plateforme)"""
        subscription = SellerSubscription.query.get_or_404(subscription_id)
        
        # Activer l'abonnement
        subscription.status = 'active'
        subscription.subscription_start_date = datetime.utcnow()
        subscription.subscription_end_date = datetime.utcnow() + timedelta(days=30)
        subscription.last_payment_date = datetime.utcnow()
        subscription.pending_payment = False
        
        # Créer le paiement
        payment = SellerPayment(
            subscription_id=subscription.id,
            amount=5.0,
            payment_method='offline',
            status='completed',
            is_offline=True,
            offline_confirmed_by=current_user.id,
            offline_confirmed_at=datetime.utcnow(),
            notes=f"Activé manuellement par {current_user.first_name} {current_user.last_name}"
        )
        db.session.add(payment)
        
        # Créer une tâche de confirmation
        task = SellerPaymentTask(
            shop_id=subscription.shop_id,
            subscription_id=subscription.id,
            task_type='activation',
            status='completed',
            title=f"Abonnement activé - {subscription.shop.name}",
            description=f"L'admin {current_user.first_name} {current_user.last_name} a activé l'abonnement suite au paiement hors plateforme de 5$.",
            amount=5.0,
            payment_method='offline',
            completed_by=current_user.id,
            completed_at=datetime.utcnow()
        )
        db.session.add(task)
        
        # Créer une notification pour le vendeur
        notification = AdminNotification(
            admin_id=current_user.id,
            notification_type='subscription_activated',
            title=f"Abonnement activé : {subscription.shop.name}",
            message=f"Vous avez activé l'abonnement de {subscription.shop.name} ({subscription.shop.owner_email}). Prochain renouvellement : {subscription.subscription_end_date.strftime('%d/%m/%Y')}",
            icon='fa-check-circle',
            color='green',
            reference_type='subscription',
            reference_id=subscription.id
        )
        db.session.add(notification)
        
        db.session.commit()
        
        flash(f"Abonnement de {subscription.shop.name} activé avec succès pour 1 mois.", "success")
        return redirect(url_for('tekanayo_admin_subscriptions'))

    @app.route("/admin/subscriptions/<int:subscription_id>/suspend", methods=["POST"])
    @admin_required("manage_sellers")
    def admin_suspend_subscription(subscription_id):
        """Suspendre un abonnement"""
        subscription = SellerSubscription.query.get_or_404(subscription_id)
        
        subscription.status = 'suspended'
        
        task = SellerPaymentTask(
            shop_id=subscription.shop_id,
            subscription_id=subscription.id,
            task_type='deactivation',
            status='completed',
            title=f"Abonnement suspendu - {subscription.shop.name}",
            description=f"L'admin {current_user.first_name} {current_user.last_name} a suspendu l'abonnement.",
            completed_by=current_user.id,
            completed_at=datetime.utcnow()
        )
        db.session.add(task)
        db.session.commit()
        
        flash(f"Abonnement de {subscription.shop.name} suspendu.", "warning")
        return redirect(url_for('tekanayo_admin_subscriptions'))

    @app.route("/admin/payment-tasks")
    @admin_required()
    def admin_payment_tasks():
        """Liste des tâches de paiement en attente"""
        # Récupérer toutes les tâches en attente
        pending_tasks = SellerPaymentTask.query.filter_by(status='pending').order_by(SellerPaymentTask.created_at.desc()).all()
        
        # Marquer comme vues
        for task in pending_tasks:
            if not task.is_viewed:
                task.is_viewed = True
                task.viewed_at = datetime.utcnow()
                task.viewed_by = current_user.id
        
        db.session.commit()
        
        return render_template("admin/payment_tasks.html", tasks=pending_tasks)

    @app.route("/admin/about")
    @admin_required()
    def tekanayo_admin_about():
        return _render_tekanayo_admin_page("about")

    @app.route("/admin/about/update", methods=["POST"])
    @admin_required("manage_settings")
    def admin_update_about_content():
        about_content = (request.form.get("about_content") or "").strip()
        settings = _get_platform_settings()
        if not settings:
            settings = PlatformSettings()
            db.session.add(settings)
        settings.admin_about_content = about_content
        db.session.commit()
        record_activity(
            "Mise à jour du contenu À propos (Admin)",
            actor=current_user,
            extra=f"length={len(about_content)}",
        )
        flash("Contenu mis à jour avec succès.", "success")
        return redirect(url_for("tekanayo_admin_about"))

    @app.route("/tekanayo-admin")
    @admin_required()
    def legacy_tekanayo_admin_panel():
        return redirect(url_for("tekanayo_admin_panel"), code=302)

    @app.route("/admin/settings/update", methods=["POST"])
    @admin_required("manage_settings")
    def admin_update_platform_settings():
        settings = _get_platform_settings()
        settings.platform_name = (request.form.get("platform_name") or "Tekanayo App").strip() or "Tekanayo App"
        portal_logo = _save_uploaded_image(request.files.get("portal_logo"), "platform/logos")
        admin_logo = _save_uploaded_image(request.files.get("admin_logo"), "platform/logos")
        deliverer_logo = _save_uploaded_image(request.files.get("deliverer_logo"), "platform/logos")
        seller_login_logo = _save_uploaded_image(request.files.get("seller_login_logo"), "platform/logos")
        deliverer_login_logo = _save_uploaded_image(request.files.get("deliverer_login_logo"), "platform/logos")
        if portal_logo:
            settings.portal_logo_url = portal_logo
        if admin_logo:
            settings.admin_logo_url = admin_logo
        if deliverer_logo:
            settings.deliverer_logo_url = deliverer_logo
        if seller_login_logo:
            settings.seller_login_logo_url = seller_login_logo
        if deliverer_login_logo:
            settings.deliverer_login_logo_url = deliverer_login_logo
        settings.contact_email = (request.form.get("contact_email") or "").strip().lower() or None
        settings.contact_phone = (request.form.get("contact_phone") or "").strip() or None
        settings.facebook_url = (request.form.get("facebook_url") or "").strip() or None
        settings.whatsapp_number = (request.form.get("whatsapp_number") or "").strip() or None
        settings.whatsapp_group_url = (request.form.get("whatsapp_group_url") or "").strip() or None
        settings.whatsapp_url = (request.form.get("whatsapp_url") or "").strip() or None
        settings.telegram_username = (request.form.get("telegram_username") or "").strip() or None
        settings.telegram_url = (request.form.get("telegram_url") or "").strip() or None
        settings.currency = (request.form.get("currency") or "USD").strip().upper()
        if settings.currency not in {"USD", "CDF"}:
            settings.currency = "USD"
        settings.tax_rate = _safe_float(request.form.get("tax_rate"), 0.0)
        settings.shipping_cost = _safe_float(request.form.get("shipping_cost"), 0.0)
        settings.shipping_cost_out = _safe_float(request.form.get("shipping_cost_out"), 0.0)
        settings.office_address = (request.form.get("office_address") or "").strip() or None
        settings.portal_about_content = (request.form.get("portal_about_content") or "").strip() or None
        settings.portal_legal_content = (request.form.get("portal_legal_content") or "").strip() or None
        settings.portal_terms_content = (request.form.get("portal_terms_content") or "").strip() or None
        settings.portal_returns_content = (request.form.get("portal_returns_content") or "").strip() or None
        settings.portal_privacy_content = (request.form.get("portal_privacy_content") or "").strip() or None
        settings.exchange_rate_usd_cdf = _safe_float(request.form.get("exchange_rate_usd_cdf"), 2800.0)
        settings.default_currency = (request.form.get("default_currency") or "USD").strip().upper()
        if settings.default_currency not in {"USD", "CDF"}:
            settings.default_currency = "USD"

        lat, lon, geo = _geocode_address(settings.office_address or "")
        if lat is not None and lon is not None:
            settings.office_latitude = lat
            settings.office_longitude = lon
            settings.office_geocoded = geo

        db.session.commit()
        record_activity("Mise à jour paramètres Tekanayo", actor=current_user)
        flash("Paramètres plateforme mis à jour.", "success")
        return redirect(url_for("tekanayo_admin_settings"))

    @app.route("/tekanayo-admin/settings/update", methods=["POST"])
    @admin_required("manage_settings")
    def legacy_admin_update_platform_settings():
        return redirect(url_for("admin_update_platform_settings"), code=307)

    @app.route("/admin/announcements/add", methods=["POST"])
    @admin_required("manage_announcements")
    def admin_add_announcement():
        title = (request.form.get("title") or "").strip()
        content = (request.form.get("content") or "").strip()
        cta_label = (request.form.get("cta_label") or "").strip()
        cta_url = (request.form.get("cta_url") or "").strip()
        if not title or not content:
            flash("Titre et contenu requis.", "error")
            return redirect(url_for("tekanayo_admin_announcements"))
        item = PlatformAnnouncement(title=title, content=content, cta_label=cta_label or None, cta_url=cta_url or None, created_by=current_user.id)
        db.session.add(item)
        db.session.commit()
        record_activity(f"Publication annonce '{title}'", actor=current_user)
        flash("Annonce publiée.", "success")
        return redirect(url_for("tekanayo_admin_announcements"))

    @app.route("/tekanayo-admin/announcements/add", methods=["POST"])
    @admin_required("manage_announcements")
    def legacy_admin_add_announcement():
        return redirect(url_for("admin_add_announcement"), code=307)

    @app.route("/admin/products/add", methods=["POST"])
    @admin_required("manage_products")
    def admin_add_platform_product():
        shop = _portal_shop()
        if not shop:
            flash("Aucune boutique portail active pour enregistrer un produit.", "error")
            return redirect(url_for("tekanayo_admin_products"))
        name = (request.form.get("name") or "").strip()
        category = (request.form.get("category") or "").strip()
        description = (request.form.get("description") or "").strip()
        price = _safe_float(request.form.get("price"), 0.0)
        quantity = int(_safe_float(request.form.get("quantity"), 0))
        if not name or not category or price <= 0:
            flash("Produit invalide: nom, catégorie et prix sont obligatoires.", "error")
            return redirect(url_for("tekanayo_admin_products"))
        image = _save_uploaded_image(request.files.get("image_file"), "platform/products")
        item = SellerProduct(
            shop_id=shop.id,
            name=name,
            category=category,
            description=description or None,
            price=price,
            quantity=max(0, quantity),
            image_url=image,
            is_promoted=(request.form.get("is_promoted") == "on"),
            is_active=(request.form.get("is_active") != "off"),
        )
        db.session.add(item)
        db.session.commit()
        flash("Produit Tekanayo ajouté.", "success")
        return redirect(url_for("tekanayo_admin_products"))

    @app.route("/admin/products/<int:product_id>/delete", methods=["POST"])
    @admin_required("manage_products")
    def admin_delete_platform_product(product_id):
        shop = _portal_shop()
        item = SellerProduct.query.get_or_404(product_id)
        if shop and item.shop_id != shop.id:
            flash("Produit hors portail Tekanayo.", "error")
            return redirect(url_for("tekanayo_admin_products"))
        db.session.delete(item)
        db.session.commit()
        flash("Produit supprimé.", "success")
        return redirect(url_for("tekanayo_admin_products"))

    @app.route("/admin/orders/<int:order_id>/status", methods=["POST"])
    @admin_required("manage_orders")
    def admin_update_platform_order_status(order_id):
        order = SellerOrder.query.get_or_404(order_id)
        new_status = (request.form.get("status") or "").strip().lower()
        if new_status not in {"pending", "processing", "delivering", "delivered", "cancelled"}:
            flash("Statut de commande invalide.", "error")
            return redirect(url_for("tekanayo_admin_orders"))
        order.status = new_status
        db.session.commit()
        flash("Statut de la commande mis à jour.", "success")
        return redirect(url_for("tekanayo_admin_orders"))

    @app.route("/admin/deliverers/add", methods=["POST"])
    @admin_required("manage_deliverers")
    def admin_add_platform_deliverer():
        first_name = (request.form.get("first_name") or "").strip()
        last_name = (request.form.get("last_name") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        country_code = (request.form.get("country_code") or "").strip() or None
        phone_number = (request.form.get("phone_number") or "").strip() or None
        address = (request.form.get("address") or "").strip() or None
        if not first_name or not last_name or "@" not in email:
            flash("Informations livreur invalides.", "error")
            return redirect(url_for("tekanayo_admin_deliverers"))
        if phone_number and (len(phone_number) != 9 or not phone_number.isdigit()):
            flash("Le numéro de téléphone doit contenir exactement 9 chiffres.", "error")
            return redirect(url_for("tekanayo_admin_deliverers"))
        if PlatformDeliverer.query.filter_by(email=email).first():
            flash("Cet email livreur existe déjà.", "error")
            return redirect(url_for("tekanayo_admin_deliverers"))
        password = secrets.token_urlsafe(10)
        d = PlatformDeliverer(first_name=first_name, last_name=last_name, email=email, country_code=country_code, phone_number=phone_number, address=address, status="available", is_active=True)
        d.set_password(password)
        db.session.add(d)
        db.session.commit()
        deliverer_login_url = f"{request.url_root.rstrip('/')}/deliverer"
        html = _email_shell(
            "Compte Livreur Tekanayo App",
            f"<p>Bonjour {first_name},</p><p>Votre compte livreur Tekanayo est créé.</p><p>Email de connexion : <strong>{email}</strong></p><p>Mot de passe temporaire : <strong>{password}</strong></p><p>Lien de connexion : <a href='{deliverer_login_url}'>{deliverer_login_url}</a></p><p>Veuillez changer votre mot de passe après la première connexion pour plus de sécurité.</p>",
            "Tekanayo App Livreurs",
            "#0e7490",
        )
        _send_email(email, "Compte livreur Tekanayo App", f"Connexion: {deliverer_login_url}\nMot de passe: {password}", html)
        flash("Mot de passe généré et envoyé par email.", "success")
        return redirect(url_for("tekanayo_admin_deliverers"))

    @app.route("/admin/deliverers/<int:deliverer_id>/toggle", methods=["POST"])
    @admin_required("manage_deliverers")
    def admin_toggle_platform_deliverer(deliverer_id):
        d = PlatformDeliverer.query.get_or_404(deliverer_id)
        d.is_active = not bool(d.is_active)
        db.session.commit()
        flash("Statut du livreur mis à jour.", "success")
        return redirect(url_for("tekanayo_admin_deliverers"))

    @app.route("/admin/deliverers/<int:deliverer_id>/verify", methods=["POST"])
    @admin_required("manage_deliverers")
    def admin_verify_platform_deliverer(deliverer_id):
        d = PlatformDeliverer.query.get_or_404(deliverer_id)
        if d.verification_status == "verified":
            d.verification_status = "pending"
            d.verified_by = None
            d.verified_at = None
            flash("La vérification du livreur a été annulée.", "success")
        else:
            d.verification_status = "verified"
            d.verified_by = current_user.id
            d.verified_at = datetime.utcnow()
            flash("Livreur marqué comme vérifié.", "success")
        db.session.commit()
        return redirect(url_for("tekanayo_admin_deliverers"))

    @app.route("/admin/deliverers/<int:deliverer_id>")
    @admin_required("manage_deliverers")
    def admin_view_platform_deliverer(deliverer_id):
        deliverer = PlatformDeliverer.query.get_or_404(deliverer_id)
        return _render_tekanayo_admin_page("deliverers", selected_deliverer=deliverer)

    @app.route("/admin/categories/rename", methods=["POST"])
    @admin_required("manage_categories")
    def admin_rename_platform_category():
        shop = _portal_shop()
        old_name = (request.form.get("old_name") or "").strip()
        new_name = (request.form.get("new_name") or "").strip()
        if not shop or not old_name or not new_name:
            flash("Renommage catégorie invalide.", "error")
            return redirect(url_for("tekanayo_admin_categories"))
        SellerProduct.query.filter_by(shop_id=shop.id, category=old_name).update({"category": new_name}, synchronize_session=False)
        db.session.commit()
        flash("Catégorie renommée.", "success")
        return redirect(url_for("tekanayo_admin_categories"))

    @app.route("/admin/categories/delete", methods=["POST"])
    @admin_required("manage_categories")
    def admin_delete_platform_category():
        shop = _portal_shop()
        category_name = (request.form.get("category_name") or "").strip()
        if not shop or not category_name:
            flash("Suppression catégorie invalide.", "error")
            return redirect(url_for("tekanayo_admin_categories"))
        SellerProduct.query.filter_by(shop_id=shop.id, category=category_name).update({"category": "Sans catégorie"}, synchronize_session=False)
        db.session.commit()
        flash("Catégorie supprimée (produits déplacés vers 'Sans catégorie').", "success")
        return redirect(url_for("tekanayo_admin_categories"))

    @app.route("/admin/sellers/<int:shop_id>/toggle", methods=["POST"])
    @admin_required("manage_sellers")
    def admin_toggle_seller(shop_id):
        shop = SellerShop.query.get_or_404(shop_id)
        shop.is_active = not bool(shop.is_active)
        if not shop.is_active:
            shop.subscription_status = "suspended"
        elif shop.subscription_status == "suspended":
            shop.subscription_status = "active"
        db.session.commit()
        record_activity(
            f"Changement statut boutique '{shop.name}'",
            actor=current_user,
            extra=f"is_active={shop.is_active}, subscription={shop.subscription_status}",
        )
        flash("Statut boutique vendeur mis à jour.", "success")
        return redirect(url_for("tekanayo_admin_sellers"))

    @app.route("/admin/sellers/<int:shop_id>/verify", methods=["POST"])
    @admin_required("manage_sellers")
    def admin_verify_seller(shop_id):
        shop = SellerShop.query.get_or_404(shop_id)
        if shop.verification_status == "verified":
            shop.verification_status = "pending"
            shop.verified_by = None
            shop.verified_at = None
            flash("La vérification de la boutique a été annulée.", "success")
        else:
            shop.verification_status = "verified"
            shop.verified_by = current_user.id
            shop.verified_at = datetime.utcnow()
            flash("Boutique marquée comme vérifiée.", "success")
        db.session.commit()
        record_activity(
            f"Changement vérification boutique '{shop.name}'",
            actor=current_user,
            extra=f"verification_status={shop.verification_status}",
        )
        return redirect(url_for("tekanayo_admin_sellers"))

    @app.route("/tekanayo-admin/sellers/<int:shop_id>/toggle", methods=["POST"])
    @admin_required("manage_sellers")
    def legacy_admin_toggle_seller(shop_id):
        return redirect(url_for("admin_toggle_seller", shop_id=shop_id), code=307)

    @app.route("/admin/sellers/<int:shop_id>/view")
    @admin_required("manage_sellers")
    def admin_seller_view(shop_id):
        shop = SellerShop.query.get_or_404(shop_id)
        admins = SellerAdmin.query.filter_by(shop_id=shop.id).all()
        products_count = SellerProduct.query.filter_by(shop_id=shop.id).count()
        orders_count = SellerOrder.query.filter_by(shop_id=shop.id).count()
        deliverers_count = SellerDeliverer.query.filter_by(shop_id=shop.id).count()
        subscription = SellerSubscription.query.filter_by(shop_id=shop.id).first()
        return render_template(
            "admin/seller_view.html",
            shop=shop,
            admins=admins,
            products_count=products_count,
            orders_count=orders_count,
            deliverers_count=deliverers_count,
            subscription=subscription,
            active_tab="sellers",
            Countries=Countries,
        )

    @app.route("/admin/admins/add", methods=["POST"])
    @admin_required("manage_admins")
    def admin_add_platform_admin():
        email = (request.form.get("email") or "").strip().lower()
        first_name = (request.form.get("first_name") or "").strip()
        last_name = (request.form.get("last_name") or "").strip()
        country_code = (request.form.get("country_code") or "").strip().upper()
        phone_number = (request.form.get("phone_number") or "").strip()
        allowed = set(ADMIN_PERMISSION_LABELS.keys())
        picked = [p.strip() for p in request.form.getlist("permissions") if p and p.strip() in allowed]
        permissions = ",".join(sorted(set(picked)))
        if not all([email, first_name, last_name]):
            flash("Champs incomplets.", "error")
            return redirect(url_for("tekanayo_admin_panel"))
        if phone_number and not (phone_number.isdigit() and len(phone_number) == 9):
            flash("Le numéro de téléphone doit contenir exactement 9 chiffres.", "error")
            return redirect(url_for("tekanayo_admin_panel"))
        if PlatformAdmin.query.filter_by(email=email).first():
            flash("Email déjà utilisé.", "error")
            return redirect(url_for("tekanayo_admin_panel"))
        password = secrets.token_urlsafe(10)
        admin = PlatformAdmin(
            email=email,
            first_name=first_name,
            last_name=last_name,
            country_code=country_code or None,
            phone_number=phone_number or None,
            permissions=permissions or "manage_products,manage_orders,manage_deliverers,manage_clients,manage_categories,manage_announcements",
        )
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        record_activity(f"Création admin plateforme '{email}'", actor=current_user, extra=f"permissions={admin.permissions}")
        login_url = f"{request.url_root.rstrip('/')}/admin"
        html = _email_shell(
            "Compte Admin Tekanayo App",
            f"<p>Bonjour {first_name},</p><p>Votre compte administrateur plateforme est créé.</p><p>Connexion: <a href='{login_url}'>{login_url}</a></p><p>Mot de passe temporaire: <strong>{password}</strong></p><p>Veuillez changer votre mot de passe après la première connexion.</p>",
            "Tekanayo App Administration",
            "#0f172a",
        )
        _send_email(email, "Compte admin Tekanayo App", f"Connexion: {login_url}\nMot de passe: {password}", html)
        flash("Mot de passe généré et envoyé par email.", "success")
        return redirect(url_for("tekanayo_admin_admins"))

    @app.route("/admin/admins/<int:admin_id>/toggle", methods=["POST"])
    @admin_required("manage_admins")
    def admin_toggle_platform_admin(admin_id):
        target = PlatformAdmin.query.get_or_404(admin_id)
        if target.id == current_user.id:
            flash("Impossible de désactiver votre propre compte.", "error")
            return redirect(url_for("tekanayo_admin_admins"))
        target.is_active = not bool(target.is_active)
        db.session.commit()
        record_activity(
            f"Changement statut admin '{target.email}'",
            actor=current_user,
            extra=f"is_active={target.is_active}",
        )
        flash("Statut administrateur mis à jour.", "success")
        return redirect(url_for("tekanayo_admin_admins"))

    @app.route("/admin/admins/<int:admin_id>/edit-permissions", methods=["POST"])
    @admin_required("manage_admins")
    def admin_edit_platform_admin_permissions(admin_id):
        target = PlatformAdmin.query.get_or_404(admin_id)
        if target.role == "super_admin":
            flash("Impossible de modifier les permissions d'un super-admin.", "error")
            return redirect(url_for("tekanayo_admin_admins"))
        if target.id == current_user.id:
            flash("Utilisez la page profil pour modifier vos propres permissions.", "error")
            return redirect(url_for("tekanayo_admin_admins"))
        
        allowed = set(ADMIN_PERMISSION_LABELS.keys())
        picked = [p.strip() for p in request.form.getlist("permissions") if p and p.strip() in allowed]
        permissions = ",".join(sorted(set(picked)))
        
        old_permissions = target.permissions
        target.permissions = permissions
        db.session.commit()
        record_activity(
            f"Modification permissions admin '{target.email}'",
            actor=current_user,
            extra=f"old={old_permissions}, new={permissions}",
        )
        flash("Permissions administrateur mises à jour.", "success")
        return redirect(url_for("tekanayo_admin_admins"))

    @app.route("/tekanayo-admin/admins/add", methods=["POST"])
    @admin_required("manage_admins")
    def legacy_admin_add_platform_admin():
        return redirect(url_for("admin_add_platform_admin"), code=307)

    @app.route("/admin/profile/update", methods=["POST"])
    @admin_required()
    def admin_profile_update():
        first_name = (request.form.get("first_name") or "").strip()
        last_name = (request.form.get("last_name") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        country_code = (request.form.get("country_code") or "").strip() or None
        phone_number = (request.form.get("phone_number") or "").strip() or None
        address = (request.form.get("address") or "").strip() or None
        uploaded_profile_picture = _save_uploaded_image(request.files.get("profile_picture_file"), "platform/profiles")

        if not all([first_name, last_name, email]) or "@" not in email:
            flash("Informations profil invalides.", "error")
            return redirect(url_for("tekanayo_admin_profile"))

        if phone_number and (len(phone_number) != 9 or not phone_number.isdigit()):
            flash("Le numéro de téléphone doit contenir exactement 9 chiffres.", "error")
            return redirect(url_for("tekanayo_admin_profile"))

        existing = PlatformAdmin.query.filter(PlatformAdmin.email == email, PlatformAdmin.id != current_user.id).first()
        if existing:
            flash("Cet email est déjà utilisé par un autre admin.", "error")
            return redirect(url_for("tekanayo_admin_profile"))

        current_user.first_name = first_name
        current_user.last_name = last_name
        current_user.email = email
        current_user.country_code = country_code
        current_user.phone_number = phone_number
        current_user.address = address
        if uploaded_profile_picture:
            current_user.profile_picture = uploaded_profile_picture
        db.session.commit()
        record_activity("Mise à jour profil admin", actor=current_user)
        flash("Profil administrateur mis à jour.", "success")
        return redirect(url_for("tekanayo_admin_profile"))

    @app.route("/admin/profile/password", methods=["POST"])
    @admin_required()
    def admin_profile_password():
        current_password = (request.form.get("current_password") or "").strip()
        new_password = (request.form.get("new_password") or "").strip()
        confirm_password = (request.form.get("confirm_password") or "").strip()
        if not current_user.check_password(current_password):
            flash("Mot de passe actuel incorrect.", "error")
            return redirect(url_for("tekanayo_admin_profile"))
        if len(new_password) < 6:
            flash("Le nouveau mot de passe doit contenir au moins 6 caractères.", "error")
            return redirect(url_for("tekanayo_admin_profile"))
        if new_password != confirm_password:
            flash("La confirmation du mot de passe ne correspond pas.", "error")
            return redirect(url_for("tekanayo_admin_profile"))
        current_user.set_password(new_password)
        db.session.commit()
        record_activity("Mise à jour mot de passe admin", actor=current_user)
        flash("Mot de passe mis à jour.", "success")
        return redirect(url_for("tekanayo_admin_profile"))

    @app.route("/admin/access-requests/request", methods=["POST"])
    @admin_required()
    def admin_request_access():
        requested = [p.strip() for p in request.form.getlist("permissions_requested") if p.strip()]
        one_feature = (request.form.get("feature") or "").strip()
        if one_feature:
            requested.append(one_feature)
        message = (request.form.get("message") or "").strip()
        requested = [p for p in requested if p in ADMIN_PERMISSION_LABELS]

        if not requested:
            flash("Sélectionnez au moins une permission.", "error")
            return redirect(url_for("tekanayo_admin_access_requests"))

        req = PlatformAccessRequest(
            admin_id=current_user.id,
            feature=",".join(requested),
            message=message or None,
            status="pending",
        )
        db.session.add(req)
        db.session.commit()
        record_activity("Demande d'accès créée", actor=current_user, extra=f"permissions={req.feature}")

        super_admins = PlatformAdmin.query.filter_by(role="super_admin", is_active=True).all()
        for sa in super_admins:
            if sa.email:
                _send_email(
                    sa.email,
                    "Nouvelle demande d'accès admin",
                    f"{current_user.first_name} {current_user.last_name} demande: {req.feature}",
                )

        flash("Demande d'accès envoyée au super admin.", "success")
        return redirect(url_for("tekanayo_admin_access_requests"))

    @app.route("/admin/access-requests/<int:request_id>/process", methods=["POST"])
    @admin_required()
    def admin_process_access_request(request_id):
        if current_user.role != "super_admin" and not current_user.has_permission("manage_admins"):
            flash("Vous n'êtes pas autorisé à traiter les demandes d'accès.", "error")
            return redirect(url_for("tekanayo_admin_access_requests"))

        ar = PlatformAccessRequest.query.get_or_404(request_id)
        if ar.status != "pending":
            flash("Cette demande est déjà traitée.", "warning")
            return redirect(url_for("tekanayo_admin_access_requests"))

        action = (request.form.get("action") or request.form.get("decision") or "").strip().lower()
        response = (request.form.get("response_message") or "").strip()
        requester = PlatformAdmin.query.get(ar.admin_id)
        perms_requested = [p.strip() for p in (ar.feature or "").split(",") if p.strip()]

        if action in {"approve", "approved"}:
            current = {p.strip() for p in (requester.permissions or "").split(",") if p.strip()} if requester else set()
            current.update(perms_requested)
            if requester:
                requester.permissions = ",".join(sorted(current))
            ar.status = "approved"
            flash("Demande approuvée.", "success")
        elif action in {"reject", "rejected"}:
            ar.status = "rejected"
            flash("Demande rejetée.", "warning")
        else:
            flash("Action invalide.", "error")
            return redirect(url_for("tekanayo_admin_access_requests"))

        ar.processed_by = current_user.id
        ar.response_message = response or None
        ar.processed_at = datetime.utcnow()
        db.session.commit()
        record_activity(
            f"Traitement demande accès #{ar.id}",
            actor=current_user,
            extra=f"action={ar.status}; requester={requester.email if requester else ar.admin_id}",
        )

        if requester and requester.email:
            _send_email(
                requester.email,
                f"Votre demande d'accès a été {ar.status}",
                f"Statut: {ar.status}. Réponse: {ar.response_message or '-'}",
            )
        return redirect(url_for("tekanayo_admin_access_requests"))

    @app.route("/vendeur", methods=["GET", "POST"])
    @app.route("/vendeur/", methods=["GET", "POST"])
    @app.route("/vendeur/login", methods=["POST"])
    @limiter.limit("5 per minute")
    def seller_entrypoint():
        if request.method == "GET":
            shop_hint = (request.args.get("shop") or "").strip()
            hinted_shop = _resolve_shop_identifier(shop_hint) if shop_hint else None
            return render_template(
                "vendeur/seller_entry.html",
                selected_shop=hinted_shop,
                seller_login_action=url_for("seller_entry_for_shop_key", shop_key=_shop_access_key(hinted_shop)) if hinted_shop else url_for("seller_entrypoint"),
            )

        email = (request.form.get("email") or "").strip().lower()
        password = (request.form.get("password") or "").strip()
        shop_hint = (request.form.get("shop_slug") or request.args.get("shop") or "").strip()
        hinted_shop = _resolve_shop_identifier(shop_hint) if shop_hint else None
        admin = SellerAdmin.query.filter_by(email=email, is_active=True).first()
        if not admin or not admin.shop or not admin.check_password(password):
            flash("Identifiants vendeur invalides.", "error")
            if hinted_shop:
                return redirect(url_for("seller_entry_for_shop_key", shop_key=_shop_access_key(hinted_shop)))
            return redirect(url_for("seller_entrypoint"))
        if hinted_shop and admin.shop_id != hinted_shop.id:
            flash("Ce compte vendeur n'appartient pas à cette boutique.", "error")
            return redirect(url_for("seller_entry_for_shop_key", shop_key=_shop_access_key(hinted_shop)))
        session["seller_admin_id"] = admin.id
        return redirect(url_for("seller_space", slug=admin.shop.slug))

    @app.route("/<shop_key>/vendeur", methods=["GET", "POST"])
    @limiter.limit("5 per minute")
    def seller_entry_for_shop_key(shop_key):
        shop = _resolve_shop_access_key(shop_key)
        if not shop:
            flash("Boutique introuvable.", "error")
            return redirect(url_for("seller_entrypoint"))
        canonical_key = _shop_access_key(shop)
        if (shop_key or "").strip().lower() != canonical_key:
            return redirect(url_for("seller_entry_for_shop_key", shop_key=canonical_key), code=307 if request.method == "POST" else 302)
        if request.method == "GET":
            return render_template(
                "vendeur/seller_entry.html",
                selected_shop=shop,
                seller_login_action=url_for("seller_entry_for_shop_key", shop_key=canonical_key),
            )

        email = (request.form.get("email") or "").strip().lower()
        password = (request.form.get("password") or "").strip()
        admin = SellerAdmin.query.filter_by(email=email, shop_id=shop.id, is_active=True).first()
        if not admin or not admin.check_password(password):
            flash("Identifiants vendeur invalides pour cette boutique.", "error")
            return redirect(url_for("seller_entry_for_shop_key", shop_key=canonical_key))
        session["seller_admin_id"] = admin.id
        return redirect(url_for("seller_space", slug=shop.slug))

    @app.route("/vendeur/reset_password", methods=["GET", "POST"])
    def seller_reset_request():
        if request.method == "GET":
            return render_template("reset_request.html", role="vendeur")
        email = (request.form.get("email") or "").strip().lower()
        seller_admin = SellerAdmin.query.filter_by(email=email, is_active=True).first()
        if seller_admin and seller_admin.shop:
            token = _generate_reset_token("seller", seller_admin.id)
            reset_url = f"{request.url_root.rstrip('/')}{url_for('seller_reset_with_token', token=token)}"
            html = _email_shell(
                f"Réinitialisation - {seller_admin.shop.name}",
                f"<p>Bonjour {seller_admin.first_name},</p><p>Réinitialisez votre mot de passe via ce lien:</p><p><a href='{reset_url}'>{reset_url}</a></p>",
                seller_admin.shop.name,
                "#2563eb",
            )
            _send_email(seller_admin.email, f"Reset password - {seller_admin.shop.name}", f"Lien reset: {reset_url}", html)
        flash("Si cet email existe, un lien a été envoyé.", "success")
        return redirect(url_for("seller_entrypoint"))

    @app.route("/vendeur/reset_password/<token>", methods=["GET", "POST"])
    def seller_reset_with_token(token):
        payload = _verify_reset_token(token)
        if not payload or payload.get("role") != "seller":
            flash("Lien invalide ou expiré.", "error")
            return redirect(url_for("seller_reset_request"))
        seller_admin = SellerAdmin.query.get(payload.get("id"))
        if not seller_admin:
            flash("Compte introuvable.", "error")
            return redirect(url_for("seller_reset_request"))
        if request.method == "GET":
            return render_template("reset_form.html", role="vendeur", token=token)
        password = (request.form.get("password") or "").strip()
        confirm = (request.form.get("confirm_password") or "").strip()
        if len(password) < 6 or password != confirm:
            flash("Mot de passe invalide ou confirmation différente.", "error")
            return redirect(url_for("seller_reset_with_token", token=token))
        seller_admin.set_password(password)
        db.session.commit()
        flash("Mot de passe vendeur mis à jour.", "success")
        return redirect(url_for("seller_entrypoint"))

    @app.route("/vendeur/<slug>", methods=["GET", "POST"])
    def seller_space(slug):
        shop = SellerShop.query.filter_by(slug=slug).first_or_404()
        sid = session.get("seller_admin_id")
        seller_admin = SellerAdmin.query.filter_by(id=sid, shop_id=shop.id, is_active=True).first() if sid else None
        if not seller_admin:
            flash("Veuillez vous connecter à l'espace vendeur.", "warning")
            return redirect(url_for("seller_entry_for_shop_key", shop_key=_shop_access_key(shop)))
        return redirect(url_for("seller_dashboard_page", slug=slug), code=307 if request.method == "POST" else 302)

    @app.route("/vendeur/<slug>/profile", methods=["GET", "POST"])
    @seller_session_required
    def seller_admin_profile_update(slug):
        shop = SellerShop.query.filter_by(slug=slug).first_or_404()
        sid = session.get("seller_admin_id")
        seller_admin = SellerAdmin.query.filter_by(id=sid, shop_id=shop.id, is_active=True).first_or_404()

        if request.method == "GET":
            _, _, context, redirect_response = _seller_page_context(slug)
            if redirect_response:
                return redirect_response
            return render_template("vendeur/profile.html", shop=shop, admin=seller_admin, active_page="profile", **context)

        seller_admin.first_name = (request.form.get("first_name") or seller_admin.first_name).strip()
        seller_admin.last_name = (request.form.get("last_name") or seller_admin.last_name).strip()
        
        # Handle phone number (from phone-input component)
        country_code = (request.form.get("country_code") or "").strip() or None
        phone_number = (request.form.get("phone_number") or "").strip() or None
        
        # Validate phone number: exactly 9 digits
        if phone_number and (len(phone_number) != 9 or not phone_number.isdigit()):
            flash("Le numéro de téléphone doit contenir exactement 9 chiffres.", "error")
            return redirect(url_for("seller_space", slug=slug))
        
        seller_admin.country_code = country_code
        seller_admin.phone_number = phone_number
        
        uploaded_profile_picture = _save_uploaded_image(request.files.get("profile_picture_file"), "seller/profiles")
        if uploaded_profile_picture:
            seller_admin.profile_picture = uploaded_profile_picture
        new_password = (request.form.get("new_password") or "").strip()
        if new_password:
            if len(new_password) < 6:
                flash("Le nouveau mot de passe vendeur doit contenir au moins 6 caractères.", "error")
                return redirect(url_for("seller_space", slug=slug))
            seller_admin.set_password(new_password)

        db.session.commit()
        flash("Profil vendeur mis à jour.", "success")
        return redirect(url_for("seller_space", slug=slug))

    @app.route("/vendeur/<slug>/logout")
    def seller_logout(slug):
        shop = SellerShop.query.filter_by(slug=slug).first_or_404()
        session.pop("seller_admin_id", None)
        return redirect(url_for("seller_entry_for_shop_key", shop_key=_shop_access_key(shop)))

    # ========================================================================
    # ROUTES D'ABONNEMENT ET DE PAIEMENT VENDEUR
    # ========================================================================

    @app.route("/vendeur/<slug>/subscription")
    @seller_session_required
    def seller_subscription_page(slug):
        """Page de gestion de l'abonnement du vendeur"""
        shop = SellerShop.query.filter_by(slug=slug).first_or_404()
        subscription = SellerSubscription.query.filter_by(shop_id=shop.id).first_or_404()
        
        # Vérifier si l'abonnement est expiré
        if subscription.is_expired() and subscription.status != "cancelled":
            subscription.status = "expired"
            db.session.commit()
        
        return render_template(
            "vendeur/subscription.html",
            shop=shop,
            subscription=subscription
        )

    @app.route("/vendeur/<slug>/subscription/payment")
    @seller_session_required
    def seller_payment_page(slug):
        """Page de paiement pour renouveler l'abonnement"""
        shop = SellerShop.query.filter_by(slug=slug).first_or_404()
        subscription = SellerSubscription.query.filter_by(shop_id=shop.id).first_or_404()
        
        # Méthodes de paiement disponibles
        payment_methods = [
            {"id": "airtel", "name": "Airtel Money", "icon": "fa-mobile-screen", "color": "#ff0000"},
            {"id": "orange", "name": "Orange Money", "icon": "fa-mobile-screen-button", "color": "#ff7900"},
            {"id": "mpesa", "name": "M-Pesa Vodacom", "icon": "fa-mobile", "color": "#00a8e0"},
            {"id": "afrimoney", "name": "Afrimoney", "icon": "fa-wallet", "color": "#ff6600"},
            {"id": "paypal", "name": "PayPal", "icon": "fa-paypal", "color": "#003087"},
            {"id": "stripe", "name": "Carte Bancaire (Stripe)", "icon": "fa-credit-card", "color": "#635bff"},
            {"id": "offline", "name": "Paiement Hors Plateforme", "icon": "fa-handshake", "color": "#10b981"},
        ]
        
        return render_template(
            "vendeur/payment.html",
            shop=shop,
            subscription=subscription,
            payment_methods=payment_methods
        )

    @app.route("/vendeur/<slug>/subscription/payment/process", methods=["POST"])
    @seller_session_required
    def seller_payment_process(slug):
        """Traiter le paiement de l'abonnement"""
        shop = SellerShop.query.filter_by(slug=slug).first_or_404()
        subscription = SellerSubscription.query.filter_by(shop_id=shop.id).first_or_404()
        
        payment_method = request.form.get("payment_method")
        is_offline = payment_method == "offline"
        
        # Créer le paiement
        payment = SellerPayment(
            subscription_id=subscription.id,
            amount=5.0,
            payment_method=payment_method,
            is_offline=is_offline,
            status="completed" if is_offline else "pending",
        )
        db.session.add(payment)
        
        if is_offline:
            # Paiement hors plateforme : créer une tâche pour l'admin
            task = SellerPaymentTask(
                shop_id=shop.id,
                subscription_id=subscription.id,
                task_type="offline_payment",
                status="pending",
                title=f"Paiement hors plateforme - {shop.name}",
                description=f"Le vendeur {shop.owner_email} a confirmé un paiement hors plateforme de 5$ via {payment_method}. Veuillez vérifier et activer l'abonnement.",
                amount=5.0,
                payment_method=payment_method,
            )
            db.session.add(task)
            
            # Mettre à jour l'abonnement en attente
            subscription.pending_payment = True
            subscription.status = "suspended"
            
            flash("Paiement hors plateforme confirmé. Un admin va vérifier et activer votre abonnement sous 24-48h.", "info")
        else:
            # Paiement en ligne : simulation (à intégrer avec les vrais APIs)
            # TODO: Intégrer les APIs de paiement réelles
            payment.status = "completed"
            payment.transaction_id = f"TXN_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            
            # Activer l'abonnement automatiquement
            subscription.status = "active"
            subscription.subscription_start_date = datetime.utcnow()
            subscription.subscription_end_date = datetime.utcnow() + timedelta(days=30)  # 1 mois
            subscription.last_payment_date = datetime.utcnow()
            subscription.total_paid += 5.0
            subscription.pending_payment = False
            
            # Créer une tâche de notification pour l'admin
            task = SellerPaymentTask(
                shop_id=shop.id,
                subscription_id=subscription.id,
                task_type="payment_completed",
                status="completed",
                title=f"Paiement automatique - {shop.name}",
                description=f"Le vendeur {shop.owner_email} a payé 5$ via {payment_method}. Abonnement activé automatiquement.",
                amount=5.0,
                payment_method=payment_method,
            )
            db.session.add(task)
            
            flash("Paiement réussi ! Votre abonnement a été activé pour 1 mois.", "success")
        
        db.session.commit()
        return redirect(url_for("seller_subscription_page", slug=slug))

    @app.route("/vendeur/<slug>/subscription/history")
    @seller_session_required
    def seller_payment_history(slug):
        """Historique des paiements du vendeur"""
        shop = SellerShop.query.filter_by(slug=slug).first_or_404()
        subscription = SellerSubscription.query.filter_by(shop_id=shop.id).first_or_404()
        payments = SellerPayment.query.filter_by(subscription_id=subscription.id).order_by(SellerPayment.created_at.desc()).all()
        
        return render_template(
            "vendeur/payment_history.html",
            shop=shop,
            subscription=subscription,
            payments=payments
        )

    @app.route("/vendeur/<slug>/products/add", methods=["POST"])
    @seller_session_required
    def seller_add_product(slug):
        shop = SellerShop.query.filter_by(slug=slug).first_or_404()
        current_admin = SellerAdmin.query.filter_by(id=session.get("seller_admin_id"), shop_id=shop.id, is_active=True).first()
        if not current_admin or (not current_admin.is_owner and not current_admin.has_permission("manage_products")):
            flash("Permission insuffisante pour gérer les produits.", "error")
            return redirect(url_for("seller_products_page", slug=slug))
        name = (request.form.get("name") or "").strip()
        category = (request.form.get("category") or "").strip()
        description = (request.form.get("description") or "").strip()
        image_url = (request.form.get("image_url") or "").strip()
        price = float(request.form.get("price") or 0)
        quantity = int(request.form.get("quantity") or 0)
        if not name or not category or price <= 0:
            flash("Produit invalide.", "error")
            return redirect(url_for("seller_space", slug=slug))
        p = SellerProduct(shop_id=shop.id, name=name, category=category, description=description, image_url=image_url or None, price=price, quantity=max(quantity, 0))
        db.session.add(p)
        db.session.commit()
        flash("Produit ajouté.", "success")
        return redirect(url_for("seller_products_page", slug=slug))

    @app.route("/vendeur/<slug>/products/<int:product_id>/promo", methods=["POST"])
    @seller_session_required
    def seller_toggle_promo(slug, product_id):
        shop = SellerShop.query.filter_by(slug=slug).first_or_404()
        current_admin = SellerAdmin.query.filter_by(id=session.get("seller_admin_id"), shop_id=shop.id, is_active=True).first()
        if not current_admin or (not current_admin.is_owner and not current_admin.has_permission("manage_products")):
            flash("Permission insuffisante pour gérer les produits.", "error")
            return redirect(url_for("seller_products_page", slug=slug))
        p = SellerProduct.query.filter_by(id=product_id, shop_id=shop.id).first_or_404()
        if not p.is_promoted:
            promoted_count = SellerProduct.query.filter_by(shop_id=shop.id, is_promoted=True, is_active=True).count()
            if promoted_count >= 4:
                flash("Maximum 4 produits promus.", "warning")
                return redirect(url_for("seller_space", slug=slug))
        p.is_promoted = not p.is_promoted
        db.session.commit()
        flash("Promotion mise à jour.", "success")
        return redirect(url_for("seller_products_page", slug=slug))

    @app.route("/vendeur/<slug>/settings", methods=["POST"])
    @seller_session_required
    def seller_update_settings(slug):
        shop = SellerShop.query.filter_by(slug=slug).first_or_404()
        current_admin = SellerAdmin.query.filter_by(id=session.get("seller_admin_id"), shop_id=shop.id, is_active=True).first()
        if not current_admin or (not current_admin.is_owner and not current_admin.has_permission("manage_settings")):
            flash("Permission insuffisante pour modifier les paramètres.", "error")
            return redirect(url_for("seller_settings_page", slug=slug))
        new_name = (request.form.get("name") or request.form.get("shop_name") or "").strip()
        if new_name:
            shop.name = new_name
        uploaded_seller_space_logo = _save_uploaded_image(
            request.files.get("seller_space_logo_file") or request.files.get("admin_logo"),
            "seller/logos",
        )
        uploaded_shop_logo = _save_uploaded_image(
            request.files.get("shop_logo_file") or request.files.get("shop_logo"),
            "seller/logos",
        )
        uploaded_deliverer_logo = _save_uploaded_image(
            request.files.get("deliverer_space_logo_file") or request.files.get("deliverer_logo"),
            "seller/logos",
        )
        if uploaded_seller_space_logo:
            shop.seller_space_logo_url = uploaded_seller_space_logo
        if uploaded_shop_logo:
            shop.logo_url = uploaded_shop_logo
        if uploaded_deliverer_logo:
            shop.deliverer_logo_url = uploaded_deliverer_logo
        shop.support_email = (request.form.get("support_email") or request.form.get("shop_email") or "").strip().lower() or None
        shop.support_phone = (request.form.get("support_phone") or request.form.get("shop_phone") or "").strip() or None
        shop.facebook_url = (request.form.get("facebook_url") or "").strip() or None
        shop.whatsapp_number = (request.form.get("whatsapp_number") or "").strip() or None
        shop.whatsapp_group_url = (request.form.get("whatsapp_group_url") or "").strip() or None
        shop.telegram_username = (request.form.get("telegram_username") or "").strip() or None
        shop.telegram_url = (request.form.get("telegram_url") or "").strip() or None
        shop.address = (request.form.get("address") or request.form.get("shop_address") or "").strip() or None
        shop.description = (request.form.get("description") or "").strip() or None
        shop.about_page_content = (request.form.get("about_page_content") or "").strip() or None
        shop.legal_page_content = (request.form.get("legal_page_content") or "").strip() or None
        shop.terms_page_content = (request.form.get("terms_page_content") or "").strip() or None
        shop.returns_page_content = (request.form.get("returns_page_content") or "").strip() or None
        shop.privacy_page_content = (request.form.get("privacy_page_content") or "").strip() or None
        shop.currency = (request.form.get("currency") or "USD").strip().upper()
        if shop.currency not in {"USD", "CDF"}:
            shop.currency = "USD"
        shop.tax_rate = _safe_float(request.form.get("tax_rate"), 0.0)
        shop.shipping_cost = _safe_float(request.form.get("shipping_cost"), 0.0)
        shop.shipping_cost_out = _safe_float(request.form.get("shipping_cost_out"), 0.0)
        shop.exchange_rate_usd_cdf = _safe_float(request.form.get("exchange_rate_usd_cdf"), 2800.0)
        shop.invoice_theme = (request.form.get("invoice_theme") or "classic").strip().lower()
        shop.category_niche = (request.form.get("category_niche") or "shopdivers").strip().lower()
        custom_domain = (request.form.get("custom_domain") or "").strip().lower()
        if custom_domain:
            conflict = SellerShop.query.filter(SellerShop.custom_domain == custom_domain, SellerShop.id != shop.id).first()
            if conflict:
                flash("Ce nom de domaine est déjà utilisé.", "error")
                return redirect(url_for("seller_space", slug=slug))
            shop.custom_domain = custom_domain
        else:
            shop.custom_domain = None
        db.session.commit()
        flash("Configuration boutique mise à jour.", "success")
        return redirect(url_for("seller_settings_page", slug=slug))

    @app.route("/vendeur/<slug>/deliverers/add", methods=["POST"])
    @seller_session_required
    def seller_add_deliverer(slug):
        shop = SellerShop.query.filter_by(slug=slug).first_or_404()
        current_admin = SellerAdmin.query.filter_by(id=session.get("seller_admin_id"), shop_id=shop.id, is_active=True).first()
        if not current_admin or (not current_admin.is_owner and not current_admin.has_permission("manage_deliverers")):
            flash("Permission insuffisante pour gérer les livreurs.", "error")
            return redirect(url_for("seller_deliverers_page", slug=slug))
        first_name = (request.form.get("first_name") or "").strip()
        last_name = (request.form.get("last_name") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        country_code = (request.form.get("country_code") or "").strip() or None
        phone_number = (request.form.get("phone_number") or "").strip() or None
        if not all([first_name, last_name, email]):
            flash("Champs livreur incomplets.", "error")
            return redirect(url_for("seller_space", slug=slug))
        if phone_number and (len(phone_number) != 9 or not phone_number.isdigit()):
            flash("Le numéro de téléphone doit contenir exactement 9 chiffres.", "error")
            return redirect(url_for("seller_space", slug=slug))
        if SellerDeliverer.query.filter_by(email=email).first():
            flash("Email livreur déjà utilisé.", "error")
            return redirect(url_for("seller_space", slug=slug))
        generated_password = _generate_temp_password(10)
        d = SellerDeliverer(shop_id=shop.id, first_name=first_name, last_name=last_name, email=email, country_code=country_code, phone_number=phone_number)
        d.set_password(generated_password)
        db.session.add(d)
        db.session.commit()
        login_url = f"{request.url_root.rstrip('/')}/{_shop_access_key(shop)}/livreur"
        html = _email_shell(
            f"Accès livreur - {shop.name}",
            (
                f"<p>Bonjour {first_name} {last_name},</p>"
                f"<p>Vous êtes ajouté comme livreur de <strong>{shop.name}</strong>.</p>"
                f"<p><strong>Connexion livreur</strong></p>"
                f"<p>Email: <strong>{email}</strong><br>Mot de passe temporaire: <strong>{generated_password}</strong></p>"
                f"<p>URL: <a href='{login_url}'>{login_url}</a></p>"
                f"<p>Après connexion, modifiez votre mot de passe depuis votre profil.</p>"
            ),
            f"{shop.name} - Livraison",
            "#059669",
        )
        _send_email(
            email,
            f"Accès livreur - {shop.name}",
            f"Email: {email} | Mot de passe temporaire: {generated_password} | URL: {login_url}",
            html,
        )
        flash("Livreur ajouté. Mot de passe généré et envoyé par email.", "success")
        return redirect(url_for("seller_space", slug=slug))

    @app.route("/vendeur/<slug>/deliverers/<int:deliverer_id>/verify", methods=["POST"])
    @seller_session_required
    def seller_verify_deliverer(slug, deliverer_id):
        shop = SellerShop.query.filter_by(slug=slug).first_or_404()
        current_admin = SellerAdmin.query.filter_by(id=session.get("seller_admin_id"), shop_id=shop.id, is_active=True).first()
        if not current_admin or (not current_admin.is_owner and not current_admin.has_permission("manage_deliverers")):
            flash("Permission insuffisante pour gérer les livreurs.", "error")
            return redirect(url_for("seller_deliverers_page", slug=slug))
        d = SellerDeliverer.query.filter_by(id=deliverer_id, shop_id=shop.id).first_or_404()
        if d.verification_status == "verified":
            d.verification_status = "pending"
            d.verified_by = None
            d.verified_at = None
            flash("La vérification du livreur a été annulée.", "success")
        else:
            d.verification_status = "verified"
            d.verified_by = None  # Seller admins don't link to platform admins
            d.verified_at = datetime.utcnow()
            flash("Livreur marqué comme vérifié.", "success")
        db.session.commit()
        return redirect(url_for("seller_deliverers_page", slug=slug))

    def _seller_page_context(slug, required_permission=None):
        shop = SellerShop.query.filter_by(slug=slug).first_or_404()
        settings = _get_platform_settings()
        sid = session.get("seller_admin_id")
        seller_admin = SellerAdmin.query.filter_by(id=sid, shop_id=shop.id, is_active=True).first() if sid else None
        if not seller_admin:
            flash("Veuillez vous connecter à l'espace vendeur.", "warning")
            return None, None, None, redirect(url_for("seller_entry_for_shop_key", shop_key=_shop_access_key(shop)))
        seller_permissions = {
            p.strip()
            for p in (seller_admin.permissions or "").replace("|", ",").split(",")
            if p.strip()
        }
        if required_permission and (not seller_admin.is_owner) and (required_permission not in seller_permissions):
            flash("Vous n'avez pas la permission d'accéder à cette page.", "error")
            return None, None, None, redirect(url_for("seller_dashboard_page", slug=slug))

        products = SellerProduct.query.filter_by(shop_id=shop.id).order_by(SellerProduct.created_at.desc()).all()
        orders = SellerOrder.query.filter_by(shop_id=shop.id).order_by(SellerOrder.created_at.desc()).all()
        deliverers = SellerDeliverer.query.filter_by(shop_id=shop.id).order_by(SellerDeliverer.created_at.desc()).all()
        clients = SellerCustomer.query.filter_by(shop_id=shop.id).order_by(SellerCustomer.created_at.desc()).all()
        team_admins = SellerAdmin.query.filter_by(shop_id=shop.id, is_active=True).order_by(SellerAdmin.created_at.desc()).all()

        category_counts = {}
        for p in products:
            key = (p.category or "Sans catégorie").strip() or "Sans catégorie"
            category_counts[key] = category_counts.get(key, 0) + 1

        events = []
        for o in orders[:20]:
            events.append({"kind": "Commande", "label": o.order_number, "by": o.customer_name or "Client", "created_at": o.created_at})
        for d in deliverers[:20]:
            events.append({"kind": "Livreur", "label": f"{d.first_name} {d.last_name}".strip(), "by": d.email, "created_at": d.created_at})
        for c in clients[:20]:
            events.append({"kind": "Client", "label": f"{c.first_name} {c.last_name}".strip(), "by": c.email, "created_at": c.created_at})
        for a in team_admins[:20]:
            events.append({"kind": "Admin", "label": f"{a.first_name} {a.last_name}".strip(), "by": a.email, "created_at": a.created_at})
        events.sort(key=lambda e: e.get("created_at") or datetime.min, reverse=True)

        now = datetime.utcnow()
        week_start = now - timedelta(days=now.weekday())
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        week_end = week_start + timedelta(days=7)
        weekly_progress = {}
        for d in deliverers:
            delivered_count = (
                SellerOrder.query.filter_by(shop_id=shop.id, deliverer_id=d.id)
                .filter(SellerOrder.status == "delivered")
                .filter(SellerOrder.created_at >= week_start)
                .filter(SellerOrder.created_at < week_end)
                .count()
            )
            bonus_count = delivered_count // 8
            weekly_progress[d.id] = {
                "count": delivered_count,
                "percent": min(100, int(((delivered_count % 8) / 8) * 100)) if delivered_count else 0,
                "eligible": bonus_count > 0,
                "outstanding": bonus_count,
            }

        root_url = request.url_root.rstrip("/")
        shop_key = _shop_access_key(shop)
        context = {
            "settings": settings,
            "products": products,
            "orders": orders,
            "deliverers": deliverers,
            "clients": clients,
            "team_admins": team_admins,
            "seller_permissions": seller_permissions,
            "permission_labels": SELLER_PERMISSION_LABELS,
            "category_counts": category_counts,
            "weekly_progress": weekly_progress,
            "task_events": events[:60],
            "stats": {
                "total_products": len(products),
                "total_orders": len(orders),
                "total_deliverers": len(deliverers),
                "total_clients": len(clients),
                "total_admins": len(team_admins),
                "total_revenue": sum(float(o.total_amount or 0.0) for o in orders),
            },
            "seller_space_url": f"{root_url}/{shop_key}/vendeur",
            "shop_public_url": f"{root_url}/{shop_key}",
            "deliverer_space_url": f"{root_url}{url_for('deliverer_space', slug=shop.slug)}",
            "deliverer_entry_url": f"{root_url}/{shop_key}/livreur",
            "countries": Countries,
        }
        return shop, seller_admin, context, None

    @app.route("/vendeur/<slug>/dashboard")
    @seller_session_required
    def seller_dashboard_page(slug):
        shop, admin, context, redirect_response = _seller_page_context(slug)
        if redirect_response:
            return redirect_response
        return render_template("vendeur/seller_space.html", shop=shop, admin=admin, active_page="dashboard", **context)

    @app.route("/vendeur/<slug>/products")
    @seller_session_required
    def seller_products_page(slug):
        shop, admin, context, redirect_response = _seller_page_context(slug, required_permission="manage_products")
        if redirect_response:
            return redirect_response
        return render_template("vendeur/products.html", shop=shop, admin=admin, active_page="products", **context)

    @app.route("/vendeur/<slug>/orders")
    @seller_session_required
    def seller_orders_page(slug):
        shop, admin, context, redirect_response = _seller_page_context(slug, required_permission="manage_orders")
        if redirect_response:
            return redirect_response
        return render_template("vendeur/orders.html", shop=shop, admin=admin, active_page="orders", **context)

    @app.route("/vendeur/<slug>/orders/<int:order_id>")
    @seller_session_required
    def seller_order_detail_page(slug, order_id):
        shop, admin, context, redirect_response = _seller_page_context(slug, required_permission="manage_orders")
        if redirect_response:
            return redirect_response
        order = SellerOrder.query.filter_by(id=order_id, shop_id=shop.id).first_or_404()
        return render_template("vendeur/order_detail.html", shop=shop, admin=admin, order=order, active_page="orders", **context)

    @app.route("/vendeur/<slug>/deliverers")
    @seller_session_required
    def seller_deliverers_page(slug):
        shop, admin, context, redirect_response = _seller_page_context(slug, required_permission="manage_deliverers")
        if redirect_response:
            return redirect_response
        return render_template("vendeur/deliverers.html", shop=shop, admin=admin, active_page="deliverers", **context)

    @app.route("/vendeur/<slug>/deliverers/<int:deliverer_id>")
    @seller_session_required
    def seller_deliverer_view_page(slug, deliverer_id):
        shop, admin, context, redirect_response = _seller_page_context(slug, required_permission="manage_deliverers")
        if redirect_response:
            return redirect_response
        deliverer = SellerDeliverer.query.filter_by(id=deliverer_id, shop_id=shop.id).first_or_404()
        return render_template("vendeur/deliverer_view.html", shop=shop, admin=admin, deliverer=deliverer, active_page="deliverers", **context)

    @app.route("/vendeur/<slug>/clients")
    @seller_session_required
    def seller_clients_page(slug):
        shop, admin, context, redirect_response = _seller_page_context(slug, required_permission="manage_clients")
        if redirect_response:
            return redirect_response
        return render_template("vendeur/clients.html", shop=shop, admin=admin, active_page="clients", **context)

    @app.route("/vendeur/<slug>/categories")
    @seller_session_required
    def seller_categories_page(slug):
        shop, admin, context, redirect_response = _seller_page_context(slug, required_permission="manage_categories")
        if redirect_response:
            return redirect_response
        return render_template("vendeur/categories.html", shop=shop, admin=admin, active_page="categories", **context)

    @app.route("/vendeur/<slug>/admins")
    @seller_session_required
    def seller_admins_page(slug):
        shop, admin, context, redirect_response = _seller_page_context(slug, required_permission="manage_admins")
        if redirect_response:
            return redirect_response
        return render_template("vendeur/admins.html", shop=shop, admin=admin, active_page="admins", **context)

    @app.route("/vendeur/<slug>/admins/<int:admin_id>")
    @seller_session_required
    def seller_admin_view_page(slug, admin_id):
        shop, admin, context, redirect_response = _seller_page_context(slug, required_permission="manage_admins")
        if redirect_response:
            return redirect_response
        member = SellerAdmin.query.filter_by(id=admin_id, shop_id=shop.id, is_active=True).first_or_404()
        return render_template("vendeur/admin_view.html", shop=shop, admin=admin, member=member, active_page="admins", **context)

    @app.route("/vendeur/<slug>/admins/add", methods=["POST"])
    @seller_session_required
    def seller_add_admin(slug):
        shop = SellerShop.query.filter_by(slug=slug).first_or_404()
        current_admin = SellerAdmin.query.filter_by(id=session.get("seller_admin_id"), shop_id=shop.id, is_active=True).first_or_404()
        if (not current_admin.is_owner) and (not current_admin.has_permission("manage_admins")):
            flash("Permission insuffisante pour créer des membres d'équipe vendeur.", "error")
            return redirect(url_for("seller_admins_page", slug=slug))

        first_name = (request.form.get("first_name") or "").strip()
        last_name = (request.form.get("last_name") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        country_code = (request.form.get("country_code") or "").strip() or None
        phone_number = (request.form.get("phone_number") or "").strip() or None
        if not all([first_name, last_name, email]):
            flash("Champs administrateur incomplets.", "error")
            return redirect(url_for("seller_admins_page", slug=slug))
        if SellerAdmin.query.filter_by(email=email).first():
            flash("Cet email est déjà utilisé.", "error")
            return redirect(url_for("seller_admins_page", slug=slug))
        if phone_number and (len(phone_number) != 9 or not phone_number.isdigit()):
            flash("Le numéro de téléphone doit contenir exactement 9 chiffres.", "error")
            return redirect(url_for("seller_admins_page", slug=slug))

        allowed = set(SELLER_PERMISSION_LABELS.keys())
        picked = [p.strip() for p in request.form.getlist("permissions") if p and p.strip() in allowed]
        if "view_dashboard" not in picked:
            picked.insert(0, "view_dashboard")
        assigned_permissions = ",".join(sorted(set(picked)))

        generated_password = _generate_temp_password(10)
        member = SellerAdmin(
            shop_id=shop.id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            country_code=country_code,
            phone_number=phone_number,
            permissions=assigned_permissions,
            is_owner=False,
            is_active=True,
        )
        member.set_password(generated_password)
        db.session.add(member)
        db.session.commit()

        seller_login_url = f"{request.url_root.rstrip('/')}/{_shop_access_key(shop)}/vendeur"
        _send_email(
            email,
            f"Accès équipe vendeur - {shop.name}",
            f"Email: {email} | Mot de passe temporaire: {generated_password} | URL: {seller_login_url}",
            _email_shell(
                f"Accès équipe vendeur - {shop.name}",
                (
                    f"<p>Bonjour {first_name} {last_name},</p>"
                    f"<p>Vous avez été ajouté comme membre de l'équipe vendeur de <strong>{shop.name}</strong>.</p>"
                    f"<p>Email: <strong>{email}</strong><br>Mot de passe temporaire: <strong>{generated_password}</strong></p>"
                    f"<p>Connexion: <a href='{seller_login_url}'>{seller_login_url}</a></p>"
                ),
                f"{shop.name} - Espace vendeur",
                "#2563eb",
            ),
        )
        flash("Membre d'équipe vendeur ajouté. Mot de passe envoyé par email.", "success")
        return redirect(url_for("seller_admins_page", slug=slug))

    @app.route("/vendeur/<slug>/admins/<int:admin_id>/edit-permissions", methods=["POST"])
    @seller_session_required
    def seller_edit_admin_permissions(slug, admin_id):
        shop, current_admin, context, redirect_response = _seller_page_context(slug)
        if redirect_response:
            return redirect_response
        if not current_admin.is_owner:
            flash("Seul le propriétaire peut modifier les permissions.", "error")
            return redirect(url_for("seller_admins_page", slug=slug))
        
        target = SellerAdmin.query.filter_by(id=admin_id, shop_id=shop.id).first_or_404()
        if target.is_owner:
            flash("Impossible de modifier les permissions du propriétaire.", "error")
            return redirect(url_for("seller_admins_page", slug=slug))
        if target.id == current_admin.id:
            flash("Utilisez la page profil pour modifier vos propres permissions.", "error")
            return redirect(url_for("seller_admins_page", slug=slug))
        
        allowed = set(SELLER_PERMISSION_LABELS.keys())
        picked = [p.strip() for p in request.form.getlist("permissions") if p and p.strip() in allowed]
        if "view_dashboard" not in picked:
            picked.insert(0, "view_dashboard")
        permissions = ",".join(sorted(set(picked)))
        
        old_permissions = target.permissions
        target.permissions = permissions
        db.session.commit()
        record_activity(
            f"Modification permissions admin vendeur '{target.email}' pour {shop.name}",
            actor=current_admin,
            extra=f"old={old_permissions}, new={permissions}",
        )
        flash("Permissions administrateur mises à jour.", "success")
        return redirect(url_for("seller_admins_page", slug=slug))

    @app.route("/vendeur/<slug>/tasks")
    @seller_session_required
    def seller_tasks_page(slug):
        shop, admin, context, redirect_response = _seller_page_context(slug, required_permission="view_tasks")
        if redirect_response:
            return redirect_response
        return render_template("vendeur/tasks.html", shop=shop, admin=admin, active_page="tasks", **context)

    @app.route("/vendeur/<slug>/settings/page")
    @seller_session_required
    def seller_settings_page(slug):
        shop, admin, context, redirect_response = _seller_page_context(slug, required_permission="manage_settings")
        if redirect_response:
            return redirect_response
        return render_template("vendeur/settings.html", shop=shop, admin=admin, active_page="settings", **context)

    @app.route("/vendeur/<slug>/about")
    @seller_session_required
    def seller_about_page(slug):
        shop, admin, context, redirect_response = _seller_page_context(slug, required_permission="view_about")
        if redirect_response:
            return redirect_response
        return render_template("vendeur/about.html", shop=shop, admin=admin, active_page="about", **context)

    @app.route("/vendeur/<slug>/about/update", methods=["POST"])
    @seller_session_required
    def seller_update_about_content(slug):
        shop = SellerShop.query.filter_by(slug=slug).first_or_404()
        current_admin = SellerAdmin.query.filter_by(id=session.get("seller_admin_id"), shop_id=shop.id, is_active=True).first_or_404()
        if not current_admin.is_owner:
            flash("Seul le propriétaire peut modifier le contenu.", "error")
            return redirect(url_for("seller_about_page", slug=slug))
        
        about_content = (request.form.get("about_content") or "").strip()
        shop.about_page_content = about_content
        db.session.commit()
        record_activity(
            f"Mise à jour du contenu À propos ({shop.name})",
            actor=current_admin,
            extra=f"length={len(about_content)}",
        )
        flash("Contenu mis à jour avec succès.", "success")
        return redirect(url_for("seller_about_page", slug=slug))

    @app.route("/vendeur/<slug>/access_requests")
    @seller_session_required
    def seller_access_requests_page(slug):
        shop, admin, context, redirect_response = _seller_page_context(slug, required_permission="manage_access_requests")
        if redirect_response:
            return redirect_response
        return render_template("vendeur/access_requests.html", shop=shop, admin=admin, active_page="access_requests", **context)

    @app.route("/vendeur/<slug>/admin_views")
    @seller_session_required
    def seller_admin_views_page(slug):
        return redirect(url_for("seller_admins_page", slug=slug), code=302)

    @app.route("/vendeur/<slug>/deliverer")
    @seller_session_required
    def seller_deliverer_page(slug):
        return redirect(url_for("seller_deliverers_page", slug=slug), code=302)
    @app.route("/<shop_key>")
    def shop_public_entry(shop_key):
        reserved = {"livreur", "vendeur", "admin", "about", "set-currency"}
        if shop_key in reserved:
            if shop_key == "livreur":
                return redirect(url_for("deliverer_entrypoint"))
            if shop_key == "vendeur":
                return redirect(url_for("seller_entrypoint"))
            if shop_key == "admin":
                return redirect(url_for("admin_login_page"))
            if shop_key == "about":
                return redirect(url_for("about"))
            if shop_key == "set-currency":
                return redirect(url_for("tekanayo_portal"))
        shop = _resolve_shop_access_key(shop_key)
        if not shop:
            return redirect(url_for("tekanayo_portal"))
        canonical_key = _shop_access_key(shop)
        if (shop_key or "").strip().lower() != canonical_key:
            return redirect(url_for("shop_public_entry", shop_key=canonical_key, **request.args), code=302)
        selected_category = request.args.get("category", "").strip()
        search_term = request.args.get("q", "").strip()
        selected_product = request.args.get("product_id")
        view = _build_shop_page_context(shop, selected_category, search_term, selected_product)
        return render_template("clientvendeur/shoptheme/index.html", shop=shop, **view)

    @app.route("/<shop_key>/livreur", methods=["GET", "POST"])
    def deliverer_entry_for_shop_key(shop_key):
        shop = _resolve_shop_access_key(shop_key)
        if not shop:
            flash("Boutique introuvable.", "error")
            return redirect(url_for("deliverer_entrypoint"))
        canonical_key = _shop_access_key(shop)
        if request.method == "GET":
            return render_template(
                "deliverer/deliverertheme/deliverer_entry.html",
                deliverer_brand_name=shop.name,
                selected_shop=shop,
                deliverer_login_action=url_for("deliverer_entry_for_shop_key", shop_key=canonical_key),
            )

        email = (request.form.get("email") or "").strip().lower()
        password = (request.form.get("password") or "").strip()
        found = SellerDeliverer.query.filter_by(email=email, shop_id=shop.id, is_active=True).first()
        if not found or not found.check_password(password):
            flash("Connexion livreur invalide pour cette boutique.", "error")
            return redirect(url_for("deliverer_entry_for_shop_key", shop_key=canonical_key))
        session["seller_deliverer_id"] = found.id
        return redirect(url_for("deliverer_space", slug=shop.slug))

    @app.route("/boutique<int:shop_id>")
    def seller_shop_by_id(shop_id):
        shop = SellerShop.query.filter_by(id=shop_id, is_active=True).first_or_404()
        return redirect(url_for("shop_public_entry", shop_key=_shop_access_key(shop), **request.args))

    @app.route("/boutique/<slug>")
    def seller_shop(slug):
        shop = _resolve_shop_identifier(slug)
        if not shop:
            flash("Boutique introuvable.", "error")
            return redirect(url_for("tekanayo_portal"))
        return redirect(url_for("shop_public_entry", shop_key=_shop_access_key(shop), **request.args), code=302)

    @app.route("/boutique/<slug>/categories")
    @app.route("/<slug>/categories")
    def seller_shop_categories(slug):
        shop = _resolve_shop_identifier(slug)
        if not shop:
            flash("Boutique introuvable.", "error")
            return redirect(url_for("tekanayo_portal"))
        selected_category = request.args.get("category", "").strip()
        search_term = request.args.get("q", "").strip()
        view = _build_shop_page_context(shop, selected_category, search_term)
        view["page"] = 1
        view["total_pages"] = 1
        return render_template("clientvendeur/shoptheme/categories.html", shop=shop, **view)

    @app.route("/boutique/<slug>/products")
    @app.route("/<slug>/products")
    def seller_shop_products(slug):
        shop = _resolve_shop_identifier(slug)
        if not shop:
            flash("Boutique introuvable.", "error")
            return redirect(url_for("tekanayo_portal"))
        selected_category = request.args.get("category", "").strip()
        search_term = request.args.get("q", "").strip()
        view = _build_shop_page_context(shop, selected_category, search_term)
        return render_template("clientvendeur/shoptheme/products.html", shop=shop, **view)

    @app.route("/boutique/<slug>/product/<int:product_id>")
    @app.route("/<slug>/product/<int:product_id>")
    def seller_shop_product_detail(slug, product_id):
        shop = _resolve_shop_identifier(slug)
        if not shop:
            flash("Boutique introuvable.", "error")
            return redirect(url_for("tekanayo_portal"))
        view = _build_shop_page_context(shop, selected_product_id=product_id)
        product = view.get("selected_product")
        if not product:
            flash("Produit introuvable.", "error")
            return redirect(url_for("seller_shop_products", slug=_shop_access_key(shop)))
        return render_template("clientvendeur/shoptheme/product_detail.html", shop=shop, product=product, **view)

    @app.route("/boutique/<slug>/about")
    @app.route("/<slug>/about")
    def seller_shop_about(slug):
        shop = _resolve_shop_identifier(slug)
        if not shop:
            flash("Boutique introuvable.", "error")
            return redirect(url_for("tekanayo_portal"))
        view = _build_shop_page_context(shop)
        return render_template("clientvendeur/shoptheme/about.html", shop=shop, **view)

    @app.route("/boutique/<slug>/legal")
    @app.route("/<slug>/legal")
    def seller_shop_legal(slug):
        shop = _resolve_shop_identifier(slug)
        if not shop:
            flash("Boutique introuvable.", "error")
            return redirect(url_for("tekanayo_portal"))
        view = _build_shop_page_context(shop)
        return render_template("clientvendeur/shoptheme/legal.html", shop=shop, **view)

    @app.route("/boutique/<slug>/terms")
    @app.route("/<slug>/terms")
    def seller_shop_terms(slug):
        shop = _resolve_shop_identifier(slug)
        if not shop:
            flash("Boutique introuvable.", "error")
            return redirect(url_for("tekanayo_portal"))
        view = _build_shop_page_context(shop)
        return render_template("clientvendeur/shoptheme/terms.html", shop=shop, **view)

    @app.route("/boutique/<slug>/returns")
    @app.route("/<slug>/returns")
    def seller_shop_returns(slug):
        shop = _resolve_shop_identifier(slug)
        if not shop:
            flash("Boutique introuvable.", "error")
            return redirect(url_for("tekanayo_portal"))
        view = _build_shop_page_context(shop)
        return render_template("clientvendeur/shoptheme/returns.html", shop=shop, **view)

    @app.route("/boutique/<slug>/privacy")
    @app.route("/<slug>/privacy")
    def seller_shop_privacy(slug):
        shop = _resolve_shop_identifier(slug)
        if not shop:
            flash("Boutique introuvable.", "error")
            return redirect(url_for("tekanayo_portal"))
        view = _build_shop_page_context(shop)
        return render_template("clientvendeur/shoptheme/privacy.html", shop=shop, **view)

    @app.route("/boutique/<slug>/cart")
    @app.route("/<slug>/cart")
    def seller_shop_cart(slug):
        shop = _resolve_shop_identifier(slug)
        if not shop:
            flash("Boutique introuvable.", "error")
            return redirect(url_for("tekanayo_portal"))
        view = _build_shop_page_context(shop)
        view["total"] = view.get("cart_total", 0.0)
        return render_template("clientvendeur/shoptheme/cart.html", shop=shop, **view)

    @app.route("/boutique/<slug>/checkout", methods=["GET"])
    @app.route("/<slug>/checkout", methods=["GET"])
    def seller_shop_checkout_page(slug):
        shop = _resolve_shop_identifier(slug)
        if not shop:
            flash("Boutique introuvable.", "error")
            return redirect(url_for("tekanayo_portal"))
        view = _build_shop_page_context(shop)
        if not view.get("cart_items"):
            flash("Votre panier est vide.", "warning")
            return redirect(url_for("seller_shop_products", slug=_shop_access_key(shop)))
        customer = view.get("shop_customer")
        view["prefill"] = {
            "first_name": customer.first_name if customer else "",
            "last_name": customer.last_name if customer else "",
            "email": customer.email if customer else "",
            "phone": customer.phone if customer else "",
            "shipping_address": customer.address if customer else "",
        }
        return render_template("clientvendeur/shoptheme/checkout.html", shop=shop, **view)

    @app.route("/boutique/<slug>/login", methods=["GET"])
    @app.route("/<slug>/login", methods=["GET"])
    def seller_shop_login(slug):
        shop = _resolve_shop_identifier(slug)
        if not shop:
            flash("Boutique introuvable.", "error")
            return redirect(url_for("tekanayo_portal"))
        view = _build_shop_page_context(shop)
        return render_template("clientvendeur/shoptheme/login.html", shop=shop, **view)

    @app.route("/boutique/<slug>/register", methods=["GET"])
    @app.route("/<slug>/register", methods=["GET"])
    def seller_shop_register(slug):
        shop = _resolve_shop_identifier(slug)
        if not shop:
            flash("Boutique introuvable.", "error")
            return redirect(url_for("tekanayo_portal"))
        view = _build_shop_page_context(shop)
        return render_template("clientvendeur/shoptheme/register.html", shop=shop, **view)

    @app.route("/boutique/<slug>/reset_password", methods=["GET", "POST"])
    @app.route("/<slug>/reset_password", methods=["GET", "POST"])
    def seller_shop_reset_request(slug):
        shop = _resolve_shop_identifier(slug)
        if not shop:
            flash("Boutique introuvable.", "error")
            return redirect(url_for("tekanayo_portal"))
        view = _build_shop_page_context(shop)
        if request.method == "GET":
            return render_template("clientvendeur/shoptheme/reset_request.html", shop=shop, **view)

        email = (request.form.get("email") or "").strip().lower()
        customer = SellerCustomer.query.filter_by(shop_id=shop.id, email=email).first() if email else None
        if customer:
            token = _generate_reset_token("shop_customer", customer.id)
            reset_url = f"{request.url_root.rstrip('/')}{url_for('seller_shop_reset_with_token', slug=_shop_access_key(shop), token=token)}"
            html = _email_shell(
                f"Réinitialisation mot de passe - {shop.name}",
                (
                    f"<p>Bonjour {customer.first_name},</p>"
                    f"<p>Utilisez ce lien pour choisir un nouveau mot de passe :</p>"
                    f"<p><a href='{reset_url}'>{reset_url}</a></p>"
                ),
                shop.name,
                "#0f766e",
            )
            _send_email(customer.email, f"Reset password - {shop.name}", f"Lien reset: {reset_url}", html)

        flash("Si cet email existe, un lien de réinitialisation a été envoyé.", "success")
        return redirect(url_for("seller_shop_login", slug=_shop_access_key(shop)))

    @app.route("/boutique/<slug>/reset_password/<token>", methods=["GET", "POST"])
    @app.route("/<slug>/reset_password/<token>", methods=["GET", "POST"])
    def seller_shop_reset_with_token(slug, token):
        shop = _resolve_shop_identifier(slug)
        if not shop:
            flash("Boutique introuvable.", "error")
            return redirect(url_for("tekanayo_portal"))
        payload = _verify_reset_token(token)
        if not payload or payload.get("role") != "shop_customer":
            flash("Lien invalide ou expiré.", "error")
            return redirect(url_for("seller_shop_reset_request", slug=_shop_access_key(shop)))

        customer = SellerCustomer.query.filter_by(id=payload.get("id"), shop_id=shop.id).first()
        if not customer:
            flash("Compte client introuvable.", "error")
            return redirect(url_for("seller_shop_reset_request", slug=_shop_access_key(shop)))

        view = _build_shop_page_context(shop)
        if request.method == "GET":
            return render_template("clientvendeur/shoptheme/reset_password.html", shop=shop, token=token, **view)

        password = (request.form.get("password") or "").strip()
        if len(password) < 6:
            flash("Le mot de passe doit contenir au moins 6 caractères.", "error")
            return redirect(url_for("seller_shop_reset_with_token", slug=_shop_access_key(shop), token=token))

        customer.set_password(password)
        db.session.commit()
        flash("Mot de passe réinitialisé avec succès.", "success")
        return redirect(url_for("seller_shop_login", slug=_shop_access_key(shop)))

    @app.route("/boutique/<slug>/profile", methods=["GET"])
    @app.route("/<slug>/profile", methods=["GET"])
    def seller_shop_profile(slug):
        shop = _resolve_shop_identifier(slug)
        if not shop:
            flash("Boutique introuvable.", "error")
            return redirect(url_for("tekanayo_portal"))
        view = _build_shop_page_context(shop)
        if not view.get("shop_customer"):
            flash("Connectez-vous pour accéder à votre profil.", "warning")
            return redirect(url_for("seller_shop_login", slug=_shop_access_key(shop)))
        return render_template("clientvendeur/shoptheme/profile.html", shop=shop, **view)

    @app.route("/boutique/<slug>/orders")
    @app.route("/<slug>/orders")
    def seller_shop_orders(slug):
        shop = _resolve_shop_identifier(slug)
        if not shop:
            flash("Boutique introuvable.", "error")
            return redirect(url_for("tekanayo_portal"))
        view = _build_shop_page_context(shop)
        if not view.get("shop_customer"):
            flash("Connectez-vous pour consulter vos commandes.", "warning")
            return redirect(url_for("seller_shop_login", slug=_shop_access_key(shop)))
        return render_template("clientvendeur/shoptheme/orders.html", shop=shop, orders=view.get("customer_orders", []), **view)

    @app.route("/boutique/<slug>/orders/<int:order_id>")
    @app.route("/<slug>/orders/<int:order_id>")
    def seller_shop_order_detail(slug, order_id):
        shop = _resolve_shop_identifier(slug)
        if not shop:
            flash("Boutique introuvable.", "error")
            return redirect(url_for("tekanayo_portal"))
        view = _build_shop_page_context(shop)
        customer = view.get("shop_customer")
        if not customer:
            flash("Connectez-vous pour consulter vos commandes.", "warning")
            return redirect(url_for("seller_shop_login", slug=_shop_access_key(shop)))
        order = (
            SellerOrder.query
            .filter_by(id=order_id, shop_id=shop.id, customer_id=customer.id)
            .first()
        )
        if not order:
            flash("Commande introuvable.", "error")
            return redirect(url_for("seller_shop_orders", slug=_shop_access_key(shop)))
        return render_template("clientvendeur/shoptheme/order_detail.html", shop=shop, order=order, **view)

    @app.route("/boutique/<slug>/orders/<int:order_id>/invoice")
    @app.route("/<slug>/orders/<int:order_id>/invoice")
    def seller_shop_customer_invoice(slug, order_id):
        shop = _resolve_shop_identifier(slug)
        if not shop:
            flash("Boutique introuvable.", "error")
            return redirect(url_for("tekanayo_portal"))
        customer = _get_shop_customer(shop.id)
        if not customer:
            flash("Connectez-vous pour télécharger votre facture.", "warning")
            return redirect(url_for("seller_shop_login", slug=_shop_access_key(shop)))
        order = (
            SellerOrder.query
            .filter_by(id=order_id, shop_id=shop.id, customer_id=customer.id)
            .first()
        )
        if not order:
            flash("Commande introuvable.", "error")
            return redirect(url_for("seller_shop_orders", slug=_shop_access_key(shop)))
        if order.status != "delivered":
            flash("La facture est disponible après la livraison.", "warning")
            return redirect(url_for("seller_shop_order_detail", slug=_shop_access_key(shop), order_id=order.id))
        pdf = generate_seller_invoice_pdf(order, shop)
        return send_file(pdf, as_attachment=True, mimetype="application/pdf", download_name=f"facture_{order.order_number}.pdf")

    @app.route("/boutique/<slug>/forum")
    @app.route("/<slug>/forum")
    def seller_shop_forum(slug):
        shop = _resolve_shop_identifier(slug)
        if not shop:
            flash("Boutique introuvable.", "error")
            return redirect(url_for("tekanayo_portal"))
        view = _build_shop_page_context(shop)
        return render_template("clientvendeur/shoptheme/forum.html", shop=shop, **view)

    @app.route("/boutique/<slug>/cart/add/<int:product_id>", methods=["POST"])
    @app.route("/<slug>/cart/add/<int:product_id>", methods=["POST"])
    def seller_shop_add_to_cart(slug, product_id):
        shop = _resolve_shop_identifier(slug)
        if not shop:
            flash("Boutique introuvable.", "error")
            return redirect(url_for("tekanayo_portal"))
        product = SellerProduct.query.filter_by(id=product_id, shop_id=shop.id, is_active=True).first_or_404()
        qty = max(1, int(request.form.get("quantity") or 1))
        if product.quantity <= 0:
            flash("Produit en rupture de stock.", "error")
            return redirect(url_for("seller_shop_product_detail", slug=_shop_access_key(shop), product_id=product.id))

        cart = _get_shop_cart(shop.id)
        found = False
        for item in cart:
            if item["product_id"] == product.id:
                item["quantity"] = min(max(product.quantity, 1), item["quantity"] + qty)
                found = True
                break
        if not found:
            cart.append({"product_id": product.id, "quantity": min(qty, max(product.quantity, 1))})
        _set_shop_cart(shop.id, cart)
        flash(f"{product.name} ajouté au panier.", "success")
        return redirect(url_for("seller_shop_cart", slug=_shop_access_key(shop)))

    @app.route("/boutique/<slug>/cart/update/<int:product_id>", methods=["POST"])
    @app.route("/<slug>/cart/update/<int:product_id>", methods=["POST"])
    def seller_shop_update_cart(slug, product_id):
        shop = _resolve_shop_identifier(slug)
        if not shop:
            flash("Boutique introuvable.", "error")
            return redirect(url_for("tekanayo_portal"))
        product = SellerProduct.query.filter_by(id=product_id, shop_id=shop.id, is_active=True).first_or_404()
        qty = int(request.form.get("quantity") or 1)
        cart = _get_shop_cart(shop.id)
        next_cart = []
        for item in cart:
            if item["product_id"] == product.id:
                if qty > 0:
                    item["quantity"] = min(max(product.quantity, 1), qty)
                    next_cart.append(item)
            else:
                next_cart.append(item)
        _set_shop_cart(shop.id, next_cart)
        flash("Panier mis à jour.", "success")
        return redirect(url_for("seller_shop_cart", slug=_shop_access_key(shop)))

    @app.route("/boutique/<slug>/cart/remove/<int:product_id>", methods=["POST"])
    @app.route("/<slug>/cart/remove/<int:product_id>", methods=["POST"])
    def seller_shop_remove_from_cart(slug, product_id):
        shop = _resolve_shop_identifier(slug)
        if not shop:
            flash("Boutique introuvable.", "error")
            return redirect(url_for("tekanayo_portal"))
        cart = [item for item in _get_shop_cart(shop.id) if item["product_id"] != int(product_id)]
        _set_shop_cart(shop.id, cart)
        flash("Produit retiré du panier.", "success")
        return redirect(url_for("seller_shop_cart", slug=_shop_access_key(shop)))

    @app.route("/boutique/<slug>/cart/clear", methods=["POST"])
    @app.route("/<slug>/cart/clear", methods=["POST"])
    def seller_shop_clear_cart(slug):
        shop = _resolve_shop_identifier(slug)
        if not shop:
            flash("Boutique introuvable.", "error")
            return redirect(url_for("tekanayo_portal"))
        _set_shop_cart(shop.id, [])
        flash("Panier vidé.", "success")
        return redirect(url_for("seller_shop_cart", slug=_shop_access_key(shop)))

    @app.route("/boutique/<slug>/customer/register", methods=["POST"])
    @app.route("/<slug>/customer/register", methods=["POST"])
    def seller_shop_customer_register(slug):
        shop = _resolve_shop_identifier(slug)
        if not shop:
            flash("Boutique introuvable.", "error")
            return redirect(url_for("tekanayo_portal"))

        first_name = (request.form.get("first_name") or "").strip()
        last_name = (request.form.get("last_name") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        phone = (request.form.get("phone") or "").strip()
        address = (request.form.get("address") or "").strip()
        profile_picture = (request.form.get("profile_picture") or "").strip() or None
        password = (request.form.get("password") or "").strip()

        if not all([first_name, last_name, email, password]) or "@" not in email or len(password) < 6:
            flash("Informations client invalides.", "error")
            return redirect(url_for("seller_shop_register", slug=_shop_access_key(shop)))

        existing = SellerCustomer.query.filter_by(shop_id=shop.id, email=email).first()
        if existing:
            flash("Cet email est déjà utilisé dans cette boutique.", "error")
            return redirect(url_for("seller_shop_register", slug=_shop_access_key(shop)))

        customer = SellerCustomer(
            shop_id=shop.id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone or None,
            address=address or None,
            profile_picture=profile_picture,
        )
        customer.set_password(password)
        db.session.add(customer)
        db.session.commit()

        root_url = request.url_root.rstrip("/")
        shop_key = _shop_access_key(shop)
        shop_link = f"{root_url}/{shop_key}"
        _send_email(
            customer.email,
            f"Bienvenue chez {shop.name}",
            f"Votre compte client est créé. Accès boutique: {shop_link}",
            _email_shell(
                f"Bienvenue chez {shop.name}",
                (
                    f"<div style='text-align:center;padding:20px 0;'>"
                    f"<div style='font-size:48px;margin-bottom:10px;'>🎉</div>"
                    f"<h1 style='color:#1e293b;margin:0;font-size:24px;'>Bienvenue {customer.first_name} !</h1>"
                    f"</div>"
                    f"<p style='font-size:16px;color:#475569;line-height:1.6;'>"
                    f"Votre compte client a été créé avec succès sur <strong style='color:#059669;'>{shop.name}</strong> !"
                    f"</p>"
                    f"<div style='background:linear-gradient(135deg,#ecfdf5,#d1fae5);padding:20px;border-radius:12px;margin:20px 0;border:1px solid #a7f3d0;'>"
                    f"<h3 style='margin:0 0 15px 0;color:#059669;font-size:16px;'>🛍️ Votre compte client</h3>"
                    f"<table style='width:100%;border-collapse:collapse;'>"
                    f"<tr><td style='padding:8px 0;color:#6b7280;font-size:14px;'>👤 Nom</td><td style='padding:8px 0;font-weight:bold;color:#1e293b;'>{customer.first_name} {customer.last_name}</td></tr>"
                    f"<tr><td style='padding:8px 0;color:#6b7280;font-size:14px;'>📧 Email</td><td style='padding:8px 0;font-weight:bold;color:#1e293b;'>{customer.email}</td></tr>"
                    f"</table>"
                    f"</div>"
                    f"<div style='text-align:center;margin:25px 0;'>"
                    f"<a href='{shop_link}' style='display:inline-block;background:#059669;color:white;text-decoration:none;padding:14px 32px;border-radius:8px;font-weight:bold;font-size:16px;'>🌐 Accéder à la boutique</a>"
                    f"</div>"
                    f"<div style='background:#f0fdf4;padding:15px;border-radius:8px;margin:20px 0;border:1px solid #bbf7d0;'>"
                    f"<h4 style='margin:0 0 8px 0;color:#16a34a;font-size:14px;'>💡 Ce que vous pouvez faire</h4>"
                    f"<ul style='margin:0;padding-left:20px;color:#475569;font-size:13px;line-height:1.8;'>"
                    f"<li>Parcourir les produits et catégories</li>"
                    f"<li>Ajouter des articles à votre panier</li>"
                    f"<li>Passer des commandes en ligne</li>"
                    f"<li>Suivre vos commandes en temps réel</li>"
                    f"<li>Télécharger vos factures</li>"
                    f"</ul>"
                    f"</div>"
                ),
                shop.name,
                "#059669",
            ),
        )

        _set_shop_customer(shop.id, customer.id)
        flash("Compte client créé et connecté.", "success")
        return redirect(url_for("seller_shop_profile", slug=_shop_access_key(shop)))

    @app.route("/boutique/<slug>/customer/login", methods=["POST"])
    @app.route("/<slug>/customer/login", methods=["POST"])
    def seller_shop_customer_login(slug):
        shop = _resolve_shop_identifier(slug)
        if not shop:
            flash("Boutique introuvable.", "error")
            return redirect(url_for("tekanayo_portal"))

        email = (request.form.get("email") or "").strip().lower()
        password = (request.form.get("password") or "").strip()
        customer = SellerCustomer.query.filter_by(shop_id=shop.id, email=email).first()
        if not customer or not customer.check_password(password):
            flash("Connexion client invalide.", "error")
            return redirect(url_for("seller_shop_login", slug=_shop_access_key(shop)))

        _set_shop_customer(shop.id, customer.id)
        flash("Connexion client réussie.", "success")
        return redirect(url_for("seller_shop_profile", slug=_shop_access_key(shop)))

    @app.route("/boutique/<slug>/customer/logout", methods=["GET", "POST"])
    @app.route("/<slug>/customer/logout", methods=["GET", "POST"])
    def seller_shop_customer_logout(slug):
        shop = _resolve_shop_identifier(slug)
        if not shop:
            flash("Boutique introuvable.", "error")
            return redirect(url_for("tekanayo_portal"))
        _set_shop_customer(shop.id, None)
        flash("Déconnexion client effectuée.", "success")
        return redirect(url_for("shop_public_entry", shop_key=_shop_access_key(shop)))

    @app.route("/boutique/<slug>/customer/profile", methods=["POST"])
    @app.route("/<slug>/customer/profile", methods=["POST"])
    def seller_shop_customer_profile(slug):
        shop = _resolve_shop_identifier(slug)
        if not shop:
            flash("Boutique introuvable.", "error")
            return redirect(url_for("tekanayo_portal"))
        customer = _get_shop_customer(shop.id)
        if not customer:
            flash("Connectez-vous pour modifier votre profil.", "error")
            return redirect(url_for("seller_shop_login", slug=_shop_access_key(shop)))

        customer.first_name = (request.form.get("first_name") or customer.first_name).strip()
        customer.last_name = (request.form.get("last_name") or customer.last_name).strip()
        
        # Handle phone number (from phone-input component)
        country_code = (request.form.get("country_code") or "").strip() or None
        phone_number = (request.form.get("phone_number") or "").strip() or None
        
        # Validate phone number: exactly 9 digits
        if phone_number and (len(phone_number) != 9 or not phone_number.isdigit()):
            flash("Le numéro de téléphone doit contenir exactement 9 chiffres.", "error")
            return redirect(url_for("seller_shop_profile", slug=_shop_access_key(shop)))
        
        customer.country_code = country_code
        customer.phone_number = phone_number
        customer.address = (request.form.get("address") or "").strip() or None
        uploaded_profile = _save_uploaded_image(request.files.get("profile_picture_file"), "seller/customer_profiles")
        if uploaded_profile:
            customer.profile_picture = uploaded_profile
        elif "profile_picture" in request.form:
            customer.profile_picture = (request.form.get("profile_picture") or "").strip() or None

        db.session.commit()
        flash("Profil client mis à jour.", "success")
        # Rediriger vers la page d'origine (portal ou boutique)
        referrer = request.referrer or url_for("seller_shop_profile", slug=_shop_access_key(shop))
        return redirect(referrer)

    @app.route("/boutique/<slug>/customer/change_password", methods=["POST"])
    @app.route("/<slug>/customer/change_password", methods=["POST"])
    def seller_shop_customer_change_password(slug):
        shop = _resolve_shop_identifier(slug)
        if not shop:
            flash("Boutique introuvable.", "error")
            return redirect(url_for("tekanayo_portal"))
        customer = _get_shop_customer(shop.id)
        if not customer:
            flash("Connectez-vous pour modifier votre profil.", "error")
            return redirect(url_for("seller_shop_login", slug=_shop_access_key(shop)))

        current_pwd = (request.form.get("current_password") or "").strip()
        new_pwd = (request.form.get("new_password") or "").strip()
        confirm_pwd = (request.form.get("confirm_password") or "").strip()

        if not customer.check_password(current_pwd):
            flash("Le mot de passe actuel est incorrect.", "error")
            return redirect(request.referrer or url_for("seller_shop_profile", slug=_shop_access_key(shop)))
        if len(new_pwd) < 6:
            flash("Le nouveau mot de passe doit contenir au moins 6 caractères.", "error")
            return redirect(request.referrer or url_for("seller_shop_profile", slug=_shop_access_key(shop)))
        if new_pwd != confirm_pwd:
            flash("Les mots de passe ne correspondent pas.", "error")
            return redirect(request.referrer or url_for("seller_shop_profile", slug=_shop_access_key(shop)))

        customer.set_password(new_pwd)
        db.session.commit()
        flash("Mot de passe mis à jour.", "success")
        return redirect(request.referrer or url_for("seller_shop_profile", slug=_shop_access_key(shop)))

    @app.route("/boutique/<slug>/customer/delete_account", methods=["POST"])
    @app.route("/<slug>/customer/delete_account", methods=["POST"])
    def seller_shop_customer_delete_account(slug):
        shop = _resolve_shop_identifier(slug)
        if not shop:
            flash("Boutique introuvable.", "error")
            return redirect(url_for("tekanayo_portal"))
        customer = _get_shop_customer(shop.id)
        if not customer:
            flash("Connectez-vous pour modifier votre profil.", "error")
            return redirect(url_for("seller_shop_login", slug=_shop_access_key(shop)))

        current_pwd = (request.form.get("current_password") or "").strip()
        confirm_delete = (request.form.get("confirm_delete") or "").strip().upper()
        if not customer.check_password(current_pwd):
            flash("Mot de passe incorrect.", "error")
            return redirect(request.referrer or url_for("seller_shop_profile", slug=_shop_access_key(shop)))
        if confirm_delete != "SUPPRIMER":
            flash('Merci de taper "SUPPRIMER" pour confirmer.', "error")
            return redirect(request.referrer or url_for("seller_shop_profile", slug=_shop_access_key(shop)))

        SellerOrder.query.filter_by(shop_id=shop.id, customer_id=customer.id).update({"customer_id": None})
        db.session.delete(customer)
        _set_shop_customer(shop.id, None)
        db.session.commit()
        flash("Votre compte client a été supprimé.", "success")
        return redirect(url_for("shop_public_entry", shop_key=_shop_access_key(shop)))

    @app.route("/boutique/<slug>/checkout", methods=["POST"])
    @app.route("/<slug>/checkout", methods=["POST"])
    def seller_shop_checkout(slug):
        shop = _resolve_shop_identifier(slug)
        if not shop:
            flash("Boutique introuvable.", "error")
            return redirect(url_for("tekanayo_portal"))

        cart_entries = _get_shop_cart(shop.id)
        if not cart_entries:
            flash("Votre panier est vide.", "warning")
            return redirect(url_for("seller_shop_cart", slug=_shop_access_key(shop)))

        products = SellerProduct.query.filter(
            SellerProduct.shop_id == shop.id,
            SellerProduct.id.in_([i["product_id"] for i in cart_entries]),
            SellerProduct.is_active.is_(True),
        ).all()
        product_map = {p.id: p for p in products}
        cart_total = 0.0
        for item in cart_entries:
            p = product_map.get(item["product_id"])
            if not p:
                flash("Un produit du panier n'est plus disponible.", "error")
                return redirect(url_for("seller_shop_cart", slug=_shop_access_key(shop)))
            if p.quantity < item["quantity"]:
                flash(f"Stock insuffisant pour {p.name}.", "error")
                return redirect(url_for("seller_shop_cart", slug=_shop_access_key(shop)))
            cart_total += float(p.price or 0.0) * int(item["quantity"])

        first_name = (request.form.get("first_name") or "").strip()
        last_name = (request.form.get("last_name") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        phone = (request.form.get("phone") or "").strip()
        shipping_address = (request.form.get("shipping_address") or "").strip()
        payment_method = (request.form.get("payment_method") or "cash_on_delivery").strip()

        customer = _get_shop_customer(shop.id)
        if customer:
            customer.first_name = first_name or customer.first_name
            customer.last_name = last_name or customer.last_name
            customer.phone = phone or customer.phone
            customer.address = shipping_address or customer.address
            if email and email != customer.email:
                clash = SellerCustomer.query.filter_by(shop_id=shop.id, email=email).first()
                if clash and clash.id != customer.id:
                    flash("Cet email est déjà utilisé dans la boutique.", "error")
                    return redirect(url_for("seller_shop_checkout_page", slug=_shop_access_key(shop)))
                customer.email = email
        else:
            if not all([first_name, last_name, email, phone, shipping_address]) or "@" not in email:
                flash("Informations client incomplètes.", "error")
                return redirect(url_for("seller_shop_checkout_page", slug=_shop_access_key(shop)))

        order_number = f"ORD-{shop.id}-{int(datetime.utcnow().timestamp())}-{secrets.token_hex(2).upper()}"
        order = SellerOrder(
            shop_id=shop.id,
            customer_id=customer.id if customer else None,
            order_number=order_number,
            customer_name=f"{first_name} {last_name}".strip() if not customer else f"{customer.first_name} {customer.last_name}".strip(),
            shipping_address=shipping_address or (customer.address if customer else None),
            total_amount=round(cart_total, 2),
            status="pending",
        )
        db.session.add(order)

        for item in cart_entries:
            p = product_map[item["product_id"]]
            p.quantity = max(0, p.quantity - int(item["quantity"]))

        db.session.commit()
        _set_shop_cart(shop.id, [])

        contact_email = email if not customer else customer.email
        if contact_email:
            body_html = _email_shell(
                f"Commande confirmée - {shop.name}",
                (
                    f"<p>Bonjour {order.customer_name},</p>"
                    f"<p>Votre commande <strong>{order.order_number}</strong> est enregistrée.</p>"
                    f"<p>Total: <strong>{order.total_amount:.2f} {shop.currency}</strong></p>"
                    f"<p>Paiement: {payment_method}</p>"
                ),
                shop.name,
                "#0f766e",
            )
            _send_email(contact_email, f"Confirmation commande - {shop.name}", f"Commande {order.order_number}", body_html)

        flash(f"Commande {order.order_number} validée avec succès.", "success")
        return redirect(url_for("seller_shop_orders", slug=_shop_access_key(shop)))

    @app.route("/livreur", methods=["GET", "POST"])
    @app.route("/livreur/", methods=["GET", "POST"])
    @app.route("/livreur/login", methods=["POST"])
    def deliverer_entrypoint():
        if request.method == "GET":
            settings = _get_platform_settings()
            shop_hint = (request.args.get("shop") or "").strip()
            hinted_shop = _resolve_shop_identifier(shop_hint) if shop_hint else None
            platform_brand = (settings.platform_name or "Tekanayo App").replace(" App", "").strip() or "Tekanayo"
            deliverer_brand_name = hinted_shop.name if hinted_shop else platform_brand
            return render_template(
                "deliverer/deliverertheme/deliverer_entry.html",
                deliverer_brand_name=deliverer_brand_name,
                selected_shop=hinted_shop,
                deliverer_login_action=url_for("deliverer_entry_for_shop_key", shop_key=_shop_access_key(hinted_shop)) if hinted_shop else url_for("deliverer_entrypoint"),
            )

        email = (request.form.get("email") or "").strip().lower()
        password = (request.form.get("password") or "").strip()
        shop_hint = (request.form.get("shop_slug") or request.args.get("shop") or "").strip()
        hinted_shop = _resolve_shop_identifier(shop_hint) if shop_hint else None
        found = SellerDeliverer.query.filter_by(email=email, is_active=True).first()
        if not found or not found.check_password(password):
            flash("Connexion livreur invalide.", "error")
            if hinted_shop:
                return redirect(url_for("deliverer_entry_for_shop_key", shop_key=_shop_access_key(hinted_shop)))
            return redirect(url_for("deliverer_entrypoint"))
        if not found.shop or not found.shop.is_active:
            flash("La boutique associée à ce compte livreur est inactive.", "error")
            return redirect(url_for("deliverer_entrypoint"))
        if hinted_shop and found.shop_id != hinted_shop.id:
            flash("Ce compte livreur n'appartient pas à cette boutique.", "error")
            return redirect(url_for("deliverer_entry_for_shop_key", shop_key=_shop_access_key(hinted_shop)))
        session["seller_deliverer_id"] = found.id
        return redirect(url_for("deliverer_space", slug=found.shop.slug))

    @app.route("/livreur/<slug>/login", methods=["GET", "POST"])
    def deliverer_entry_for_shop(slug):
        shop = SellerShop.query.filter_by(slug=slug, is_active=True).first_or_404()
        return redirect(url_for("deliverer_entry_for_shop_key", shop_key=_shop_access_key(shop)), code=307 if request.method == "POST" else 302)

    @app.route("/livreur/reset_password", methods=["GET", "POST"])
    def deliverer_reset_request():
        if request.method == "GET":
            return render_template("reset_request.html", role="livreur")
        email = (request.form.get("email") or "").strip().lower()
        deliverer = SellerDeliverer.query.filter_by(email=email, is_active=True).first()
        if deliverer and deliverer.shop:
            token = _generate_reset_token("deliverer", deliverer.id)
            reset_url = f"{request.url_root.rstrip('/')}{url_for('deliverer_reset_with_token', token=token)}"
            html = _email_shell(
                f"Réinitialisation livreur - {deliverer.shop.name}",
                f"<p>Bonjour {deliverer.first_name},</p><p>Utilisez ce lien pour définir un nouveau mot de passe:</p><p><a href='{reset_url}'>{reset_url}</a></p>",
                f"{deliverer.shop.name} - Livraison",
                "#059669",
            )
            _send_email(deliverer.email, f"Reset password livreur - {deliverer.shop.name}", f"Lien reset: {reset_url}", html)
        flash("Si cet email existe, un lien a été envoyé.", "success")
        return redirect(url_for("deliverer_entrypoint"))

    @app.route("/livreur/reset_password/<token>", methods=["GET", "POST"])
    def deliverer_reset_with_token(token):
        payload = _verify_reset_token(token)
        if not payload or payload.get("role") != "deliverer":
            flash("Lien invalide ou expiré.", "error")
            return redirect(url_for("deliverer_reset_request"))
        deliverer = SellerDeliverer.query.get(payload.get("id"))
        if not deliverer:
            flash("Compte introuvable.", "error")
            return redirect(url_for("deliverer_reset_request"))
        if request.method == "GET":
            return render_template("reset_form.html", role="livreur", token=token)
        password = (request.form.get("password") or "").strip()
        confirm = (request.form.get("confirm_password") or "").strip()
        if len(password) < 6 or password != confirm:
            flash("Mot de passe invalide ou confirmation différente.", "error")
            return redirect(url_for("deliverer_reset_with_token", token=token))
        deliverer.set_password(password)
        db.session.commit()
        flash("Mot de passe livreur mis à jour.", "success")
        return redirect(url_for("deliverer_entrypoint"))

    @app.route("/livreur/<slug>", methods=["GET", "POST"])
    def deliverer_space(slug):
        shop = SellerShop.query.filter_by(slug=slug).first_or_404()
        settings = _get_platform_settings()
        did = session.get("seller_deliverer_id")
        deliverer = SellerDeliverer.query.filter_by(id=did, shop_id=shop.id, is_active=True).first() if did else None
        if did and not deliverer:
            actual = SellerDeliverer.query.filter_by(id=did, is_active=True).first()
            if actual and actual.shop:
                return redirect(url_for("deliverer_space", slug=actual.shop.slug))
            session.pop("seller_deliverer_id", None)
            flash("Veuillez vous reconnecter en tant que livreur.", "warning")
            return redirect(url_for("deliverer_entry_for_shop_key", shop_key=_shop_access_key(shop)))
        if not deliverer:
            flash("Veuillez vous connecter en tant que livreur.", "warning")
            return redirect(url_for("deliverer_entry_for_shop_key", shop_key=_shop_access_key(shop)))

        def compute_deliverer_commission(total_amount: float) -> float:
            total = _safe_float(total_amount, 0.0)
            if total <= 25:
                return 3.0
            if total < 80:
                return 4.0
            return 4.0 + (0.02 * total)

        orders = SellerOrder.query.filter_by(shop_id=shop.id, deliverer_id=deliverer.id).order_by(SellerOrder.created_at.desc()).all()

        delivered_orders = [o for o in orders if (o.status or "").strip().lower() == "delivered"]
        now = datetime.utcnow()
        month_delivered = [
            o for o in delivered_orders
            if o.created_at and o.created_at.year == now.year and o.created_at.month == now.month
        ]
        week_start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        week_delivered = [o for o in delivered_orders if o.created_at and o.created_at >= week_start]

        monthly_commission = sum(compute_deliverer_commission(o.total_amount or 0.0) for o in month_delivered)
        commission_due_estimate = sum(compute_deliverer_commission(o.total_amount or 0.0) for o in delivered_orders)
        weekly_bonus_estimate = (len(week_delivered) // 8) * 5

        history_by_month = {}
        for o in delivered_orders:
            key = o.created_at.strftime("%Y-%m") if o.created_at else "N/A"
            block = history_by_month.setdefault(key, {"count": 0, "amount": 0.0})
            block["count"] += 1
            block["amount"] += compute_deliverer_commission(o.total_amount or 0.0)
        commission_history = [
            {"month": k, "count": v["count"], "amount": round(v["amount"], 2)}
            for k, v in sorted(history_by_month.items(), reverse=True)
        ][:6]

        return render_template(
            "deliverer/deliverertheme/deliverer_space.html",
            shop=shop,
            deliverer=deliverer,
            orders=orders,
            settings=settings,
            active_section=(request.args.get("section") or "dashboard").strip().lower(),
            monthly_stats={
                "deliveries_this_month": len(month_delivered),
                "commission_this_month": round(monthly_commission, 2),
                "weekly_deliveries": len(week_delivered),
                "weekly_bonus_estimate": round(weekly_bonus_estimate, 2),
            },
            commission_due_estimate=round(commission_due_estimate, 2),
            commission_history=commission_history,
        )

    @app.route("/livreur/<slug>/profile", methods=["POST"])
    @deliverer_session_required
    def deliverer_profile_update(slug):
        did = session.get("seller_deliverer_id")
        deliverer = SellerDeliverer.query.get_or_404(did)
        deliverer.first_name = (request.form.get("first_name") or deliverer.first_name).strip()
        deliverer.last_name = (request.form.get("last_name") or deliverer.last_name).strip()
        
        # Handle phone number (from phone-input component)
        country_code = (request.form.get("country_code") or "").strip() or None
        phone_number = (request.form.get("phone_number") or "").strip() or None
        
        # Validate phone number: exactly 9 digits
        if phone_number and (len(phone_number) != 9 or not phone_number.isdigit()):
            flash("Le numéro de téléphone doit contenir exactement 9 chiffres.", "error")
            return redirect(url_for("deliverer_space", slug=slug))
        
        deliverer.country_code = country_code
        deliverer.phone_number = phone_number
        deliverer.address = (request.form.get("address") or "").strip() or None
        uploaded_profile_picture = _save_uploaded_image(request.files.get("profile_picture_file"), "deliverer/profiles")
        if uploaded_profile_picture:
            deliverer.profile_picture = uploaded_profile_picture
        new_password = (request.form.get("new_password") or "").strip()
        if new_password:
            if len(new_password) < 6:
                flash("Le nouveau mot de passe doit contenir au moins 6 caractères.", "error")
                return redirect(url_for("deliverer_space", slug=slug))
            deliverer.set_password(new_password)
        db.session.commit()
        flash("Profil livreur mis à jour.", "success")
        return redirect(url_for("deliverer_space", slug=slug))

    @app.route("/livreur/<slug>/logout")
    def deliverer_logout(slug):
        session.pop("seller_deliverer_id", None)
        shop = SellerShop.query.filter_by(slug=slug).first()
        if shop:
            return redirect(url_for("deliverer_entry_for_shop_key", shop_key=_shop_access_key(shop)))
        return redirect(url_for("deliverer_entrypoint"))

    @app.route("/livreur/<slug>/status", methods=["POST"])
    @deliverer_session_required
    def deliverer_set_status(slug):
        did = session.get("seller_deliverer_id")
        deliverer = SellerDeliverer.query.get_or_404(did)
        status = (request.form.get("status") or "").strip().lower()
        if status in {"available", "busy", "offline"}:
            deliverer.status = status
            db.session.commit()
        return redirect(url_for("deliverer_space", slug=slug, section="dashboard"))

    @app.route("/livreur/<slug>/orders/<int:order_id>/status", methods=["POST"])
    @deliverer_session_required
    def deliverer_update_order_status(slug, order_id):
        did = session.get("seller_deliverer_id")
        deliverer = SellerDeliverer.query.get_or_404(did)
        order = SellerOrder.query.filter_by(
            id=order_id,
            shop_id=deliverer.shop_id,
            deliverer_id=deliverer.id,
        ).first_or_404()

        new_status = (request.form.get("status") or "").strip().lower()
        allowed = {"pending", "in_progress", "delivered", "postponed", "cancelled"}
        if new_status not in allowed:
            flash("Statut de livraison invalide.", "error")
            return redirect(url_for("deliverer_space", slug=slug, section="dashboard"))

        order.status = new_status
        db.session.commit()
        flash(f"Commande {order.order_number} mise à jour.", "success")
        return redirect(url_for("deliverer_space", slug=slug, section="dashboard"))

    @app.route("/vendeur/<slug>/orders/<int:order_id>/invoice")
    @seller_session_required
    def seller_order_invoice(slug, order_id):
        shop = SellerShop.query.filter_by(slug=slug).first_or_404()
        order = SellerOrder.query.filter_by(id=order_id, shop_id=shop.id).first_or_404()
        pdf = generate_seller_invoice_pdf(order, shop)
        return send_file(pdf, as_attachment=True, mimetype="application/pdf", download_name=f"facture_{order.order_number}.pdf")

    return app

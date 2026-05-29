from datetime import datetime

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash


db = SQLAlchemy()


class PlatformAdmin(UserMixin, db.Model):
    __tablename__ = "platform_admins"

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(30))  # Deprecated: Use country_code + phone_number instead
    country_code = db.Column(db.String(2))  # e.g., 'CD', 'CM', 'ML'
    phone_number = db.Column(db.String(9))  # Exactly 9 digits, e.g., '813091409'
    address = db.Column(db.Text)
    profile_picture = db.Column(db.String(255))
    role = db.Column(db.String(30), default="admin")  # super_admin, admin
    permissions = db.Column(db.Text, default="manage_sellers,manage_subscriptions,manage_announcements,manage_admins,manage_settings")
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def has_permission(self, perm: str) -> bool:
        if self.role == "super_admin":
            return True
        perms = {p.strip() for p in (self.permissions or "").split(",") if p.strip()}
        if perm in perms:
            return True
        # Backward compatibility: old "manage_sellers" used to unlock most operational pages.
        legacy_map = {
            "manage_products",
            "manage_orders",
            "manage_deliverers",
            "manage_clients",
            "manage_categories",
            "view_tasks",
        }
        if "manage_sellers" in perms and perm in legacy_map:
            return True
        return False

    @property
    def is_super_admin(self) -> bool:
        return self.role == "super_admin"

    @property
    def is_admin(self) -> bool:
        return True


class PlatformActivityLog(db.Model):
    __tablename__ = "platform_activity_logs"

    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(255), nullable=False)
    actor_id = db.Column(db.Integer, db.ForeignKey("platform_admins.id"))
    actor_email = db.Column(db.String(120))
    actor_name = db.Column(db.String(120))
    actor_phone = db.Column(db.String(30))
    extra = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    actor = db.relationship("PlatformAdmin", foreign_keys=[actor_id])


class PlatformAccessRequest(db.Model):
    __tablename__ = "platform_access_requests"

    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey("platform_admins.id"), nullable=False)
    feature = db.Column(db.String(255), nullable=False)  # comma-separated permissions
    message = db.Column(db.Text)
    status = db.Column(db.String(20), default="pending")  # pending, approved, rejected
    processed_by = db.Column(db.Integer, db.ForeignKey("platform_admins.id"))
    response_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime)

    requester = db.relationship("PlatformAdmin", foreign_keys=[admin_id], backref="access_requests")
    processor = db.relationship("PlatformAdmin", foreign_keys=[processed_by])


class PlatformAnnouncement(db.Model):
    __tablename__ = "platform_announcements"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(180), nullable=False)
    content = db.Column(db.Text, nullable=False)
    cta_label = db.Column(db.String(60))
    cta_url = db.Column(db.String(255))
    is_published = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey("platform_admins.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    author = db.relationship("PlatformAdmin", foreign_keys=[created_by])


class PlatformSettings(db.Model):
    __tablename__ = "platform_settings"

    id = db.Column(db.Integer, primary_key=True)
    platform_name = db.Column(db.String(120), default="Tekanayo App")
    portal_logo_url = db.Column(db.String(255))
    admin_logo_url = db.Column(db.String(255))
    deliverer_logo_url = db.Column(db.String(255))
    seller_login_logo_url = db.Column(db.String(255))
    deliverer_login_logo_url = db.Column(db.String(255))
    portal_about_content = db.Column(db.Text)
    portal_legal_content = db.Column(db.Text)
    portal_terms_content = db.Column(db.Text)
    portal_returns_content = db.Column(db.Text)
    portal_privacy_content = db.Column(db.Text)
    admin_about_content = db.Column(db.Text)
    contact_email = db.Column(db.String(120))
    contact_phone = db.Column(db.String(30))
    facebook_url = db.Column(db.String(255))
    whatsapp_number = db.Column(db.String(30))
    whatsapp_group_url = db.Column(db.String(255))
    whatsapp_url = db.Column(db.String(255))
    telegram_username = db.Column(db.String(60))
    telegram_url = db.Column(db.String(255))
    currency = db.Column(db.String(10), default="USD")
    tax_rate = db.Column(db.Float, default=0.0)
    shipping_cost = db.Column(db.Float, default=0.0)
    shipping_cost_out = db.Column(db.Float, default=0.0)
    office_address = db.Column(db.Text)
    office_latitude = db.Column(db.Float)
    office_longitude = db.Column(db.Float)
    office_geocoded = db.Column(db.Text)
    exchange_rate_usd_cdf = db.Column(db.Float, default=2800.0)
    default_currency = db.Column(db.String(10), default="USD")
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============================================================================
# SYSTÈME D'ABONNEMENT SAAS POUR VENDEURS
# ============================================================================

class SellerSubscription(db.Model):
    """
    Gestion des abonnements des vendeurs
    - Période d'essai gratuite de 2 mois
    - Abonnement mensuel à 5$
    - Suivi des paiements et activations
    """
    __tablename__ = "seller_subscriptions"

    id = db.Column(db.Integer, primary_key=True)
    shop_id = db.Column(db.Integer, db.ForeignKey("seller_shops.id"), nullable=False, unique=True)
    
    # Statut de l'abonnement
    status = db.Column(db.String(20), default="trial")  # trial, active, suspended, expired, cancelled
    
    # Dates importantes
    trial_start_date = db.Column(db.DateTime, default=datetime.utcnow)  # Début essai gratuit
    trial_end_date = db.Column(db.DateTime)  # Fin essai gratuit (2 mois après)
    subscription_start_date = db.Column(db.DateTime)  # Début abonnement payant
    subscription_end_date = db.Column(db.DateTime)  # Fin abonnement en cours
    last_payment_date = db.Column(db.DateTime)  # Date dernier paiement
    cancelled_date = db.Column(db.DateTime)  # Date d'annulation
    
    # Informations de paiement
    payment_method = db.Column(db.String(50))  # airtel, orange, mpesa, vodacom, afri, paypal, stripe, offline
    monthly_price = db.Column(db.Float, default=5.0)  # Prix mensuel en USD
    total_paid = db.Column(db.Float, default=0.0)  # Total payé depuis le début
    pending_payment = db.Column(db.Boolean, default=False)  # Paiement en attente (hors plateforme)
    
    # Métadonnées
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relation avec la boutique
    shop = db.relationship("SellerShop", backref=db.backref("subscription", uselist=False))
    
    # Historique des paiements
    payments = db.relationship("SellerPayment", backref="subscription", lazy=True, cascade="all, delete-orphan")
    
    def is_trial_active(self):
        """Vérifie si la période d'essai est toujours active"""
        if self.status != "trial":
            return False
        return datetime.utcnow() < self.trial_end_date if self.trial_end_date else False
    
    def is_active(self):
        """Vérifie si l'abonnement est actif (essai ou payant)"""
        if self.status == "trial" and self.is_trial_active():
            return True
        if self.status == "active" and self.subscription_end_date:
            return datetime.utcnow() < self.subscription_end_date
        return False
    
    def days_remaining(self):
        """Nombre de jours restants avant expiration"""
        if self.status == "trial" and self.trial_end_date:
            delta = self.trial_end_date - datetime.utcnow()
            return max(0, delta.days)
        if self.status == "active" and self.subscription_end_date:
            delta = self.subscription_end_date - datetime.utcnow()
            return max(0, delta.days)
        return 0
    
    def is_expired(self):
        """Vérifie si l'abonnement est expiré"""
        return not self.is_active()


class SellerPayment(db.Model):
    """
    Historique des paiements des vendeurs
    - Garde trace de tous les paiements effectués
    - Supporte plusieurs méthodes de paiement
    - Inclut les paiements hors plateforme
    """
    __tablename__ = "seller_payments"

    id = db.Column(db.Integer, primary_key=True)
    subscription_id = db.Column(db.Integer, db.ForeignKey("seller_subscriptions.id"), nullable=False)
    
    # Informations de paiement
    amount = db.Column(db.Float, nullable=False)  # Montant payé
    currency = db.Column(db.String(10), default="USD")  # Devise
    payment_method = db.Column(db.String(50), nullable=False)  # Méthode de paiement
    payment_type = db.Column(db.String(20), default="subscription")  # subscription, reactivation
    
    # Statut
    status = db.Column(db.String(20), default="pending")  # pending, completed, failed, refunded
    transaction_id = db.Column(db.String(255))  # ID de transaction (Stripe, PayPal, etc.)
    
    # Paiement hors plateforme
    is_offline = db.Column(db.Boolean, default=False)  # Paiement hors plateforme
    offline_confirmed_by = db.Column(db.Integer, db.ForeignKey("platform_admins.id"))  # Admin qui a confirmé
    offline_confirmed_at = db.Column(db.DateTime)  # Date de confirmation
    
    # Métadonnées
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)  # Notes additionnelles
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relation avec l'admin qui a confirmé (pour hors plateforme)
    confirmed_by_admin = db.relationship("PlatformAdmin", foreign_keys=[offline_confirmed_by])


class SellerPaymentTask(db.Model):
    """
    Tâches de paiement pour l'admin
    - Suit les paiements hors plateforme en attente
    - Notifications d'activation/désactivation
    - Historique des actions admin
    """
    __tablename__ = "seller_payment_tasks"

    id = db.Column(db.Integer, primary_key=True)
    shop_id = db.Column(db.Integer, db.ForeignKey("seller_shops.id", name='fk_payment_task_shop'), nullable=False)
    subscription_id = db.Column(db.Integer, db.ForeignKey("seller_subscriptions.id", name='fk_payment_task_subscription'))
    
    # Type de tâche
    task_type = db.Column(db.String(50), nullable=False)  # offline_payment, activation, deactivation, reminder
    
    # Statut
    status = db.Column(db.String(20), default="pending")  # pending, completed, cancelled
    
    # Informations
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    amount = db.Column(db.Float)  # Montant concerné
    payment_method = db.Column(db.String(50))  # Méthode de paiement
    
    # Assignation
    assigned_to = db.Column(db.Integer, db.ForeignKey("platform_admins.id", name='fk_payment_task_assigned'))
    completed_by = db.Column(db.Integer, db.ForeignKey("platform_admins.id", name='fk_payment_task_completed'))
    completed_at = db.Column(db.DateTime)  # Date de complétion
    
    # Vu ou non par l'admin
    is_viewed = db.Column(db.Boolean, default=False)  # Indique si la tâche a été vue
    viewed_at = db.Column(db.DateTime)  # Date de consultation
    viewed_by = db.Column(db.Integer, db.ForeignKey("platform_admins.id", name='fk_payment_task_viewed'))  # Admin qui a vu
    
    # Métadonnées
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    shop = db.relationship("SellerShop", backref="payment_tasks")
    subscription = db.relationship("SellerSubscription", backref="tasks")
    assigned_admin = db.relationship("PlatformAdmin", foreign_keys=[assigned_to])
    completed_admin = db.relationship("PlatformAdmin", foreign_keys=[completed_by])
    viewed_admin = db.relationship("PlatformAdmin", foreign_keys=[viewed_by])


class AdminNotification(db.Model):
    """
    Système de notifications pour les admins
    - Notifications de nouvelles tâches
    - Notifications de paiement
    - Notifications système
    - Badge de notification (non lu/lu)
    """
    __tablename__ = "admin_notifications"

    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey("platform_admins.id", name='fk_admin_notification_admin'), nullable=False)
    
    # Type de notification
    notification_type = db.Column(db.String(50), nullable=False)  
    # task_pending, payment_completed, subscription_expired, system
    
    # Statut de lecture
    is_read = db.Column(db.Boolean, default=False)  # Non lu par défaut
    read_at = db.Column(db.DateTime)  # Date de lecture
    
    # Informations
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text, nullable=False)
    icon = db.Column(db.String(50), default="fa-bell")  # Icône FontAwesome
    color = db.Column(db.String(20), default="blue")  # blue, green, yellow, red
    
    # Lien associé (optionnel)
    link = db.Column(db.String(500))  # URL vers la page concernée
    link_text = db.Column(db.String(100))  # Texte du lien
    
    # Référence à une entité (optionnel)
    reference_type = db.Column(db.String(50))  # task, payment, subscription, shop
    reference_id = db.Column(db.Integer)  # ID de l'entité
    
    # Métadonnées
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)  # Expiration de la notification
    
    # Relation avec l'admin
    admin = db.relationship("PlatformAdmin", backref=db.backref("notifications", lazy=True))
    
    def mark_as_read(self):
        """Marquer la notification comme lue"""
        self.is_read = True
        self.read_at = datetime.utcnow()


class SellerShop(db.Model):
    __tablename__ = "seller_shops"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140), nullable=False)
    slug = db.Column(db.String(160), unique=True, nullable=False, index=True)
    custom_domain = db.Column(db.String(255), unique=True)
    logo_url = db.Column(db.String(255))
    seller_space_logo_url = db.Column(db.String(255))
    deliverer_logo_url = db.Column(db.String(255))
    owner_email = db.Column(db.String(120), nullable=False)
    support_email = db.Column(db.String(120))
    support_phone = db.Column(db.String(30))
    facebook_url = db.Column(db.String(255))
    whatsapp_number = db.Column(db.String(30))
    whatsapp_group_url = db.Column(db.String(255))
    telegram_username = db.Column(db.String(60))
    telegram_url = db.Column(db.String(255))
    address = db.Column(db.Text)
    description = db.Column(db.Text)
    about_page_content = db.Column(db.Text)
    legal_page_content = db.Column(db.Text)
    terms_page_content = db.Column(db.Text)
    returns_page_content = db.Column(db.Text)
    privacy_page_content = db.Column(db.Text)
    currency = db.Column(db.String(10), default="USD")
    tax_rate = db.Column(db.Float, default=0.0)
    shipping_cost = db.Column(db.Float, default=0.0)
    shipping_cost_out = db.Column(db.Float, default=0.0)
    exchange_rate_usd_cdf = db.Column(db.Float, default=2800.0)
    subscription_status = db.Column(db.String(20), default="trial")  # trial, active, suspended
    invoice_theme = db.Column(db.String(30), default="classic")
    category_niche = db.Column(db.String(60), default="shopdivers")
    is_active = db.Column(db.Boolean, default=True)
    is_portal_shop = db.Column(db.Boolean, default=False)  # Boutique portail Tekanayo
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Champs pour la validation des documents (NOUVEAUX)
    id_document_path = db.Column(db.String(500))  # Chemin vers pièce d'identité
    address_document_path = db.Column(db.String(500))  # Chemin vers justificatif d'adresse
    verification_status = db.Column(db.String(20), default="pending")  # pending, verified, rejected
    verified_by = db.Column(db.Integer, db.ForeignKey("platform_admins.id", name='fk_seller_verified_by'))
    verified_at = db.Column(db.DateTime)
    verification_notes = db.Column(db.Text)  # Notes de l'admin

    admins = db.relationship("SellerAdmin", backref="shop", lazy=True, cascade="all, delete-orphan")
    products = db.relationship("SellerProduct", backref="shop", lazy=True, cascade="all, delete-orphan")
    orders = db.relationship("SellerOrder", backref="shop", lazy=True, cascade="all, delete-orphan")
    deliverers = db.relationship("SellerDeliverer", backref="shop", lazy=True, cascade="all, delete-orphan")


class SellerAdmin(db.Model):
    __tablename__ = "seller_admins"

    id = db.Column(db.Integer, primary_key=True)
    shop_id = db.Column(db.Integer, db.ForeignKey("seller_shops.id"), nullable=False)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    profile_picture = db.Column(db.String(255))
    country_code = db.Column(db.String(2))  # e.g., 'CD', 'CM', 'ML'
    phone_number = db.Column(db.String(9))  # Exactly 9 digits, e.g., '813091409'
    permissions = db.Column(db.Text, default="manage_products,manage_orders,view_dashboard")
    is_owner = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class SellerProduct(db.Model):
    __tablename__ = "seller_products"

    id = db.Column(db.Integer, primary_key=True)
    shop_id = db.Column(db.Integer, db.ForeignKey("seller_shops.id"), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False, default=0)
    compare_price = db.Column(db.Float)  # Prix de comparaison (barré)
    quantity = db.Column(db.Integer, default=0)
    image_url = db.Column(db.String(255))
    is_promoted = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    is_featured = db.Column(db.Boolean, default=False)  # Produit mis en avant
    sku = db.Column(db.String(100), unique=True, sparse=True)  # Code SKU optionnel
    import_batch_id = db.Column(db.String(100))  # ID du batch d'import
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class StockHistory(db.Model):
    __tablename__ = "stock_history"

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("seller_products.id"), nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    user_type = db.Column(db.String(20), default='seller')
    old_quantity = db.Column(db.Integer, default=0)
    new_quantity = db.Column(db.Integer, default=0)
    quantity_change = db.Column(db.Integer)
    reason = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    product = db.relationship("SellerProduct", backref=db.backref("stock_history", lazy=True))

    def __repr__(self):
        return f"<StockHistory product={self.product_id} {self.old_quantity}->{self.new_quantity}>"


class SellerDeliverer(db.Model):
    __tablename__ = "seller_deliverers"

    id = db.Column(db.Integer, primary_key=True)
    shop_id = db.Column(db.Integer, db.ForeignKey("seller_shops.id"), nullable=False)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(30))  # Deprecated: Use country_code + phone_number instead
    country_code = db.Column(db.String(2))  # e.g., 'CD', 'CM', 'ML'
    phone_number = db.Column(db.String(9))  # Exactly 9 digits, e.g., '813091409'
    address = db.Column(db.Text)
    profile_picture = db.Column(db.String(255))
    status = db.Column(db.String(20), default="available")
    is_active = db.Column(db.Boolean, default=True)
    verification_status = db.Column(db.String(20), default="pending")  # pending, verified, rejected
    verified_by = db.Column(db.Integer, db.ForeignKey("platform_admins.id", name='fk_seller_deliverer_verified_by'))
    verified_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class PlatformDeliverer(UserMixin, db.Model):
    """
    Livreurs de la plateforme Tekanayo
    - Indépendants de toute boutique spécifique
    - Gérés par les administrateurs plateforme
    - Peuvent livrer pour toutes les boutiques
    """
    __tablename__ = "platform_deliverers"

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(30))  # Deprecated: Use country_code + phone_number instead
    country_code = db.Column(db.String(2))  # e.g., 'CD', 'CM', 'ML'
    phone_number = db.Column(db.String(9))  # Exactly 9 digits, e.g., '813091409'
    address = db.Column(db.Text)
    profile_picture = db.Column(db.String(255))
    status = db.Column(db.String(20), default="available")  # available, busy, offline
    is_active = db.Column(db.Boolean, default=True)
    verification_status = db.Column(db.String(20), default="pending")  # pending, verified, rejected
    verified_by = db.Column(db.Integer, db.ForeignKey("platform_admins.id", name='fk_platform_deliverer_verified_by'))
    verified_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class PortalCustomer(UserMixin, db.Model):
    """
    Clients du portail principal Tekanayo
    - Compte unique pour naviguer sur le portail (pas lié à une boutique spécifique)
    - Peut passer commande dans plusieurs boutiques
    """
    __tablename__ = "portal_customers"

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    profile_picture = db.Column(db.String(255))
    country_code = db.Column(db.String(2))  # e.g., 'CD', 'CM', 'ML'
    phone_number = db.Column(db.String(9))  # Exactly 9 digits, e.g., '813091409'
    address = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class SellerCustomer(db.Model):
    __tablename__ = "seller_customers"

    id = db.Column(db.Integer, primary_key=True)
    shop_id = db.Column(db.Integer, db.ForeignKey("seller_shops.id"), nullable=False, index=True)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    profile_picture = db.Column(db.String(255))
    phone = db.Column(db.String(30))  # Deprecated: Use country_code + phone_number instead
    country_code = db.Column(db.String(2))  # e.g., 'CD', 'CM', 'ML'
    phone_number = db.Column(db.String(9))  # Exactly 9 digits, e.g., '813091409'
    address = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint("shop_id", "email", name="uq_seller_customer_shop_email"),)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class SellerOrder(db.Model):
    __tablename__ = "seller_orders"

    id = db.Column(db.Integer, primary_key=True)
    shop_id = db.Column(db.Integer, db.ForeignKey("seller_shops.id"), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey("seller_customers.id"))
    deliverer_id = db.Column(db.Integer, db.ForeignKey("seller_deliverers.id"))
    order_number = db.Column(db.String(30), nullable=False)
    customer_name = db.Column(db.String(120), nullable=False)
    shipping_address = db.Column(db.Text)
    total_amount = db.Column(db.Float, default=0)
    status = db.Column(db.String(20), default="pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    customer = db.relationship("SellerCustomer", foreign_keys=[customer_id])
    deliverer = db.relationship("SellerDeliverer", foreign_keys=[deliverer_id])

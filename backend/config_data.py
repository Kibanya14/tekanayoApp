"""
Constantes de configuration pour TekanayoApp
Extrait de apps.py pour alléger le fichier principal
"""

# ============================================================================
# CATÉGORIES ET NICHES DE BOUTIQUES
# ============================================================================

CATEGORY_NICHES = {
    "shopdivers": [
        "fa-store", "fa-gift", "fa-basket-shopping", "fa-box-open", "fa-bag-shopping",
        "fa-cart-shopping", "fa-handshake", "fa-tags", "fa-shop", "fa-cart-plus",
        "fa-bag-shopping", "fa-barcode", "fa-receipt", "fa-wallet", "fa-credit-card"
    ],
    "allimentation": [
        "fa-apple-whole", "fa-carrot", "fa-bowl-food", "fa-fish", "fa-drumstick-bite",
        "fa-cheese", "fa-bacon", "fa-egg", "fa-lemon", "fa-pepper-hot",
        "fa-wheat-awn", "fa-jar", "fa-bottle-water", "fa-can-food", "fa-box-tissue"
    ],
    "restaurant": [
        "fa-utensils", "fa-mug-hot", "fa-pizza-slice", "fa-burger", "fa-hotdog",
        "fa-ice-cream", "fa-cookie", "fa-wine-glass", "fa-martini-glass", "fa-beer-mug",
        "fa-fork-knife", "fa-blender", "fa-cake-candles", "fa-donut", "fa-sandwich"
    ],
    "maison_habillement": [
        "fa-shirt", "fa-vest", "fa-socks", "fa-person-dress", "fa-user-tie",
        "fa-hat-cowboy", "fa-glasses", "fa-ring", "fa-gem", "fa-crown",
        "fa-shirt", "fa-person-dress", "fa-person", "fa-vest-patches", "fa-scarf"
    ],
    "pharmacie_soin": [
        "fa-briefcase-medical", "fa-pills", "fa-heart-pulse", "fa-prescription-bottle-medical",
        "fa-syringe", "fa-vial", "fa-bandage", "fa-stethoscope", "fa-user-doctor",
        "fa-hospital", "fa-kit-medical", "fa-pump-medical", "fa-mortar-pestle", "fa-flask",
        "fa-jar", "fa-pump-soap", "fa-hands-bubbles", "fa-tooth", "fa-eye"
    ],
    "boulangerie": [
        "fa-bread-slice", "fa-cookie", "fa-cake-candles", "fa-mug-saucer", "fa-croissant",
        "fa-baguette", "fa-pie", "fa-candy-cane", "fa-ice-cream", "fa-donut",
        "fa-cookie-bite", "fa-cheese", "fa-egg", "fa-wheat-awn", "fa-jar"
    ],
    "locations_voiture": [
        "fa-car", "fa-gas-pump", "fa-road", "fa-key", "fa-car-side",
        "fa-truck", "fa-motorcycle", "fa-bus", "fa-van-shuttle", "fa-plane",
        "fa-taxi", "fa-tractor", "fa-truck-pickup", "fa-shuttle-space", "fa-car-rear"
    ],
    "location_chambre": [
        "fa-bed", "fa-door-open", "fa-key", "fa-hotel", "fa-suitcase",
        "fa-bell-concierge", "fa-elevator", "fa-person-booth", "fa-door-closed", "fa-couch",
        "fa-tv", "fa-wifi", "fa-snowflake", "fa-fan", "fa-bath"
    ],
    "location_maison": [
        "fa-house", "fa-couch", "fa-shower", "fa-map-location-dot", "fa-kitchen-set",
        "fa-tv", "fa-wifi", "fa-snowflake", "fa-fan", "fa-bath",
        "fa-toilet", "fa-sink", "fa-chair", "fa-lightbulb", "fa-door-open"
    ],
    "vente_maison": [
        "fa-house-circle-check", "fa-city", "fa-building", "fa-handshake", "fa-house-chimney",
        "fa-building-columns", "fa-hotel", "fa-house-lock", "fa-house-flag", "fa-landmark",
        "fa-map-location", "fa-sign-hanging", "fa-key", "fa-file-contract", "fa-pen-ruler"
    ],
    "livres": [
        "fa-book", "fa-book-open", "fa-graduation-cap", "fa-pen", "fa-pencil",
        "fa-bookmark", "fa-library", "fa-chalkboard", "fa-ruler", "fa-calculator",
        "fa-laptop", "fa-book-journal-whills", "fa-scroll", "fa-feather", "fa-award"
    ],
    "electronique": [
        "fa-laptop", "fa-mobile-screen", "fa-headphones", "fa-keyboard", "fa-mouse",
        "fa-tv", "fa-camera", "fa-watch", "fa-battery-full", "fa-plug",
        "fa-wifi", "fa-bluetooth", "fa-hard-drive", "fa-memory", "fa-microchip"
    ],
    "mode": [
        "fa-shirt", "fa-person-dress", "fa-shoe-prints", "fa-hat-cowboy", "fa-glasses",
        "fa-ring", "fa-gem", "fa-crown", "fa-vest", "fa-socks",
        "fa-user-tie", "fa-person-dress", "fa-person", "fa-scarf", "fa-mitten"
    ],
    "maison": [
        "fa-couch", "fa-lightbulb", "fa-sink", "fa-toilet", "fa-shower",
        "fa-tree", "fa-leaf", "fa-seedling", "fa-faucet", "fa-broom",
        "fa-spray-can", "fa-plug", "fa-door-open", "fa-window-maximize", "fa-blender"
    ],
    "sport": [
        "fa-futbol", "fa-basketball", "fa-volleyball", "fa-baseball-bat-ball", "fa-tennis-ball",
        "fa-bicycle", "fa-person-running", "fa-person-swimming", "fa-dumbbell", "fa-trophy",
        "fa-medal", "fa-whistle", "fa-stopwatch", "fa-person-skiing", "fa-person-snowboarding"
    ],
    "beaute": [
        "fa-spa", "fa-hands-bubbles", "fa-spray-can", "fa-scissors", "fa-brush",
        "fa-mirror", "fa-pump-soap", "fa-bath", "fa-jar", "fa-flask",
        "fa-heart-pulse", "fa-weight-scale", "fa-person-running", "fa-apple-whole", "fa-syringe"
    ],
    "autres": [
        "fa-box-open", "fa-gift", "fa-tags", "fa-shop", "fa-cart-shopping",
        "fa-handshake", "fa-star", "fa-thumbs-up", "fa-check", "fa-plus",
        "fa-circle-question", "fa-circle-info", "fa-circle-exclamation", "fa-bell", "fa-envelope"
    ]
}

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

ALLOWED_UPLOAD_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}

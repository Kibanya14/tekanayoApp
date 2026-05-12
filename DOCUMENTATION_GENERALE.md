# 📚 Documentation Générale - TekanayoApp

## 🎯 Vue d'Ensemble du Projet

**TekanayoApp** est une plateforme e-commerce multi-vendeurs complète développée avec Flask (Python).

### Architecture Principale

```
┌─────────────────────────────────────────────────────────────┐
│                    TEKANAYO APP                             │
├─────────────────────────────────────────────────────────────┤
│  📊 Portail Admin (Plateforme)                              │
│     - Super Admin avec permissions complètes                │
│     - Gestion vendeurs, abonnements, annonces, admins       │
├─────────────────────────────────────────────────────────────┤
│  🏪 Portail Vendeur (Multi-boutiques)                       │
│     - Chaque vendeur a sa boutique personnalisée            │
│     - Gestion produits, commandes, livreurs, clients        │
├─────────────────────────────────────────────────────────────┤
│  🚚 Interface Livreur                                       │
│     - Gestion des livraisons par boutique                   │
├─────────────────────────────────────────────────────────────┤
│  🛒 Portail Client                                          │
│     - Navigation par boutique                               │
│     - Panier, commandes, historique                         │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 Structure du Projet

```
/home/kibanya/Documents/TekanayoApp/
├── backend/
│   ├── apps.py              # Application factory + routes principales
│   ├── models.py            # Modèles de base de données (SQLAlchemy)
│   ├── countries_routes.py  # Routes pour les pays
│   └── utils/
│       └── invoice_generator.py  # Générateur de factures
├── frontend/
│   ├── templates/
│   │   ├── admin/           # Templates interface admin
│   │   ├── vendeur/         # Templates interface vendeur
│   │   ├── deliverer/       # Templates interface livreur
│   │   ├── portal/          # Templates portail principal
│   │   └── clientvendeur/   # Templates boutiques clients
│   └── static/
│       ├── js/
│       │   └── phone-input.js    # Composant téléphone professionnel
│       └── css/
│           └── phone-input.css   # Styles du composant téléphone
├── migrations/              # Migrations de base de données (Alembic)
├── uploads/                 # Fichiers uploadés (images, documents)
├── countries.py             # Données des pays (195 pays + indicatifs)
├── config.py                # Configuration de l'application
└── run.py                   # Point d'entrée principal
```

---

## 🗄️ Base de Données

### Entités Principales

#### 1. PlatformAdmin (Administrateurs de la Plateforme)
```python
class PlatformAdmin:
    id              # Identifiant unique
    first_name      # Prénom
    last_name       # Nom
    email           # Email unique
    password_hash   # Mot de passe haché
    country_code    # Code pays ISO (ex: 'CD')
    phone_number    # Numéro à 9 chiffres (ex: '813091409')
    role            # 'super_admin' ou 'admin'
    permissions     # Permissions (CSV)
```

#### 2. SellerShop (Boutiques Vendeurs)
```python
class SellerShop:
    id              # Identifiant unique
    name            # Nom de la boutique
    slug            # URL friendly (ex: 'ma-boutique-1')
    owner_email     # Email du propriétaire
    support_phone   # Téléphone de support
    subscription_status  # 'trial', 'active', 'suspended'
```

#### 3. SellerAdmin (Admins de Boutique)
```python
class SellerAdmin:
    id              # Identifiant unique
    shop_id         # Référence à la boutique
    first_name      # Prénom
    last_name       # Nom
    email           # Email unique
    country_code    # Code pays ISO
    phone_number    # Numéro à 9 chiffres
    permissions     # Permissions de la boutique
```

#### 4. SellerProduct (Produits)
```python
class SellerProduct:
    id              # Identifiant unique
    shop_id         # Référence à la boutique
    name            # Nom du produit
    category        # Catégorie
    price           # Prix
    quantity        # Stock disponible
    is_promoted     # Produit en promotion
```

---

## 📞 Composant Téléphone Professionnel

### Description

Le composant téléphone permet la saisie de numéros de téléphone avec :
- ✅ Sélecteur de pays avec drapeau et indicatif
- ✅ Validation stricte à 9 chiffres
- ✅ Feedback visuel en temps réel
- ✅ 201 pays disponibles (54 africains prioritaires)

### Fichiers

- **`frontend/static/js/phone-input.js`** - Logique JavaScript
- **`frontend/static/css/phone-input.css`** - Styles CSS
- **`countries.py`** - Données des pays (Python)

### Utilisation dans les Templates

```html
<!-- 1. Inclure le CSS -->
{% block styles %}
{{ super() }}
<link rel="stylesheet" href="{{ url_for('static', filename='css/phone-input.css') }}">
{% endblock %}

<!-- 2. Ajouter le composant -->
<div class="phone-input-wrapper" 
     data-country="{{ user.country_code or 'CD' }}" 
     data-phone="{{ user.phone_number or '' }}">
</div>

<!-- 3. Injecter les données des pays -->
{% block scripts %}
{{ super() }}
<script src="{{ url_for('static', filename='js/phone-input.js') }}"></script>
<script>
window.COUNTRIES_DATA = [
    {% for code, name, dial_code in countries_with_dial_codes() %}
    ['{{ code }}', '{{ get_country_flag(code) }}', '{{ name }}', '{{ dial_code }}'],
    {% endfor %}
];

// 4. Initialiser le composant
window.addEventListener('load', function() {
    const wrapper = document.querySelector('.phone-input-wrapper');
    if (wrapper) {
        new PhoneInputComponent(wrapper, {
            defaultCountry: 'CD',
            requiredLength: 9,
            africanCountriesFirst: true
        });
    }
});
</script>
{% endblock %}
```

### Données Retournées

Lors de la soumission du formulaire :
```python
country_code = request.form.get("country_code")  # 'CD'
phone_number = request.form.get("phone_number")  # '813091409'

# Validation
if len(phone_number) != 9 or not phone_number.isdigit():
    flash("Le numéro doit contenir exactement 9 chiffres.", "error")
```

---

## 🌍 Système de Pays (countries.py)

### Description

Fichier Python contenant les données de 201 pays avec :
- Code ISO (2 lettres)
- Drapeau emoji
- Nom du pays
- Indicatif téléphonique

### Fonctions Principales

```python
# Obtenir tous les pays
Countries.get_countries()  
# Retour: [(code, flag, name, dial_code), ...]

# Obtenir les pays pour select HTML
Countries.get_countries_for_select()  
# Retour: [(code, name, dial_code), ...]

# Obtenir les pays africains
Countries.get_african_countries_with_dial_codes()  
# Retour: [(code, name, dial_code), ...]

# Obtenir infos d'un pays
Countries.get_country_info('CD')  
# Retour: ('🇨🇩', 'Congo, Democratic Republic of the', '+243')

# Obtenir le drapeau
Countries.get_country_flag('CD')  
# Retour: '🇨🇩'

# Obtenir l'indicatif
Countries.get_country_dial_code('CD')  
# Retour: '+243'
```

### Utilisation dans les Templates Jinja2

```html
<!-- Liste de tous les pays -->
{% for code, name, dial_code in countries_with_dial_codes() %}
    <option value="{{ code }}">{{ name }} (+{{ dial_code }})</option>
{% endfor %}

<!-- Pays africains uniquement -->
{% for code, name, dial_code in african_countries_with_dial_codes() %}
    <option value="{{ code }}">{{ name }} (+{{ dial_code }})</option>
{% endfor %}

<!-- Afficher un drapeau -->
{{ get_country_flag('CD') }}  <!-- 🇨🇩 -->

<!-- Afficher un indicatif -->
{{ get_country_dial_code('CD') }}  <!-- +243 -->
```

---

## 🔐 Authentification et Permissions

### Niveaux d'Accès

#### 1. Super Admin
- ✅ Accès complet à la plateforme
- ✅ Gère les vendeurs, admins, annonces, paramètres
- ✅ Permissions: `manage_sellers,manage_subscriptions,manage_announcements,manage_admins,manage_settings`

#### 2. Admin (Plateforme)
- ✅ Permissions limitées selon configuration
- ✅ Peut être restreint à certaines fonctionnalités

#### 3. Seller Admin (Vendeur)
- ✅ Gère sa boutique
- ✅ Permissions: `manage_products,manage_orders,view_dashboard,...`

#### 4. Deliverer (Livreur)
- ✅ Gère ses livraisons
- ✅ Statut: `available`, `busy`, `offline`

#### 5. Customer (Client)
- ✅ Passe des commandes
- ✅ Historique des commandes

---

## 📊 Routes Principales

### Admin (Plateforme)

```python
@app.route("/admin")              # Page de connexion admin
@app.route("/admin/dashboard")    # Tableau de bord
@app.route("/admin/profile")      # Profil admin
@app.route("/admin/settings")     # Paramètres plateforme
@app.route("/admin/sellers")      # Liste des vendeurs
@app.route("/admin/admins")       # Liste des admins
@app.route("/admin/deliverers")   # Liste des livreurs
```

### Vendeur (Boutique)

```python
@app.route("/vendeur/register")   # Devenir vendeur (maintenant /portal/register)
@app.route("/vendeur/<slug>")     # Espace vendeur
@app.route("/vendeur/<slug>/profile")    # Profil vendeur
@app.route("/vendeur/<slug>/settings")   # Paramètres boutique
@app.route("/vendeur/<slug>/products")   # Gestion produits
```

### Portal (Client)

```python
@app.route("/portal")             # Portail principal
@app.route("/portal/products")    # Liste des produits
@app.route("/portal/register")    # Enregistrement vendeur
@app.route("/portal/profile")     # Profil client
```

---

## 🎨 Templates et Base Templates

### Base Templates

Chaque section a son template de base :

```
admin/basee.html       # Base pour toutes les pages admin
vendeur/basee.html     # Base pour toutes les pages vendeur
portal/base.html       # Base pour toutes les pages portal
clientvendeur/shoptheme/base.html  # Base pour les boutiques
```

### Héritage de Template

```html
{% extends "admin/basee.html" %}

{% block title %}Mon Titre{% endblock %}
{% block header_title %}Titre Principal{% endblock %}

{% block styles %}
{{ super() }}
<link rel="stylesheet" href="...">
{% endblock %}

{% block content %}
<!-- Contenu de la page -->
{% endblock %}

{% block scripts %}
{{ super() }}
<script src="..."></script>
{% endblock %}
```

---

## 🔧 Configuration et Environnement

### Fichier .env

```bash
# Configuration Flask
FLASK_ENV=development
SECRET_KEY=votre-clé-secrète
DATABASE_URL=sqlite:////path/to/database.db

# Configuration Email (Gmail SMTP)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=votre-email@gmail.com
MAIL_PASSWORD=votre-mot-de-passe-app

# Super Admin
SUPERADMIN_FIRST_NAME=Admin
SUPERADMIN_LAST_NAME=Principal
SUPERADMIN_EMAIL=admin@tekanayo.com
SUPERADMIN_PASSWORD=mot-de-passe

# Taux de change USD/CDF
EXCHANGE_RATE_USD_CDF=2800
```

### Chargement dans Python

```python
from dotenv import load_dotenv
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "clé-par-défaut")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///database.db")
```

---

## 📝 Bonnes Pratiques

### 1. Validation des Données

```python
# Toujours valider les entrées utilisateur
if not email or "@" not in email:
    flash("Email invalide", "error")
    return redirect(request.url)

# Validation téléphone : exactement 9 chiffres
if len(phone_number) != 9 or not phone_number.isdigit():
    flash("Le numéro doit contenir exactement 9 chiffres", "error")
    return redirect(request.url)
```

### 2. Sécurité

```python
# Hasher les mots de passe
user.set_password(password)  # Utilise werkzeug.security

# Vérifier les mots de passe
if not user.check_password(password):
    flash("Mot de passe incorrect", "error")

# Tokens CSRF dans les formulaires
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
```

### 3. Gestion des Erreurs

```python
try:
    db.session.commit()
    flash("Opération réussie", "success")
except Exception as e:
    db.session.rollback()
    flash(f"Erreur: {str(e)}", "error")
```

---

## 🚀 Déploiement

### Développement

```bash
cd /home/kibanya/Documents/TekanayoApp
source ecom/bin/activate
python run.py
```

### Production

```bash
# Utiliser Gunicorn
gunicorn --bind 0.0.0.0:5000 wsgi:app

# Ou avec Nginx en reverse proxy
```

---

## 📞 Support et Documentation

### Fichiers de Documentation

- `PHONE_SYSTEM_DOCUMENTATION.md` - Documentation complète du système téléphone
- `DEPLOYMENT_COMPLETE.md` - État du déploiement
- `COUNTRIES_LIST_FIXED.md` - Correction liste des pays
- `CLICK_ISSUE_FIXED.md` - Correction problème de clic
- `FINAL_PHONE_FIX.md` - Corrections finales

### Commandes Utiles

```bash
# Vérifier les migrations
flask db current

# Appliquer les migrations
flask db upgrade

# Créer une nouvelle migration
flask db migrate -m "Description"
```

---

**Date de création :** Mars 2026  
**Version :** 1.0.0  
**Auteur :** TekanayoApp Team

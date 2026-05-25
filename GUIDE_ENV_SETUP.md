# 📋 GUIDE DE REMPLISSAGE DU FICHIER .env

## 🎯 Vue d'ensemble

Ce guide vous aide à remplir le fichier `.env.template` pour configurer votre application TekanayoApp localement.

---

## 📥 ÉTAPES INITIALES

### 1. Copier le template

```bash
# Copier le fichier template
cp .env.template .env

# ⚠️ NE PAS COMMITTER .env!
# Vérifier que .gitignore contient: .env
```

### 2. Ajouter à .gitignore

```bash
echo ".env" >> .gitignore
echo ".env.local" >> .gitignore
echo ".env.*.local" >> .gitignore
```

---

## 🔧 SECTION PAR SECTION

### 1️⃣ CONFIGURATION FLASK DE BASE

```env
FLASK_ENV=development              # ✅ Pour développement local
SECRET_KEY=your-secret-here        # 🔐 Générer avec: python -c "import secrets; print(secrets.token_hex(32))"
DEBUG=True                         # ✅ Activer debug en dev
APP_VERSION=1.0.0                  # Version de l'app
```

**Comment générer SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
# Résultat: a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0e
```

---

### 2️⃣ BASE DE DONNÉES

#### Option A: SQLite (Local/Développement)

```env
DATABASE_URL=sqlite:///database.db
```

#### Option B: PostgreSQL (Production recommandé)

```env
DATABASE_URL=postgresql://username:password@localhost:5432/tekanayo_db
```

**Installation PostgreSQL:**
```bash
# macOS
brew install postgresql

# Linux (Ubuntu)
sudo apt-get install postgresql postgresql-contrib

# Créer la base
createdb tekanayo_db
```

#### Variables Supabase (Optionnel - stockage cloud)

```env
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...  # Clé secrète long token
SUPABASE_BUCKET=uploads
```

---

### 3️⃣ CONFIGURATION EMAIL

#### Avec Gmail (Recommandé pour développement)

```env
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USE_SSL=False
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password        # App Password, pas le mot de passe gmail
MAIL_DEFAULT_SENDER=your-email@gmail.com
```

**Comment obtenir App Password Gmail:**
1. Aller sur: https://myaccount.google.com/security
2. Activer "2-Step Verification"
3. Aller à "App passwords"
4. Sélectionner "Mail" et "Windows Computer"
5. Google génère un mot de passe (16 caractères)
6. Copier et coller dans `MAIL_PASSWORD`

#### Avec autre fournisseur (Mailgun, SendGrid, etc)

```env
MAIL_SERVER=smtp.mailgun.org
MAIL_PORT=587
MAIL_USERNAME=postmaster@yourdomain.com
MAIL_PASSWORD=your-mailgun-password
```

#### En développement (Désactiver envoi)

```env
MAIL_SUPPRESS_SEND=True
# Les emails ne seront pas envoyés réellement
```

---

### 4️⃣ SUPER ADMIN INITIAL

```env
SUPERADMIN_FIRST_NAME=Jonas
SUPERADMIN_LAST_NAME=Kibanya
SUPERADMIN_EMAIL=admin@tekanayo.com
SUPERADMIN_PASSWORD=ChangeMe123!
# ⚠️ Créé au premier lancement, changez-le à la première connexion
```

---

### 5️⃣ PAIEMENTS - MOBILE MONEY (Afrique)

#### Airtel Money
```env
AIRTEL_API_KEY=your-airtel-api-key
AIRTEL_API_SECRET=your-airtel-secret
AIRTEL_MERCHANT_ID=your-merchant-id
```

#### Orange Money
```env
ORANGE_API_KEY=your-orange-api-key
ORANGE_API_SECRET=your-orange-secret
ORANGE_MERCHANT_ID=your-merchant-id
```

#### M-PESA (Kenya)
```env
MPESA_API_KEY=your-mpesa-key
MPESA_API_SECRET=your-mpesa-secret
MPESA_CONSUMER_KEY=your-consumer-key
MPESA_CONSUMER_SECRET=your-consumer-secret
```

**Où obtenir les clés:**
- Airtel: Portal développeur Airtel
- Orange: Platform Orange Developer
- M-PESA: Safaricom Developer Portal

---

### 6️⃣ PAIEMENTS - CARTES & INTERNATIONAL

#### PayPal
```env
PAYPAL_CLIENT_ID=your-paypal-client-id
PAYPAL_CLIENT_SECRET=your-paypal-secret
PAYPAL_MODE=sandbox              # sandbox pour test, live pour production
```

**Obtenir les clés:**
1. Créer compte PayPal Developer: https://developer.paypal.com
2. Créer une app
3. Copier Client ID et Secret

#### Stripe
```env
STRIPE_PUBLISHABLE_KEY=pk_test_... # Commence par pk_test ou pk_live
STRIPE_SECRET_KEY=sk_test_...       # Commence par sk_test ou sk_live
STRIPE_WEBHOOK_SECRET=whsec_...     # Pour les webhooks
```

**Obtenir les clés:**
1. https://dashboard.stripe.com/apikeys
2. Utiliser les clés TEST en développement

#### Flutterwave
```env
FLW_PUBLIC_KEY=FLWPUBK_TEST-...
FLW_SECRET_KEY=FLWSECK_TEST-...
FLW_ENCRYPTION_KEY=FLWENCRYPTION_KEY_...
FLW_WEBHOOK_SECRET=webhook-secret
```

---

### 7️⃣ DEVISE & FINANCE

```env
EXCHANGE_RATE_USD_CDF=2800         # 1 USD = 2800 CDF (exemple)
BASE_CURRENCY=CDF                  # Devise par défaut
```

**Obtenir les taux actuels:**
```bash
curl https://api.exchangerate-api.com/v4/latest/USD
```

---

### 8️⃣ DOMAINES PERSONNALISÉS

```env
TEKANAYO_SERVER_IP=92.132.145.33   # IP du serveur (à mettre à jour)
TEKANAYO_APP_HOST=tekanayo.com     # Domaine principal
```

---

### 9️⃣ ANTIVIRUS (Optionnel)

```env
ANTIVIRUS_ENABLED=False            # False en développement
CLAMAV_HOST=localhost
CLAMAV_PORT=3310
ANTIVIRUS_TIMEOUT=30
```

**Installation ClamAV (optionnel):**
```bash
# macOS
brew install clamav

# Linux
sudo apt-get install clamav

# Démarrer le daemon
clamd -c /etc/clamav/clamd.conf
```

---

### 🔟 MONITORING & LOGGING

#### Sentry (Error Tracking)
```env
SENTRY_DSN=https://xxxxx@xxxxx.ingest.sentry.io/xxxxx
SENTRY_ENVIRONMENT=development
SENTRY_TRACES_SAMPLE_RATE=0.1
```

**Obtenir DSN:**
1. https://sentry.io (créer compte gratuit)
2. Créer nouveau projet
3. Copier la clé DSN

#### Logging
```env
LOG_LEVEL=INFO              # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

---

### 1️⃣1️⃣ SÉCURITÉ

```env
FORCE_HTTPS=False                  # True en production
ALLOWED_HOSTS=localhost,127.0.0.1  # Hôtes autorisés
PASSWORD_HASH_SALT=your-salt       # Générée auto si vide
```

---

### 1️⃣2️⃣ STOCKAGE FICHIERS

```env
UPLOAD_ROOT=uploads/               # Dossier des uploads
MAX_UPLOAD_SIZE=50                 # MB
ALLOWED_EXTENSIONS=jpg,jpeg,png,gif,pdf,doc,docx,xls,xlsx,txt
```

---

### 1️⃣3️⃣ REDIS (Optionnel - Cache)

```env
REDIS_URL=redis://localhost:6379/0
```

**Installation Redis:**
```bash
# macOS
brew install redis

# Linux
sudo apt-get install redis-server

# Démarrer
redis-server
```

---

### 1️⃣4️⃣ GOOGLE MAPS

```env
GOOGLE_MAPS_API_KEY=your-google-maps-key
```

**Obtenir la clé:**
1. https://cloud.google.com/console
2. Créer nouveau projet
3. Activer "Maps JavaScript API"
4. Créer clé API

---

### 1️⃣5️⃣ RECAPTCHA (Protection bot)

```env
RECAPTCHA_SITE_KEY=your-site-key       # Public
RECAPTCHA_SECRET_KEY=your-secret-key   # Secret
```

**Obtenir les clés:**
1. https://www.google.com/recaptcha/admin
2. Créer un site
3. Copier les clés

---

### 1️⃣6️⃣ JWT (API Tokens)

```env
JWT_SECRET_KEY=your-jwt-secret
JWT_EXPIRATION_TIME=3600  # Secondes (1 heure)
```

---

### 1️⃣7️⃣ DÉVELOPPEMENT LOCAL

```env
FLASK_DEBUG=True
VERBOSE_LOGGING=True
DISABLE_CACHE=False
TESTING=False
```

---

## 🚀 LANCER L'APPLICATION

### 1. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 2. Initialiser la base
```bash
flask db upgrade
# ou
python migrate.py
```

### 3. Créer le super admin (si première fois)
```bash
flask shell
> from backend.models import User, db
> user = User(email="admin@tekanayo.com", first_name="Admin", last_name="User")
> user.set_password("password123")
> db.session.add(user)
> db.session.commit()
> exit()
```

### 4. Lancer le serveur
```bash
python run.py
# ou
flask run

# Résultat: http://localhost:5000
```

---

## ✅ CHECKLIST DE CONFIGURATION

- [ ] `FLASK_ENV` = development
- [ ] `SECRET_KEY` = généré (32 caractères hex)
- [ ] `DATABASE_URL` = sqlite:///database.db ou PostgreSQL
- [ ] `MAIL_SERVER` = smtp.gmail.com
- [ ] `MAIL_USERNAME` = votre email
- [ ] `MAIL_PASSWORD` = App Password Gmail
- [ ] `SUPERADMIN_EMAIL` = email admin
- [ ] `SUPERADMIN_PASSWORD` = password temporaire
- [ ] `.gitignore` contient `.env`
- [ ] Fichier `.env` créé (ne pas committer!)

---

## 🧪 TESTER LA CONFIGURATION

### Vérifier les variables chargées
```bash
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('SECRET_KEY:', os.getenv('SECRET_KEY')[:10] + '...')"
```

### Tester la base de données
```bash
python
> from backend.models import db
> db.create_all()
> print("✅ Database OK")
> exit()
```

### Tester email
```bash
python
> from backend.apps import _send_email
> _send_email("test@example.com", "Test", "Ceci est un test")
> print("✅ Email sent!")
> exit()
```

---

## 🆘 PROBLÈMES COURANTS

### ❌ "No module named 'backend'"
**Solution:** Vérifier que vous êtes dans le bon dossier
```bash
ls -la backend/  # Doit exister
```

### ❌ "SECRET_KEY is empty"
**Solution:** Générer une clé secrète
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### ❌ "Email not sending"
**Solutions:**
- Vérifier MAIL_USERNAME et MAIL_PASSWORD
- Activer App Passwords dans Gmail
- Vérifier MAIL_SUPPRESS_SEND = False

### ❌ "Database connection error"
**Solutions:**
- Vérifier DATABASE_URL est correct
- Si PostgreSQL: vérifier le serveur tourne
- Si SQLite: vérifier les permissions du dossier

### ❌ "PayPal/Stripe tests échouent"
**Solution:** Utiliser les clés TEST (pk_test_, sk_test_)

---

## 📝 PRODUCTION vs DÉVELOPPEMENT

| Paramètre | Développement | Production |
|-----------|---------------|------------|
| FLASK_ENV | development | production |
| DEBUG | True | False |
| DATABASE_URL | sqlite:///database.db | postgresql://... |
| SECRET_KEY | any | générer avec secrets |
| FORCE_HTTPS | False | True |
| PAYPAL_MODE | sandbox | live |
| STRIPE_KEY | pk_test_ | pk_live_ |

---

## 🔐 BONNES PRATIQUES

1. **Ne JAMAIS committer .env**
2. **Utiliser .gitignore**
3. **Générer des clés secrètes fortes**
4. **Changer les mots de passe par défaut**
5. **Utiliser des clés TEST avant production**
6. **Sauvegarder les clés quelque part de sûr**
7. **Limiter l'accès au fichier .env**

---

**Date:** 25 Mai 2026  
**Status:** ✅ Complet  
**Prêt pour:** Développement local 🚀

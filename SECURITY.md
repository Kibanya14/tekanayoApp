# 🔐 Guide de Sécurité TekanayoApp

## AVANT LA MISE EN LIGNE

### 1. 🔑 Secret Management

```python
# ❌ JAMAIS en production
SECRET_KEY = "my-secret"
DATABASE_PASSWORD = "password123"

# ✅ CORRECT: utiliser les variables d'environnement
SECRET_KEY = os.getenv('SECRET_KEY')
DB_PASSWORD = os.getenv('DATABASE_PASSWORD')
```

**Générer un SECRET_KEY sécurisé:**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### 2. 🔒 Configuration HTTPS/SSL

```python
# app.py - Configuration Flask pour HTTPS
class ProductionConfig:
    # Force HTTPS
    PREFERRED_URL_SCHEME = 'https'
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Disable debug
    DEBUG = False
    TESTING = False
```

### 3. 🚨 CORS et Security Headers

```python
# Ajouter à app.py
from flask_cors import CORS

# CORS configuration
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "https://tekanayo.rw",
            "https://www.tekanayo.rw"
        ],
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "max_age": 3600
    }
})

# Security headers
@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'"
    return response
```

### 4. 🛡️ Protection contre les Attaques

#### SQL Injection
```python
# ❌ JAMAIS
query = f"SELECT * FROM users WHERE id = {user_id}"

# ✅ CORRECT
user = User.query.filter_by(id=user_id).first()
```

#### XSS (Cross-Site Scripting)
```python
# ❌ Jinja2 - par défaut unsafe
{{ user_input }}

# ✅ CORRECT - échapper le contenu
{{ user_input | safe }}  # Seulement si vous faites confiance
{{ user_input | escape }}  # Default en Jinja2
```

#### CSRF (Cross-Site Request Forgery)
```python
# ✅ Flask-WTF protège automatiquement
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect(app)

# Dans les formulaires HTML
<form method="POST">
    {{ csrf_token() }}
    <input type="submit">
</form>
```

#### Rate Limiting
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.route('/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    pass
```

### 5. 🔑 Password Security

```python
from werkzeug.security import generate_password_hash, check_password_hash

# Hash les passwords
hashed = generate_password_hash('password', method='pbkdf2:sha256')

# Vérifier password
if check_password_hash(hashed, 'password'):
    print("Correct!")
```

### 6. 📄 Validation Input

```python
# ❌ JAMAIS faire confiance à l'input utilisateur
filename = request.files['file'].filename
file.save(filename)  # DANGEREUX - injection de chemin

# ✅ CORRECT - Sanitiser
from werkzeug.utils import secure_filename

filename = secure_filename(request.files['file'].filename)
random_prefix = secrets.token_hex(8)
final_name = f"{random_prefix}_{filename}"
```

### 7. 🔐 Supabase RLS Policies

```sql
-- ✅ Politique pour documents privés (vendeur seulement)
CREATE POLICY "Vendeur accès ses documents"
ON storage.objects
USING (auth.uid() = (
    SELECT user_id FROM seller_admin 
    WHERE seller_id = (
        SPLIT_PART(name, '/', 3)::int
    )
))
```

### 8. 📊 Auditing & Logging

```python
# Logger les actions sensibles
def log_security_event(event_type, user_id, details):
    from backend.logger import StructuredLogger
    
    logger = StructuredLogger()
    logger.warning(
        f"SECURITY EVENT: {event_type}",
        user_id=user_id,
        details=details,
        timestamp=datetime.utcnow().isoformat()
    )
```

### 9. 🧪 Antivirus Scanning

```python
from backend.antivirus import AntivirusScanner

# Avant d'accepter un fichier uploaddé
is_safe, message = AntivirusScanner.scan_file(file_path, 'documents')

if not is_safe:
    return {"error": "Fichier non sûr"}, 400
```

### 10. 🔄 Mise à Jour & Patches

```bash
# Vérifier les vulnérabilités
pip install safety
safety check

# Mettre à jour les dépendances
pip install --upgrade pip
pip install -r requirements.txt --upgrade
```

---

## CHECKLIST DE SÉCURITÉ PRÉ-PRODUCTION

- [ ] **SECRET_KEY** généré avec secrets cryptographiques
- [ ] **HTTPS/SSL** activé (Let's Encrypt gratuit)
- [ ] **Database URL** sur PostgreSQL (pas SQLite)
- [ ] **CORS** configuré pour les domaines spécifiques
- [ ] **Security Headers** ajoutés
- [ ] **Rate Limiting** activé
- [ ] **CSRF Protection** activée
- [ ] **SQL Injection** prévenue (ORM usage)
- [ ] **XSS** prévenue (Jinja2 escaping)
- [ ] **Antivirus** activé pour documents
- [ ] **Logging** structuré pour audit
- [ ] **Error Handling** masque les détails sensitifs
- [ ] **Database Backups** automatisé
- [ ] **Admin Panel** sécurisé
- [ ] **API Authentication** JWT/Token
- [ ] **File Upload** validé et sanitisé
- [ ] **Environment Variables** jamais commitées
- [ ] **Dependencies** sans vulnérabilités (`safety check`)
- [ ] **SSL Certificate** auto-renouvellement activé
- [ ] **Monitoring** configuré pour anomalies

---

## POUR LES INCIDENTS

### En cas de breach/hack:
1. ✅ Changer immédiatement SECRET_KEY
2. ✅ Révoquer tous les tokens JWT
3. ✅ Forcer le changement de passwords admin
4. ✅ Examiner les logs pour comprendre l'accès
5. ✅ Notifier les utilisateurs affectés
6. ✅ Effectuer audit de sécurité
7. ✅ Déployer le patch

### En cas de data leak:
1. ✅ Isoler les données exposées
2. ✅ Auditer qui a accès
3. ✅ Notifier les utilisateurs concernés
4. ✅ Renforcer l'authentification
5. ✅ Revoir les RLS policies

---

## RESOURCES IMPORTANTES

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Flask Security](https://flask.palletsprojects.com/en/latest/security/)
- [Werkzeug Security](https://werkzeug.palletsprojects.com/en/latest/security/)
- [Supabase RLS](https://supabase.com/docs/guides/realtime/security)
- [Let's Encrypt](https://letsencrypt.org/)

---

## TESTS DE SÉCURITÉ RÉGULIERS

Tous les **mois**:
- `pip install safety && safety check` - Vérifier vulnérabilités
- Audit des logs pour accès suspects  
- Rotation des certificats SSL
- Backup restoration test

Tous les **trimestres**:
- Audit de sécurité complet
- Pen testing interne
- Revoir les RLS policies

Annuellement:
- Audit de sécurité externe
- Mise à jour de tous les dépendances majeures
- Analyse des risques

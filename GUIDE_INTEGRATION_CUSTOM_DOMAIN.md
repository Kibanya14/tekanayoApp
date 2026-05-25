# 🚀 GUIDE D'INTÉGRATION - DOMAINES PERSONNALISÉS POUR VENDEURS

## 📋 Vue d'ensemble

Ce guide vous montre comment intégrer les domaines personnalisés dans votre application Tekanayo pour permettre aux vendeurs (comme Manianga) d'utiliser leurs propres domaines.

**Résultat final:**
- ✅ `https://mangastore.com` → Boutique Manianga
- ✅ `https://tekanayo.com/mangastore-1` → Même boutique (URL alternative)
- ✅ Gestion 100% dans la page Settings du vendeur

---

## 📦 FICHIERS CRÉÉS

### 1. **backend/apps_custom_domain.py**
Contient toutes les routes et fonctions pour gérer les domaines:
- `seller_update_custom_domain()` - POST: Ajouter/modifier/supprimer domaine
- `api_vendor_verify_dns()` - Vérifier la configuration DNS
- `identify_shop_by_custom_domain()` - Identifier la boutique par domaine
- `shop_public_entry()` - Afficher la boutique
- Fonctions utilitaires de validation

### 2. **frontend/templates/vendeur/settings_custom_domain.html**
Section HTML complète pour intégrer dans `vendeur/settings.html`:
- Interface de configuration domaine
- Guide DNS interactif
- Vérification DNS en temps réel
- Design professionnel avec Tailwind CSS

---

## 🔧 ÉTAPE 1: Modifier `backend/models.py`

Le champ `custom_domain` existe déjà dans `SellerShop` (ligne 356):

```python
class SellerShop(db.Model):
    # ... autres champs ...
    custom_domain = db.Column(db.String(255), unique=True)  # ✅ Déjà là!
```

✅ **AUCUNE modification nécessaire!**

---

## 🔌 ÉTAPE 2: Intégrer les routes dans `backend/apps.py`

### Option A: Copier/coller le contenu (RECOMMANDÉ)

1. Ouvrir `backend/apps_custom_domain.py`
2. Copier TOUT le contenu
3. Coller dans `backend/apps.py` (à la fin, avant la fermeture de l'app)

### Option B: Importer le module

À ajouter au début de `backend/apps.py`:

```python
# À ajouter après les autres imports
from backend.apps_custom_domain import (
    seller_update_custom_domain,
    api_vendor_verify_dns,
    identify_shop_by_custom_domain,
    shop_public_entry,
    _validate_domain_format,
    get_dns_help_info
)
```

Puis ajouter ces décorateurs dans `app.route()`:

```python
@app.route("/vendeur/<slug>/settings/update_domain", methods=["POST"])
@seller_session_required
def seller_update_custom_domain(slug):
    # Contenu de la fonction importée
    pass
```

---

## 🎨 ÉTAPE 3: Modifier `frontend/templates/vendeur/settings.html`

### Localiser le bon endroit

Trouver cette ligne (environ ligne 201):

```html
</div>
<!-- FIN de la section Logos -->

<!-- 👇 AJOUTER ICI 👇 -->
```

### Intégrer la section domaine

**Option 1: Include (simple)**

```html
<!-- Domaine personnalisé -->
{% include 'vendeur/settings_custom_domain.html' %}
```

**Option 2: Copier/coller direct**

Copier tout le contenu de `settings_custom_domain.html` et insérer directement après la section Logos.

### Exemple complet:

```html
    </div>
</div>
<!-- Fin section Logos -->

<!-- ════════════════════════════════════════════════════════════
     DOMAINE PERSONNALISÉ
     ════════════════════════════════════════════════════════════ -->
<div class="card-surface rounded-xl shadow-md p-6 border border-gray-200">
    <h3 class="text-xl font-semibold text-gray-800 mb-6 flex items-center space-x-2">
        <i class="fas fa-globe text-indigo-600"></i>
        <span>🌐 Domaine Personnalisé</span>
    </h3>
    <!-- ... reste du contenu ... -->
</div>

<!-- Bouton sauvegarde de la fin du formulaire -->
<div class="flex justify-end">
    <button type="submit" class="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700">Enregistrer</button>
</div>
</form>
```

---

## ⚙️ ÉTAPE 4: Configuration dans `before_request`

Localiser la fonction `@app.before_request` existante et ajouter:

```python
@app.before_request
def before_request():
    # Autres vérifications existantes...
    
    # Ajouter ceci:
    identify_shop_by_custom_domain()
```

---

## 🗄️ ÉTAPE 5: Migration Base de Données (si nécessaire)

Si le champ `custom_domain` n'existe pas (peu probable), ajouter la migration:

```bash
flask db migrate -m "Add custom_domain field to SellerShop"
flask db upgrade
```

---

## 🧪 TEST COMPLET

### 1. **Tester l'interface**

```
1. Aller sur: http://localhost/vendeur/mangastore-1/settings/page
2. Scroller jusqu'à "🌐 Domaine Personnalisé"
3. Sélectionner "J'ai un domaine personnalisé"
4. Entrer: mangastore.test
5. Cliquer: Ajouter
```

**Résultat attendu:** ✅ "Domaine 'mangastore.test' ajouté!"

### 2. **Tester la validation**

```
Essayer:
- "-invalid.com" → ❌ Format invalide
- "mangastore.com.." → ❌ Format invalide
- "mangastore@com" → ❌ Format invalide
- "valid-shop.com" → ✅ Format valide
```

### 3. **Tester l'unicité**

```
1. Ajouter "test.com" à la boutique 1
2. Aller à la boutique 2
3. Essayer d'ajouter "test.com"
   → ❌ "Le domaine 'test.com' est déjà utilisé"
```

### 4. **Tester la vérification DNS** (optionnel)

```
1. Configurer DNS localement (si possible)
   ou
   Utiliser un domaine réel (ex: mangastore.cd)

2. Cliquer: [✓ Vérifier la configuration DNS]
3. Résultat:
   - Si DNS OK: ✅ "pointe correctement vers Tekanayo"
   - Si DNS KO: ⏳ "Réessayez dans quelques minutes"
```

---

## 📝 VARIABLES D'ENVIRONNEMENT

Ajouter à votre `.env`:

```env
# Domaines personnalisés
TEKANAYO_SERVER_IP=92.132.145.33
TEKANAYO_APP_HOST=tekanayo.com
```

Puis modifier `apps_custom_domain.py`:

```python
import os

TEKANAYO_IP = os.getenv('TEKANAYO_SERVER_IP', '92.132.145.33')
```

---

## 🚀 DÉPLOIEMENT EN PRODUCTION

### 1. **DNS du serveur**

Assurez-vous que votre serveur accepte tous les domaines:

```nginx
# nginx configuration
server {
    server_name ~^(.*)\.tekanayo\.com$ tekanayo.com *.mangastore.com;
    # ... reste de la config
}
```

Ou pour Apache:

```apache
ServerAlias *.tekanayo.com tekanayo.com *.mangastore.com
```

### 2. **Certificat SSL**

Utiliser un wildcard certificate:

```bash
certbot certonly --manual \
  -d tekanayo.com \
  -d "*.tekanayo.com" \
  -d "*.mangastore.com"
```

Ou Let's Encrypt avec wildcard:

```bash
certbot certonly --dns-cloudflare \
  -d "*.tekanayo.com" \
  -d "tekanayo.com"
```

### 3. **Redirection HTTPS**

S'assurer que:
```nginx
# Forcer HTTPS
server {
    listen 80;
    server_name _;
    return 301 https://$host$request_uri;
}
```

---

## 🔍 DÉBOGAGE

### Problème 1: Domaine non résolu

```python
# Ajouter dans apps.py pour débogage
@app.route("/debug/domain")
def debug_domain():
    host = request.host
    shop = SellerShop.query.filter_by(custom_domain=host).first()
    return {
        'request_host': host,
        'shop_found': bool(shop),
        'shop_name': shop.name if shop else None
    }
```

### Problème 2: Vérification DNS échoue

```python
# Tester manuellement
import socket
try:
    ip = socket.gethostbyname('mangastore.test')
    print(f"✅ {ip}")
except socket.gaierror as e:
    print(f"❌ {e}")
```

### Problème 3: CORS sur vérification DNS

S'assurer que `/api/vendor/verify-dns` n'est accessible que par vendeurs authentifiés:

```python
@app.route("/api/vendor/verify-dns", methods=["POST"])
@seller_session_required  # ✅ Vérification requise!
def api_vendor_verify_dns():
    # ...
```

---

## 📊 SUIVI / ANALYTICS

Ajouter le tracking dans la DB:

```python
# Dans SellerPaymentTask ou nouveau modèle
class DomainChangeLog(db.Model):
    __tablename__ = "domain_change_logs"
    
    id = db.Column(db.Integer, primary_key=True)
    shop_id = db.Column(db.Integer, db.ForeignKey("seller_shops.id"))
    old_domain = db.Column(db.String(255))
    new_domain = db.Column(db.String(255))
    admin_id = db.Column(db.Integer, db.ForeignKey("seller_admins.id"))
    action = db.Column(db.String(20))  # "add", "remove", "change"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

---

## ✅ CHECKLIST FINALE

- [ ] ✅ Fichier `backend/models.py` - champ `custom_domain` existe
- [ ] ✅ Fichier `backend/apps_custom_domain.py` - créé et copié dans `apps.py`
- [ ] ✅ Fichier `frontend/templates/vendeur/settings_custom_domain.html` - créé
- [ ] ✅ Intégré dans `vendeur/settings.html`
- [ ] ✅ Routes ajoutées dans `apps.py`
- [ ] ✅ `before_request` configuré
- [ ] ✅ Variables d'env mises à jour
- [ ] ✅ Tests passant
- [ ] ✅ SSL/HTTPS configuré
- [ ] ✅ DNS wildcard OK
- [ ] ✅ Prêt pour production! 🚀

---

## 💡 CAS D'USAGE

### Manianga (Manga Store)

```
1. Va dans Settings
2. Section "🌐 Domaine Personnalisé"
3. Sélectionne "J'ai un domaine personnalisé"
4. Entre: mangastore.com
5. Clique: Ajouter
6. Suit le guide DNS
7. Vérifie configuration
8. Résultat: https://mangastore.com ✅
```

### Autre vendeur

```
Même process avec son propre domaine
Ex: boutique-kivu.cd, shop-kasai.com, etc.
```

---

## 📞 SUPPORT

**Questions fréquentes:**

**Q: Combien de domaines par boutique?**
A: 1 domaine par boutique (unique dans la BD)

**Q: Puis-je changer de domaine?**
A: Oui, retirer l'ancien et ajouter le nouveau

**Q: L'URL Tekanayo fonctionne toujours?**
A: Oui, `tekanayo.com/boutique-slug` continue de marcher

**Q: Qui voit le guide DNS?**
A: Seulement le propriétaire (is_owner=true)

---

**Date:** 25 Mai 2026  
**Status:** ✅ Production-ready  
**Version:** 1.0

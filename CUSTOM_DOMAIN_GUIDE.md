# 🌐 GUIDE COMPLET : DOMAINES PERSONNALISÉS POUR BOUTIQUES

## Vue d'Ensemble

Avec **TekanayoApp**, chaque vendeur peut faire fonctionner sa boutique sous son **propre domaine personnalisé** et apparaître comme un **site e-commerce complètement indépendant**.

---

## 📋 ARCHITECTURES POSSIBLES

### Architecture 1: Domaine Personnalisé Simple (Recommandée)

```
Vendeur: Manianga Ngayo
Domaine acheté: manianga-ngayo.com

Configuration:
├─ Achète le domaine chez Godaddy/Namecheap: ~$10-15/an
├─ Configure DNS pour pointer vers tekanayo.app
└─ Ajoute dans TekanayoApp admin: custom_domain = "manianga-ngayo.com"

Résultat:
https://manianga-ngayo.com → Boutique Manianga (site indépendant)
https://tekanayo.com/manianga-ngayo-1 → Même boutique (URL alternative)
```

### Architecture 2: Sous-domaine Tekanayo

```
Vendeur: Manianga Ngayo
Domaine Tekanayo: manianga.tekanayo.com

Configuration:
├─ Tekanayo admin configure le DNS
├─ manianga.tekanayo.com pointe vers tekanayo.com
└─ Automatiquement routé vers boutique Manianga

Résultat:
https://manianga.tekanayo.com → Boutique Manianga (branding personnalisé)
```

### Architecture 3: Domaine avec Hébergeur Externe

```
Vendeur achète domaine chez un autre registrar
Utilisé pour redirection ou DNS forwarding
Pointe vers manianga-ngayo.tekanayo.com
```

---

## 🔧 SETUP TECHNIQUE

### Étape 1: DNS Configuration

**Pour un domaine personnalisé (manianga-ngayo.com):**

```
Type: A Record
Name: @
Value: IP_de_tekanayo (ex: 92.132.145.33)
TTL: 3600

OU

Type: CNAME
Name: @
Value: tekanayo.app
TTL: 3600
```

**Pour un sous-domaine (manianga.tekanayo.com):**

```
Type: CNAME
Name: manianga
Value: tekanayo.app
TTL: 3600
```

### Étape 2: Configuration dans TekanayoApp

**Admin panel → Vendeurs → Sélectionner boutique:**

```
Onglet: Paramètres
Champ: "Domaine personnalisé"
Valeur: manianga-ngayo.com

Sauvegarde ✅
```

### Étape 3: Configuration SSL/HTTPS

TekanayoApp gère automatiquement les certificats SSL wildcard:

```
*.tekanayo.com → Certificat wildcard inclus

Pour domaines personnalisés:
- Acheteur configure le certificat (inclus gratuit via Let's Encrypt)
- Ou Tekanayo admin configure automatiquement
```

---

## 📊 AFFICHAGE PAR DOMAINE

### Visite sur manianga-ngayo.com

```
Affichage COMPLET comme site indépendant:
├─ Titre navigateur: "Manianga Manga Store"
├─ Logo: Logo personnalisé Manianga
├─ Barre d'adresse: manianga-ngayo.com (AUCUNE mention Tekanayo)
├─ Footer: © Manianga Ngayo. Tous droits réservés.
├─ Contact: Email/Téléphone de Manianga
├─ Pages: À propos, Conditions, Politique de confidentialité (personnalisées)
└─ Produits: Produits de Manianga

Aucune trace de Tekanayo sauf mention "Propulsé par Tekanayo" en petit (optionnel)
```

### Visite sur tekanayo.com/manianga-ngayo-1

```
Affichage avec branding Tekanayo + boutique:
├─ Titre navigateur: "Manianga Manga Store | Tekanayo"
├─ Navigation principale: Portal Tekanayo visible
├─ Mention Tekanayo: Bien visible
└─ Boutique: Affichée comme une boutique parmi d'autres
```

### Visite sur admin.tekanayo.com

```
Panel d'administration Tekanayo
Gestion de toutes les boutiques, vendeurs, paiements, etc.
```

---

## 💾 BASE DE DONNÉES

### Table: seller_shops

```sql
-- Exemple pour Manianga Ngayo
INSERT INTO seller_shops (
    id,
    name,
    slug,
    custom_domain,
    logo_url,
    owner_email,
    support_email,
    support_phone,
    address,
    description,
    category_niche,
    is_active,
    created_at
) VALUES (
    1,
    'Manianga Manga Store',
    'manianga-ngayo-1',
    'manianga-ngayo.com',
    '/uploads/logos/manianga-logo.png',
    'manianga@email.com',
    'support@manianga-ngayo.com',
    '+243813091409',
    'Kinshasa, DRC',
    'Meilleure boutique de mangas en ligne',
    'shopdivers',
    TRUE,
    NOW()
);
```

### Champs Clés:

```python
class SellerShop(db.Model):
    # Identifiants uniques
    id: Integer
    slug: String(unique) → "manianga-ngayo-1"
    custom_domain: String(unique) → "manianga-ngayo.com"
    
    # Branding
    name: String → "Manianga Manga Store"
    logo_url: String → URL du logo personnalisé
    description: Text → Description de la boutique
    
    # Contact
    support_email: String
    support_phone: String
    address: Text
    facebook_url: String
    whatsapp_number: String
    telegram_username: String
    
    # Pages personnalisées
    about_page_content: Text
    terms_page_content: Text
    privacy_page_content: Text
    returns_page_content: Text
    legal_page_content: Text
```

---

## 🚀 ROUTING WORKFLOW

### Requête 1: Visite sur manianga-ngayo.com

```python
# 1. Flask reçoit la requête
@app.route("/<shop_key>")
def shop_public_entry(shop_key):
    
    # 2. Flask obtient le HOST de la requête
    host = request.host  # "manianga-ngayo.com"
    
    # 3. Résolution du domaine
    shop = SellerShop.query.filter_by(
        custom_domain="manianga-ngayo.com",
        is_active=True
    ).first()
    # ✅ Trouve: SellerShop(id=1, name="Manianga Manga Store")
    
    # 4. Rendu de la boutique avec branding
    return render_template(
        "clientvendeur/shoptheme/index.html",
        shop=shop,
        products=shop.products,
        branding=shop.get_branding()
    )
```

### Requête 2: Visite sur tekanayo.com/manianga-ngayo-1

```python
# 1. Flask reçoit /manianga-ngayo-1
@app.route("/<shop_key>")
def shop_public_entry(shop_key):
    
    # 2. shop_key = "manianga-ngayo-1"
    
    # 3. Résolution par slug
    shop = SellerShop.query.filter_by(
        slug="manianga-ngayo-1",
        is_active=True
    ).first()
    # ✅ Trouve la même boutique
    
    # 4. Rendu (même résultat)
    return render_template(
        "clientvendeur/shoptheme/index.html",
        shop=shop,
        products=shop.products
    )
```

---

## 💰 FACTURATION & TARIFICATION

### Pour Manianga Ngayo avec domaine personnalisé:

| Item | Coût | Payeur |
|------|------|--------|
| **Domaine .com/cd** | $10-15/an | Manianga |
| **Abonnement Tekanayo** | $5/mois | Manianga (à Tekanayo) |
| **Hébergement** | INCLUS | Tekanayo |
| **Maintenance** | INCLUS | Tekanayo |
| **SSL/HTTPS** | INCLUS | Tekanayo |
| **Backups** | INCLUS | Tekanayo |
| **Support** | INCLUS | Tekanayo |

**TOTAL: ~$5-6/mois + ~$1/mois domaine = $6-7/mois**

---

## 🎨 CUSTOMISATION PAR BOUTIQUE

Chaque boutique peut personnaliser:

```python
# Dans l'interface vendeur
shop.name = "Manianga Manga Store"
shop.logo_url = "/uploads/manianga-logo.png"
shop.support_email = "support@manianga-ngayo.com"
shop.support_phone = "+243813091409"
shop.address = "Kinshasa, DRC"
shop.facebook_url = "https://facebook.com/manianga"
shop.whatsapp_number = "+243813091409"
shop.telegram_username = "@manianga_store"

# Pages complètement personnalisées
shop.about_page_content = "..." # Qui sommes-nous
shop.terms_page_content = "..." # Conditions d'utilisation
shop.privacy_page_content = "..." # Politique de confidentialité
shop.returns_page_content = "..." # Politique de retours
shop.legal_page_content = "..." # Mentions légales
```

---

## 🔒 SÉCURITÉ & VALIDATION

### Validation d'unicité:

```python
# Chaque domaine personnalisé est UNIQUE dans la base
custom_domain: String(unique=True)

# Vérification lors de l'enregistrement
conflict = SellerShop.query.filter_by(
    custom_domain="manianga-ngayo.com"
).first()

if conflict:
    flash("Ce domaine est déjà utilisé par une autre boutique", "error")
    return redirect(...)
```

### Sécurité HTTPS:

```
- Certificats Let's Encrypt automatiques
- Wildcard pour *.tekanayo.com
- Domaines personnalisés: certificat dédié requis
```

---

## 📱 EXEMPLE COMPLET: SETUP MANIANGA NGAYO

### Étape 1: Achat du domaine

```
Site: godaddy.com
Domaine: manianga-ngayo.com
Prix: $12/an
```

### Étape 2: Configuration DNS (Godaddy)

```
DNS Management:
├─ A Record
│  ├─ Name: @
│  ├─ Type: A
│  └─ Value: 92.132.145.33 (IP tekanayo)
│
└─ CNAME (optionnel pour www)
   ├─ Name: www
   ├─ Type: CNAME
   └─ Value: manianga-ngayo.com
```

### Étape 3: Configuration Tekanayo

```
1. Admin login → tekanayo.com/admin
2. Sélectionner Manianga Ngayo dans liste vendeurs
3. Onglet Paramètres
4. Remplir:
   - Domaine personnalisé: manianga-ngayo.com
   - Logo: Uploader logo Manianga
   - Email support: support@manianga-ngayo.com
   - Téléphone: +243813091409
5. Sauvegarde ✅
```

### Étape 4: Vérification

```
URL 1: https://manianga-ngayo.com
✅ Affiche boutique Manianga (site indépendant)

URL 2: https://tekanayo.com/manianga-ngayo-1
✅ Affiche même boutique (URL alternative)

HTTPS: ✅ Certificat automatiqueement déployé
```

---

## 🎯 RÉSULTAT FINAL

**Manianga Ngayo obtient:**

```
✅ Son site e-commerce professionnel
✅ Domaine personnalisé (manianga-ngayo.com)
✅ Branding 100% personnalisé
✅ Support technique 24/7
✅ Maintenance automatique
✅ Sécurité SSL/TLS
✅ Backups quotidiens
✅ Coût minimal (~$5-6/mois)

ET

✅ ZÉRO effort technique
✅ ZÉRO serveur à gérer
✅ ZÉRO domaine/SSL à configurer
✅ Peut se concentrer sur les VENTES!
```

---

## 📞 SUPPORT

Pour questions sur la configuration:
- Admin Tekanayo: support@tekanayo.com
- Documentation: docs.tekanayo.com
- Chat: chat.tekanayo.com

# 🎯 GUIDE CLAIR: AJOUT DE DOMAINE PERSONNALISÉ POUR VENDEURS

## 📌 CLARIFICATION IMPORTANTE

### Tekanayo - Infrastructure (Responsable: Admin Tekanayo)

```
EXTERNE - Hors de l'application:

1. Tekanayo achète le domaine: tekanayo.com (~$10-15/an)
   Chez: Namecheap, Godaddy, etc.

2. Tekanayo configure DNS chez le fournisseur:
   Type: A Record
   Name: @
   Value: IP_du_serveur_tekanayo (92.132.145.33)
   
3. Tekanayo achète certificat SSL:
   Wildcard: *.tekanayo.com (ou Let's Encrypt gratuit)

4. Tekanayo deploy l'application sur le serveur:
   $ git clone https://github.com/Kibanya14/tekanayoApp
   $ python app.py
   → Application accessible via https://tekanayo.com

⚠️ TOUT ÇA: CONFIGURATION EXTERNE, PAS DANS L'APP
```

### Vendeur (Manianga Ngayo) - Espace Vendeur (Responsable: Vendeur)

```
DANS L'APPLICATION - Espace vendeur:

Manianga accède à: https://tekanayo.com/vendeur/mangastore-1

Menu vendeur:
├─ Dashboard
├─ Produits
├─ Commandes
├─ Livreurs
├─ Clients
└─ SETTINGS ← ICIIII

Dans Settings, Manianga voit:
┌────────────────────────────────────────────┐
│ PARAMÈTRES BOUTIQUE MANGASTORE             │
├────────────────────────────────────────────┤
│ Nom: Mangastore                           │
│ Email support: support@mangastore.com     │
│ Téléphone: +243813091409                  │
│ ...                                        │
│                                            │
│ [NOUVEAU] DOMAINE PERSONNALISÉ:           │
│ ┌────────────────────────────────────────┐│
│ │ Avez-vous un domaine personnalisé?    ││
│ │                                        ││
│ │ ○ Non, je n'ai pas de domaine        ││
│ │ ○ Oui, j'ai acheté un domaine        ││
│ │                                        ││
│ │ Si oui, entrez votre domaine:         ││
│ │ [mangastore.com                    ] ││
│ │                                        ││
│ │ Guide: lire docs/domaine-perso.md    ││
│ └────────────────────────────────────────┘│
│                                            │
│ [Sauvegarde]                              │
└────────────────────────────────────────────┘
```

---

## 🔄 WORKFLOW COMPLET POUR MANIANGA NGAYO

### ÉTAPE 1: Manianga crée sa boutique

```
URL: https://tekanayo.com/portal/sellerregister

Formulaire:
├─ Nom boutique: "Mangastore"
├─ Email: manianga@email.com
├─ Téléphone: +243813091409
├─ Niche: Boutique générale
├─ Description: "Vente de mangas et produits divers"
└─ [Créer boutique]

Résultat:
✅ Boutique créée
✅ URL: https://tekanayo.com/mangastore-1
✅ Espace vendeur: https://tekanayo.com/vendeur/mangastore-1
```

### ÉTAPE 2A: Manianga NE veut PAS de domaine personnalisé

```
Manianga fait RIEN ✅

Sa boutique reste accessible uniquement à:
https://tekanayo.com/mangastore-1

C'est tout!
```

### ÉTAPE 2B: Manianga VEUT un domaine personnalisé

#### SUBSTEP 1: Manianga achète un domaine EXTERNE

```
⚠️ HORS DE L'APPLICATION - Tâche de Manianga

Manianga va sur: https://www.namecheap.com
Ou: https://www.godaddy.com

Recherche: mangastore.com (ou mangastore.cd, etc.)
Achète le domaine pour 1 an (~$10-15)
Reçoit un email de confirmation ✅

Maintenant Manianga possède: mangastore.com
```

#### SUBSTEP 2: Manianga configure DNS CHEZ LE FOURNISSEUR

```
⚠️ HORS DE L'APPLICATION - Tâche de Manianga

Namecheap Dashboard:
1. Login avec les identifiants
2. Aller à: Manage → DNS

Configurer DNS Record:
┌─────────────────────────────────────┐
│ DNS Management                      │
├─────────────────────────────────────┤
│ Add A Record:                       │
│ Type: A                             │
│ Host: @                             │
│ Value: 92.132.145.33 (IP Tekanayo)  │ ← Tekanayo donne cette IP
│ TTL: 3600                           │
│ [Add Record]                        │
└─────────────────────────────────────┘

OU (Alternatif - CNAME):
┌─────────────────────────────────────┐
│ Type: CNAME                         │
│ Host: @                             │
│ Value: tekanayo.com                 │
│ TTL: 3600                           │
│ [Add Record]                        │
└─────────────────────────────────────┘

Manianga appuie sur [Save] ✅

⏳ Attendre 5-30 minutes pour propagation DNS
```

#### SUBSTEP 3: Manianga rentre le domaine dans son espace vendeur

```
✅ DANS L'APPLICATION - Tâche de Manianga

URL: https://tekanayo.com/vendeur/mangastore-1
Menu: Settings

Remplir le champ:
┌────────────────────────────────────────┐
│ Domaine personnalisé                  │
├────────────────────────────────────────┤
│ ○ Je n'ai pas de domaine              │
│ ● J'ai acheté un domaine (SÉLECTIONNÉ)│
│                                        │
│ Mon domaine: [mangastore.com        ] │
│                                        │
│ Configuration DNS (pour votre aide):  │
│ ┌──────────────────────────────────┐  │
│ │ Type: A                          │  │
│ │ Host: @                          │  │
│ │ Value: 92.132.145.33             │  │
│ │                                  │  │
│ │ [Copier vers le presse-papiers]  │  │
│ └──────────────────────────────────┘  │
│                                        │
│ [Vérifier Configuration]               │
│ [Sauvegarde]                          │
└────────────────────────────────────────┘

Tekanayo valide en backend:
- Vérifie l'unicité: mangastore.com pas utilisé ailleurs ✅
- Enregistre: shop.custom_domain = "mangastore.com"
- Sauvegarde en DB ✅

Message: "✅ Domaine ajouté avec succès!"
```

#### SUBSTEP 4: Vérification

```
Manianga teste dans son navigateur:
1. https://mangastore.com
   ↓
   Résolution DNS chez Namecheap
   ↓
   IP: 92.132.145.33 (serveur Tekanayo)
   ↓
   Flask identifie le domaine: custom_domain = "mangastore.com"
   ↓
   ✅ Affiche sa boutique Mangastore

2. https://tekanayo.com/mangastore-1
   ↓
   ✅ Affiche AUSSI sa boutique (URL alternative)

Résultat: Deux URLs, MÊME boutique ✅
```

---

## 💻 IMPLÉMENTATION CODE DANS L'APP

### 1️⃣ Model (backend/models.py)

```python
class SellerShop(db.Model):
    __tablename__ = "seller_shops"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(140), nullable=False)
    slug = db.Column(db.String(160), unique=True, nullable=False)
    
    # ✨ NOUVEAU CHAMP
    custom_domain = db.Column(
        db.String(255), 
        unique=True,  # Chaque domaine est unique
        nullable=True  # Peut être vide (pas de domaine perso)
    )
    
    logo_url = db.Column(db.String(255))
    owner_email = db.Column(db.String(120), nullable=False)
    # ... autres champs
```

### 2️⃣ Route Settings Vendeur (backend/apps.py)

```python
@app.route("/vendeur/<slug>/settings/page", methods=["GET", "POST"])
@seller_session_required
def seller_settings_page(slug):
    """Page des paramètres du vendeur"""
    
    shop = SellerShop.query.filter_by(slug=slug).first_or_404()
    
    if request.method == "GET":
        # Afficher la page
        return render_template(
            "vendeur/settings.html",
            shop=shop,
            # Passer l'IP du serveur Tekanayo pour montrer la config DNS
            tekanayo_server_ip="92.132.145.33",
            active_page="settings"
        )
    
    # POST - Mise à jour
    new_name = (request.form.get("shop_name") or "").strip()
    custom_domain = (request.form.get("custom_domain") or "").strip().lower()
    
    if new_name:
        shop.name = new_name
    
    # ✨ GESTION DU DOMAINE PERSONNALISÉ
    if custom_domain:
        # Vérifier l'unicité
        existing = SellerShop.query.filter(
            SellerShop.custom_domain == custom_domain,
            SellerShop.id != shop.id  # Pas la boutique actuelle
        ).first()
        
        if existing:
            flash(
                f"❌ Le domaine '{custom_domain}' est déjà utilisé par une autre boutique!",
                "error"
            )
            return redirect(url_for("seller_settings_page", slug=slug))
        
        # Valider le format du domaine
        import re
        if not re.match(r'^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?(\.[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?)*$', custom_domain):
            flash("❌ Format de domaine invalide!", "error")
            return redirect(url_for("seller_settings_page", slug=slug))
        
        shop.custom_domain = custom_domain
        flash(f"✅ Domaine '{custom_domain}' ajouté avec succès!", "success")
    
    elif request.form.get("remove_domain"):
        # Manianga veut retirer le domaine
        if shop.custom_domain:
            old_domain = shop.custom_domain
            shop.custom_domain = None
            flash(f"✅ Domaine '{old_domain}' supprimé!", "success")
    
    db.session.commit()
    return redirect(url_for("seller_settings_page", slug=slug))
```

### 3️⃣ Template Settings (frontend/templates/vendeur/settings.html)

```html
<!-- Fichier: frontend/templates/vendeur/settings.html -->

<div class="settings-section">
    <h3>🌐 Domaine Personnalisé</h3>
    
    <form method="POST" action="{{ url_for('seller_settings_page', slug=shop.slug) }}">
        <fieldset>
            <legend>Avez-vous un domaine personnalisé?</legend>
            
            <label>
                <input type="radio" name="has_domain" value="no" 
                    {% if not shop.custom_domain %}checked{% endif %}>
                Non, je n'ai pas de domaine personnalisé
            </label>
            
            <label>
                <input type="radio" name="has_domain" value="yes" 
                    {% if shop.custom_domain %}checked{% endif %}>
                Oui, j'ai acheté un domaine
            </label>
        </fieldset>
        
        <div id="domain-input" style="display: none; margin-top: 20px;">
            <label for="custom_domain">Votre nom de domaine:</label>
            <input 
                type="text" 
                id="custom_domain" 
                name="custom_domain" 
                placeholder="exemple: mangastore.com"
                value="{{ shop.custom_domain or '' }}"
                pattern="^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?(\.[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?)*$"
                title="Format: exemple.com ou sous-domaine.exemple.com"
            >
            
            <!-- AIDE: Configuration DNS -->
            <details>
                <summary>📖 Comment configurer mon domaine?</summary>
                <div class="dns-help">
                    <h4>Configuration DNS chez votre fournisseur:</h4>
                    <p>1. Allez sur <strong>Namecheap.com</strong> (ou Godaddy, etc.)</p>
                    <p>2. Allez dans <strong>DNS Management</strong></p>
                    <p>3. Ajoutez ce record A:</p>
                    <pre>
Type: A
Host: @
Value: {{ tekanayo_server_ip }}
TTL: 3600
                    </pre>
                    <button type="button" class="btn-copy" onclick="copierDNS()">
                        📋 Copier
                    </button>
                    <p>4. Cliquez <strong>[Save]</strong></p>
                    <p>⏳ Attendre 5-30 minutes pour la propagation DNS</p>
                    <p>5. Revenez ici et entrez votre domaine: <code>{{ shop.custom_domain or 'mangastore.com' }}</code></p>
                </div>
            </details>
            
            <!-- Bouton de vérification -->
            <button type="button" id="verify-domain" class="btn btn-secondary">
                ✓ Vérifier la configuration
            </button>
        </div>
        
        <div class="form-buttons">
            <button type="submit" class="btn btn-primary">💾 Sauvegarde</button>
        </div>
    </form>
</div>

<script>
    // Afficher/masquer le champ domaine
    document.querySelectorAll('input[name="has_domain"]').forEach(radio => {
        radio.addEventListener('change', function() {
            document.getElementById('domain-input').style.display = 
                this.value === 'yes' ? 'block' : 'none';
        });
    });
    
    // Copier les infos DNS
    function copierDNS() {
        const texte = `Type: A\nHost: @\nValue: {{ tekanayo_server_ip }}\nTTL: 3600`;
        navigator.clipboard.writeText(texte).then(() => {
            alert('✅ Copié dans le presse-papiers!');
        });
    }
    
    // Vérifier la configuration DNS
    document.getElementById('verify-domain')?.addEventListener('click', async function() {
        const domain = document.getElementById('custom_domain').value;
        if (!domain) {
            alert('❌ Entrez d\'abord votre domaine');
            return;
        }
        
        try {
            const response = await fetch('/api/verify-domain', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({domain: domain})
            });
            const data = await response.json();
            
            if (data.valid) {
                alert('✅ Configuration DNS détectée! Vous pouvez maintenant sauvegarder.');
            } else {
                alert('⏳ Configuration DNS non encore propagée. Réessayez dans 5-10 minutes.');
            }
        } catch (e) {
            alert('❌ Erreur lors de la vérification');
        }
    });
</script>
```

### 4️⃣ API Vérification DNS (backend/apps.py)

```python
@app.route("/api/verify-domain", methods=["POST"])
@seller_session_required
def api_verify_domain():
    """Vérifie si le DNS est correctement configuré"""
    
    import socket
    
    data = request.get_json()
    domain = (data.get("domain") or "").strip().lower()
    
    if not domain:
        return jsonify({"valid": False, "error": "Domaine requis"}), 400
    
    try:
        # Essayer de résoudre le domaine
        ip = socket.gethostbyname(domain)
        
        # Vérifier que l'IP pointe vers Tekanayo
        tekanayo_ip = os.getenv("SERVER_IP", "92.132.145.33")
        
        if ip == tekanayo_ip:
            return jsonify({
                "valid": True,
                "message": f"✅ {domain} pointe correctement vers Tekanayo",
                "ip": ip
            })
        else:
            return jsonify({
                "valid": False,
                "message": f"⚠️ {domain} pointe vers {ip} au lieu de {tekanayo_ip}",
                "ip": ip
            })
    
    except socket.gaierror:
        return jsonify({
            "valid": False,
            "error": "Domaine non résolvable. Vérifiez la configuration DNS."
        })
    except Exception as e:
        return jsonify({
            "valid": False,
            "error": str(e)
        })
```

### 5️⃣ Identification de la boutique par domaine

```python
# Dans apps.py - Avant chaque requête

@app.before_request
def identify_shop_by_domain():
    """Identifie la boutique selon le domaine visité"""
    
    host = request.host.lower().split(':')[0]
    
    # Chercher une boutique avec ce custom_domain
    shop = SellerShop.query.filter_by(
        custom_domain=host,
        is_active=True
    ).first()
    
    if shop:
        g.current_shop = shop
        g.shop_via_custom_domain = True
    else:
        g.current_shop = None
        g.shop_via_custom_domain = False


@app.route("/<shop_key>")
def shop_public_entry(shop_key):
    """Affiche une boutique"""
    
    # Si accédée via custom domain
    if g.current_shop:
        shop = g.current_shop
    else:
        # Sinon chercher par slug
        shop = SellerShop.query.filter_by(
            slug=shop_key,
            is_active=True
        ).first()
    
    if not shop:
        flash("Boutique introuvable", "error")
        return redirect(url_for("tekanayo_portal"))
    
    # Afficher
    view = _build_shop_page_context(shop)
    
    return render_template(
        "clientvendeur/shoptheme/index.html",
        shop=shop,
        is_custom_domain=g.shop_via_custom_domain,
        **view
    )
```

---

## 🎯 RÉSUMÉ POUR MANIANGA NGAYO

### Cas 1: SANS domaine personnalisé

```
Manianga fait RIEN dans les settings ✅

Sa boutique:
https://tekanayo.com/mangastore-1

C'est tout!
```

### Cas 2: AVEC domaine personnalisé

```
1. Manianga achète mangastore.com chez Namecheap
   (5 min) ✅

2. Manianga configure DNS chez Namecheap:
   - Type: A
   - Host: @
   - Value: 92.132.145.33
   (5 min) ✅

3. Manianga attend 5-30 min (propagation DNS)
   ⏳

4. Manianga va dans son espace vendeur:
   https://tekanayo.com/vendeur/mangastore-1

5. Settings → Domaine personnalisé
   Saisit: mangastore.com
   Clique: [Vérifier]
   Clique: [Sauvegarde]
   (2 min) ✅

6. Manianga teste:
   https://mangastore.com
   ✅ Sa boutique s'affiche!

Effort total: ~15 min pour Manianga
Configuration: 90% HORS de l'app
```

---

## 📋 CHECKLIST IMPLÉMENTATION

- [ ] Ajouter champ `custom_domain` à SellerShop model
- [ ] Créer/mettre à jour template `vendeur/settings.html`
- [ ] Créer route POST `/vendeur/<slug>/settings`
- [ ] Créer endpoint `/api/verify-domain`
- [ ] Ajouter `@app.before_request` pour identifier domaine
- [ ] Tester avec un domaine réel
- [ ] Documentation pour vendeurs
- [ ] Support pour migration (sans domaine → avec domaine)

**STATUS:** 🚀 Prêt à implémenter!

# 📄 Système de Validation des Documents Vendeur

## 🎯 Vue d'Ensemble

Les vendeurs doivent maintenant uploader 2 documents obligatoires lors de l'inscription :
1. ✅ **Pièce d'identité** (Carte d'identité ou Passeport)
2. ✅ **Justificatif d'adresse** (Facture eau/électricité)

Ces documents seront vérifiés par l'admin Tekanayo avant d'activer le vendeur.

---

## 📁 Fichiers à Créer (Backend)

### 1. Mettre à jour `backend/models.py`

Ajouter les champs pour stocker les documents :

```python
class SellerShop(db.Model):
    # ... champs existants ...
    
    # Documents de validation (NOUVEAUX)
    id_document_path = db.Column(db.String(500))  # Chemin vers pièce d'identité
    address_document_path = db.Column(db.String(500))  # Chemin vers justificatif d'adresse
    verification_status = db.Column(db.String(20), default="pending")  # pending, verified, rejected
    verified_by = db.Column(db.Integer, db.ForeignKey("platform_admins.id"))
    verified_at = db.Column(db.DateTime)
    verification_notes = db.Column(db.Text)  # Notes de l'admin
```

---

### 2. Mettre à jour `backend/apps.py`

#### A. Gérer l'upload des documents

```python
from werkzeug.utils import secure_filename
import os
from datetime import datetime

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'pdf'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_file(file, folder):
    """Sauvegarde un fichier uploadé et retourne le chemin"""
    if not file or not allowed_file(file.filename):
        return None
    
    # Créer le dossier s'il n'existe pas
    upload_folder = os.path.join(app.config['UPLOAD_ROOT'], folder)
    os.makedirs(upload_folder, exist_ok=True)
    
    # Nommer le fichier avec timestamp
    timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{timestamp}_{secrets.token_hex(4)}.{ext}"
    
    # Sauvegarder
    filepath = os.path.join(upload_folder, filename)
    file.save(filepath)
    
    # Retourner le chemin relatif
    return f"/uploads/{folder}/{filename}"

@app.route("/portal/register", methods=["POST"])
def become_seller():
    # ... code existant ...
    
    # Gérer l'upload des documents
    id_document = request.files.get('id_document')
    address_document = request.files.get('address_document')
    
    id_document_path = None
    address_document_path = None
    
    if id_document and allowed_file(id_document.filename):
        id_document_path = save_uploaded_file(id_document, 'seller_documents/id')
    
    if address_document and allowed_file(address_document.filename):
        address_document_path = save_uploaded_file(address_document, 'seller_documents/address')
    
    # Créer la boutique avec les documents
    shop = SellerShop(
        name=shop_name,
        slug=slug,
        owner_email=email,
        # ... autres champs ...
        id_document_path=id_document_path,
        address_document_path=address_document_path,
        verification_status='pending',  # En attente de validation
    )
    
    # ... suite du code ...
```

---

#### B. Routes Admin pour la Validation

```python
@app.route("/admin/sellers/verification")
@admin_required("manage_sellers")
def admin_sellers_verification():
    """Liste des vendeurs en attente de validation"""
    pending_sellers = SellerShop.query.filter_by(
        verification_status='pending'
    ).order_by(SellerShop.created_at.desc()).all()
    
    return render_template(
        "admin/sellers_verification.html",
        pending_sellers=pending_sellers
    )

@app.route("/admin/sellers/<int:shop_id>/verify", methods=["GET", "POST"])
@admin_required("manage_sellers")
def admin_verify_seller(shop_id):
    """Page de validation d'un vendeur"""
    shop = SellerShop.query.get_or_404(shop_id)
    
    if request.method == "POST":
        action = request.form.get('action')  # 'approve' or 'reject'
        notes = request.form.get('verification_notes', '').strip()
        
        if action == 'approve':
            shop.verification_status = 'verified'
            shop.verified_by = current_user.id
            shop.verified_at = datetime.utcnow()
            shop.verification_notes = notes
            
            # Activer l'abonnement
            subscription = SellerSubscription.query.filter_by(shop_id=shop.id).first()
            if subscription:
                subscription.status = 'active'
            
            flash(f"Vendeur {shop.name} approuvé avec succès !", "success")
            
        elif action == 'reject':
            shop.verification_status = 'rejected'
            shop.verified_by = current_user.id
            shop.verified_at = datetime.utcnow()
            shop.verification_notes = notes
            
            # Suspendre l'abonnement
            subscription = SellerSubscription.query.filter_by(shop_id=shop.id).first()
            if subscription:
                subscription.status = 'suspended'
            
            flash(f"Vendeur {shop.name} rejeté.", "warning")
        
        db.session.commit()
        return redirect(url_for('admin_sellers_verification'))
    
    return render_template("admin/verify_seller.html", shop=shop)

@app.route("/admin/sellers/documents/<path:filename>")
@admin_required()
def admin_view_seller_document(filename):
    """Afficher un document vendeur (sécurisé)"""
    from flask import send_from_directory
    
    return send_from_directory(
        os.path.join(app.config['UPLOAD_ROOT'], 'seller_documents'),
        filename,
        as_attachment=False
    )
```

---

## 🎨 Templates Admin à Créer

### 1. `admin/sellers_verification.html`

```html
{% extends "admin/basee.html" %}
{% block title %}Validation Vendeurs{% endblock %}
{% block header_title %}Validation des Vendeurs{% endblock %}

{% block content %}
<div class="space-y-6">
    <!-- Statistiques -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div class="card-surface rounded-xl p-6 border border-yellow-200 bg-yellow-50">
            <p class="text-sm font-medium text-yellow-800">En attente</p>
            <p class="text-3xl font-bold text-yellow-900 mt-2">{{ pending_sellers|length }}</p>
        </div>
        <div class="card-surface rounded-xl p-6 border border-green-200 bg-green-50">
            <p class="text-sm font-medium text-green-800">Validés</p>
            <p class="text-3xl font-bold text-green-900 mt-2">{{ stats.verified }}</p>
        </div>
        <div class="card-surface rounded-xl p-6 border border-red-200 bg-red-50">
            <p class="text-sm font-medium text-red-800">Rejetés</p>
            <p class="text-3xl font-bold text-red-900 mt-2">{{ stats.rejected }}</p>
        </div>
    </div>

    <!-- Liste des vendeurs en attente -->
    <div class="card-surface rounded-xl shadow-md p-6">
        <h3 class="text-xl font-semibold mb-4">Vendeurs en attente de validation</h3>
        
        {% if pending_sellers %}
        <div class="overflow-x-auto">
            <table class="min-w-full">
                <thead>
                    <tr class="text-left text-gray-500 border-b">
                        <th class="py-3">Boutique</th>
                        <th class="py-3">Email</th>
                        <th class="py-3">Date</th>
                        <th class="py-3">Documents</th>
                        <th class="py-3">Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {% for shop in pending_sellers %}
                    <tr class="border-b hover:bg-gray-50">
                        <td class="py-3">
                            <p class="font-semibold">{{ shop.name }}</p>
                            <p class="text-xs text-gray-500">{{ shop.slug }}</p>
                        </td>
                        <td class="py-3">{{ shop.owner_email }}</td>
                        <td class="py-3 text-sm">{{ shop.created_at.strftime('%d/%m/%Y') }}</td>
                        <td class="py-3">
                            {% if shop.id_document_path and shop.address_document_path %}
                            <span class="text-green-700 text-sm">
                                <i class="fas fa-check-circle"></i> Complets
                            </span>
                            {% else %}
                            <span class="text-red-700 text-sm">
                                <i class="fas fa-exclamation-circle"></i> Incomplets
                            </span>
                            {% endif %}
                        </td>
                        <td class="py-3">
                            <a href="{{ url_for('admin_verify_seller', shop_id=shop.id) }}"
                               class="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 text-sm">
                                <i class="fas fa-eye mr-1"></i>
                                Vérifier
                            </a>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        {% else %}
        <p class="text-center text-gray-500 py-8">Aucun vendeur en attente</p>
        {% endif %}
    </div>
</div>
{% endblock %}
```

---

### 2. `admin/verify_seller.html`

```html
{% extends "admin/basee.html" %}
{% block title %}Vérifier {{ shop.name }}{% endblock %}

{% block content %}
<div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
    <!-- Informations boutique -->
    <div class="card-surface rounded-xl p-6">
        <h3 class="text-xl font-semibold mb-4">Informations</h3>
        <dl class="space-y-3">
            <div>
                <dt class="text-sm font-medium text-gray-500">Boutique</dt>
                <dd class="text-lg font-semibold">{{ shop.name }}</dd>
            </div>
            <div>
                <dt class="text-sm font-medium text-gray-500">Email</dt>
                <dd>{{ shop.owner_email }}</dd>
            </div>
            <div>
                <dt class="text-sm font-medium text-gray-500">Niche</dt>
                <dd>{{ shop.category_niche|title }}</dd>
            </div>
            <div>
                <dt class="text-sm font-medium text-gray-500">Description</dt>
                <dd class="text-sm">{{ shop.description }}</dd>
            </div>
        </dl>
    </div>

    <!-- Documents -->
    <div class="card-surface rounded-xl p-6">
        <h3 class="text-xl font-semibold mb-4">Documents</h3>
        
        <div class="space-y-4">
            <!-- Pièce d'identité -->
            <div class="border rounded-lg p-4">
                <p class="font-semibold mb-2">
                    <i class="fas fa-id-card text-purple-600 mr-2"></i>
                    Pièce d'identité
                </p>
                {% if shop.id_document_path %}
                <a href="{{ shop.id_document_path }}" target="_blank"
                   class="text-purple-600 hover:underline text-sm">
                    <i class="fas fa-external-link-alt mr-1"></i>
                    Voir le document
                </a>
                {% else %}
                <p class="text-red-600 text-sm">Document non fourni</p>
                {% endif %}
            </div>

            <!-- Justificatif d'adresse -->
            <div class="border rounded-lg p-4">
                <p class="font-semibold mb-2">
                    <i class="fas fa-file-alt text-purple-600 mr-2"></i>
                    Justificatif d'adresse
                </p>
                {% if shop.address_document_path %}
                <a href="{{ shop.address_document_path }}" target="_blank"
                   class="text-purple-600 hover:underline text-sm">
                    <i class="fas fa-external-link-alt mr-1"></i>
                    Voir le document
                </a>
                {% else %}
                <p class="text-red-600 text-sm">Document non fourni</p>
                {% endif %}
            </div>
        </div>
    </div>

    <!-- Formulaire de validation -->
    <div class="card-surface rounded-xl p-6 lg:col-span-2">
        <h3 class="text-xl font-semibold mb-4">Validation</h3>
        
        <form method="POST" class="space-y-4">
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">
                    Notes de validation (optionnel)
                </label>
                <textarea name="verification_notes" rows="3"
                          class="w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-purple-500"
                          placeholder="Ajoutez des notes sur cette validation..."></textarea>
            </div>

            <div class="flex gap-3">
                <button type="submit" name="action" value="approve"
                        class="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 font-semibold">
                    <i class="fas fa-check-circle mr-2"></i>
                    Approuver
                </button>

                <button type="submit" name="action" value="reject"
                        class="px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 font-semibold">
                    <i class="fas fa-times-circle mr-2"></i>
                    Rejeter
                </button>

                <a href="{{ url_for('admin_sellers_verification') }}"
                   class="px-6 py-3 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400 font-semibold">
                    Annuler
                </a>
            </div>
        </form>
    </div>
</div>
{% endblock %}
```

---

## 📊 Workflow de Validation

```
1. Vendeur s'inscrit
   ↓
2. Upload pièce d'identité + justificatif
   ↓
3. Boutique créée avec status "pending"
   ↓
4. Admin reçoit notification
   ↓
5. Admin vérifie les documents
   ↓
6a. Approuvé → status "verified", boutique activée
6b. Rejeté → status "rejected", boutique suspendue
   ↓
7. Vendeur reçoit notification
```

---

## ✅ Checklist d'Implémentation

- [ ] Mettre à jour `backend/models.py` avec les champs de documents
- [ ] Ajouter les fonctions d'upload dans `backend/apps.py`
- [ ] Créer la route `become_seller` avec gestion des fichiers
- [ ] Créer les routes admin de validation
- [ ] Créer les templates admin
- [ ] Tester le flux complet
- [ ] Ajouter les notifications email

---

**Date :** 13 Mars 2026  
**Statut :** 📝 Prêt à implémenter

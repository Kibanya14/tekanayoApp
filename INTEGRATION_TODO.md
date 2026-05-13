# 🔧 INTÉGRATION PHASE 2 - ÉTAPES RESTANTES

**Status**: Phase 2 modules créés ✅, prêt pour intégration dans app.py

---

## 📝 ÉTAPES À FAIRE

### 1. **Intégrer le Logger** (30 min)

```python
# Dans app.py - au début du fichier

from backend.logger import StructuredLogger, setup_sentry, log_app_startup

# Initialiser le logger
logger = StructuredLogger()

# Setup Sentry si configuré
setup_sentry(app)

# Log au démarrage
log_app_startup("TekanayoApp", "1.0.0")

# Add before/after request logging
@app.before_request
def before_request():
    g.start_time = time.time()
    logger.info(f"Request: {request.method} {request.path}")

@app.after_request
def after_request(response):
    if hasattr(g, 'start_time'):
        elapsed = (time.time() - g.start_time) * 1000
        logger.info(
            f"Response: {response.status_code}",
            elapsed_ms=f"{elapsed:.2f}",
            path=request.path
        )
    return response
```

### 2. **Intégrer le Stock Manager** (45 min)

```python
# Dans app.py - ajouter les imports
from backend.stock_manager import StockManager, create_stock_history_model

# Dans la fonction de création du modèle de database
# Ajouter: StockHistory = create_stock_history_model(db)

# IMPORTANT: Créer une migration
# flask db migrate -m "Add StockHistory model"
# flask db upgrade

# Exemple d'utilisation dans une route de vente:
@app.route('/seller/products/<product_id>/sell', methods=['POST'])
def sell_product(product_id):
    quantity = request.form.get('quantity', 1)
    product = SellerProduct.query.get(product_id)
    
    if product.quantity < quantity:
        return {"error": "Stock insuffisant"}, 400
    
    # Mettre à jour le stock
    success, msg = StockManager.bulk_update_stock(
        product_id=product_id,
        new_quantity=product.quantity - quantity,
        reason="sale",
        user_id=current_user.id
    )
    
    if success:
        logger.info(f"Product sold: {product_id}, qty: {quantity}")
        return {"success": True, "message": msg}
    else:
        return {"error": msg}, 400
```

### 3. **Intégrer l'Antivirus** (30 min)

```python
# Dans app.py - ajouter import
from backend.antivirus import AntivirusScanner, validate_upload_safe

# Dans la route d'upload de documents (portal.py ou apps.py):
@app.route('/upload/document', methods=['POST'])
def upload_document():
    file = request.files.get('document')
    if not file:
        return {"error": "No file"}, 400
    
    # Sauvegarder temporairement
    temp_path = f"/tmp/{file.filename}"
    file.save(temp_path)
    
    try:
        # Scanner le fichier
        is_safe, message = validate_upload_safe(temp_path, 'documents')
        
        if not is_safe:
            logger.warning(f"Unsafe file detected: {file.filename}")
            os.remove(temp_path)
            return {"error": message}, 400
        
        # Si sûr, procéder à l'upload vers Supabase
        result = storage_client.upload_file(
            file=file,
            category=FileCategory.SELLER_ID_DOC,
            optimize_image=False,
            seller_id=current_user.seller_id
        )
        
        logger.info(f"Document uploaded: {file.filename}")
        return {"success": True, "path": result["path"]}
        
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
```

### 4. **Document Versioning** (45 min)

```python
# Créer backend/document_versions.py

from datetime import datetime

class DocumentVersioning:
    """Gestion du versioning des documents"""
    
    @staticmethod
    def create_version(document_path, version_number, user_id, change_description):
        """Créer une nouvelle version d'un document"""
        version_entry = DocumentVersion(
            original_path=document_path,
            version_number=version_number,
            versioned_path=f"{document_path}__v{version_number}",
            created_by=user_id,
            created_at=datetime.utcnow(),
            change_description=change_description
        )
        db.session.add(version_entry)
        db.session.commit()
        return version_entry
    
    @staticmethod
    def get_document_history(document_id):
        """Récupérer l'historique d'un document"""
        return DocumentVersion.query \
            .filter_by(original_path=document_id) \
            .order_by(DocumentVersion.created_at.desc()) \
            .all()
```

### 5. **Ajouter Database Migrations** (20 min)

```bash
# Créer une migration pour les nouveaux modèles
flask db migrate -m "Add Phase 2 models: StockHistory, DocumentVersion"

# Vérifier la migration
cat migrations/versions/xxxx_add_phase_2_models.py

# Appliquer la migration
flask db upgrade
```

### 6. **Tester en Local** (30 min)

```bash
# Installer les nouveaux packages
pip install -r requirements.txt

# Lancer l'app
python run.py

# Tests manuels:
# 1. Upload un document (test antivirus)
# 2. Vendre un produit (test stock history)
# 3. Vérifier les logs (tail -f app.log)
# 4. Tester error handling (break something)
```

---

## 📋 CHECKLIST INTÉGRATION

### Logging
- [ ] Importer StructuredLogger dans app.py
- [ ] Initialiser logger au démarrage
- [ ] Add before_request/after_request handlers
- [ ] Setup Sentry si SENTRY_DSN configuré
- [ ] Test des logs en console

### Stock Manager
- [ ] Créer migration pour StockHistory
- [ ] Appliquer la migration (flask db upgrade)
- [ ] Ajouter des exemples d'utilisation dans routes
- [ ] Test: Créer un changement de stock
- [ ] Test: Vérifier l'historique
- [ ] Test: Alerte stock faible générée

### Antivirus
- [ ] Importer AntivirusScanner dans app.py
- [ ] Ajouter au route d'upload
- [ ] Test: Upload fichier sûr ✅
- [ ] Test: Upload fichier dangereux (ZIP) ✅ → Quarantine
- [ ] Test: Vérifier log de détection

### Database
- [ ] Créer migrations pour nouveaux modèles
- [ ] Appliquer migrations en local
- [ ] Tester requêtes aux nouvelles tables
- [ ] Vérifier intégrité des données

### Testing
- [ ] Tests unitaires pour chaque module
- [ ] Tests d'intégration avec app
- [ ] Tests de sécurité (antivirus, etc.)
- [ ] Load test (simulated users)
- [ ] Error handling test

---

## 🔗 POINTS D'INTÉGRATION CLÉS

### app.py - Top level
```python
# Ligne 1-50
from backend.logger import StructuredLogger, setup_sentry
from backend.stock_manager import StockManager
from backend.antivirus import AntivirusScanner

logger = StructuredLogger()
setup_sentry(app)
```

### routes/seller.py ou apps.py - Upload routes
```python
# Avant upload
is_safe, msg = validate_upload_safe(file_path, category)
if not is_safe:
    AntivirusScanner.quarantine_file(file_path)
    return error
```

### models.py - Database models
```python
# Ajouter les nouvelles relations
class SellerProduct(db.Model):
    stock_history = db.relationship('StockHistory', backref='product')

class StockHistory(db.Model):
    # Model complet dans stock_manager.py
    pass
```

### Database - Migrations
```bash
flask db migrate -m "Add Phase 2: Stock history and document versioning"
flask db upgrade
```

---

## 🚀 APRÈS INTÉGRATION

### Déploiement Local
```bash
# 1. Vérifier syntaxe
python -m py_compile backend/antivirus.py backend/stock_manager.py backend/logger.py

# 2. Lancer app
FLASK_ENV=development python run.py

# 3. Tester features
curl -X POST http://localhost:5000/upload/document -F file=@test.pdf
```

### Déploiement Production
```bash
# 1. Push au git
git add backend/antivirus.py backend/stock_manager.py backend/logger.py
git commit -m "Phase 2: Add antivirus, stock manager, logging"
git push origin main

# 2. Render détecte le push
# 3. Auto-deploy et migrations appliquées
# 4. Monitoring en temps réel
```

---

## 📊 ESTIMATIONS DE TEMPS

| Tâche | Temps |
|-------|-------|
| Logger integration | 30 min |
| Stock Manager | 45 min |
| Antivirus | 30 min |
| Database migrations | 20 min |
| Local testing | 30 min |
| Documentation | 15 min |
| **TOTAL** | **~3 heures** |

---

## ✅ SUCCÈS CRITERIA

- ✅ App démarre sans erreur en local
- ✅ Logs structurés en JSON
- ✅ Stock history enregistré et récupéré
- ✅ Antivirus détecte fichiers dangereux
- ✅ Email alertes stock envoyées
- ✅ Database migrations appliquées
- ✅ Sentry capture les erreurs
- ✅ Deploy sur Render réussi

---

## 🆘 EN CAS DE PROBLÈME

### Import error: ModuleNotFoundError
```bash
# Solution:
pip install -r requirements.txt
# Vérifier que le module est dans __init__.py des packages
```

### Database migration fails
```bash
# Rollback et réessayer
flask db downgrade
flask db migrate -m "Fix: ..."
flask db upgrade
```

### Logger not working
```bash
# Vérifier SENTRY_DSN et LOG_LEVEL dans .env
echo $SENTRY_DSN
echo $LOG_LEVEL
# Si vide, ajouter à .env
```

### Antivirus not scanning
```bash
# Vérifier le chemin du fichier temporaire
# Vérifier les permissions /tmp
ls -la /tmp | grep tekanayo
```

---

## 📞 SUPPORT

- Logs: `tail -f app.log`
- Errors: Sentry dashboard
- Database: `flask shell` puis `db.session.query(...)`
- Issues: Ouvrir GitHub issue

---

**Après avoir complété ces étapes, TekanayoApp sera prêt pour production! 🚀**

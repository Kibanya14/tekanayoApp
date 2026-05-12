# 🔴 FAILLES & AMÉLIORATIONS - Alignement Complet

**Date**: 10 mai 2026  
**Scope**: Migration vers Supabase Storage + Optimisations nécessaires  
**Priorité**: CRITIQUE → MOYENNE

---

## 🚨 FAILLES DE SÉCURITÉ CRITIQUES

### **1. Accès public aux documents privés (CRITIQUE)**
- **Problème**: Route `/uploads/<path:filename>` **SANS contrôle d'accès**
- **Impact**: N'importe qui peut télécharger les pièces d'identité et adresses des vendeurs
- **Exemple d'exploitation**: 
  ```
  https://site.com/uploads/seller_documents/id/20260510143052_abc123.jpg
  → Accessible sans login!
  ```
- **Solution**: Migrer vers Supabase + RLS (Row Level Security)
- **Effort**: Moyen (2-3 jours)

### **2. Pas de validation de taille de fichier consistante (HAUTE)**
- **Problème**: Upload images limité à 5MB seulement dans la fonction helper
- **Impact**: 
  - Potentiellement contournable si upload directs ailleurs
  - Risque DoS (saturation disque)
- **Solution**: 
  - Valider à tous les points d'upload
  - Mettre limit Supabase côté serveur
- **Effort**: Bas (< 1 jour)

### **3. Pas de scanning antivirus (MOYENNE)**
- **Problème**: Documents uploadés (pièces d'identité) non scannés
- **Impact**: Malwares/virus potentiels dans les documents
- **Solution**: Intégrer ClamAV ou antivirus AWS
- **Effort**: Moyen (1-2 jours)

### **4. Pas de versioning des documents (MOYENNE)**
- **Problème**: Si un vendeur upload une nouvelle pièce d'identité, l'ancienne est remplacée (perdue)
- **Impact**: Pas d'audit trail, pas d'historique
- **Solution**: Keeper anciens fichiers avec timestamps
- **Effort**: Moyen (1-2 jours)

---

## 🔐 FAILLES D'ACCÈS & LOGS

### **5. Pas de logs d'accès aux documents (MOYENNE)**
- **Problème**: Impossible de savoir qui a accédé à quel document privé et quand
- **Impact**: Pas d'audit pour conformité RGPD
- **Solution**: Ajouter logging côté Supabase + table audit en BD
- **Effort**: Moyen (1-2 jours)

### **6. Pas de contrôle granulaire d'accès (HAUTE)**
- **Problème**: Actuellement c'est "admin avec manage_sellers" ou rien
- **Impact**: Un vendeur peut potentiellement voir les docs d'autres vendeurs
- **Solution**: RLS Supabase avec contrôle par seller_id
- **Effort**: Moyen (1-2 jours)

### **7. Pas de permissions sur les images vendeur (HAUTE)**
- **Problème**: SellerAdmin peut upload des images partout sans limite
- **Impact**: Spam potentiel, limites de stockage
- **Solution**: Rate limiting + quotas par seller
- **Effort**: Moyen (1 jour)

---

## 🖼️ FAILLES IMAGES PRODUITS

### **8. Pas d'optimisation/redimensionnement d'images (MOYENNE)**
- **Problème**: Images uploadées en taille originale = lent pour les clients
- **Impact**: 
  - Chargement lent des pages produit
  - Consommation data mobile élevée
- **Solution**: Redimensionner avec Pillow (Python) ou Sharp
- **Effort**: Moyen (1-2 jours)

### **9. Galerie d'images monofichier (MOYENNE)**
- **Problème**: Seulement 1 image par produit (pas de galerie)
- **Impact**: Mauvaise UX pour les clients
- **Solution**: 
  - Ajouter table `ProductImage` avec FK vers Product
  - Ou Supabase: folder `products/{product_id}/{image_1,2,3,etc}.jpg`
- **Effort**: Moyen (2 jours)

### **10. Pas de métadonnées images (BASSE)**
- **Problème**: Pas d'info sur dimensions, résolution, format optimisé
- **Impact**: Pas de contrôle qualité
- **Solution**: Ajouter champs width, height, file_size à ProductImage
- **Effort**: Bas (< 1 jour)

---

## 📦 FAILLES GESTION STOCK

### **11. Pas d'alertes stock bas (MOYENNE)**
- **Problème**: Aucune notification quand stock < seuil
- **Impact**: Vendeurs ne savent pas quand commander
- **Solution**: 
  - Ajouter field `stock_alert_threshold` à SellerProduct
  - Background task vérifie et envoie emails
- **Effort**: Moyen (2 jours)

### **12. Pas d'historique de stock (MOYENNE)**
- **Problème**: Impossible de voir les variations historiques de stock
- **Impact**: Pas de tendances, impossible de trouver les produits best-sellers
- **Solution**: 
  - Ajouter table `StockHistory` (product_id, quantity_before, quantity_after, reason, timestamp)
  - Ou intégrer avec Supabase Vector pour analytics
- **Effort**: Moyen (2-3 jours)

### **13. Pas de prélèvement de stock à la commande (CRITIQUE)**
- **Problème**: ⚠️ Stock n'est pas décrémenté quand une commande est passée!
- **Impact**: 
  - Overselling (vendre plus que dispo)
  - Deux clients achètent le dernier exemplaire
- **Solution**: Décrémenter stock à `order.status = "confirmed"`
- **Effort**: Bas (1 jour) mais URGENT

### **14. Pas de restock/achat automatique (BASSE)**
- **Problème**: Pas de système d'achat/reorder automatique
- **Impact**: Vendeurs gèrent manuellement
- **Solution**: Futur : intégrer API fournisseur
- **Effort**: Élevé (> 5 jours) - FUTURE PHASE

---

## 📊 FAILLES STATISTIQUES

### **15. Pas de statistiques d'accès fichiers (BASSE)**
- **Problème**: Pas de tracking sur qui voit quels produits/images
- **Impact**: Pas de données usage pour optimisation
- **Solution**: Ajouter pixel tracking côté frontend
- **Effort**: Moyen (2 jours) - FUTURE

### **16. Pas de rapports stock (MOYENNE)**
- **Problème**: Impossible de générer rapports "Top 10 best-sellers", "produits invendus", etc.
- **Impact**: Les vendeurs/admins ne voient pas les tendances
- **Solution**: 
  - Dashboard avec graphiques Plotly/Chart.js
  - Intégrer avec StockHistory (point 12)
- **Effort**: Moyen (2-3 jours)

### **17. Pas d'export de données (BASSE)**
- **Problème**: Impossible d'exporter factures, stock, rapports en CSV/Excel
- **Impact**: Vendeurs ne peuvent pas faire leur compta externement
- **Solution**: Ajouter route `/export` qui retourne CSV
- **Effort**: Bas (1 jour)

---

## 🌐 FAILLES D'ARCHITECTURE FICHIERS

### **18. Stockage sur disque serveur (CRITIQUE)**
- **Problème**: Fichiers en `/uploads/` sur serveur local
- **Impact**: 
  - Pas de backup auto
  - Pas de CDN (lent)
  - Limite de stockage = limite disque serveur
  - Perte lors migration serveur
- **Solution**: Supabase Storage (AWS S3 backend)
- **Effort**: Élevé (3-5 jours) - PRIORITY #1

### **19. Pas de compression fichiers (BASSE)**
- **Problème**: Fichiers stockés en taille originale
- **Impact**: Costs Supabase plus élevés
- **Solution**: Compresser avec gzip avant upload
- **Effort**: Bas (< 1 jour)

### **20. Pas de CDN/caching (MOYENNE)**
- **Problème**: Images servi directement du backend
- **Impact**: Lent pour utilisateurs géographiquement loin
- **Solution**: Supabase + Cloudflare/Bunny CDN
- **Effort**: Bas (< 1 jour) - Automatique avec Supabase

---

## ⚡ FAILLES PERFORMANCE

### **21. Pas de pagination images (MOYENNE)**
- **Problème**: Si un produit a 100 images, toutes se chargent
- **Impact**: UI lente
- **Solution**: Lazy loading + pagination
- **Effort**: Moyen (1-2 jours)

### **22. Pas de cache images (MOYENNE)**
- **Problème**: Chaque chargement page re-download les images
- **Impact**: Bande passante élevée
- **Solution**: HTTP cache headers + browser cache
- **Effort**: Bas (< 1 jour)

---

## 📋 TABLEAU RÉSUMÉ - PRIORITÉS

| # | Faille | Sévérité | Effort | Dépendance | Phase |
|---|---|---|---|---|---|
| 1 | Accès public docs privés | 🔴 CRITIQUE | Moyen | - | 1 |
| 13 | Stock pas décrémenté commande | 🔴 CRITIQUE | Bas | - | 1 |
| 18 | Stockage disque local | 🔴 CRITIQUE | Élevé | - | 1 |
| 2 | Pas validation taille fichier | 🟠 HAUTE | Bas | - | 1 |
| 6 | Pas contrôle accès granulaire | 🟠 HAUTE | Moyen | 1 | 1 |
| 7 | Pas permissions images | 🟠 HAUTE | Moyen | - | 1 |
| 3 | Pas antivirus | 🟡 MOYENNE | Moyen | - | 2 |
| 4 | Pas versioning docs | 🟡 MOYENNE | Moyen | 1 | 2 |
| 5 | Pas logs accès | 🟡 MOYENNE | Moyen | 1 | 2 |
| 8 | Pas optimisation images | 🟡 MOYENNE | Moyen | - | 2 |
| 9 | Galerie monofichier | 🟡 MOYENNE | Moyen | - | 2 |
| 11 | Pas alertes stock bas | 🟡 MOYENNE | Moyen | - | 2 |
| 12 | Pas historique stock | 🟡 MOYENNE | Moyen | - | 2 |
| 16 | Pas rapports stock | 🟡 MOYENNE | Moyen | 12 | 3 |
| 10 | Pas métadonnées images | 🟢 BASSE | Bas | - | 3 |
| 14 | Pas restock auto | 🟢 BASSE | Élevé | 12 | Future |
| 15 | Pas stats accès fichiers | 🟢 BASSE | Moyen | - | Future |
| 17 | Pas export données | 🟢 BASSE | Bas | - | 3 |
| 19 | Pas compression fichiers | 🟢 BASSE | Bas | 18 | 2 |
| 20 | Pas CDN/caching | 🟢 BASSE | Bas | 18 | Automatic |
| 21 | Pas pagination images | 🟢 BASSE | Moyen | - | 3 |
| 22 | Pas cache images | 🟢 BASSE | Bas | - | 3 |

---

## 🎯 PLAN EXÉCUTION - 3 PHASES

### **PHASE 1: SÉCURITÉ CRITIQUE (Semaine 1-2)**
*Résout les 3 failles CRITIQUES*

1. ✅ Configurer Supabase + buckets
2. ✅ Implémenter RLS (documentspriv privés)
3. ✅ Fixer les routes de download sécurisées
4. ✅ Ajouter validation taille fichier partout
5. ✅ **FIX URGENT**: Décrémenter stock à la confirmation commande
6. ✅ Ajouter permissions granulaires (seller ne voit que ses docs)

**Résultat**: Application sécurisée, pas d'overselling

---

### **PHASE 2: QUALITÉ (Semaine 3-4)**
*Améliore UX et fiabilité*

1. ✅ Implémenter antivirus documents
2. ✅ Versioning des documents (garder historique)
3. ✅ Logs d'accès fichiers
4. ✅ Optimisation/resize images produits
5. ✅ Multi-images par produit (galerie)
6. ✅ Alertes stock bas
7. ✅ Historique stock (StockHistory table)
8. ✅ Compression fichiers

**Résultat**: App plus rapide, vendeurs informés, audit trail complet

---

### **PHASE 3: ANALYTICS & EXPORT (Semaine 5-6)**
*Donne insights commerciaux*

1. ✅ Rapports stock (best-sellers, etc.)
2. ✅ Export en CSV/Excel
3. ✅ Pagination lazy-loading images
4. ✅ Caching images côté client
5. ✅ Métadonnées images (dimensions, size)

**Résultat**: Vendeurs ont outils de business intelligence

---

## 💾 APPRENTISSAGE PÉDAGOGIQUE

Pour chaque faille, vous allez apprendre :

| Faille | Concept SQL | Concept Backend | Concept Sécurité |
|---|---|---|---|
| #1 Accès public | `WHERE user_id = ?` | RLS policies | Authentication + Authorization |
| #13 Stock décrémenté | `UPDATE quantity SET quantity - 1` | Transactions | Race conditions |
| #18 Supabase | Clustering | S3 API, signed URLs | Cloud storage security |
| #3 Antivirus | Logs table | File scanning middleware | Malware detection |
| #4 Versioning | Version history table | Soft deletes | Audit trails |
| #5 Logs accès | Audit log table | Logging middleware | GDPR compliance |

---

## ✅ Êtes-vous prêt pour PHASE 1 ?

Répondez à ces 3 questions et on commence :

1. **Compte Supabase existant** ? (oui/non) + Link si oui
2. **Accès MSSQL local** ? (pour tester migrations)
3. **Infrastructure** : Où est hébergée l'app actuellement ? (local, Heroku, AWS, etc.)


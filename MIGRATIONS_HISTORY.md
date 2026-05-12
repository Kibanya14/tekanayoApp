# 📦 Historique des Migrations - TekanayoApp

## 🎯 État Actuel

**Migration actuelle :** `5f0b424c3b2a (head)`  
**Statut :** ✅ À jour avec le modèle de données  
**Dernière mise à jour :** 13 Mars 2026

---

## 📜 Liste des Migrations

### 1. `5f0b424c3b2a` - Add SaaS Subscription System ⭐ NOUVEAU
**Date :** 13 Mars 2026  
**Parent :** `36dbafdc9534`  
**Description :** Ajout du système complet d'abonnement SaaS pour les vendeurs

**Tables créées :**
- ✅ `seller_subscriptions` - Gestion des abonnements
- ✅ `seller_payments` - Historique des paiements
- ✅ `seller_payment_tasks` - Tâches pour l'admin

**Détails :**
```sql
-- Table: seller_subscriptions
- id (INTEGER, PRIMARY KEY)
- shop_id (INTEGER, UNIQUE, FK → seller_shops)
- status (VARCHAR(20)) -- trial, active, suspended, expired, cancelled
- trial_start_date (DATETIME)
- trial_end_date (DATETIME)
- subscription_start_date (DATETIME)
- subscription_end_date (DATETIME)
- last_payment_date (DATETIME)
- cancelled_date (DATETIME)
- payment_method (VARCHAR(50))
- monthly_price (FLOAT, default=5.0)
- total_paid (FLOAT, default=0.0)
- pending_payment (BOOLEAN, default=False)
- created_at (DATETIME)
- updated_at (DATETIME)

-- Table: seller_payments
- id (INTEGER, PRIMARY KEY)
- subscription_id (INTEGER, FK → seller_subscriptions)
- amount (FLOAT, NOT NULL)
- currency (VARCHAR(10), default='USD')
- payment_method (VARCHAR(50), NOT NULL)
- payment_type (VARCHAR(20), default='subscription')
- status (VARCHAR(20)) -- pending, completed, failed, refunded
- transaction_id (VARCHAR(255))
- is_offline (BOOLEAN, default=False)
- offline_confirmed_by (INTEGER, FK → platform_admins)
- offline_confirmed_at (DATETIME)
- payment_date (DATETIME)
- notes (TEXT)
- created_at (DATETIME)

-- Table: seller_payment_tasks
- id (INTEGER, PRIMARY KEY)
- shop_id (INTEGER, FK → seller_shops)
- subscription_id (INTEGER, FK → seller_subscriptions)
- task_type (VARCHAR(50), NOT NULL)
- status (VARCHAR(20)) -- pending, completed, cancelled
- title (VARCHAR(255), NOT NULL)
- description (TEXT)
- amount (FLOAT)
- payment_method (VARCHAR(50))
- assigned_to (INTEGER, FK → platform_admins)
- completed_by (INTEGER, FK → platform_admins)
- completed_at (DATETIME)
- created_at (DATETIME)
- updated_at (DATETIME)
```

**Commandes :**
```bash
# Créer la migration
flask db migrate -m "Add SaaS subscription system with SellerSubscription, SellerPayment, and SellerPaymentTask models"

# Appliquer la migration
flask db upgrade
```

---

### 2. `36dbafdc9534` - Limit Phone Number to 9 Digits
**Date :** 7 Mars 2026  
**Parent :** `add_phone_separation`  
**Description :** Limite le champ `phone_number` à exactement 9 caractères

**Modifications :**
- `platform_admins.phone_number` : VARCHAR(20) → VARCHAR(9)
- `seller_admins.phone_number` : VARCHAR(20) → VARCHAR(9)
- `seller_customers.phone_number` : VARCHAR(20) → VARCHAR(9)
- `seller_deliverers.phone_number` : VARCHAR(20) → VARCHAR(9)

---

### 3. `add_phone_separation` - Add Country Code and Phone Number Fields
**Date :** 7 Mars 2026  
**Parent :** `730c7142aef6`  
**Description :** Séparation du numéro de téléphone en code pays + numéro

**Champs ajoutés :**
- `country_code` VARCHAR(2) - Code ISO du pays
- `phone_number` VARCHAR(20) - Numéro de téléphone (9 chiffres)

**Tables concernées :**
- `platform_admins`
- `seller_admins`
- `seller_deliverers`
- `seller_customers`

---

### 4. `730c7142aef6` - Baseline Tekanayo Clean
**Date :** 6 Mars 2026  
**Parent :** `<base>`  
**Description :** Migration de base pour TekanayoApp

**Tables créées :**
- `platform_admins`
- `platform_activity_logs`
- `platform_access_requests`
- `platform_announcements`
- `platform_settings`
- `seller_shops`
- `seller_admins`
- `seller_products`
- `seller_deliverers`
- `seller_customers`
- `seller_orders`

---

## 🔄 Commandes de Migration Utiles

### Vérifier le statut actuel
```bash
cd /home/kibanya/Documents/TekanayoApp
source ecom/bin/activate
flask db current
```

### Voir l'historique complet
```bash
flask db history
```

### Appliquer toutes les migrations
```bash
flask db upgrade
```

### Revenir à une migration précédente
```bash
# Revenir d'une migration en arrière
flask db downgrade -1

# Revenir à une migration spécifique
flask db downgrade <revision_id>
```

### Créer une nouvelle migration
```bash
# Après avoir modifié models.py
flask db migrate -m "Description de vos changements"

# Appliquer la migration
flask db upgrade
```

### Vérifier les migrations en attente
```bash
flask db heads
```

---

## 📊 Schéma de la Base de Données

### Tables Principales

```
┌─────────────────────┐
│  platform_admins    │
├─────────────────────┤
│ - id                │
│ - first_name        │
│ - last_name         │
│ - email             │
│ - password_hash     │
│ - country_code      │
│ - phone_number      │
│ - role              │
│ - permissions       │
│ - is_active         │
└─────────────────────┘

┌─────────────────────┐
│  seller_shops       │
├─────────────────────┤
│ - id                │
│ - name              │
│ - slug              │
│ - owner_email       │
│ - category_niche    │
│ - subscription      │◄───────┐
│ - is_active         │        │
└─────────────────────┘        │
                               │
                               │ 1:1
                               │
                    ┌──────────▼──────────┐
                    │ seller_subscriptions│ (NOUVEAU - 13/03/2026)
                    ├─────────────────────┤
                    │ - id                │
                    │ - shop_id (UNIQUE)  │
                    │ - status            │
                    │ - trial_end_date    │
                    │ - monthly_price     │
                    │ - total_paid        │
                    └──────────┬──────────┘
                               │
                               │ 1:N
                               │
                    ┌──────────▼──────────┐
                    │   seller_payments   │ (NOUVEAU - 13/03/2026)
                    ├─────────────────────┤
                    │ - id                │
                    │ - subscription_id   │
                    │ - amount            │
                    │ - payment_method    │
                    │ - status            │
                    │ - is_offline        │
                    └─────────────────────┘
```

---

## ✅ Checklist de Vérification

### Après chaque migration

- [ ] La migration a été créée avec `flask db migrate`
- [ ] Le fichier de migration est dans `migrations/versions/`
- [ ] La migration a été appliquée avec `flask db upgrade`
- [ ] Le statut actuel est vérifié avec `flask db current`
- [ ] Les nouvelles tables/colonnes existent dans la BD
- [ ] Les données existantes ne sont pas affectées
- [ ] Les tests passent toujours

---

## 🎯 Bonnes Pratiques

### 1. Toujours créer une migration après avoir modifié `models.py`

```bash
# Modifier backend/models.py
# Ajouter/modifier des classes

# Créer la migration
flask db migrate -m "Description claire et concise"

# Vérifier le fichier généré
cat migrations/versions/<revision_id>_*.py

# Appliquer la migration
flask db upgrade
```

### 2. Messages de Migration Clairs

**Bon :**
```bash
flask db migrate -m "Add SaaS subscription system with SellerSubscription model"
```

**Mauvais :**
```bash
flask db migrate -m "update"
```

### 3. Version Control des Migrations

Les fichiers de migration doivent être commités dans Git :
```bash
git add migrations/versions/<revision_id>_*.py
git commit -m "Add migration for subscription system"
```

### 4. Testing avant Production

```bash
# Tester en local
flask db downgrade -1
flask db upgrade

# Vérifier que tout fonctionne
python -m pytest tests/
```

---

## 📝 Notes Importantes

### ⚠️ Ne Jamais Modifier les Migrations Existantes

Une fois qu'une migration est appliquée en production :
- ❌ Ne jamais modifier le fichier
- ❌ Ne jamais changer le `revision_id`
- ✅ Créer une nouvelle migration pour les corrections

### 🔄 Rollback en Cas de Problème

```bash
# Annuler la dernière migration
flask db downgrade -1

# Corriger le problème dans models.py
# Créer une nouvelle migration
flask db migrate -m "Fix subscription model issue"
flask db upgrade
```

### 📊 Statistiques

- **Total des migrations :** 4
- **Dernière migration :** 13 Mars 2026
- **Tables créées :** 13+
- **Colonnes ajoutées :** 50+

---

**Date de mise à jour :** 13 Mars 2026  
**Statut :** ✅ Toutes les migrations appliquées  
**Prochaine action :** Tester le système d'abonnement

# 📦 État des Migrations - TekanayoApp

## ✅ Status Actuel

**Migration actuelle :** `36dbafdc9534 (head)`  
**Status :** ✅ À jour avec le modèle de données

---

## 📜 Historique des Migrations

### 1. `36dbafdc9534` - Limit phone_number to exactly 9 digits
**Date :** 7 Mars 2026  
**Description :** Limite le champ `phone_number` à exactement 9 caractères

**Tables concernées :**
- ✅ `platform_admins` - `phone_number` VARCHAR(20) → VARCHAR(9)
- ✅ `seller_admins` - `phone_number` VARCHAR(20) → VARCHAR(9)
- ✅ `seller_customers` - `phone_number` VARCHAR(20) → VARCHAR(9)
- ✅ `seller_deliverers` - `phone_number` VARCHAR(20) → VARCHAR(9)

---

### 2. `add_phone_separation` - Add country_code and phone_number fields
**Date :** 7 Mars 2026  
**Description :** Ajoute les champs `country_code` et `phone_number` pour séparer l'indicatif du numéro

**Champs ajoutés :**
- `country_code` VARCHAR(2) - Code ISO du pays (ex: 'CD', 'CM')
- `phone_number` VARCHAR(20) - Numéro de téléphone (maintenant 9 chiffres)

**Tables concernées :**
- ✅ `platform_admins`
- ✅ `seller_admins`
- ✅ `seller_deliverers`
- ✅ `seller_customers`

---

### 3. `730c7142aef6` - baseline tekanayo clean
**Date :** 6 Mars 2026  
**Description :** Migration de base pour TekanayoApp

---

## 🗄️ Schéma Actuel de la Base de Données

### Table `platform_admins`
```sql
id              INTEGER PRIMARY KEY
first_name      VARCHAR(80) NOT NULL
last_name       VARCHAR(80) NOT NULL
email           VARCHAR(120) UNIQUE NOT NULL
password_hash   VARCHAR(255) NOT NULL
phone           VARCHAR(30) NULL          -- Deprecated (legacy)
country_code    VARCHAR(2) NULL           -- Nouveau: 'CD', 'CM', etc.
phone_number    VARCHAR(9) NULL           -- Nouveau: exactement 9 chiffres
address         TEXT NULL
profile_picture VARCHAR(255) NULL
role            VARCHAR(30) NULL
permissions     TEXT NULL
is_active       BOOLEAN NULL
created_at      DATETIME NULL
```

### Table `seller_admins`
```sql
id              INTEGER PRIMARY KEY
shop_id         INTEGER NOT NULL (FK)
first_name      VARCHAR(80) NOT NULL
last_name       VARCHAR(80) NOT NULL
email           VARCHAR(120) UNIQUE NOT NULL
password_hash   VARCHAR(255) NOT NULL
profile_picture VARCHAR(255) NULL
country_code    VARCHAR(2) NULL           -- Nouveau: 'CD', 'CM', etc.
phone_number    VARCHAR(9) NULL           -- Nouveau: exactement 9 chiffres
permissions     TEXT NULL
is_owner        BOOLEAN NULL
is_active       BOOLEAN NULL
created_at      DATETIME NULL
```

### Table `seller_deliverers`
```sql
id              INTEGER PRIMARY KEY
shop_id         INTEGER NOT NULL (FK)
first_name      VARCHAR(80) NOT NULL
last_name       VARCHAR(80) NOT NULL
email           VARCHAR(120) UNIQUE NOT NULL
password_hash   VARCHAR(255) NOT NULL
phone           VARCHAR(30) NULL          -- Deprecated (legacy)
country_code    VARCHAR(2) NULL           -- Nouveau: 'CD', 'CM', etc.
phone_number    VARCHAR(9) NULL           -- Nouveau: exactement 9 chiffres
address         TEXT NULL
profile_picture VARCHAR(255) NULL
status          VARCHAR(20) NULL
is_active       BOOLEAN NULL
created_at      DATETIME NULL
```

### Table `seller_customers`
```sql
id              INTEGER PRIMARY KEY
shop_id         INTEGER NOT NULL (FK)
first_name      VARCHAR(80) NOT NULL
last_name       VARCHAR(80) NOT NULL
email           VARCHAR(120) NOT NULL
password_hash   VARCHAR(255) NOT NULL
profile_picture VARCHAR(255) NULL
phone           VARCHAR(30) NULL          -- Deprecated (legacy)
country_code    VARCHAR(2) NULL           -- Nouveau: 'CD', 'CM', etc.
phone_number    VARCHAR(9) NULL           -- Nouveau: exactement 9 chiffres
address         TEXT NULL
created_at      DATETIME NULL
```

---

## 🎯 Format des Données

### Exemple de Stockage
```
Pays: Congo (RDC)
Indicatif: +243
Numéro: 813091409

Stocké en BD:
├─ country_code: 'CD'
└─ phone_number: '813091409'  (exactement 9 caractères)

Numéro complet (calculé): +243813091409
```

### Validation
- ✅ `country_code` : 2 caractères (code ISO)
- ✅ `phone_number` : exactement 9 chiffres
- ✅ Validation backend : `len(phone_number) == 9 and phone_number.isdigit()`

---

## 🔄 Commandes de Migration Utiles

### Vérifier le statut
```bash
cd /home/kibanya/Documents/TekanayoApp
source ecom/bin/activate
flask db current
```

### Voir l'historique
```bash
flask db history
```

### Appliquer les migrations
```bash
flask db upgrade
```

### Revenir en arrière (déconseillé en production)
```bash
flask db downgrade -1
```

### Créer une nouvelle migration
```bash
flask db migrate -m "Description de la modification"
```

---

## ✅ Vérification Effectuée

**Date :** 12 Mars 2026

### Tables Vérifiées
- ✅ `platform_admins` - `country_code` VARCHAR(2), `phone_number` VARCHAR(9)
- ✅ `seller_admins` - `country_code` VARCHAR(2), `phone_number` VARCHAR(9)
- ✅ `seller_deliverers` - `country_code` VARCHAR(2), `phone_number` VARCHAR(9)
- ✅ `seller_customers` - `country_code` VARCHAR(2), `phone_number` VARCHAR(9)

### Status
- ✅ Toutes les migrations sont appliquées
- ✅ La base de données est synchronisée avec les modèles
- ✅ Aucune migration supplémentaire n'est nécessaire
- ✅ Le champ `phone_number` est limité à 9 caractères

---

## 📝 Notes Importantes

1. **Champ `phone` (legacy)** : Conservé pour compatibilité arrière mais déprécié
2. **Nouveaux champs** : Utiliser `country_code` + `phone_number` pour toutes les nouvelles fonctionnalités
3. **Validation** : Toujours valider que `phone_number` contient exactement 9 chiffres
4. **Format international** : Pour afficher le numéro complet, concaténer : `+{dial_code}{phone_number}`

---

## 🎉 Conclusion

**Les migrations sont déjà à jour et prêtes pour la production !** ✅

Aucune action supplémentaire n'est requise au niveau de la base de données.

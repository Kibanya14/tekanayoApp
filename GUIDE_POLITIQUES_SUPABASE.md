# GUIDE SIMPLE : Créer les politiques dans Supabase Storage

## 📍 Étape 1 : Aller dans Storage → Policies

```
Supabase Dashboard
    ↓
Menu gauche → "Storage"
    ↓
Cliquez sur votre bucket "uploads"
    ↓
En haut : Onglet "Policies"
    ↓
Vous voyez : "No policies yet"
```

## 📋 Étape 2 : Créer 5 politiques simples

### **Politique 1 : Fichiers publics**
```
+ New policy
    ↓
Policy name: Public files
    ↓
Allowed operation: SELECT (lecture)
    ↓
Policy definition:
bucket_id = 'uploads' AND name LIKE 'public/%'
    ↓
Save policy
```

### **Politique 2 : Fichiers semi-privés**
```
+ New policy
    ↓
Policy name: Semi-private files
    ↓
Allowed operation: SELECT (lecture)
    ↓
Policy definition:
bucket_id = 'uploads' AND name LIKE 'semi_private/%' AND auth.role() = 'authenticated'
    ↓
Save policy
```

### **Politique 3 : Documents privés vendeurs**
```
+ New policy
    ↓
Policy name: Private seller documents
    ↓
Allowed operation: SELECT (lecture)
    ↓
Policy definition:
bucket_id = 'uploads' AND name LIKE 'private/%' AND auth.jwt() ->> 'role' = 'service_role'
    ↓
Save policy
```

### **Politique 4 : Permettre l'upload**
```
+ New policy
    ↓
Policy name: Allow uploads
    ↓
Allowed operation: INSERT (écriture)
    ↓
Policy definition:
bucket_id = 'uploads' AND auth.role() = 'authenticated'
    ↓
Save policy
```

### **Politique 5 : Permettre la suppression**
```
+ New policy
    ↓
Policy name: Allow deletions
    ↓
Allowed operation: DELETE (suppression)
    ↓
Policy definition:
bucket_id = 'uploads' AND auth.role() = 'authenticated'
    ↓
Save policy
```

## ✅ Résultat

Après ces 5 politiques, votre bucket "uploads" sera :
- **PRIVÉ** (pas accessible publiquement)
- **Sécurisé** (seules les bonnes personnes peuvent accéder)
- **Organisé** (dossiers créés automatiquement par le code Python)

## 🎯 Test rapide

Une fois les politiques créées :
1. Essayez d'uploader un fichier test via l'interface Supabase
2. Vérifiez qu'il se range dans le bon dossier
3. Testez l'accès avec différents rôles

**Confirmez quand c'est fait !** 🚀
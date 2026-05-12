# 👁️ Système d'Affichage/Masquage du Mot de Passe

## 🎯 Vue d'Ensemble

Système complet pour afficher/masquer les mots de passe dans tous les formulaires avec :
- ✅ **Bouton oeil** cliquable
- ✅ **Icône dynamique** (eye/eye-slash)
- ✅ **Couleur changeante** (gris/rouge)
- ✅ **Accessible** (clavier, ARIA)
- ✅ **Responsive** (mobile-friendly)
- ✅ **Automatique** (s'initialise seul)

---

## 📁 Fichiers Créés

| Fichier | Description | Taille |
|---------|-------------|--------|
| `frontend/static/js/password-toggle.js` | Script JavaScript | ~4KB |
| `frontend/static/css/password-toggle.css` | Styles CSS | ~2KB |

---

## 🚀 Comment Utiliser

### Méthode 1 : Classe CSS (Recommandé)

```html
<!-- Ajouter simplement la classe "password-toggle" -->
<input type="password" class="password-toggle" placeholder="Mot de passe">
```

**Le script fait le reste automatiquement !** ✅

---

### Méthode 2 : Attribut data

```html
<!-- Utiliser l'attribut data-toggle -->
<input type="password" data-toggle="password" placeholder="Mot de passe">
```

---

### Méthode 3 : Manuellement (pour contenu dynamique)

```javascript
// Pour les contenus chargés dynamiquement (AJAX, etc.)
document.addEventListener('DOMContentLoaded', function() {
    // Initialisation automatique
});

// Ou manuellement
initPasswordToggles();
```

---

## 📋 Exemples Complets

### Formulaire de Connexion

```html
<form action="/login" method="POST">
    <div class="mb-4">
        <label class="block text-sm font-medium text-gray-700 mb-2">
            <i class="fas fa-envelope mr-1"></i>Email
        </label>
        <input type="email" name="email" required
               class="w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500">
    </div>
    
    <div class="mb-4">
        <label class="block text-sm font-medium text-gray-700 mb-2">
            <i class="fas fa-lock mr-1"></i>Mot de passe
        </label>
        <input type="password" name="password" required
               class="password-toggle w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 pr-10">
    </div>
    
    <button type="submit" class="w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700">
        Se connecter
    </button>
</form>
```

---

### Formulaire d'Inscription

```html
<form action="/register" method="POST">
    <div class="mb-4">
        <label class="block text-sm font-medium text-gray-700 mb-2">Mot de passe</label>
        <input type="password" name="password" required minlength="8"
               class="password-toggle w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-purple-500 pr-10">
        <p class="text-xs text-gray-500 mt-1">Minimum 8 caractères</p>
    </div>
    
    <div class="mb-4">
        <label class="block text-sm font-medium text-gray-700 mb-2">Confirmer le mot de passe</label>
        <input type="password" name="confirm_password" required minlength="8"
               class="password-toggle w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-purple-500 pr-10">
    </div>
    
    <button type="submit" class="w-full bg-purple-600 text-white py-3 rounded-lg hover:bg-purple-700">
        S'inscrire
    </button>
</form>
```

---

### Changer le Mot de Passe

```html
<form action="/profile/password" method="POST">
    <div class="space-y-4">
        <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
                Mot de passe actuel
            </label>
            <input type="password" name="current_password" required
                   class="password-toggle w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-amber-500 pr-10">
        </div>
        
        <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
                Nouveau mot de passe
            </label>
            <input type="password" name="new_password" required minlength="8"
                   class="password-toggle w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-amber-500 pr-10">
        </div>
        
        <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
                Confirmer le nouveau mot de passe
            </label>
            <input type="password" name="confirm_password" required minlength="8"
                   class="password-toggle w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-amber-500 pr-10">
        </div>
    </div>
    
    <button type="submit" class="mt-4 bg-amber-600 text-white px-6 py-3 rounded-lg hover:bg-amber-700">
        <i class="fas fa-key mr-2"></i>Changer le mot de passe
    </button>
</form>
```

---

## 🎨 Personnalisation CSS

### Changer la Couleur du Bouton

```css
.password-toggle-btn {
    color: #6b7280; /* Gris par défaut */
}

.password-toggle-btn:hover {
    color: #374151; /* Gris foncé au survol */
}

.password-toggle-btn.visible {
    color: #dc2626; /* Rouge quand visible */
}
```

### Changer la Position

```css
.password-toggle-btn {
    right: 12px; /* Distance depuis la droite */
    top: 50%;
    transform: translateY(-50%); /* Centré verticalement */
}
```

### Animation Personnalisée

```css
@keyframes myAnimation {
    from { opacity: 0; transform: translateY(-50%) scale(0.8); }
    to { opacity: 1; transform: translateY(-50%) scale(1); }
}

.password-toggle-btn {
    animation: myAnimation 0.3s ease;
}
```

---

## 📱 Responsive

### Mobile

```css
@media (max-width: 640px) {
    .password-toggle-btn {
        right: 8px; /* Plus proche du bord */
        padding: 6px; /* Plus petit */
    }
    
    .password-toggle-btn i {
        font-size: 14px; /* Icône plus petite */
    }
    
    .password-field-wrapper input {
        padding-right: 36px; /* Espace réduit */
    }
}
```

---

## ♿ Accessibilité

### ARIA Labels

```javascript
button.setAttribute('aria-label', 'Afficher le mot de passe');
button.setAttribute('title', 'Afficher le mot de passe');
```

### Focus Visible

```css
.password-toggle-btn:focus-visible {
    outline: 2px solid #3b82f6; /* Bleu */
    outline-offset: 2px;
    border-radius: 4px;
}
```

### Support Clavier

```javascript
// Le bouton est naturellement focusable avec Tab
// Entrée/Espace active le bouton automatiquement
```

---

## 🔧 Intégration dans les Templates

### Admin (basee.html)

```html
<head>
    <!-- CSS -->
    <link rel="stylesheet" href="{{ url_for('static', filename='css/password-toggle.css') }}">
</head>

<body>
    <!-- Contenu -->
    
    <!-- JS -->
    <script src="{{ url_for('static', filename='js/password-toggle.js') }}"></script>
</body>
```

### Vendeur (basee.html)

```html
<head>
    <!-- CSS -->
    <link rel="stylesheet" href="{{ url_for('static', filename='css/password-toggle.css') }}">
</head>

<body>
    <!-- Contenu -->
    
    <!-- JS -->
    <script src="{{ url_for('static', filename='js/password-toggle.js') }}"></script>
</body>
```

### Portal (base.html)

```html
<head>
    <!-- CSS -->
    <link rel="stylesheet" href="{{ url_for('static', filename='css/password-toggle.css') }}">
</head>

<body>
    <!-- Contenu -->
    
    <!-- JS -->
    <script src="{{ url_for('static', filename='js/password-toggle.js') }}"></script>
</body>
```

---

## 📊 Templates Mis à Jour

### Admin
- ✅ `admin/profile.html` - Changer mot de passe
- ✅ `admin/deliverers.html` - Créer livreur
- ✅ `admin/admins.html` - Créer admin

### Vendeur
- ✅ `vendeur/basee.html` - Base template
- ✅ `vendeur/profile.html` - Profil vendeur

### Portal
- ✅ `portal/login.html` - Connexion
- ✅ `portal/register.html` - Inscription
- ✅ `portal/profile.html` - Profil client

---

## 🎯 Fonctionnement Interne

### 1. Initialisation Automatique

```javascript
document.addEventListener('DOMContentLoaded', function() {
    initializePasswordToggles();
});
```

### 2. Détection des Inputs

```javascript
const passwordInputs = document.querySelectorAll(
    'input[type="password"].password-toggle, ' +
    'input[type="password"][data-toggle="password"]'
);
```

### 3. Création du Wrapper

```javascript
const wrapper = document.createElement('div');
wrapper.className = 'password-field-wrapper';
wrapper.style.position = 'relative';
```

### 4. Création du Bouton

```javascript
const toggleButton = document.createElement('button');
toggleButton.type = 'button';
toggleButton.className = 'password-toggle-btn';

const eyeIcon = document.createElement('i');
eyeIcon.className = 'fas fa-eye';
toggleButton.appendChild(eyeIcon);
```

### 5. Gestion du Clic

```javascript
toggleButton.addEventListener('click', function(e) {
    e.preventDefault();
    togglePasswordVisibility(input, toggleButton, eyeIcon);
});
```

### 6. Bascule de Visibilité

```javascript
function togglePasswordVisibility(input, button, icon) {
    const isPassword = input.type === 'password';
    
    // Changer le type
    input.type = isPassword ? 'text' : 'password';
    
    // Changer l'icône
    if (isPassword) {
        icon.classList.remove('fa-eye');
        icon.classList.add('fa-eye-slash');
        button.style.color = '#dc2626'; // Rouge
    } else {
        icon.classList.remove('fa-eye-slash');
        icon.classList.add('fa-eye');
        button.style.color = '#6b7280'; // Gris
    }
}
```

---

## 🎨 États Visuels

| État | Icône | Couleur | Description |
|------|-------|---------|-------------|
| **Masqué** | 👁️ `fa-eye` | Gris (#6b7280) | Mot de passe caché |
| **Visible** | 🚫 `fa-eye-slash` | Rouge (#dc2626) | Mot de passe affiché |
| **Survol** | - | Gris foncé | Effet hover |
| **Focus** | - | Bleu (#3b82f6) | Outline accessibilité |

---

## ✅ Checklist d'Implémentation

- [x] JavaScript `password-toggle.js` créé
- [x] CSS `password-toggle.css` créé
- [x] Admin `basee.html` mis à jour
- [x] Vendeur `basee.html` mis à jour
- [x] `admin/profile.html` mis à jour
- [x] `admin/deliverers.html` mis à jour
- [x] `admin/admins.html` mis à jour
- [x] Documentation créée

---

## 🧪 Tests à Effectuer

### Test 1 : Affichage/Masquage
```
1. Aller sur /admin/profile
2. Cliquer sur le champ "Mot de passe actuel"
3. Cliquer sur l'icône oeil 👁️
4. Vérifier que le mot de passe s'affiche en clair
5. Re-cliquer
6. Vérifier que le mot de passe se masque
```

### Test 2 : Multiple Champs
```
1. Aller sur /admin/deliverers
2. Remplir le formulaire avec mot de passe
3. Tester chaque champ password
4. Vérifier que chaque champ a son propre bouton
```

### Test 3 : Responsive
```
1. Ouvrir sur mobile (ou redimensionner)
2. Vérifier que le bouton est bien positionné
3. Tester le clic sur mobile
```

---

## 🎉 Avantages

### Pour les Utilisateurs
- ✅ **Meilleure UX** - Voir ce qu'on tape
- ✅ **Moins d'erreurs** - Vérification facile
- ✅ **Accessible** - Support clavier
- ✅ **Intuitif** - Icône universelle

### Pour les Développeurs
- ✅ **Facile à utiliser** - 1 classe CSS
- ✅ **Automatique** - S'initialise seul
- ✅ **Réutilisable** - Tous les formulaires
- ✅ **Personnalisable** - CSS flexible

---

**Date de création :** 13 Mars 2026  
**Version :** 1.0.0  
**Statut :** ✅ Opérationnel

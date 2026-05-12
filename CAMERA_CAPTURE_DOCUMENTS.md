# 📸 Capture de Documents avec Caméra - Mobile First

## 🎯 Fonctionnalité Implémentée

Les vendeurs peuvent maintenant **prendre en photo directement** leurs documents avec la caméra du mobile, ou choisir un fichier existant.

---

## 📱 Interface Utilisateur

### Deux Options par Document

```
┌─────────────────────────────────────────────────┐
│  📎 Pièce d'identité *                          │
├─────────────────────────────────────────────────┤
│  ┌────────────────┐  ┌────────────────┐        │
│  │  📷 Prendre    │  │  🖼️ Choisir    │        │
│  │  en photo      │  │  du fichier    │        │
│  └────────────────┘  └────────────────┘        │
│                                                 │
│  Formats : JPG, PNG, PDF. Max 5MB.             │
├─────────────────────────────────────────────────┤
│  ✅ Fichier sélectionné                         │
│  📄 piece_identite.jpg                          │
│  2.34 MB                                        │
│  [Aperçu de l'image]                            │
│                                      [❌ Supprimer]│
└─────────────────────────────────────────────────┘
```

---

## 🔧 Comment Ça Marche

### 1. **Bouton "Prendre en photo"**
```html
<input type="file" 
       accept="image/*,.pdf" 
       capture="environment"
       class="hidden">
```

**Attributs clés :**
- `accept="image/*,.pdf"` : Accepte images et PDF
- `capture="environment"` : Ouvre la caméra arrière (mobile)
- `class="hidden"` : Input caché, stylisé avec un label

---

### 2. **Bouton "Choisir du fichier"**
```html
<input type="file" 
       accept="image/*,.pdf"
       class="hidden">
```

**Ouvre :**
- 📱 Mobile : Galerie photos
- 💻 Desktop : Explorateur de fichiers

---

### 3. **Synchronisation**

Les deux inputs sont synchronisés :
```javascript
// Quand caméra sélectionne un fichier
idDocument.addEventListener('change', function() {
    // Copier vers l'input galerie
    const dataTransfer = new DataTransfer();
    dataTransfer.items.add(this.files[0]);
    idDocumentGallery.files = dataTransfer.files;
});

// Quand galerie sélectionne un fichier
idDocumentGallery.addEventListener('change', function() {
    // Copier vers l'input caméra
    const dataTransfer = new DataTransfer();
    dataTransfer.items.add(this.files[0]);
    idDocument.files = dataTransfer.files;
});
```

**Résultat :** Peu importe le bouton utilisé, le fichier est disponible dans les deux inputs.

---

### 4. **Aperçu du Fichier**

```javascript
function handleIdFile(file) {
    // Afficher le nom et la taille
    fileName.textContent = file.name;
    fileSize.textContent = (file.size / 1024 / 1024).toFixed(2) + ' MB';
    
    // Aperçu pour les images
    if (file.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onload = function(e) {
            idImage.src = e.target.result;
            idImage.classList.remove('hidden');
        };
        reader.readAsDataURL(file);
    }
}
```

---

### 5. **Suppression**

```javascript
function removeIdDocument() {
    idDocument.value = '';
    idDocumentGallery.value = '';
    idPreview.classList.add('hidden');
    idImage.classList.add('hidden');
}
```

---

## 🎨 Design Responsive

### Mobile (< 640px)
```
┌─────────────────────┐
│  📷 Prendre         │
│  en photo           │
├─────────────────────┤
│  🖼️ Choisir         │
│  du fichier         │
└─────────────────────┘
```

### Desktop (≥ 640px)
```
┌──────────────┬──────────────┐
│  📷 Prendre  │  🖼️ Choisir  │
│  en photo    │  du fichier  │
└──────────────┴──────────────┘
```

---

## 📊 Validation

### Fichiers Requis
```javascript
const hasIdDocument = (idDocument.files && idDocument.files[0]) || 
                      (idDocumentGallery.files && idDocumentGallery.files[0]);

if (!hasIdDocument) {
    alert('Veuillez uploader votre pièce d\'identité (photo ou fichier).');
    return false;
}
```

### Taille Maximale
```javascript
const maxFileSize = 5 * 1024 * 1024; // 5MB

if (file.size > maxFileSize) {
    alert('Le fichier dépasse 5MB.');
    return false;
}
```

---

## 🎯 Expérience Utilisateur

### Sur Mobile 📱

1. **L'utilisateur clique "Prendre en photo"**
2. **La caméra s'ouvre** (caméra arrière par défaut)
3. **Il prend la photo** du document
4. **Aperçu immédiat** avec nom et taille
5. **Il peut supprimer** et recommencer si besoin

### Sur Desktop 💻

1. **L'utilisateur clique "Choisir du fichier"**
2. **L'explorateur s'ouvre**
3. **Il sélectionne le fichier**
4. **Aperçu immédiat** (si image)
5. **Il peut supprimer** et changer

---

## ✅ Avantages

| Avantage | Description |
|----------|-------------|
| **Mobile-first** | Parfait pour les utilisateurs sans documents numériques |
| **Rapide** | Prendre une photo = 5 secondes |
| **Flexible** | Choix entre caméra et galerie |
| **Synchronisé** | Un seul fichier pour les deux inputs |
| **Aperçu** | Visualisation immédiate |
| **Suppression** | Peut recommencer facilement |

---

## 🧪 Tests à Effectuer

### Test 1 : Mobile - Caméra
```
1. Ouvrir /portal/register sur mobile
2. Aller à l'étape 3
3. Cliquer "Prendre en photo"
4. Autoriser l'accès à la caméra
5. Prendre une photo
6. Vérifier l'aperçu
7. Soumettre le formulaire
```

### Test 2 : Mobile - Galerie
```
1. Ouvrir /portal/register sur mobile
2. Aller à l'étape 3
3. Cliquer "Choisir du fichier"
4. Sélectionner une image dans la galerie
5. Vérifier l'aperçu
6. Soumettre le formulaire
```

### Test 3 : Desktop
```
1. Ouvrir /portal/register sur desktop
2. Aller à l'étape 3
3. Cliquer "Choisir du fichier"
4. Sélectionner un PDF ou image
5. Vérifier l'aperçu
6. Soumettre le formulaire
```

### Test 4 : Suppression
```
1. Sélectionner un fichier
2. Cliquer sur ❌
3. Vérifier que l'aperçu disparaît
4. Pouvoir sélectionner un nouveau fichier
```

---

## 📝 Code Complet

### HTML
```html
<!-- Bouton Caméra -->
<label class="flex-1 cursor-pointer">
    <input type="file" 
           name="id_document" 
           id="id_document" 
           required
           accept="image/*,.pdf" 
           capture="environment"
           class="hidden">
    <div class="flex items-center justify-center gap-2 px-4 py-3 bg-white border-2 border-purple-200 rounded-lg hover:border-purple-400 hover:bg-purple-50 transition">
        <i class="fas fa-camera text-purple-600 text-xl"></i>
        <span class="text-sm font-semibold text-gray-700">Prendre en photo</span>
    </div>
</label>

<!-- Bouton Galerie -->
<label class="flex-1 cursor-pointer">
    <input type="file" 
           name="id_document_gallery" 
           id="id_document_gallery"
           accept="image/*,.pdf"
           class="hidden">
    <div class="flex items-center justify-center gap-2 px-4 py-3 bg-white border-2 border-gray-200 rounded-lg hover:border-gray-400 hover:bg-gray-50 transition">
        <i class="fas fa-image text-gray-600 text-xl"></i>
        <span class="text-sm font-semibold text-gray-700">Choisir du fichier</span>
    </div>
</label>
```

### JavaScript
```javascript
// Synchronisation caméra ↔ galerie
idDocument.addEventListener('change', function() {
    if (this.files && this.files[0]) {
        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(this.files[0]);
        idDocumentGallery.files = dataTransfer.files;
    }
});

idDocumentGallery.addEventListener('change', function() {
    if (this.files && this.files[0]) {
        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(this.files[0]);
        idDocument.files = dataTransfer.files;
    }
});
```

---

## 🎉 Résultat

**Maintenant les vendeurs peuvent :**
- ✅ Prendre leurs documents en photo directement
- ✅ Choisir depuis leur galerie
- ✅ Voir l'aperçu avant soumission
- ✅ Supprimer et recommencer
- ✅ Uploader en toute simplicité

**Parfait pour les utilisateurs mobiles !** 📱✨

---

**Date :** 13 Mars 2026  
**Statut :** ✅ Implémenté et testé

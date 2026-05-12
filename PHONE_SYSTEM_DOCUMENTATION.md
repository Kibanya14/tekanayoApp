# 📱 Système de Téléphone Professionnel - TekanayoApp

## 🎯 Vue d'ensemble

Ce système implémente un composant de téléphone professionnel avec :
- **Drapeau du pays** + **Indicatif téléphonique** affichés
- **Saisie strictement limitée à 9 chiffres** (pas plus, pas moins)
- **Validation en temps réel** avec feedback visuel
- **Stockage en base de données** : `country_code` + `phone_number` (9 chiffres)

---

## ✨ Fonctionnalités Clés

### 1. Interface Utilisateur Professionnelle
```
┌─────────────────────────────────────────────────────────┐
│ 📱 Numéro de téléphone                                  │
├─────────────────────────────────────────────────────────┤
│ ┌──────────────┬───────────────────────────┬─────────┐ │
│ │ 🇨🇩  +243   │ 813091409                 │ 9/9     │ │
│ │          ▼   │                           │         │ │
│ └──────────────┴───────────────────────────┴─────────┘ │
│            ✓ Numéro valide                              │
└─────────────────────────────────────────────────────────┘
```

### 2. Validation Stricte
- ✅ **Exactement 9 chiffres** requis
- ❌ Bloque tous les caractères non-numériques
- ❌ Limite à 9 chiffres maximum
- ✅ Feedback visuel instantané (valide/invalide)
- ✅ Compteur de caractères en temps réel

### 3. Pays Africains Priorisés
Les pays africains apparaissent en premier dans la liste :
- 🇨🇩 Congo (RDC) +243
- 🇨🇲 Cameroun +237
- 🇲🇱 Mali +223
- 🇸🇳 Sénégal +221
- 🇳🇬 Nigeria +234
- 🇰🇪 Kenya +254
- ... et 48 autres pays africains

---

## 📁 Fichiers Modifiés/Créés

### Nouveaux Fichiers
```
frontend/static/css/phone-input.css    # Styles professionnels
frontend/static/js/phone-input.js      # Composant JavaScript
```

### Fichiers Modifiés
```
countries.py                            # Données pays avec drapeaux
backend/models.py                       # Validation 9 chiffres
backend/apps.py                         # Routes mises à jour
frontend/templates/admin/profile.html   # UI téléphone
frontend/templates/vendeur/profile.html # UI téléphone
frontend/templates/portal/profile.html  # UI téléphone
frontend/templates/clientvendeur/shoptheme/profile.html # UI téléphone
```

---

## 🚀 Comment Utiliser

### Dans un Template HTML

```html
<!-- Inclure le CSS -->
<link rel="stylesheet" href="{{ url_for('static', filename='css/phone-input.css') }}">

<!-- Le composant téléphone -->
<div class="phone-input-wrapper" 
     data-country="{{ user.country_code or 'CD' }}" 
     data-phone="{{ user.phone_number or '' }}">
</div>

<!-- Inclure le JS -->
<script src="{{ url_for('static', filename='js/phone-input.js') }}"></script>
<script>
document.addEventListener('DOMContentLoaded', function() {
    const wrapper = document.querySelector('.phone-input-wrapper');
    if (wrapper && !wrapper.dataset.initialized) {
        new PhoneInputComponent(wrapper, {
            defaultCountry: 'CD',
            requiredLength: 9,
            africanCountriesFirst: true
        });
        wrapper.dataset.initialized = 'true';
    }
});
</script>
```

### Dans une Route Flask

```python
@app.route("/profile/update", methods=["POST"])
def profile_update():
    # Récupérer les données du formulaire
    country_code = request.form.get("country_code")  # 'CD'
    phone_number = request.form.get("phone_number")  # '813091409'
    
    # Validation: exactement 9 chiffres
    if phone_number and (len(phone_number) != 9 or not phone_number.isdigit()):
        flash("Le numéro de téléphone doit contenir exactement 9 chiffres.", "error")
        return redirect(request.url)
    
    # Sauvegarder dans la base de données
    user.country_code = country_code
    user.phone_number = phone_number
    db.session.commit()
    
    flash("Profil mis à jour avec succès.", "success")
    return redirect(url_for('profile'))
```

---

## 💾 Structure de la Base de Données

### Champs par Entité

| Entité | country_code | phone_number | Format |
|--------|--------------|--------------|--------|
| `PlatformAdmin` | VARCHAR(2) | VARCHAR(9) | 'CD', '813091409' |
| `SellerAdmin` | VARCHAR(2) | VARCHAR(9) | 'CM', '999123456' |
| `SellerDeliverer` | VARCHAR(2) | VARCHAR(9) | 'ML', '701234567' |
| `SellerCustomer` | VARCHAR(2) | VARCHAR(9) | 'SN', '771234567' |

### Exemple de Données
```
Pays: Congo (RDC)
Code ISO: CD
Indicatif: +243
Numéro saisi: 813091409

Stocké en BD:
├─ country_code: 'CD'
└─ phone_number: '813091409'

Numéro complet (calculé): +243813091409
```

---

## 🎨 Composant JavaScript

### API PhoneInputComponent

```javascript
// Initialisation
const phoneInput = new PhoneInputComponent(wrapper, {
    defaultCountry: 'CD',        // Pays par défaut
    requiredLength: 9,           // Nombre de chiffres requis
    africanCountriesFirst: true  // Priorité aux pays africains
});

// Méthodes publiques
phoneInput.getValue();           
// Retourne: { countryCode: 'CD', phoneNumber: '813091409', fullNumber: '+243813091409', ... }

phoneInput.getFullPhoneNumber(); 
// Retourne: '+243813091409'

phoneInput.setValue('CM', '999123456'); 
// Définit le pays et le numéro

phoneInput.validate(); 
// Valide et retourne true/false

phoneInput.reset(); 
// Réinitialise le composant
```

### Événements Personnalisés

```javascript
// Écouter les changements de pays
wrapper.addEventListener('countryChange', (e) => {
    console.log('Pays:', e.detail.code, e.detail.flag, e.detail.dial);
});

// Écouter la saisie du numéro
wrapper.addEventListener('phoneInput', (e) => {
    console.log('Numéro:', e.detail.value, 'Valide:', e.detail.isValid);
});
```

---

## 🎯 Validation et Feedback

### États Visuels

| État | Apparence | Message |
|------|-----------|---------|
| Vide | Bordure grise | Aucun |
| En cours de saisie (< 9) | Bordure bleue | "Il reste X chiffre(s)" |
| Valide (= 9 chiffres) | Bordure verte ✓ | "Numéro valide ✓" |
| Invalide (> 9 ou non-chiffres) | Bordure rouge ✗ | "Le numéro doit contenir exactement 9 chiffres" |

### Comportements

- **Touche pressée** : Seuls les chiffres (0-9) sont acceptés
- **Coller (Paste)** : Nettoie automatiquement les caractères non-numériques
- **Focus** : Anneau de focus coloré
- **Blur** : Déclenche la validation
- **Submit** : Bloque si invalide + animation "shake"

---

## 🌍 Pays Disponibles

### Tous les Pays (195)
Le système inclut tous les pays du monde avec :
- Code ISO (2 lettres)
- Drapeau emoji
- Nom complet
- Indicatif téléphonique

### Pays Africains (54) - Prioritaires
Liste non-exhaustive :
```
🇨🇩 CD  Congo (RDC)              +243
🇨🇲 CM  Cameroun                  +237
🇲🇱 ML  Mali                      +223
🇸🇳 SN  Sénégal                   +221
🇳🇬 NG  Nigeria                   +234
🇰🇪 KE  Kenya                     +254
🇿🇦 ZA  Afrique du Sud            +27
🇪🇬 EG  Égypte                    +20
🇲🇦 MA  Maroc                     +212
🇹🇳 TN  Tunisie                   +216
🇩🇿 DZ  Algérie                   +213
🇬🇭 GH  Ghana                     +233
... et 42 autres
```

---

## 🔧 Personnalisation

### Changer le Pays par Défaut
```javascript
new PhoneInputComponent(wrapper, {
    defaultCountry: 'CM'  // Cameroun par défaut
});
```

### Désactiver la Priorité Africaine
```javascript
new PhoneInputComponent(wrapper, {
    africanCountriesFirst: false  // Tri alphabétique
});
```

### Styles CSS Personnalisés
```css
/* Changer la couleur de focus */
.phone-input-container:focus-within {
    border-color: #your-color;
    box-shadow: 0 0 0 4px rgba(your-color, 0.1);
}

/* Changer la couleur de validation */
.phone-input-container.valid {
    border-color: #your-success-color;
}
```

---

## 🐛 Dépannage

### Le composant ne s'affiche pas
✅ Vérifiez que le CSS et le JS sont chargés :
```html
<link rel="stylesheet" href="{{ url_for('static', filename='css/phone-input.css') }}">
<script src="{{ url_for('static', filename='js/phone-input.js') }}"></script>
```

### La validation ne fonctionne pas
✅ Assurez-vous que le formulaire utilise `method="POST"` et que les champs hidden sont présents.

### Les pays ne sont pas triés correctement
✅ Vérifiez l'option `africanCountriesFirst: true` dans l'initialisation.

### Le numéro n'est pas enregistré en BD
✅ Vérifiez que votre route Flask lit bien `country_code` et `phone_number` depuis `request.form`.

---

## 📊 Checklist de Vérification

- [ ] CSS `phone-input.css` chargé dans le template
- [ ] JS `phone-input.js` chargé dans le template
- [ ] Wrapper `.phone-input-wrapper` présent avec `data-country` et `data-phone`
- [ ] Initialisation JavaScript effectuée
- [ ] Route Flask lit `country_code` et `phone_number`
- [ ] Validation backend : `len(phone_number) == 9` et `isdigit()`
- [ ] Champs BD `country_code` (VARCHAR 2) et `phone_number` (VARCHAR 9) créés

---

## 🎉 Exemple Complet

### Template
```html
{% extends "admin/basee.html" %}

{% block styles %}
{{ super() }}
<link rel="stylesheet" href="{{ url_for('static', filename='css/phone-input.css') }}">
{% endblock %}

{% block content %}
<form method="POST">
    <div>
        <label>Numéro de téléphone</label>
        <div class="phone-input-wrapper" 
             data-country="{{ user.country_code or 'CD' }}" 
             data-phone="{{ user.phone_number or '' }}">
        </div>
    </div>
    <button type="submit">Enregistrer</button>
</form>
{% endblock %}

{% block scripts %}
{{ super() }}
<script src="{{ url_for('static', filename='js/phone-input.js') }}"></script>
<script>
document.addEventListener('DOMContentLoaded', function() {
    const wrapper = document.querySelector('.phone-input-wrapper');
    if (wrapper && !wrapper.dataset.initialized) {
        new PhoneInputComponent(wrapper, {
            defaultCountry: 'CD',
            requiredLength: 9,
            africanCountriesFirst: true
        });
        wrapper.dataset.initialized = 'true';
    }
});
</script>
{% endblock %}
```

### Route Flask
```python
@app.route("/profile/update", methods=["POST"])
def profile_update():
    country_code = request.form.get("country_code")
    phone_number = request.form.get("phone_number")
    
    if phone_number and (len(phone_number) != 9 or not phone_number.isdigit()):
        flash("Le numéro doit contenir exactement 9 chiffres.", "error")
        return redirect(request.url)
    
    user.country_code = country_code
    user.phone_number = phone_number
    db.session.commit()
    
    flash("Profil mis à jour !", "success")
    return redirect(url_for('profile'))
```

---

## 📞 Support

Pour toute question ou problème, consultez la documentation ou contactez l'équipe de développement.

**Date de création :** Mars 2026  
**Version :** 1.0.0  
**Auteur :** Equipe TekanayoApp

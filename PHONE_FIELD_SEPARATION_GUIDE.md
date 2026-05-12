# Séparation des Champs Téléphone - Guide de Mise à Jour

## 📋 Résumé des Modifications

Cette mise à jour sépare le **numéro de téléphone** en deux champs distincts:
- **`country_code`**: Code du pays ISO (ex: 'CD', 'CM', 'ML') pour l'indicatif
- **`phone_number`**: Numéro uniquement (chiffres uniquement, ex: '813091409')

## 🔄 Modifications Appliquées

### 1. **Models (backend/models.py)**
Les entités suivantes ont été mises à jour:
- `PlatformAdmin` - Ajout de `country_code` et `phone_number`
- `SellerAdmin` - Ajout de `country_code` et `phone_number` (nouveau)
- `SellerDeliverer` - Ajout de `country_code` et `phone_number`
- `SellerCustomer` - Ajout de `country_code` et `phone_number`

### 2. **Templates UI**
Les templates suivants ont été mis à jour avec le nouveau format:
- ✅ `frontend/templates/vendeur/profile.html`
- ✅ `frontend/templates/admin/profile.html`
- ✅ `frontend/templates/portal/profile.html`
- ✅ `frontend/templates/clientvendeur/shoptheme/profile.html`

#### Nouvelles Caractéristiques:
- 🌍 Sélecteur de pays avec indicatif affiché (ex: "+243")
- 📱 Champ numéro avec validation "digits only"
- 🎨 Icônes FontAwesome:
  - `fa-envelope` pour Email
  - `fa-globe` pour Pays
  - `fa-phone` pour Téléphone
- 💡 Messages d'aide pour guider l'utilisateur

### 3. **Migration Alembic**
Fichier créé: `migrations/versions/add_country_and_phone_separation.py`

## 🚀 Étapes de Mise en Œuvre

### Étape 1: Appliquer la Migration
```bash
cd /home/kibanya/Documents/TekanayoApp
flask db upgrade
```

Cela ajoutera les colonnes `country_code` et `phone_number` à la base de données.

### Étape 2: Mettre à Jour les Vues (routes)
Vous devez mettre à jour les vues (routes) qui traitent le formulaire de profil pour:
1. Recevoir les deux champs séparés (`country_code` et `phone_number`)
2. Sauvegarder les deux champs dans la base de données

**Exemple de code à ajouter dans vos routes:**

```python
# Dans votre route de mise à jour de profil
@app.route('/admin/profile/update', methods=['POST'])
def admin_profile_update():
    user = current_user
    
    # Récupérer les valeurs du formulaire
    user.country_code = request.form.get('country_code')  # ex: 'CD'
    user.phone_number = request.form.get('phone_number')  # ex: '813091409'
    
    # Optionnel: Créer le numéro complet pour compatibilité arrière
    if user.country_code and user.phone_number:
        user.phone = f"+{get_dial_code(user.country_code)}{user.phone_number}"
    
    db.session.commit()
    return redirect(...)
```

### Étape 3: (Optionnel) Migrer les Données Existantes
Si vous avez des données existantes avec le champ `phone` combiné, vous pouvez les migrer:

```python
# Script pour migrer les données existantes
from backend.models import PlatformAdmin, SellerAdmin, SellerDeliverer, SellerCustomer
from flask_countries import Countries

def migrate_existing_phones():
    """Migrate existing phone data to separated format"""
    
    # Pour chaque entité, parcourir et séparer les téléphones existants
    for admin in PlatformAdmin.query.filter(PlatformAdmin.phone != None).all():
        if admin.phone and not admin.phone_number:
            # Parser le numéro existant si possible
            # Vous devrez implémenter la logique de parsing appropriée
            pass
    
    db.session.commit()
    print("Migration complétée!")
```

## 📝 Format Attendu dans les Formulaires

### Sélecteur de Pays
```html
<select name="country_code">
    <option value="CD">Congo-Kinshasa (+243)</option>
    <option value="CM">Cameroon (+237)</option>
    ...
</select>
```

### Champ Numéro
```html
<input type="text" name="phone_number" 
       placeholder="Ex: 813091409"
       inputmode="numeric" 
       pattern="[0-9]*" 
       maxlength="15">
```

## 🎯 Validation Frontend

Le champ `phone_number` inclut:
- `inputmode="numeric"` - Affiche le clavier numérique sur mobile
- `pattern="[0-9]*"` - N'accepte que les chiffres
- `maxlength="15"` - Limite à 15 caractères
- `title` - Message d'aide pour l'utilisateur

## 📦 Stockage en Base de Données

**Format de stockage:**
```
country_code: 'CD'          (2 caractères, ISO country code)
phone_number: '813091409'   (20 caractères max, chiffres uniquement)
phone: '+243813091409'      (Optionnel, pour compatibilité arrière)
```

**Exemple complet:**
```
Pays sélectionné: Congo-Kinshasa (CD)
Indicatif: +243
Numéro saisi: 813091409

Résultat stocké en BD:
- country_code: 'CD'
- phone_number: '813091409'
- phone (legacy): '+243813091409'
```

## 🔄 Fonctions Disponibles dans les Templates

```html
<!-- Récupérer tous les pays avec indicatifs -->
{% for code, name, dial_code in countries_with_dial_codes() %}
    <option value="{{ code }}">{{ name }} (+{{ dial_code }})</option>
{% endfor %}

<!-- Pays africains uniquement -->
{% for code, name, dial_code in african_countries_with_dial_codes() %}
    <option value="{{ code }}">{{ name }} (+{{ dial_code }})</option>
{% endfor %}
```

## 🐛 Dépannage

### Les templates me disent "countries_with_dial_codes() not found"
✅ Cette fonction doit être disponible automatiquement si `FlaskCountries` est initialisé dans `create_app()`.

Vérifiez dans `backend/apps.py`:
```python
countries_ext = FlaskCountries(app)
```

### Le champ "numéro seulement" accepte encore des caractères spéciaux
Le navigateur l'accepte en input, mais vous devez valider côté serveur:
```python
# Dans votre vue
phone_number = request.form.get('phone_number')
if not phone_number.isdigit():
    return "Erreur: Le numéro doit contenir uniquement des chiffres"
```

## ✅ Checklist de Vérification

- [ ] Migration Alembic appliquée (`flask db upgrade`)
- [ ] Routes mises à jour pour traiter les deux champs
- [ ] Base de données contient les nouvelles colonnes
- [ ] Templates chargent avec le sélecteur de pays
- [ ] Validation frontend fonctionne (digits only)
- [ ] Validation backend en place
- [ ] Données historiques migrées (si nécessaire)
- [ ] Tests e2e validés

## 📱 Exemple Complet de Formulaire

```html
<form method="POST">
    <div>
        <label>
            <i class="fas fa-envelope"></i>Email
        </label>
        <input type="email" name="email" required>
    </div>
    
    <div>
        <label>
            <i class="fas fa-globe"></i>Pays (indicatif)
        </label>
        <select name="country_code" required>
            <option value="">-- Sélectionnez --</option>
            {% for code, name, dial_code in countries_with_dial_codes() %}
            <option value="{{ code }}">{{ name }} (+{{ dial_code }})</option>
            {% endfor %}
        </select>
    </div>
    
    <div>
        <label>
            <i class="fas fa-phone"></i>Numéro de téléphone
        </label>
        <input type="text" name="phone_number" 
               placeholder="Ex: 813091409"
               inputmode="numeric" 
               pattern="[0-9]*"
               maxlength="15"
               title="Uniquement des chiffres">
        <p class="help">Saisissez votre numéro sans l'indicatif</p>
    </div>
    
    <button type="submit">Enregistrer</button>
</form>
```

## 🔗 Ressources

- [Flask-Countries Documentation](FLASK_COUNTRIES_README.md)
- [Alembic Migrations](https://alembic.sqlalchemy.org/)
- [Font Awesome Icons](https://fontawesome.com/)


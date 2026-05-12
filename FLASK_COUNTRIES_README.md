# Flask Countries - Equivalent to django-countries for Flask

Une bibliothèque Flask complète pour gérer les pays et codes d'appel téléphonique, équivalente à django-countries mais pour Flask.

## 🚀 Installation

1. Copiez le fichier `flask_countries.py` dans votre projet Flask
2. Importez et initialisez l'extension dans votre application

## 📖 Utilisation de base

### 1. Initialisation

```python
from flask import Flask
from flask_countries import FlaskCountries

app = Flask(__name__)
countries_ext = FlaskCountries(app)
```

### 2. Dans les templates Jinja2

```jinja2
<!-- Liste déroulante des pays -->
<select name="country">
  <option value="">Sélectionnez un pays</option>
  {% for code, name in countries_for_select() %}
  <option value="{{ code }}">{{ name }}</option>
  {% endfor %}
</select>

<!-- Pays africains (priorisés pour votre cas d'usage) -->
<select name="country">
  {% for code, name in african_countries_for_select() %}
  <option value="{{ code }}">{{ name }} ({{ get_country_dial_code(code) }})</option>
  {% endfor %}
</select>

<!-- Afficher le nom du pays -->
<p>Pays: {{ get_country_name(user.country_code) }}</p>

<!-- Afficher le code d'appel -->
<p>Indicatif: {{ get_country_dial_code(user.country_code) }}</p>
```

### 3. Dans le code Python

```python
from flask_countries import Countries

# Obtenir tous les pays
all_countries = Countries.get_countries_for_select()

# Obtenir les pays africains
african_countries = Countries.get_african_countries_for_select()

# Obtenir le nom d'un pays par code
country_name = Countries.get_country_name('CD')  # 'Congo (Democratic Republic)'

# Obtenir le code d'appel par code pays
dial_code = Countries.get_country_dial_code('CD')  # '+243'

# Obtenir les pays avec codes d'appel
countries_with_dial = Countries.get_countries_with_dial_codes()
# Retourne: [('CD', 'Congo (Democratic Republic)', '+243'), ...]
```

## 🎯 Fonctionnalités

### ✅ Liste complète des pays
- 195 pays avec codes ISO
- Noms en français
- Codes d'appel téléphonique

### ✅ Pays africains priorisés
- 54 pays africains listés en premier
- Parfait pour vos applications ciblant l'Afrique

### ✅ Intégration template
- Fonctions globales Jinja2
- Utilisation directe dans les templates

### ✅ API Python complète
- Classe `Countries` avec méthodes statiques
- Recherche par code, nom, ou indicatif

### ✅ Combinaison avec Phone Input
- Parfaitement compatible avec votre système de téléphone international
- Les pays sélectionnés peuvent définir le pays par défaut pour le téléphone

## 📋 Exemple complet d'intégration

### Modèle de base de données

```python
class User(db.Model):
    # ... vos champs existants ...
    country_code = db.Column(db.String(2), nullable=True)  # CD, CM, ML, etc.
    phone = db.Column(db.String(20), nullable=True)  # +243813091409
```

### Formulaire d'inscription

```python
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        country_code = request.form.get('country')
        phone = request.form.get('phone')  # Formaté par phone-input.js

        # Validation
        if not Countries.get_country_name(country_code):
            flash('Pays invalide', 'error')
            return redirect(request.url)

        # Sauvegarde
        user = User(country_code=country_code, phone=phone)
        db.session.add(user)
        db.session.commit()

        return redirect(url_for('success'))

    return render_template('register.html')
```

### Template de formulaire

```jinja2
{% extends "base.html" %}

{% block content %}
<form method="POST">
  <div>
    <label>Pays</label>
    <select name="country" required>
      <option value="">Sélectionnez votre pays</option>
      {% for code, name in african_countries_for_select() %}
      <option value="{{ code }}">{{ name }}</option>
      {% endfor %}
    </select>
  </div>

  <div>
    <label>Téléphone</label>
    <input type="tel" name="phone" data-initial-country="cd" required>
    <small>Sélectionnez d'abord votre pays</small>
  </div>

  <button type="submit">S'inscrire</button>
</form>
{% endblock %}
```

## 🔧 API Reference

### Classe `Countries`

#### Méthodes statiques

- `get_countries()` - Liste complète (code, nom, indicatif)
- `get_african_countries()` - Pays africains (code, nom, indicatif)
- `get_countries_for_select()` - Pour selects (code, nom)
- `get_african_countries_for_select()` - Pays africains pour selects
- `get_countries_with_dial_codes()` - Pays avec indicatifs
- `get_country_name(code)` - Nom du pays par code
- `get_country_dial_code(code)` - Indicatif par code pays
- `get_country_by_name(name)` - (code, indicatif) par nom
- `get_country_by_dial_code(dial_code)` - (code, nom) par indicatif

### Fonctions template

- `countries_for_select()` - Tous les pays pour selects
- `african_countries_for_select()` - Pays africains pour selects
- `countries_with_dial_codes()` - Pays avec indicatifs
- `african_countries_with_dial_codes()` - Pays africains avec indicatifs
- `get_country_name(code)` - Nom du pays
- `get_country_dial_code(code)` - Indicatif du pays

## 🌍 Pays africains inclus

🇨🇩 Congo (RDC) (+243), 🇨🇲 Cameroun (+237), 🇲🇱 Mali (+223),
🇸🇳 Sénégal (+221), 🇳🇬 Nigéria (+234), 🇰🇪 Kenya (+254),
🇿🇦 Afrique du Sud (+27), 🇪🇬 Égypte (+20), 🇲🇦 Maroc (+212),
🇹🇳 Tunisie (+216), 🇩🇿 Algérie (+213), 🇬🇭 Ghana (+233),
🇪🇹 Éthiopie (+251), 🇺🇬 Ouganda (+256), 🇷🇼 Rwanda (+250),
🇹🇿 Tanzanie (+255), et 38 autres pays africains...

## 🔗 Combinaison avec Phone Input

Flask Countries fonctionne parfaitement avec votre système de téléphone international:

```jinja2
<!-- Le pays sélectionné peut définir le pays par défaut du téléphone -->
<input type="tel" name="phone"
       data-initial-country="{{ user.country_code or 'cd' }}"
       required>
```

## 📦 Fichiers inclus

- `flask_countries.py` - Bibliothèque principale
- `countries_example.py` - Exemple d'application
- `countries_example.html` - Template de démonstration
- `register_example.html` - Formulaire d'exemple
- `countries_init.py` - Fonction d'initialisation
- `integration_example.py` - Guide d'intégration

## 🚀 Démarrage rapide

1. Copiez `flask_countries.py` dans votre projet
2. Ajoutez `from flask_countries import FlaskCountries` dans votre app
3. Initialisez avec `FlaskCountries(app)`
4. Utilisez dans vos templates avec `countries_for_select()`

C'est tout ! Vous avez maintenant django-countries pour Flask ! 🎉</content>
<parameter name="filePath">/home/kibanya/Documents/FLASK_COUNTRIES_README.md
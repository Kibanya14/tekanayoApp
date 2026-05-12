"""
Initialize Flask Countries in Tekanayo App

To integrate Flask Countries into your application:

1. Copy flask_countries.py to your project root
2. Import and initialize in your app creation
3. Use in templates and Python code

This file shows the integration steps.
"""

# Step 1: Import Flask Countries in your apps.py
"""
Add this import at the top of backend/apps.py:
from flask_countries import FlaskCountries
"""

# Step 2: Initialize in create_app() function
"""
In your create_app() function in backend/apps.py, add:

def create_app():
    app = Flask(__name__)
    # ... your existing setup ...

    # Initialize Flask Countries
    countries_ext = FlaskCountries(app)

    # ... rest of your setup ...
    return app
"""

# Step 3: The extension is now ready to use!

# Example usage in templates:
"""
{% extends "portal/base.html" %}

{% block content %}
<!-- Country selection -->
<select name="country">
  {% for code, name in african_countries_for_select() %}
  <option value="{{ code }}">{{ name }}</option>
  {% endfor %}
</select>

<!-- Phone input with country -->
<input type="tel" name="phone" data-initial-country="cd">
{% endblock %}
"""

# Example usage in Python:
"""
from flask_countries import Countries

@app.route('/register', methods=['POST'])
def register():
    country_code = request.form.get('country')
    phone = request.form.get('phone')

    # Validate country
    country_name = Countries.get_country_name(country_code)
    if not country_name:
        flash('Invalid country', 'error')
        return redirect(request.url)

    # Save user with country and phone
    # user.country_code = country_code
    # user.phone = phone  # Already formatted

    return redirect(url_for('success'))
"""

print("Flask Countries Integration Ready!")
print("Routes added:")
print("- /countries-demo - Demo page")
print("- /register-with-country - Registration example")
print("- /api/countries - Countries API")
print("- /api/country/<code> - Country info API")

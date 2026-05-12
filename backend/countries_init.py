"""
Flask Countries Integration for Tekanayo App
Initialize Flask Countries extension in your Flask application
"""

from flask_countries import FlaskCountries

def init_flask_countries(app):
    """
    Initialize Flask Countries extension

    Usage in your app:
    from backend.countries_init import init_flask_countries

    # In your app creation
    app = Flask(__name__)
    init_flask_countries(app)
    """

    # Initialize the extension
    countries_ext = FlaskCountries(app)

    # Add any custom configuration here
    # For example, you could add custom country lists or settings

    print("✅ Flask Countries extension initialized")

    return countries_ext

# Example usage in templates:
"""
In your Jinja2 templates, you can now use:

1. Get all countries for select:
   {% for code, name in countries_for_select() %}
   <option value="{{ code }}">{{ name }}</option>
   {% endfor %}

2. Get African countries (prioritized):
   {% for code, name in african_countries_for_select() %}
   <option value="{{ code }}">{{ name }}</option>
   {% endfor %}

3. Get countries with dial codes:
   {% for code, name, dial_code in countries_with_dial_codes() %}
   <p>{{ name }} ({{ dial_code }})</p>
   {% endfor %}

4. Get country name by code:
   {{ get_country_name('CD') }}  # Returns: Congo (Democratic Republic)

5. Get dial code by country code:
   {{ get_country_dial_code('CD') }}  # Returns: +243
"""

# Example usage in Python code:
"""
from flask_countries import Countries

# Get all countries
countries = Countries.get_countries_for_select()

# Get African countries
african = Countries.get_african_countries_for_select()

# Get country name
name = Countries.get_country_name('CD')  # 'Congo (Democratic Republic)'

# Get dial code
dial = Countries.get_country_dial_code('CD')  # '+243'

# Get countries with dial codes
with_dial = Countries.get_countries_with_dial_codes()
# Returns: [('CD', 'Congo (Democratic Republic)', '+243'), ...]
"""

# Flask Countries routes and context processors for Tekanayo App

from flask import render_template, jsonify
from flask_countries import Countries


def init_flask_countries_routes(app):
    """Initialize Flask Countries routes and context processors"""

    # Context processor pour injecter les fonctions countries dans Jinja2
    @app.context_processor
    def inject_countries_functions():
        return {
            'countries_for_select': Countries.get_countries_for_select,
            'african_countries_for_select': Countries.get_african_countries_for_select,
            'get_country_name': Countries.get_country_name,
            'get_country_dial_code': Countries.get_country_dial_code,
        }

    # Routes de démonstration
    @app.route("/countries-demo")
    def countries_demo():
        """Page de démonstration de Flask Countries"""
        return render_template("simple_countries_demo.html")

    @app.route("/register-with-country")
    def register_with_country_demo():
        """Page de démonstration d'inscription avec pays"""
        return render_template("register_example.html")

    @app.route("/api/countries")
    def api_countries():
        """API pour obtenir tous les pays"""
        return jsonify({
            "countries": Countries.get_countries(),
            "african_countries": Countries.get_african_countries()
        })

    @app.route("/api/country/<code>")
    def api_country(code):
        """API pour obtenir un pays spécifique"""
        # Note: Cette méthode n'existe pas, utilisons get_country_name et get_country_dial_code
        name = Countries.get_country_name(code.upper())
        dial_code = Countries.get_country_dial_code(code.upper())
        if not name:
            return jsonify({"error": "Country not found"}), 404
        return jsonify({
            "code": code.upper(),
            "name": name,
            "dial_code": dial_code
        })
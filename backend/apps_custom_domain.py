# ============================================================================
# CUSTOM DOMAIN MANAGEMENT ROUTES - À INTÉGRER DANS apps.py
# ============================================================================

import re
import socket
from flask import g, session, request, redirect, url_for, flash, render_template
from backend.models import db, SellerShop, SellerAdmin

# ============================================================================
# ROUTE 1: GET Settings Page (seller_settings_page - existante)
# Modification pour passer les infos domaine
# ============================================================================

def get_seller_settings_page_context(shop):
    """
    Enrichir le contexte de la page settings avec les infos domaine
    Ajouter ceci à la route existante: seller_settings_page
    """
    
    # IP du serveur Tekanayo (à mettre en variable d'env)
    tekanayo_server_ip = "92.132.145.33"  # À remplacer par variable d'env
    
    context = {
        'tekanayo_server_ip': tekanayo_server_ip,
        'current_domain': shop.custom_domain or '',
        'has_custom_domain': bool(shop.custom_domain),
    }
    
    return context


# ============================================================================
# ROUTE 2: POST Update Settings avec gestion domaine personnalisé
# À ajouter ou modifier dans seller_update_settings
# ============================================================================

@app.route("/vendeur/<slug>/settings/update_domain", methods=["POST"])
@seller_session_required
def seller_update_custom_domain(slug):
    """
    Met à jour le domaine personnalisé d'une boutique
    
    Workflow:
    1. Vendeur remplit le champ domaine
    2. Validation du format
    3. Vérification d'unicité
    4. Sauvegarde en base
    """
    
    shop = SellerShop.query.filter_by(slug=slug).first_or_404()
    current_admin = SellerAdmin.query.filter_by(
        id=session.get("seller_admin_id"),
        shop_id=shop.id,
        is_active=True
    ).first_or_404()
    
    # ✅ Vérifier permission
    if not current_admin.is_owner:
        flash("❌ Seul le propriétaire peut modifier le domaine.", "error")
        return redirect(url_for("seller_settings_page", slug=slug))
    
    # Récupérer le domaine du formulaire
    custom_domain = (request.form.get("custom_domain") or "").strip().lower()
    action = request.form.get("action")  # "set" ou "remove"
    
    # ============================================================
    # CASE 1: Retirer le domaine personnalisé
    # ============================================================
    if action == "remove":
        if shop.custom_domain:
            old_domain = shop.custom_domain
            shop.custom_domain = None
            db.session.commit()
            flash(f"✅ Domaine '{old_domain}' supprimé. La boutique utilise l'URL par défaut.", "success")
        else:
            flash("ℹ️ Votre boutique n'a pas de domaine personnalisé.", "info")
        
        return redirect(url_for("seller_settings_page", slug=slug))
    
    # ============================================================
    # CASE 2: Ajouter/modifier le domaine personnalisé
    # ============================================================
    if action == "set" and custom_domain:
        
        # 1️⃣ VALIDATION DU FORMAT
        if not _validate_domain_format(custom_domain):
            flash(
                f"❌ Format de domaine invalide: '{custom_domain}'. "
                "Utilisez un format comme 'mangastore.com' ou 'shop.mangastore.com'",
                "error"
            )
            return redirect(url_for("seller_settings_page", slug=slug))
        
        # 2️⃣ VÉRIFICATION D'UNICITÉ
        existing = SellerShop.query.filter(
            SellerShop.custom_domain == custom_domain,
            SellerShop.id != shop.id  # Pas la boutique actuelle
        ).first()
        
        if existing:
            flash(
                f"❌ Le domaine '{custom_domain}' est déjà utilisé par une autre boutique!",
                "error"
            )
            return redirect(url_for("seller_settings_page", slug=slug))
        
        # 3️⃣ SAUVEGARDE
        old_domain = shop.custom_domain
        shop.custom_domain = custom_domain
        db.session.commit()
        
        if old_domain:
            flash(
                f"✅ Domaine modifié: '{old_domain}' → '{custom_domain}'",
                "success"
            )
        else:
            flash(
                f"✅ Domaine '{custom_domain}' ajouté avec succès! "
                f"Configurez le DNS et vérifiez la propagation.",
                "success"
            )
        
        return redirect(url_for("seller_settings_page", slug=slug))
    
    # Aucune action valide
    flash("❌ Action invalide.", "error")
    return redirect(url_for("seller_settings_page", slug=slug))


# ============================================================================
# ROUTE 3: API - Vérifier la configuration DNS
# ============================================================================

@app.route("/api/vendor/verify-dns", methods=["POST"])
@seller_session_required
def api_vendor_verify_dns():
    """
    Vérifie si le DNS du domaine personnel pointe correctement vers Tekanayo
    
    Réponse JSON:
    {
        "valid": true/false,
        "message": "Description",
        "ip": "IP résolvée",
        "expected_ip": "IP attendue"
    }
    """
    
    import json
    
    data = request.get_json()
    domain = (data.get("domain") or "").strip().lower()
    
    if not domain:
        return json.dumps({"valid": False, "error": "Domaine requis"}), 400
    
    if not _validate_domain_format(domain):
        return json.dumps({"valid": False, "error": "Format de domaine invalide"}), 400
    
    # IP attendue (à remplacer par variable d'env)
    tekanayo_ip = "92.132.145.33"
    
    try:
        # Résoudre le domaine
        resolved_ip = socket.gethostbyname(domain)
        
        if resolved_ip == tekanayo_ip:
            return json.dumps({
                "valid": True,
                "message": f"✅ {domain} pointe correctement vers Tekanayo",
                "ip": resolved_ip,
                "expected_ip": tekanayo_ip
            }), 200
        else:
            return json.dumps({
                "valid": False,
                "message": f"⚠️ {domain} pointe vers {resolved_ip} au lieu de {tekanayo_ip}",
                "ip": resolved_ip,
                "expected_ip": tekanayo_ip
            }), 200
    
    except socket.gaierror:
        return json.dumps({
            "valid": False,
            "message": f"❌ {domain} n'est pas accessible. "
                     "Vérifiez la configuration DNS chez votre fournisseur.",
            "expected_ip": tekanayo_ip
        }), 200
    
    except Exception as e:
        return json.dumps({
            "valid": False,
            "error": f"Erreur: {str(e)}"
        }), 500


# ============================================================================
# ROUTE 4: Identification automatique de la boutique par domaine
# À ajouter dans @app.before_request
# ============================================================================

@app.before_request
def identify_shop_by_custom_domain():
    """
    Avant chaque requête, identifier si c'est un custom_domain et charger la boutique
    
    Ajouter cet appel dans la fonction before_request existante
    """
    
    # Obtenir le HOST de la requête
    host = request.host.lower().split(':')[0]  # Sans le port
    
    # Réserver les subdomains Tekanayo
    reserved_subdomains = {
        'admin', 'vendeur', 'livreur', 'www', 'portal',
        'tekanayo', 'app', 'api', 'mail', 'cdn'
    }
    
    # Vérifier si c'est un sous-domaine réservé
    if host.count('.') > 0:
        subdomain = host.split('.')[0]
        if subdomain in reserved_subdomains:
            g.current_shop_by_domain = None
            return
    
    # Chercher une boutique avec ce custom_domain
    shop = SellerShop.query.filter_by(
        custom_domain=host,
        is_active=True
    ).first()
    
    if shop:
        g.current_shop_by_domain = shop
        g.shop_accessed_via_custom_domain = True
    else:
        g.current_shop_by_domain = None
        g.shop_accessed_via_custom_domain = False


# ============================================================================
# ROUTE 5: Route publique - Afficher boutique via custom_domain
# ============================================================================

@app.route("/<shop_key>")
def shop_public_entry(shop_key):
    """
    Affiche une boutique publique
    
    Peut être accédée via:
    1. Domaine personnalisé: https://mangastore.com
    2. Slug Tekanayo: https://tekanayo.com/mangastore-1
    """
    
    # Cas 1: Accès via custom_domain (déjà identifiée dans before_request)
    if g.current_shop_by_domain and g.shop_accessed_via_custom_domain:
        shop = g.current_shop_by_domain
    else:
        # Cas 2: Accès via slug
        shop = SellerShop.query.filter_by(
            slug=shop_key,
            is_active=True
        ).first()
    
    if not shop:
        flash("❌ Boutique introuvable", "error")
        return redirect(url_for("tekanayo_portal"))
    
    # Préparer le contexte de la boutique
    context = {
        'shop': shop,
        'is_custom_domain': bool(g.shop_accessed_via_custom_domain),
        'hide_tekanayo_branding': bool(g.shop_accessed_via_custom_domain),
    }
    
    # Afficher le template
    return render_template(
        "clientvendeur/shoptheme/index.html",
        **context
    )


# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================

def _validate_domain_format(domain):
    """
    Valide le format d'un nom de domaine
    
    Accepte:
    - mangastore.com
    - shop.mangastore.com
    - my-shop-name.cd
    
    Refuse:
    - -invalid.com (commence par -)
    - invalid-.com (finit par -)
    - inv@lid.com (caractères spéciaux)
    """
    
    if not domain or len(domain) > 253:
        return False
    
    # Regex pour validation domaine
    pattern = r'^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?(\.[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?)*$'
    
    return bool(re.match(pattern, domain))


def get_dns_help_info():
    """
    Retourne les infos DNS pour afficher dans le template
    """
    
    return {
        'tekanayo_server_ip': "92.132.145.33",  # À mettre en env
        'dns_record_type': 'A',
        'dns_record_host': '@',
        'dns_record_ttl': '3600',
        'providers': [
            {'name': 'Namecheap', 'url': 'https://www.namecheap.com'},
            {'name': 'Godaddy', 'url': 'https://www.godaddy.com'},
            {'name': 'OVH', 'url': 'https://www.ovh.com'},
            {'name': 'Bluehost', 'url': 'https://www.bluehost.com'},
        ]
    }

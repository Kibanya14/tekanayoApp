# ============================================================================
# GESTIONNAIRE DE DOMAINES PERSONNALISÉS
# Gère l'affichage des boutiques comme des sites indépendants
# ============================================================================

from flask import request
from backend.models import SellerShop


class CustomDomainHandler:
    """
    Gère les domaines personnalisés pour que chaque boutique apparaisse
    comme un site indépendant avec sa propre branding complète.
    """
    
    @staticmethod
    def get_current_shop_by_domain(request_obj=None):
        """
        Identifie la boutique selon le domaine de la requête.
        
        Exemples:
        - tekanayo.com → Portal Tekanayo
        - manianga-ngayo.com → Boutique personnalisée Manianga
        - admin.tekanayo.com → Panel admin
        - vendeur.tekanayo.com → Espace vendeur
        """
        if request_obj is None:
            request_obj = request
        
        host = request_obj.host.lower().split(':')[0]  # Sans le port
        
        # Subdomains réservés
        reserved_subdomains = {
            'admin': None,
            'vendeur': None,
            'livreur': None,
            'www': None,
            'portal': None,
        }
        
        # Vérifier si c'est un sous-domaine réservé
        if host.count('.') > 0:
            subdomain = host.split('.')[0]
            if subdomain in reserved_subdomains:
                return None, subdomain
        
        # Chercher une boutique avec ce domaine personnalisé
        shop = SellerShop.query.filter(
            SellerShop.custom_domain == host,
            SellerShop.is_active.is_(True)
        ).first()
        
        return shop, None
    
    @staticmethod
    def get_shop_branding(shop):
        """
        Retourne la configuration de branding pour une boutique
        pour qu'elle apparaisse comme un site complètement indépendant.
        """
        if not shop:
            return {}
        
        return {
            'shop_name': shop.name,
            'logo': shop.logo_url,
            'favicon': shop.logo_url,  # Utiliser le logo comme favicon
            'primary_color': '#007bff',  # À personnaliser par vendeur
            'secondary_color': '#6c757d',
            'footer_text': f'© {shop.name}. Tous droits réservés.',
            'contact_email': shop.support_email or shop.owner_email,
            'contact_phone': shop.support_phone,
            'address': shop.address,
            'facebook': shop.facebook_url,
            'whatsapp': shop.whatsapp_group_url or shop.whatsapp_number,
            'telegram': shop.telegram_url or f"https://t.me/{shop.telegram_username}" if shop.telegram_username else None,
        }
    
    @staticmethod
    def is_custom_domain(host):
        """
        Vérifie si le domaine actuel est un domaine personnalisé de boutique.
        """
        shop, subdomain = CustomDomainHandler.get_current_shop_by_domain()
        return shop is not None
    
    @staticmethod
    def build_shop_url(shop, include_protocol=True):
        """
        Construit l'URL d'une boutique (avec domaine personnalisé si présent).
        
        Exemples:
        - avec custom_domain: https://manianga-ngayo.com
        - sans custom_domain: https://tekanayo.com/manianga-ngayo-1
        """
        if not shop:
            return None
        
        base_url = request.url_root.rstrip('/') if not include_protocol else None
        
        if shop.custom_domain:
            # Avec domaine personnalisé
            if include_protocol:
                protocol = 'https' if request.is_secure else 'http'
                return f"{protocol}://{shop.custom_domain}"
            return shop.custom_domain
        else:
            # Sans domaine personnalisé (slug par défaut)
            if include_protocol:
                base = request.url_root.rstrip('/')
                return f"{base}/{shop.slug}"
            return shop.slug
    
    @staticmethod
    def get_shop_context_for_template(shop):
        """
        Retourne le contexte complet pour afficher une boutique
        comme un site indépendant.
        """
        if not shop:
            return {}
        
        return {
            'is_custom_domain': bool(shop.custom_domain),
            'shop_domain': shop.custom_domain,
            'shop_url': CustomDomainHandler.build_shop_url(shop),
            'shop_branding': CustomDomainHandler.get_shop_branding(shop),
            'has_custom_branding': True,  # Afficher le branding personnalisé
            'is_independent_site': bool(shop.custom_domain),  # Affichage comme site indépendant
        }

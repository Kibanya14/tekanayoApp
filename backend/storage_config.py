# Configuration Supabase Storage - Structure automatique des dossiers

import os
from typing import Dict, List, Optional
from enum import Enum

class BucketType(Enum):
    """Types de buckets disponibles"""
    UPLOADS = "uploads"

class FileCategory(Enum):
    """Catégories de fichiers avec leurs permissions"""
    SELLER_ID_DOC = "seller_id_document"
    SELLER_ADDRESS_DOC = "seller_address_document"
    PROFILE_PICTURE = "profile_picture"
    PRODUCT_IMAGE = "product_image"
    SHOP_LOGO = "shop_logo"
    PLATFORM_LOGO = "platform_logo"
    INVOICE = "invoice"

class FilePermissions(Enum):
    """Niveaux de permissions pour les fichiers"""
    PRIVATE = "private"  # Accessible seulement par admins
    SEMI_PRIVATE = "semi_private"  # Accessible par utilisateurs loggés
    PUBLIC = "public"  # Accessible par tout le monde

class StorageConfig:
    """Configuration centralisée du stockage Supabase"""

    # Structure des dossiers par catégorie
    FILE_STRUCTURE = {
        FileCategory.SELLER_ID_DOC: {
            "path": "private/seller_documents/id/{seller_id}/",
            "permissions": FilePermissions.PRIVATE,
            "max_size_mb": 5,
            "allowed_extensions": [".jpg", ".jpeg", ".png", ".pdf"]
        },
        FileCategory.SELLER_ADDRESS_DOC: {
            "path": "private/seller_documents/address/{seller_id}/",
            "permissions": FilePermissions.PRIVATE,
            "max_size_mb": 5,
            "allowed_extensions": [".jpg", ".jpeg", ".png", ".pdf"]
        },
        FileCategory.PROFILE_PICTURE: {
            "path": "public/profiles/{user_type}/{user_id}/",
            "permissions": FilePermissions.SEMI_PRIVATE,
            "max_size_mb": 2,
            "allowed_extensions": [".jpg", ".jpeg", ".png", ".webp"]
        },
        FileCategory.PRODUCT_IMAGE: {
            "path": "public/products/{seller_id}/",
            "permissions": FilePermissions.PUBLIC,
            "max_size_mb": 10,
            "allowed_extensions": [".jpg", ".jpeg", ".png", ".webp"]
        },
        FileCategory.SHOP_LOGO: {
            "path": "public/logos/shops/{seller_id}/",
            "permissions": FilePermissions.PUBLIC,
            "max_size_mb": 2,
            "allowed_extensions": [".jpg", ".jpeg", ".png", ".webp", ".svg"]
        },
        FileCategory.PLATFORM_LOGO: {
            "path": "public/logos/platform/",
            "permissions": FilePermissions.PUBLIC,
            "max_size_mb": 2,
            "allowed_extensions": [".jpg", ".jpeg", ".png", ".webp", ".svg"]
        },
        FileCategory.INVOICE: {
            "path": "private/invoices/{order_id}/",
            "permissions": FilePermissions.SEMI_PRIVATE,
            "max_size_mb": 1,
            "allowed_extensions": [".pdf"]
        }
    }

    @classmethod
    def get_file_config(cls, category: FileCategory) -> Dict:
        """Récupère la configuration pour une catégorie de fichier"""
        return cls.FILE_STRUCTURE.get(category, {})

    @classmethod
    def build_file_path(cls, category: FileCategory, **kwargs) -> str:
        """Construit le chemin complet du fichier avec les variables"""
        config = cls.get_file_config(category)
        if not config:
            raise ValueError(f"Catégorie {category} non trouvée")

        path_template = config["path"]

        # Remplacer les variables dans le template
        try:
            file_path = path_template.format(**kwargs)
        except KeyError as e:
            raise ValueError(f"Variable manquante pour {category}: {e}")

        # Ajouter timestamp + random pour unicité
        import time
        import secrets
        timestamp = time.strftime("%Y%m%d%H%M%S")
        random_hex = secrets.token_hex(8)
        filename = f"{timestamp}_{random_hex}"

        return f"{file_path}{filename}"

    @classmethod
    def get_permissions(cls, category: FileCategory) -> FilePermissions:
        """Récupère les permissions pour une catégorie"""
        config = cls.get_file_config(category)
        return config.get("permissions", FilePermissions.PRIVATE)

    @classmethod
    def validate_file(cls, file, category: FileCategory) -> Dict[str, any]:
        """Valide un fichier selon sa catégorie"""
        config = cls.get_file_config(category)
        if not config:
            return {"valid": False, "error": f"Catégorie {category} inconnue"}

        # Vérifier la taille
        max_size = config["max_size_mb"] * 1024 * 1024  # Convertir en bytes
        if file.content_length > max_size:
            return {"valid": False, "error": f"Fichier trop gros (max {config['max_size_mb']}MB)"}

        # Vérifier l'extension
        filename = file.filename.lower()
        allowed_ext = config["allowed_extensions"]
        if not any(filename.endswith(ext) for ext in allowed_ext):
            return {"valid": False, "error": f"Extension non autorisée. Utilisez: {', '.join(allowed_ext)}"}

        return {"valid": True, "config": config}

# Exemples d'utilisation dans le code
"""
# Pour uploader une pièce d'identité vendeur
config = StorageConfig.get_file_config(FileCategory.SELLER_ID_DOC)
path = StorageConfig.build_file_path(FileCategory.SELLER_ID_DOC, seller_id=123)
permissions = StorageConfig.get_permissions(FileCategory.SELLER_ID_DOC)

# Pour uploader une photo de profil
path = StorageConfig.build_file_path(FileCategory.PROFILE_PICTURE,
                                   user_type="seller_admin",
                                   user_id=456)

# Pour uploader une image produit
path = StorageConfig.build_file_path(FileCategory.PRODUCT_IMAGE,
                                   seller_id=123,
                                   product_id=789)
"""
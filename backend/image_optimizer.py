# Optimisation et redimensionnement d'images
# Utilise Pillow pour améliorer les performances

from PIL import Image, ImageOps
import io
from typing import Tuple, Optional, Dict
import os

class ImageOptimizer:
    """Optimiseur d'images pour améliorer les performances"""

    # Tailles recommandées pour différents usages
    SIZES = {
        'thumbnail': (150, 150),      # Miniatures
        'small': (300, 300),          # Petites images
        'medium': (600, 600),         # Images moyennes
        'large': (1200, 1200),        # Grandes images
        'original': None              # Taille originale (juste optimisation)
    }

    QUALITY_SETTINGS = {
        'thumbnail': 70,              # Compression forte pour miniatures
        'small': 80,                  # Bonne compression
        'medium': 85,                 # Qualité moyenne
        'large': 90,                  # Haute qualité
        'original': 95                # Qualité maximale
    }

    @staticmethod
    def optimize_image(image_data: bytes,
                      size_name: str = 'medium',
                      maintain_aspect: bool = True) -> bytes:
        """
        Optimise une image pour le web

        Args:
            image_data: Données binaires de l'image
            size_name: Taille souhaitée ('thumbnail', 'small', 'medium', 'large', 'original')
            maintain_aspect: Préserver les proportions

        Returns:
            Données optimisées de l'image
        """
        try:
            # Ouvrir l'image
            img = Image.open(io.BytesIO(image_data))

            # Convertir en RGB si nécessaire (pour JPEG)
            if img.mode in ('RGBA', 'LA', 'P'):
                # Créer un fond blanc pour les images transparentes
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'RGBA':
                    background.paste(img, mask=img.split()[-1])  # Utiliser le canal alpha comme masque
                else:
                    background.paste(img)
                img = background

            # Redimensionner si demandé
            if size_name != 'original' and size_name in ImageOptimizer.SIZES:
                target_size = ImageOptimizer.SIZES[size_name]
                if target_size:
                    if maintain_aspect:
                        img.thumbnail(target_size, Image.Resampling.LANCZOS)
                    else:
                        img = ImageOps.fit(img, target_size, Image.Resampling.LANCZOS)

            # Optimiser et compresser
            output = io.BytesIO()
            quality = ImageOptimizer.QUALITY_SETTINGS.get(size_name, 85)

            # Sauvegarder en JPEG pour la compression
            img.save(output, format='JPEG', quality=quality, optimize=True, progressive=True)
            output.seek(0)

            return output.getvalue()

        except Exception as e:
            # En cas d'erreur, retourner l'image originale
            print(f"Erreur optimisation image: {e}")
            return image_data

    @staticmethod
    def create_responsive_images(image_data: bytes) -> Dict[str, bytes]:
        """
        Crée plusieurs versions d'une image pour le responsive design

        Returns:
            Dict avec 'original', 'large', 'medium', 'small', 'thumbnail'
        """
        versions = {}

        for size_name in ['original', 'large', 'medium', 'small', 'thumbnail']:
            versions[size_name] = ImageOptimizer.optimize_image(image_data, size_name)

        return versions

    @staticmethod
    def get_image_info(image_data: bytes) -> Dict[str, any]:
        """
        Extrait les informations d'une image

        Returns:
            Dict avec width, height, format, size
        """
        try:
            img = Image.open(io.BytesIO(image_data))
            return {
                'width': img.width,
                'height': img.height,
                'format': img.format,
                'mode': img.mode,
                'size_bytes': len(image_data)
            }
        except Exception as e:
            return {
                'error': str(e),
                'size_bytes': len(image_data)
            }

# Fonctions utilitaires pour l'intégration
def optimize_product_image(image_data: bytes) -> bytes:
    """Optimise une image produit (taille medium par défaut)"""
    return ImageOptimizer.optimize_image(image_data, 'medium')

def create_product_thumbnails(image_data: bytes) -> Dict[str, bytes]:
    """Crée les différentes tailles pour une image produit"""
    return ImageOptimizer.create_responsive_images(image_data)

def optimize_profile_picture(image_data: bytes) -> bytes:
    """Optimise une photo de profil (taille small)"""
    return ImageOptimizer.optimize_image(image_data, 'small')

def optimize_logo(image_data: bytes) -> bytes:
    """Optimise un logo (conserve la qualité)"""
    return ImageOptimizer.optimize_image(image_data, 'original')
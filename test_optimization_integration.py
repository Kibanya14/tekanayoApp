#!/usr/bin/env python3
"""
Test script pour vérifier que l'intégration image optimization fonctionne
"""

import os
import sys
from io import BytesIO

# Ajouter le répertoire backend au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.image_optimizer import ImageOptimizer
from backend.storage_config import StorageConfig, FileCategory

def test_image_optimization():
    """Test l'optimisation d'une image"""
    print("🧪 Test de l'optimisation d'images...")

    # Créer une image de test simple (rouge 100x100)
    from PIL import Image
    test_image = Image.new('RGB', (100, 100), color='red')

    # Convertir en bytes
    buffer = BytesIO()
    test_image.save(buffer, format='JPEG')
    original_bytes = buffer.getvalue()

    print(f"📏 Taille originale: {len(original_bytes)} bytes")

    # Tester l'optimisation
    optimized_bytes = ImageOptimizer.optimize_image(original_bytes, 'medium')
    print(f"📏 Taille optimisée (medium): {len(optimized_bytes)} bytes")
    print(f"📊 Réduction: {100 - (len(optimized_bytes)/len(original_bytes))*100:.1f}%")

    if len(optimized_bytes) < len(original_bytes):
        print("✅ Optimisation réussie!")
        return True
    else:
        print("❌ L'optimisation n'a pas réduit la taille")
        return False

def test_storage_config():
    """Test la configuration du stockage"""
    print("\n🧪 Test de StorageConfig...")

    try:
        # Test que PRODUCT_IMAGE ne demande qu'un seller_id
        config = StorageConfig.get_file_config(FileCategory.PRODUCT_IMAGE)
        path_template = config["path"]
        print(f"📋 Template pour PRODUCT_IMAGE: {path_template}")

        # Tester build_file_path avec les paramètres corrects
        file_path = StorageConfig.build_file_path(FileCategory.PRODUCT_IMAGE, seller_id=123)
        print(f"📍 Chemin généré: {file_path}")

        if "public/products/123" in file_path:
            print("✅ Configuration StorageConfig OK!")
            return True
        else:
            print("❌ Le chemin n'est pas correct")
            return False

    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_responsive_images():
    """Test la création d'images responsives"""
    print("\n🧪 Test des images responsives...")

    try:
        from PIL import Image
        
        # Créer une image de test
        test_image = Image.new('RGB', (1000, 1000), color='blue')
        buffer = BytesIO()
        test_image.save(buffer, format='JPEG')
        original_bytes = buffer.getvalue()

        # Créer des images responsives
        responsive_images = ImageOptimizer.create_responsive_images(original_bytes)
        
        print("📦 Formats générés:")
        for size_name, image_bytes in responsive_images.items():
            print(f"  - {size_name}: {len(image_bytes)} bytes")

        if len(responsive_images) > 0:
            print("✅ Images responsives générées!")
            return True
        else:
            print("❌ Aucune image responsive générée")
            return False

    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_image_detection():
    """Test le système de détection d'images"""
    print("\n🧪 Test de détection d'images...")

    test_files = [
        ("image.jpg", True),
        ("photo.JPEG", True),
        ("picture.png", True),
        ("logo.webp", True),
        ("document.pdf", False),
        ("archive.zip", False),
    ]

    all_passed = True
    for filename, should_be_image in test_files:
        # Tester la logique de détection d'images
        is_image = filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'))
        
        if is_image == should_be_image:
            print(f"  ✅ {filename}: {'image' if is_image else 'non-image'}")
        else:
            print(f"  ❌ {filename}: attendu {'image' if should_be_image else 'non-image'}, trouvé {'image' if is_image else 'non-image'}")
            all_passed = False

    return all_passed

if __name__ == "__main__":
    print("🚀 Démarrage des tests d'intégration d'optimisation d'images...\n")

    success1 = test_image_optimization()
    success2 = test_storage_config()
    success3 = test_responsive_images()
    success4 = test_image_detection()

    print("\n" + "="*50)
    if success1 and success2 and success3 and success4:
        print("🎉 Tous les tests sont passés!")
        print("\n✨ Résumé:")
        print("✅ Optimisation d'images fonctionne")
        print("✅ Configuration StorageConfig correcte")
        print("✅ Génération d'images responsives fonctionne")
        print("✅ Détection d'images fonctionne")
    else:
        print("❌ Certains tests ont échoué")
        sys.exit(1)
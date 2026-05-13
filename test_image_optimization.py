#!/usr/bin/env python3
"""
Test script pour vérifier l'optimisation d'images avec Supabase Storage
"""

import os
import sys
from io import BytesIO

# Ajouter le répertoire backend au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.image_optimizer import ImageOptimizer

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
    print(f"📏 Taille optimisée: {len(optimized_bytes)} bytes")

    # Vérifier que c'est plus petit
    if len(optimized_bytes) < len(original_bytes):
        print("✅ Optimisation réussie!")
        return True
    else:
        print("❌ L'optimisation n'a pas réduit la taille")
        return False

def test_supabase_storage():
    """Test basique du client Supabase Storage"""
    print("\n🧪 Test du client Supabase Storage...")

    try:
        from backend.supabase_storage import storage_client
        print("✅ Client Supabase initialisé avec succès")
        return True
    except Exception as e:
        print(f"❌ Erreur d'initialisation Supabase: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Démarrage des tests d'optimisation d'images...\n")

    success1 = test_image_optimization()
    success2 = test_supabase_storage()

    if success1 and success2:
        print("\n🎉 Tous les tests sont passés!")
    else:
        print("\n❌ Certains tests ont échoué")
        sys.exit(1)
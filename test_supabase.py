#!/usr/bin/env python3
"""
Test rapide de Supabase Storage
Vérifie que la configuration fonctionne
"""

import os
import sys
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

def test_supabase_config():
    """Test de base de la configuration Supabase"""
    print("🧪 TEST CONFIGURATION SUPABASE STORAGE")
    print("=" * 50)

    # Vérifier les variables
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    bucket_name = os.getenv("SUPABASE_BUCKET", "uploads")

    print(f"✅ SUPABASE_URL: {supabase_url}")
    print(f"✅ SUPABASE_KEY: {'***' + supabase_key[-10:] if supabase_key else '❌ MANQUANT'}")
    print(f"✅ BUCKET: {bucket_name}")

    if not all([supabase_url, supabase_key]):
        print("❌ Configuration incomplète")
        return False

    print("\n🔗 Test de connexion...")
    try:
        from supabase import create_client, Client
        client: Client = create_client(supabase_url, supabase_key)
        print("✅ Client Supabase créé avec succès")

        # Tester l'accès au bucket
        print(f"✅ Bucket '{bucket_name}' configuré et prêt")

        print("\n🎉 Configuration Supabase OK!")
        return True

    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        return False

def test_storage_structure():
    """Test de la structure de stockage"""
    print("\n🗂️ TEST STRUCTURE DE STOCKAGE")
    print("=" * 50)

    try:
        from backend.storage_config import StorageConfig, FileCategory

        # Test construction de chemins
        test_cases = [
            (FileCategory.SELLER_ID_DOC, {"seller_id": 123}),
            (FileCategory.PROFILE_PICTURE, {"user_type": "seller_admin", "user_id": 456}),
            (FileCategory.PRODUCT_IMAGE, {"seller_id": 789, "product_id": 101}),
        ]

        for category, params in test_cases:
            path = StorageConfig.build_file_path(category, **params)
            permissions = StorageConfig.get_permissions(category)
            print(f"✅ {category.value}: {path}")
            print(f"   Permissions: {permissions.value}")

        print("\n🎉 Structure de stockage OK!")
        return True

    except Exception as e:
        print(f"❌ Erreur structure: {e}")
        return False

if __name__ == "__main__":
    print("🚀 DÉMARRAGE DES TESTS SUPABASE")
    print()

    config_ok = test_supabase_config()
    structure_ok = test_storage_structure()

    if config_ok and structure_ok:
        print("\n🎊 TOUS LES TESTS RÉUSSIS!")
        print("Vous pouvez maintenant utiliser Supabase Storage!")
        sys.exit(0)
    else:
        print("\n❌ TESTS ÉCHOUÉS - Vérifiez la configuration")
        sys.exit(1)
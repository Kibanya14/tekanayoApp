# Supabase Storage Helper - Upload automatique avec structure

import os
import secrets
import time
import tempfile
from typing import Dict, Optional, BinaryIO, List
from supabase import create_client, Client
from .storage_config import StorageConfig, FileCategory, FilePermissions, BucketType
from backend.antivirus import AntivirusScanner, validate_upload_safe
from backend.logger import StructuredLogger

class SupabaseStorage:
    """Helper pour gérer le stockage Supabase avec structure automatique"""

    def __init__(self):
        """Initialise le client Supabase"""
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        self.bucket_name = os.getenv("SUPABASE_BUCKET", "uploads")

        if not all([self.supabase_url, self.supabase_key]):
            raise ValueError("SUPABASE_URL et SUPABASE_SERVICE_ROLE_KEY requis")

        self.client: Client = create_client(self.supabase_url, self.supabase_key)

    def upload_file(self,
                   file: BinaryIO,
                   category: FileCategory,
                   optimize_image: bool = True,
                   **path_vars) -> Dict[str, any]:
        """
        Upload un fichier avec structure automatique

        Args:
            file: Objet fichier (Flask request.files)
            category: Catégorie du fichier (FileCategory)
            **path_vars: Variables pour le chemin (seller_id, user_id, etc.)

        Returns:
            Dict avec succès/erreur et chemin Supabase
        """
        try:
            # 1. Valider le fichier
            validation = StorageConfig.validate_file(file, category)
            if not validation["valid"]:
                return {
                    "success": False,
                    "error": validation["error"]
                }

            # 2. Construire le chemin
            file_path = StorageConfig.build_file_path(category, **path_vars)

            # 3. Ajouter l'extension du fichier original
            filename = file.filename.lower()
            if '.' in filename:
                extension = filename.split('.')[-1]
                file_path = f"{file_path}.{extension}"

            # 4. Upload vers Supabase
            file.seek(0)  # Reset file pointer
            file_content = file.read()

            temp_path = None
            try:
                suffix = os.path.splitext(file.filename or '')[1]
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(file_content)
                    temp_path = tmp.name

                scan_category = self._get_antivirus_category(category, file.filename)
                safe, message = validate_upload_safe(temp_path, scan_category)
                if not safe:
                    StructuredLogger().error(
                        "Antivirus upload rejected",
                        extra={
                            'file': file.filename,
                            'category': str(category),
                            'reason': message
                        }
                    )
                    return {
                        "success": False,
                        "error": f"Antivirus failed: {message}"
                    }
            finally:
                if temp_path and os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except Exception:
                        pass

            # 4.5. Optimiser l'image si demandé et si c'est une image
            if optimize_image and self._is_image_file(file.filename):
                from backend.image_optimizer import ImageOptimizer
                file_content = ImageOptimizer.optimize_image(file_content, 'medium')
                print(f"✅ Image optimisée: {len(file_content)} bytes")

            response = self.client.storage.from_(self.bucket_name).upload(
                path=file_path,
                file=file_content,
                file_options={
                    "content-type": file.content_type or "application/octet-stream",
                    "cache-control": "3600"  # Cache 1 heure
                }
            )

            if response.status_code == 200:
                # 5. Générer l'URL publique si nécessaire
                permissions = StorageConfig.get_permissions(category)
                public_url = None

                StructuredLogger().info(
                    "Supabase upload succeeded",
                    extra={
                        'file': file.filename,
                        'path': file_path,
                        'category': str(category),
                        'size_mb': len(file_content) / (1024 * 1024)
                    }
                )

                if permissions == FilePermissions.PUBLIC:
                    public_url = self.get_public_url(file_path)
                elif permissions == FilePermissions.SEMI_PRIVATE:
                    # URL signée pour utilisateurs loggés (1 heure)
                    public_url = self.get_signed_url(file_path, expires_in=3600)

                return {
                    "success": True,
                    "path": file_path,
                    "public_url": public_url,
                    "permissions": permissions.value,
                    "bucket": self.bucket_name,
                    "optimized": optimize_image and self._is_image_file(file.filename)
                }
            else:
                return {
                    "success": False,
                    "error": f"Upload échoué: {response.json()}"
                }

        except Exception as e:
            return {
                "success": False,
                "error": f"Erreur upload: {str(e)}"
            }

    def get_public_url(self, file_path: str) -> str:
        """Génère une URL publique pour un fichier"""
        return self.client.storage.from_(self.bucket_name).get_public_url(file_path)

    def get_signed_url(self, file_path: str, expires_in: int = 3600) -> str:
        """Génère une URL signée temporaire"""
        try:
            response = self.client.storage.from_(self.bucket_name).create_signed_url(
                path=file_path,
                expires_in=expires_in
            )
            return response.get("signedURL", "")
        except Exception:
            return ""

    def delete_file(self, file_path: str) -> bool:
        """Supprime un fichier"""
        try:
            response = self.client.storage.from_(self.bucket_name).remove([file_path])
            return response.status_code == 200
        except Exception:
            return False

    def list_files(self, path_prefix: str) -> List[str]:
        """Liste les fichiers dans un dossier"""
        try:
            response = self.client.storage.from_(self.bucket_name).list(path=path_prefix)
            return [item["name"] for item in response] if response else []
        except Exception:
            return []

    def _is_image_file(self, filename: str) -> bool:
        """Vérifie si le fichier est une image"""
        if not filename:
            return False
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
        return any(filename.lower().endswith(ext) for ext in image_extensions)

# Instance globale
storage_client = SupabaseStorage()

# Fonctions utilitaires pour remplacer l'ancien système
def upload_seller_document(file, doc_type: str, seller_id: int) -> Dict[str, any]:
    """Upload document vendeur (ID ou address)"""
    category = {
        "id": FileCategory.SELLER_ID_DOC,
        "address": FileCategory.SELLER_ADDRESS_DOC
    }.get(doc_type)

    if not category:
        return {"success": False, "error": "Type de document invalide"}

    return storage_client.upload_file(file, category, seller_id=seller_id)

def upload_profile_picture(file, user_type: str, user_id: int) -> Dict[str, any]:
    """Upload photo de profil"""
    return storage_client.upload_file(
        file,
        FileCategory.PROFILE_PICTURE,
        user_type=user_type,
        user_id=user_id
    )

def upload_product_image(file, seller_id: int, product_id: int) -> Dict[str, any]:
    """Upload image produit"""
    return storage_client.upload_file(
        file,
        FileCategory.PRODUCT_IMAGE,
        seller_id=seller_id,
        product_id=product_id
    )

def upload_shop_logo(file, seller_id: int) -> Dict[str, any]:
    """Upload logo boutique"""
    return storage_client.upload_file(
        file,
        FileCategory.SHOP_LOGO,
        seller_id=seller_id
    )

def upload_platform_logo(file) -> Dict[str, any]:
    """Upload logo plateforme"""
    return storage_client.upload_file(file, FileCategory.PLATFORM_LOGO)

def upload_invoice(pdf_content: bytes, order_id: int) -> Dict[str, any]:
    """Upload facture PDF"""
    # Créer un objet fichier-like pour le PDF
    from io import BytesIO
    file_obj = BytesIO(pdf_content)
    file_obj.filename = f"invoice_{order_id}.pdf"
    file_obj.content_type = "application/pdf"
    file_obj.content_length = len(pdf_content)

    return storage_client.upload_file(
        file_obj,
        FileCategory.INVOICE,
        order_id=order_id
    )

# Exemples d'utilisation
"""
# Dans vos routes Flask :

from backend.supabase_storage import upload_seller_document, upload_profile_picture

@app.route('/upload/seller/document', methods=['POST'])
@login_required
def upload_seller_doc():
    file = request.files['document']
    doc_type = request.form['type']  # 'id' ou 'address'

    result = upload_seller_document(file, doc_type, current_user.seller_id)

    if result['success']:
        # Sauvegarder le path en BD
        seller = SellerShop.query.get(current_user.seller_id)
        if doc_type == 'id':
            seller.id_document_path = result['path']
        else:
            seller.address_document_path = result['path']
        db.session.commit()

        return jsonify({"message": "Document uploadé", "path": result['path']})
    else:
        return jsonify({"error": result['error']}), 400
"""
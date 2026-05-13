"""
Antivirus module for document scanning
Supports ClamAV and file validation
"""

import os
import hashlib
import mimetypes
from datetime import datetime
from typing import Dict, Tuple, Optional
from pathlib import Path

class AntivirusScanner:
    """Scanner pour documents et images pour détecter les menaces"""

    # Signatures de fichiers dangereux
    DANGEROUS_SIGNATURES = {
        b'MZ': ('executable', '.exe', 'Windows executable'),
        b'PK\x03\x04': ('archive', '.zip', 'ZIP archive'),
        b'\x1f\x8b\x08': ('archive', '.gz', 'Gzip archive'),
        b'7z\xBC\xAF': ('archive', '.7z', '7z archive'),
    }

    # Extensions autorisées par catégorie
    ALLOWED_EXTENSIONS = {
        'documents': {'.pdf', '.doc', '.docx', '.xls', '.xlsx', '.txt', '.csv'},
        'images': {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp'},
        'videos': {'.mp4', '.avi', '.mov', '.mkv'},
    }

    # Taille max par type (en MB)
    MAX_SIZES = {
        'documents': 10,
        'images': 10,
        'videos': 500,
    }

    @classmethod
    def scan_file(cls, file_path: str, file_category: str = 'documents') -> Dict:
        """
        Scan un fichier pour déterminer les risques de sécurité
        
        Args:
            file_path: Chemin du fichier
            file_category: Catégorie du fichier (documents, images, videos)
            
        Returns:
            Dict with 'safe' (bool), 'threats' (list), 'details' (str)
        """
        if not os.path.exists(file_path):
            return {
                'safe': False,
                'threats': ['FILE_NOT_FOUND'],
                'details': f'Fichier non trouvé: {file_path}'
            }

        results = {
            'safe': True,
            'threats': [],
            'details': '',
            'file_info': {
                'name': os.path.basename(file_path),
                'size_mb': os.path.getsize(file_path) / (1024 * 1024),
                'timestamp': datetime.utcnow().isoformat()
            }
        }

        # 1. Vérifier l'extension
        ext_check = cls._check_extension(file_path, file_category)
        if not ext_check['valid']:
            results['safe'] = False
            results['threats'].append(ext_check['threat'])
            results['details'] += ext_check['reason'] + ' | '

        # 2. Vérifier la taille
        size_check = cls._check_size(file_path, file_category)
        if not size_check['valid']:
            results['safe'] = False
            results['threats'].append(size_check['threat'])
            results['details'] += size_check['reason'] + ' | '

        # 3. Scan signature
        sig_check = cls._scan_signature(file_path)
        if not sig_check['valid']:
            results['safe'] = False
            results['threats'].append(sig_check['threat'])
            results['details'] += sig_check['reason'] + ' | '

        # 4. Scan ClamAV si disponible
        if os.getenv('ANTIVIRUS_ENABLED', 'False').lower() == 'true':
            clamav_check = cls._scan_clamav(file_path)
            if not clamav_check['valid']:
                results['safe'] = False
                results['threats'].append(clamav_check['threat'])
                results['details'] += clamav_check['reason'] + ' | '

        # 5. Mime type validation
        mime_check = cls._check_mime_type(file_path, file_category)
        if not mime_check['valid']:
            results['safe'] = False
            results['threats'].append(mime_check['threat'])
            results['details'] += mime_check['reason'] + ' | '

        results['details'] = results['details'].rstrip(' | ')
        
        return results

    @classmethod
    def _check_extension(cls, file_path: str, category: str) -> Dict:
        """Vérifier l'extension du fichier"""
        ext = Path(file_path).suffix.lower()
        allowed = cls.ALLOWED_EXTENSIONS.get(category, set())

        if ext not in allowed:
            return {
                'valid': False,
                'threat': 'INVALID_EXTENSION',
                'reason': f'Extension {ext} non autorisée pour {category}'
            }

        return {'valid': True}

    @classmethod
    def _check_size(cls, file_path: str, category: str) -> Dict:
        """Vérifier la taille du fichier"""
        max_mb = cls.MAX_SIZES.get(category, 10)
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)

        if file_size_mb > max_mb:
            return {
                'valid': False,
                'threat': 'FILE_TOO_LARGE',
                'reason': f'Fichier de {file_size_mb:.1f}MB > max {max_mb}MB'
            }

        return {'valid': True}

    @classmethod
    def _scan_signature(cls, file_path: str) -> Dict:
        """Scanner les signatures dangereuses (magic numbers)"""
        try:
            with open(file_path, 'rb') as f:
                header = f.read(512)  # Lire les premiers 512 bytes

            # Chercher des signatures dangereuses
            for signature, (threat_type, ext, description) in cls.DANGEROUS_SIGNATURES.items():
                if header.startswith(signature):
                    return {
                        'valid': False,
                        'threat': 'DANGEROUS_SIGNATURE',
                        'reason': f'Signature dangereuse détectée: {description}'
                    }

            return {'valid': True}
            
        except Exception as e:
            return {
                'valid': False,
                'threat': 'SCAN_ERROR',
                'reason': f'Erreur signature scan: {str(e)}'
            }

    @classmethod
    def _check_mime_type(cls, file_path: str, category: str) -> Dict:
        """Vérifier le MIME type du fichier"""
        mime_type, _ = mimetypes.guess_type(file_path)

        # Mapping des MIME types autorisés
        allowed_mimes = {
            'documents': {
                'application/pdf',
                'application/msword',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'application/vnd.ms-excel',
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                'text/plain',
                'text/csv',
            },
            'images': {
                'image/jpeg',
                'image/png',
                'image/webp',
                'image/gif',
                'image/bmp',
            },
            'videos': {
                'video/mp4',
                'video/x-msvideo',
                'video/quicktime',
                'video/x-matroska',
            }
        }

        if mime_type not in allowed_mimes.get(category, set()):
            return {
                'valid': False,
                'threat': 'INVALID_MIME_TYPE',
                'reason': f'MIME type {mime_type} non autorisé pour {category}'
            }

        return {'valid': True}

    @classmethod
    def _scan_clamav(cls, file_path: str) -> Dict:
        """Scanner avec ClamAV s'il est disponible"""
        try:
            import pyclamd
            
            clam_host = os.getenv('CLAMAV_HOST', 'localhost')
            clam_port = int(os.getenv('CLAMAV_PORT', '3310'))
            
            # Essayer de se connecter à ClamAV
            clam = pyclamd.ClamdNetworkSocket(clam_host, clam_port)
            
            if not clam.ping():
                return {
                    'valid': True,
                    'reason': 'ClamAV non disponible, skip scan'
                }

            # Scan le fichier
            result = clam.scan_file(file_path)
            
            if result:
                # Fichier infecté
                return {
                    'valid': False,
                    'threat': 'VIRUS_DETECTED',
                    'reason': f'Virus détecté par ClamAV: {result}'
                }

            return {'valid': True}
            
        except ImportError:
            # pyclamd pas installé, skip ClamAV
            return {'valid': True}
        except Exception as e:
            print(f"⚠️ Erreur ClamAV scan: {str(e)}")
            return {'valid': True, 'reason': f'ClamAV error: {str(e)}'}

    @classmethod
    def calculate_file_hash(cls, file_path: str, algorithm: str = 'sha256') -> str:
        """Calculer le hash d'un fichier pour intégrité"""
        hasher = hashlib.new(algorithm)
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hasher.update(chunk)
        
        return hasher.hexdigest()

    @classmethod
    def quarantine_file(cls, file_path: str, quarantine_dir: str = './quarantine') -> bool:
        """Mettre en quarantine un fichier suspect"""
        try:
            os.makedirs(quarantine_dir, exist_ok=True)
            
            filename = os.path.basename(file_path)
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            quarantine_path = os.path.join(quarantine_dir, f'{timestamp}_{filename}')
            
            os.rename(file_path, quarantine_path)
            
            print(f"⚠️ Fichier mis en quarantine: {quarantine_path}")
            return True
            
        except Exception as e:
            print(f"❌ Erreur quarantine: {str(e)}")
            return False


# Helper function pour integration avec Supabase
def validate_upload_safe(file_path: str, file_category: str = 'documents') -> Tuple[bool, str]:
    """
    Validate si un fichier uploadé est sûr
    
    Returns:
        (is_safe: bool, message: str)
    """
    result = AntivirusScanner.scan_file(file_path, file_category)
    
    if not result['safe']:
        threat_list = ', '.join(result['threats'])
        message = f"⚠️ Fichier non sûr - Menaces: {threat_list}. {result['details']}"
        
        # Mettre en quarantine
        AntivirusScanner.quarantine_file(file_path)
        
        return False, message
    
    return True, "✅ Fichier sûr"

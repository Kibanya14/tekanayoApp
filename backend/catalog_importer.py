"""
Module de gestion de l'importation de catalogue
Supporte les formats : CSV, XLSX, JSON
"""

import csv
import io
import json
import secrets
from datetime import datetime
from typing import List, Dict, Tuple, Any

import openpyxl
from werkzeug.datastructures import FileStorage

from backend.models import db, SellerProduct, SellerShop


class CatalogImportError(Exception):
    """Exception pour les erreurs d'import de catalogue"""
    pass


class CatalogImporter:
    """
    Classe pour gérer l'importation de catalogue
    Supporte CSV, XLSX, JSON
    """
    
    # Colonnes attendues (mappages flexibles)
    REQUIRED_FIELDS = {"name", "category", "price"}
    OPTIONAL_FIELDS = {
        "description", "quantity", "image_url", "sku",
        "compare_price", "is_promoted", "is_active"
    }
    ALL_FIELDS = REQUIRED_FIELDS | OPTIONAL_FIELDS
    
    # Limites
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_ROWS = 5000
    MAX_DESCRIPTION_LENGTH = 1000
    MAX_SKU_LENGTH = 100
    
    def __init__(self, shop: SellerShop):
        self.shop = shop
        self.import_batch_id = f"batch_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{secrets.token_hex(4)}"
        self.import_results = {
            "total_rows": 0,
            "successful": 0,
            "failed": 0,
            "skipped": 0,
            "errors": [],
            "warnings": [],
            "batch_id": self.import_batch_id,
            "created_products": [],
            "updated_products": [],
            "conflicted_products": [],
        }
    
    def import_file(self, file: FileStorage) -> Dict[str, Any]:
        """
        Importe un fichier de catalogue
        
        Args:
            file: Fichier uploadé (CSV, XLSX, ou JSON)
            
        Returns:
            Dictionnaire avec les résultats d'import
        """
        try:
            # Vérifier la taille du fichier
            file.seek(0, 2)
            file_size = file.tell()
            file.seek(0)
            
            if file_size > self.MAX_FILE_SIZE:
                raise CatalogImportError(f"Fichier trop volumineux (max {self.MAX_FILE_SIZE / 1024 / 1024}MB)")
            
            # Déterminer le format du fichier
            filename = file.filename or ""
            
            if filename.endswith(".csv"):
                rows = self._parse_csv(file)
            elif filename.endswith(".xlsx"):
                rows = self._parse_xlsx(file)
            elif filename.endswith(".json"):
                rows = self._parse_json(file)
            else:
                raise CatalogImportError("Format de fichier non supporté. Utilisez CSV, XLSX ou JSON.")
            
            # Traiter les lignes
            self._process_rows(rows)
            
            return self.import_results
            
        except CatalogImportError as e:
            self.import_results["errors"].append(str(e))
            return self.import_results
        except Exception as e:
            self.import_results["errors"].append(f"Erreur d'import : {str(e)}")
            return self.import_results
    
    def _parse_csv(self, file: FileStorage) -> List[Dict[str, str]]:
        """Parse un fichier CSV"""
        try:
            file.seek(0)
            # Détecter l'encodage
            content = file.read()
            
            try:
                text = content.decode('utf-8')
            except UnicodeDecodeError:
                text = content.decode('latin-1')
            
            file.seek(0)
            reader = csv.DictReader(io.StringIO(text))
            
            if not reader.fieldnames:
                raise CatalogImportError("Le fichier CSV est vide ou mal formaté")
            
            rows = []
            for idx, row in enumerate(reader, start=2):  # start=2 car la ligne 1 est l'en-tête
                if idx > self.MAX_ROWS + 1:  # +1 pour l'en-tête
                    self.import_results["warnings"].append(
                        f"Import limité à {self.MAX_ROWS} lignes. {idx - self.MAX_ROWS - 1} lignes ignorées."
                    )
                    break
                
                # Nettoyer les clés (minuscules, sans espaces)
                cleaned_row = {k.strip().lower(): v.strip() if v else "" for k, v in row.items()}
                if any(cleaned_row.values()):  # Ignorer les lignes vides
                    rows.append(cleaned_row)
            
            self.import_results["total_rows"] = len(rows)
            return rows
            
        except Exception as e:
            raise CatalogImportError(f"Erreur lors du parsing CSV : {str(e)}")
    
    def _parse_xlsx(self, file: FileStorage) -> List[Dict[str, str]]:
        """Parse un fichier XLSX"""
        try:
            file.seek(0)
            workbook = openpyxl.load_workbook(file, data_only=True)
            worksheet = workbook.active
            
            rows = []
            headers = None
            
            for idx, row in enumerate(worksheet.iter_rows(values_only=True), start=1):
                if idx > self.MAX_ROWS + 1:
                    self.import_results["warnings"].append(
                        f"Import limité à {self.MAX_ROWS} lignes. {idx - self.MAX_ROWS - 1} lignes ignorées."
                    )
                    break
                
                if idx == 1:  # En-têtes
                    headers = [str(h).strip().lower() if h else "" for h in row]
                    continue
                
                if not headers:
                    raise CatalogImportError("En-têtes manquants dans le fichier XLSX")
                
                # Créer un dictionnaire pour cette ligne
                row_dict = {}
                for header, value in zip(headers, row):
                    if header and value is not None:
                        row_dict[header] = str(value).strip()
                
                if any(row_dict.values()):  # Ignorer les lignes vides
                    rows.append(row_dict)
            
            self.import_results["total_rows"] = len(rows)
            return rows
            
        except Exception as e:
            raise CatalogImportError(f"Erreur lors du parsing XLSX : {str(e)}")
    
    def _parse_json(self, file: FileStorage) -> List[Dict[str, str]]:
        """Parse un fichier JSON"""
        try:
            file.seek(0)
            data = json.load(file)
            
            if not isinstance(data, list):
                raise CatalogImportError("Le fichier JSON doit contenir un tableau d'objets")
            
            rows = []
            for idx, item in enumerate(data, start=1):
                if idx > self.MAX_ROWS:
                    self.import_results["warnings"].append(
                        f"Import limité à {self.MAX_ROWS} lignes. {idx - self.MAX_ROWS} lignes ignorées."
                    )
                    break
                
                if not isinstance(item, dict):
                    self.import_results["warnings"].append(f"Ligne {idx + 1} : format invalide (ignorée)")
                    continue
                
                # Nettoyer les clés
                cleaned_row = {k.strip().lower(): str(v).strip() if v else "" for k, v in item.items()}
                if any(cleaned_row.values()):
                    rows.append(cleaned_row)
            
            self.import_results["total_rows"] = len(rows)
            return rows
            
        except json.JSONDecodeError as e:
            raise CatalogImportError(f"Erreur JSON : {str(e)}")
        except Exception as e:
            raise CatalogImportError(f"Erreur lors du parsing JSON : {str(e)}")
    
    def _process_rows(self, rows: List[Dict[str, str]]) -> None:
        """Traite chaque ligne et crée/met à jour les produits"""
        for idx, row in enumerate(rows, start=2):
            try:
                # Valider la ligne
                errors = self._validate_row(row)
                if errors:
                    self.import_results["failed"] += 1
                    self.import_results["errors"].append(f"Ligne {idx}: {'; '.join(errors)}")
                    continue
                
                # Préparer les données du produit
                product_data = self._prepare_product_data(row)
                
                # Vérifier si le produit existe (par SKU ou nom+catégorie)
                existing_product = self._find_existing_product(product_data)
                
                if existing_product:
                    # Mettre à jour le produit existant
                    self._update_product(existing_product, product_data)
                    self.import_results["successful"] += 1
                    self.import_results["updated_products"].append({
                        "id": existing_product.id,
                        "name": existing_product.name,
                    })
                else:
                    # Créer un nouveau produit
                    product = self._create_product(product_data)
                    self.import_results["successful"] += 1
                    self.import_results["created_products"].append({
                        "id": product.id,
                        "name": product.name,
                    })
                
            except Exception as e:
                self.import_results["failed"] += 1
                self.import_results["errors"].append(f"Ligne {idx}: {str(e)}")
        
        # Commit des changements
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            self.import_results["errors"].append(f"Erreur lors de la sauvegarde : {str(e)}")
            self.import_results["successful"] = 0
    
    def _validate_row(self, row: Dict[str, str]) -> List[str]:
        """Valide une ligne de données"""
        errors = []
        
        # Vérifier les champs requis
        for field in self.REQUIRED_FIELDS:
            if field not in row or not row[field]:
                errors.append(f"Champ requis manquant : {field}")
        
        if errors:
            return errors
        
        # Valider le nom
        name = row.get("name", "").strip()
        if len(name) < 2 or len(name) > 200:
            errors.append("Le nom doit contenir entre 2 et 200 caractères")
        
        # Valider la catégorie
        category = row.get("category", "").strip()
        if len(category) < 1 or len(category) > 100:
            errors.append("La catégorie doit contenir entre 1 et 100 caractères")
        
        # Valider le prix
        try:
            price = float(row.get("price", 0))
            if price < 0:
                errors.append("Le prix ne peut pas être négatif")
        except ValueError:
            errors.append("Le prix doit être un nombre valide")
        
        # Valider la quantité (optionnel)
        if "quantity" in row and row["quantity"]:
            try:
                qty = int(row["quantity"])
                if qty < 0:
                    errors.append("La quantité ne peut pas être négative")
            except ValueError:
                errors.append("La quantité doit être un nombre entier")
        
        # Valider le SKU (optionnel, doit être unique)
        if "sku" in row and row["sku"]:
            sku = row["sku"].strip()
            if len(sku) > self.MAX_SKU_LENGTH:
                errors.append(f"Le SKU ne doit pas dépasser {self.MAX_SKU_LENGTH} caractères")
            
            # Vérifier l'unicité du SKU
            existing = SellerProduct.query.filter(
                SellerProduct.sku == sku,
                SellerProduct.shop_id == self.shop.id
            ).first()
            if existing:
                errors.append(f"SKU '{sku}' existe déjà")
        
        # Valider la description (optionnel)
        if "description" in row and row["description"]:
            desc = row["description"].strip()
            if len(desc) > self.MAX_DESCRIPTION_LENGTH:
                errors.append(f"La description ne doit pas dépasser {self.MAX_DESCRIPTION_LENGTH} caractères")
        
        # Valider compare_price (optionnel)
        if "compare_price" in row and row["compare_price"]:
            try:
                compare_price = float(row["compare_price"])
                if compare_price < 0:
                    errors.append("Le prix de comparaison ne peut pas être négatif")
            except ValueError:
                errors.append("Le prix de comparaison doit être un nombre valide")
        
        return errors
    
    def _prepare_product_data(self, row: Dict[str, str]) -> Dict[str, Any]:
        """Prépare les données du produit pour création/mise à jour"""
        data = {
            "name": row.get("name", "").strip(),
            "category": row.get("category", "").strip(),
            "description": row.get("description", "").strip()[:self.MAX_DESCRIPTION_LENGTH] or None,
            "price": float(row.get("price", 0)),
            "quantity": int(row.get("quantity", 0)) if row.get("quantity") else 0,
            "image_url": row.get("image_url", "").strip() or None,
            "sku": row.get("sku", "").strip()[:self.MAX_SKU_LENGTH] or None,
            "compare_price": float(row.get("compare_price")) if row.get("compare_price") else None,
            "is_promoted": self._parse_bool(row.get("is_promoted")),
            "is_active": self._parse_bool(row.get("is_active", "true")),
            "is_featured": self._parse_bool(row.get("is_featured")),
            "import_batch_id": self.import_batch_id,
        }
        return data
    
    def _parse_bool(self, value: str) -> bool:
        """Parse une valeur booléenne depuis une chaîne"""
        if not value:
            return False
        return value.strip().lower() in {"true", "1", "yes", "oui", "vrai"}
    
    def _find_existing_product(self, product_data: Dict[str, Any]) -> Any:
        """Cherche un produit existant par SKU ou nom+catégorie"""
        # Par SKU si disponible
        if product_data["sku"]:
            product = SellerProduct.query.filter(
                SellerProduct.shop_id == self.shop.id,
                SellerProduct.sku == product_data["sku"]
            ).first()
            if product:
                return product
        
        # Par nom + catégorie
        product = SellerProduct.query.filter(
            SellerProduct.shop_id == self.shop.id,
            SellerProduct.name == product_data["name"],
            SellerProduct.category == product_data["category"]
        ).first()
        
        return product
    
    def _create_product(self, product_data: Dict[str, Any]) -> SellerProduct:
        """Crée un nouveau produit"""
        product = SellerProduct(
            shop_id=self.shop.id,
            **product_data
        )
        db.session.add(product)
        db.session.flush()  # Pour obtenir l'ID
        return product
    
    def _update_product(self, product: SellerProduct, product_data: Dict[str, Any]) -> None:
        """Met à jour un produit existant"""
        for key, value in product_data.items():
            if key != "import_batch_id":  # Ne pas mettre à jour le batch_id d'origine
                setattr(product, key, value)
        
        product.updated_at = datetime.utcnow()
        db.session.add(product)


class CatalogExporter:
    """
    Classe pour exporter le catalogue
    """
    
    @staticmethod
    def export_to_csv(shop: SellerShop) -> str:
        """Exporte le catalogue en CSV"""
        products = SellerProduct.query.filter_by(shop_id=shop.id).all()
        
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=[
            "name", "category", "description", "price", "compare_price",
            "quantity", "sku", "image_url", "is_promoted", "is_active", "is_featured"
        ])
        
        writer.writeheader()
        for product in products:
            writer.writerow({
                "name": product.name,
                "category": product.category,
                "description": product.description or "",
                "price": product.price,
                "compare_price": product.compare_price or "",
                "quantity": product.quantity,
                "sku": product.sku or "",
                "image_url": product.image_url or "",
                "is_promoted": "true" if product.is_promoted else "false",
                "is_active": "true" if product.is_active else "false",
                "is_featured": "true" if product.is_featured else "false",
            })
        
        return output.getvalue()
    
    @staticmethod
    def export_to_json(shop: SellerShop) -> str:
        """Exporte le catalogue en JSON"""
        products = SellerProduct.query.filter_by(shop_id=shop.id).all()
        
        data = []
        for product in products:
            data.append({
                "name": product.name,
                "category": product.category,
                "description": product.description,
                "price": product.price,
                "compare_price": product.compare_price,
                "quantity": product.quantity,
                "sku": product.sku,
                "image_url": product.image_url,
                "is_promoted": product.is_promoted,
                "is_active": product.is_active,
                "is_featured": product.is_featured,
            })
        
        return json.dumps(data, indent=2, ensure_ascii=False)

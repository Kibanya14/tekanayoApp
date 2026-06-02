"""
Module de gestion de l'importation de catalogue
Supporte les formats : CSV, XLSX, JSON
"""

import csv
import io
import json
import secrets
import os
import re
import unicodedata
from datetime import datetime
from typing import List, Dict, Tuple, Any

import openpyxl
from werkzeug.datastructures import FileStorage

from backend.models import db, SellerProduct, SellerShop, Category


class CatalogImportError(Exception):
    """Exception pour les erreurs d'import de catalogue"""
    pass


class CatalogImporter:
    """
    Classe pour gérer l'importation de catalogue
    Supporte CSV, XLSX, JSON
    """
    
    # Colonnes attendues (mappages flexibles)
    REQUIRED_FIELDS = {"name", "price"}
    OPTIONAL_FIELDS = {
        "description", "quantity", "image_url", "sku",
        "compare_price", "is_promoted", "is_active", "is_featured", "category", "category_id"
    }
    ALL_FIELDS = REQUIRED_FIELDS | OPTIONAL_FIELDS
    
    # Limites
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB (aligné avec l'UI)
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
            "categories": [],
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
                raise CatalogImportError(
                    f"Fichier trop volumineux ({file_size/1024/1024:.2f}MB > {self.MAX_FILE_SIZE/1024/1024:.0f}MB). "
                    "Réduisez la taille du fichier ou contactez l'administrateur."
                )
            
            # Déterminer le format du fichier
            filename = file.filename or ""
            
            ext = os.path.splitext(filename.lower())[1]
            if ext == ".csv":
                rows = self._parse_csv(file)
            elif ext in {".xlsx", ".xlsm", ".xltx", ".xltm"}:
                rows = self._parse_xlsx(file)
            elif ext == ".json":
                rows = self._parse_json(file)
            elif ext in {".docx", ".pdf", ".txt", ".tsv"}:
                rows = self._parse_legacy_supported_file(file)
            else:
                raise CatalogImportError("Format de fichier non supporté. Utilisez CSV, XLSX, JSON, DOCX, PDF, TXT ou TSV.")
            
            # Recueillir les catégories avant de créer les produits
            self.import_results["categories"] = self._collect_categories(rows)
            self._ensure_categories(self.import_results["categories"])
            self.import_results["category_count"] = len(self.import_results["categories"])

            self._warn_about_headers(rows)

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
            sample = "\n".join(text.splitlines()[:5])
            try:
                dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
            except Exception:
                dialect = csv.excel
            reader = csv.DictReader(io.StringIO(text), dialect=dialect)
            if reader.fieldnames and len(reader.fieldnames) == 1:
                alt_delimiter = None
                if ";" in reader.fieldnames[0]:
                    alt_delimiter = ";"
                elif "\t" in reader.fieldnames[0]:
                    alt_delimiter = "\t"
                elif "|" in reader.fieldnames[0]:
                    alt_delimiter = "|"
                if alt_delimiter:
                    reader = csv.DictReader(io.StringIO(text), delimiter=alt_delimiter)
                    self.import_results["warnings"].append(
                        "Séparateur détecté manuellement pour le CSV. Vérifiez les colonnes et relancez si nécessaire."
                    )
            
            if not reader.fieldnames:
                raise CatalogImportError("Le fichier CSV est vide ou mal formaté")
            
            rows = []
            for idx, row in enumerate(reader, start=2):  # start=2 car la ligne 1 est l'en-tête
                if idx > self.MAX_ROWS + 1:  # +1 pour l'en-tête
                    self.import_results["warnings"].append(
                        f"Import limité à {self.MAX_ROWS} lignes. {idx - self.MAX_ROWS - 1} lignes ignorées."
                    )
                    break
                
                cleaned_row = self._clean_and_filter_row(row)
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
                    headers = [self._normalize_field_name(str(h)) if h else "" for h in row]
                    self._warn_about_raw_headers([str(h) for h in row if h is not None])
                    continue
                
                if not headers:
                    raise CatalogImportError("En-têtes manquants dans le fichier XLSX")
                
                # Créer un dictionnaire pour cette ligne
                raw_row = {}
                for header, value in zip(headers, row):
                    if header and value is not None:
                        raw_row[header] = str(value).strip()
                cleaned_row = self._clean_and_filter_row(raw_row)
                if any(cleaned_row.values()):  # Ignorer les lignes vides
                    rows.append(cleaned_row)
            
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
                if idx == 1 and isinstance(item, dict):
                    self._warn_about_raw_headers(list(item.keys()))
                if idx > self.MAX_ROWS:
                    self.import_results["warnings"].append(
                        f"Import limité à {self.MAX_ROWS} lignes. {idx - self.MAX_ROWS} lignes ignorées."
                    )
                    break
                
                if not isinstance(item, dict):
                    self.import_results["warnings"].append(f"Ligne {idx + 1} : format invalide (ignorée)")
                    continue
                
                cleaned_row = self._clean_and_filter_row(item)
                if any(cleaned_row.values()):
                    rows.append(cleaned_row)
            
            self.import_results["total_rows"] = len(rows)
            return rows
            
        except json.JSONDecodeError as e:
            raise CatalogImportError(f"Erreur JSON : {str(e)}")
        except Exception as e:
            raise CatalogImportError(f"Erreur lors du parsing JSON : {str(e)}")

    def _parse_legacy_supported_file(self, file: FileStorage) -> List[Dict[str, str]]:
        """Parse les formats additionnels conservés par l'ancien importeur."""
        try:
            from backend.catalog_import_manager import CatalogImportManager

            file.seek(0)
            headers, rows = CatalogImportManager.parse_file(file)
            if not headers or not rows:
                raise CatalogImportError("Fichier vide ou format non reconnu")

            parsed_rows = []
            if rows:
                self._warn_about_raw_headers([k for k in (rows[0] or {}).keys() if k is not None])
            for row in rows[:self.MAX_ROWS]:
                cleaned_row = self._clean_and_filter_row(row)
                if any(cleaned_row.values()):
                    parsed_rows.append(cleaned_row)
            self.import_results["total_rows"] = len(parsed_rows)
            return parsed_rows
        except CatalogImportError:
            raise
        except Exception as e:
            raise CatalogImportError(f"Erreur lors du parsing du fichier : {str(e)}")

    def _normalize_field_name(self, key: str) -> str:
        """Normalise les noms de colonnes FR/EN vers le modèle produit."""
        value = str(key or "").strip().lower()
        value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
        value = re.sub(r"[^a-z0-9]+", "_", value).strip("_")
        aliases = {
            "product": "name",
            "produit": "name",
            "product_name": "name",
            "product_title": "name",
            "nom": "name",
            "nom_produit": "name",
            "nom_du_produit": "name",
            "titre": "name",
            "title": "name",
            "designation": "name",
            "designation_produit": "name",
            "libelle": "name",
            "libelle_produit": "name",
            "prix": "price",
            "tarif": "price",
            "product_price": "price",
            "unit_price": "price",
            "prix_unitaire": "price",
            "prix_vente": "price",
            "prix_de_vente": "price",
            "prix_ttc": "price",
            "prix_ht": "price",
            "selling_price": "price",
            "sale_price": "price",
            "categorie": "category",
            "categorie_id": "category_id",
            "category_id": "category_id",
            "category_name": "category",
            "quantite": "quantity",
            "stock": "quantity",
            "qty": "quantity",
            "prix_compare": "compare_price",
            "prix_barre": "compare_price",
            "old_price": "compare_price",
            "compare": "compare_price",
            "image": "image_url",
            "photo": "image_url",
            "actif": "is_active",
            "active": "is_active",
            "enabled": "is_active",
            "vedette": "is_featured",
            "en_vedette": "is_featured",
            "featured": "is_featured",
            "promotion": "is_promoted",
            "promoted": "is_promoted",
            "breve_description": "description",
            "description_breve": "description",
            "description_courte": "description",
        }
        return aliases.get(value, value)
    
    def _warn_about_raw_headers(self, headers: List[str]) -> None:
        if not headers:
            return
        normalized = [self._normalize_field_name(h) for h in headers]
        unknown = [h for h, n in zip(headers, normalized) if n not in self.ALL_FIELDS]
        if unknown:
            self.import_results["warnings"].append(
                "Colonnes non reconnues : " + ", ".join(unknown) + ". Ces colonnes seront ignorées si elles ne correspondent pas à un champ connu."
            )

    def _warn_about_headers(self, rows: List[Dict[str, str]]) -> None:
        if not rows:
            return
        headers = list(rows[0].keys())
        normalized = [self._normalize_field_name(h) for h in headers]
        missing = [f for f in self.REQUIRED_FIELDS if f not in normalized]
        if missing:
            raise CatalogImportError(
                "Colonnes requises manquantes : " + ", ".join(missing) +
                ". Utilisez des entêtes telles que name, price, category, quantity."
            )
        unknown = [h for h, n in zip(headers, normalized) if n not in self.ALL_FIELDS]
        if unknown:
            self.import_results["warnings"].append(
                "Colonnes non reconnues : " + ", ".join(unknown) + ". Ces colonnes seront ignorées."
            )

    def _clean_and_filter_row(self, row: dict) -> dict:
        """Normalise les clés de la ligne et ignore les colonnes non pertinentes."""
        cleaned = {}
        for key, value in (row or {}).items():
            normalized_key = self._normalize_field_name(key)
            if normalized_key not in self.ALL_FIELDS:
                continue
            cleaned[normalized_key] = str(value).strip() if value is not None else ""
        return cleaned

    def _collect_categories(self, rows: List[Dict[str, str]]) -> List[str]:
        """Recueille les catégories uniques à partir des lignes importées."""
        categories = []
        seen = set()
        for row in rows:
            category_name = row.get("category", "").strip()
            if not category_name and row.get("category_id"):
                category = self._get_category_by_id(row.get("category_id"))
                category_name = category.name if category else ""
            category = category_name or "Autres"
            if len(category) > 100:
                continue
            key = category.lower()
            if key in seen:
                continue
            seen.add(key)
            categories.append(category)
        return categories

    def _get_category_by_id(self, category_id_raw: Any):
        """Retourne une catégorie existante par ID si elle appartient à la boutique."""
        category_id = self._parse_int(category_id_raw)
        if category_id is None:
            return None
        return Category.query.filter_by(id=category_id, shop_id=self.shop.id).first()

    def _get_or_create_category(self, category_name: str) -> Category:
        """Récupère ou crée une catégorie pour la boutique."""
        name = (category_name or "").strip() or "Autres"
        existing = Category.query.filter_by(shop_id=self.shop.id).all()
        lower_existing = {cat.name.strip().lower() for cat in existing if cat.name}
        if name.strip().lower() in lower_existing:
            return next(cat for cat in existing if cat.name.strip().lower() == name.strip().lower())

        category = Category(shop_id=self.shop.id, name=name, is_active=True)
        db.session.add(category)
        db.session.flush()
        return category

    def _ensure_categories(self, categories: List[str]) -> None:
        """Créée en base toutes les catégories uniques détectées avant le traitement des produits."""
        if not categories:
            return
        existing = Category.query.filter_by(shop_id=self.shop.id).all()
        existing_lower = {cat.name.strip().lower() for cat in existing if cat.name}
        for category_name in categories:
            normalized = (category_name or "").strip() or "Autres"
            if normalized.lower() in existing_lower:
                continue
            category = Category(shop_id=self.shop.id, name=normalized, is_active=True)
            db.session.add(category)
            existing_lower.add(normalized.lower())
        db.session.flush()

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
        category = row.get("category", "Autres").strip() or "Autres"
        if len(category) > 100:
            errors.append("La catégorie ne doit pas dépasser 100 caractères")
        if "category_id" in row and row["category_id"]:
            if self._parse_int(row["category_id"]) is None:
                self.import_results["warnings"].append(
                    "category_id doit être un entier valide. La catégorie sera résolue par nom si possible."
                )
        
        # Valider le prix
        price = self._parse_float(row.get("price"))
        if price is None:
            errors.append("Le prix doit être un nombre valide")
        elif price < 0:
            errors.append("Le prix ne peut pas être négatif")
        
        # Valider la quantité (optionnel)
        if "quantity" in row and row["quantity"]:
            qty = self._parse_int(row["quantity"])
            if qty is None:
                errors.append("La quantité doit être un nombre entier")
            elif qty < 0:
                errors.append("La quantité ne peut pas être négative")
        
        # Valider le SKU (optionnel, doit être unique)
        if "sku" in row and row["sku"]:
            sku = row["sku"].strip()
            if len(sku) > self.MAX_SKU_LENGTH:
                errors.append(f"Le SKU ne doit pas dépasser {self.MAX_SKU_LENGTH} caractères")
            
        # Valider la description (optionnel)
        if "description" in row and row["description"]:
            desc = row["description"].strip()
            if len(desc) > self.MAX_DESCRIPTION_LENGTH:
                errors.append(f"La description ne doit pas dépasser {self.MAX_DESCRIPTION_LENGTH} caractères")
        
        # Valider compare_price (optionnel)
        if "compare_price" in row and row["compare_price"]:
            compare_price = self._parse_float(row["compare_price"])
            if compare_price is None:
                errors.append("Le prix de comparaison doit être un nombre valide")
            elif compare_price < 0:
                errors.append("Le prix de comparaison ne peut pas être négatif")
        
        return errors
    
    def _prepare_product_data(self, row: Dict[str, str]) -> Dict[str, Any]:
        """Prépare les données du produit pour création/mise à jour"""
        category_name = row.get("category", "").strip() or "Autres"
        category = self._get_category_by_id(row.get("category_id")) if row.get("category_id") else None
        if not category:
            category = self._get_or_create_category(category_name)

        data = {
            "name": row.get("name", "").strip(),
            "category": category.name,
            "category_id": category.id,
            "description": row.get("description", "").strip()[:self.MAX_DESCRIPTION_LENGTH] or None,
            "price": self._parse_float(row.get("price")) or 0,
            "quantity": self._parse_int(row.get("quantity")) or 0,
            "image_url": row.get("image_url", "").strip() or None,
            "sku": row.get("sku", "").strip()[:self.MAX_SKU_LENGTH] or None,
            "compare_price": self._parse_float(row.get("compare_price")),
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

    def _parse_float(self, value: Any) -> float | None:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        text = str(value).strip()
        if not text:
            return None
        text = text.replace(" ", "").replace(",", ".")
        text = re.sub(r"[^0-9.\-]", "", text)
        if text in {"", ".", "-", "-."}:
            return None
        try:
            return float(text)
        except ValueError:
            return None

    def _parse_int(self, value: Any) -> int | None:
        number = self._parse_float(value)
        if number is None:
            return None
        return int(number)
    
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
        if product_data.get("category_id") is not None:
            product = SellerProduct.query.filter(
                SellerProduct.shop_id == self.shop.id,
                SellerProduct.name == product_data["name"],
                SellerProduct.category_id == product_data["category_id"]
            ).first()
            if product:
                return product

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
            "name", "category", "category_id", "description", "price", "compare_price",
            "quantity", "sku", "image_url", "is_promoted", "is_active", "is_featured"
        ])
        
        writer.writeheader()
        for product in products:
            writer.writerow({
                "name": product.name,
                "category": product.category,
                "category_id": product.category_id or "",
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
                "category_id": product.category_id,
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

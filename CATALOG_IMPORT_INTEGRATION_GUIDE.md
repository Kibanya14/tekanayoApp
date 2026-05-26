# ============================================================================
# ROUTE D'INTÉGRATION - À AJOUTER DANS backend/apps.py
# ============================================================================
# Copiez cette section et intégrez-la dans le fichier apps.py existant
# ============================================================================

# En haut du fichier apps.py, ajouter:
# from backend.catalog_import_manager import CatalogImportManager

# Ensuite, dans la fonction create_app() ou à la suite des autres routes, ajouter:


def _setup_catalog_routes(app):
    """Configure les routes d'import de catalogue pour Admin et Vendeurs"""
    
    @app.route("/admin/import/catalog/page")
    @admin_required()
    def admin_import_catalog_page():
        """Affiche la page d'import de catalogue (Admin)"""
        shop = _portal_shop()
        total_products = SellerProduct.query.filter_by(shop_id=shop.id).count() if shop else 0
        return render_template(
            "admin/import_catalog.html",
            total_products=total_products
        )
    
    @app.route("/admin/catalog/import", methods=["POST"])
    @admin_required()
    def admin_import_catalog():
        """Importe un catalogue (Admin Tekanayo)"""
        if not request.files.get('file'):
            flash("Aucun fichier sélectionné", "error")
            return redirect(url_for("admin_import_catalog_page"))
        
        file = request.files['file']
        if not file.filename:
            flash("Fichier invalide", "error")
            return redirect(url_for("admin_import_catalog_page"))
        
        try:
            # Parser le fichier
            headers, rows = CatalogImportManager.parse_file(file)
            if not rows:
                flash("Fichier vide ou format non supporté", "error")
                return redirect(url_for("admin_import_catalog_page"))
            
            # Normaliser
            headers, rows = CatalogImportManager.normalize_data(headers, rows)
            
            # Importer
            success_count = 0
            error_count = 0
            errors = []
            
            # Boutique portail
            shop = _portal_shop()
            if not shop:
                flash("Boutique portail introuvable", "error")
                return redirect(url_for("admin_import_catalog_page"))
            
            for i, row in enumerate(rows, 1):
                if success_count >= 10000:  # Limite de sécurité
                    errors.append(f"Limite de 10,000 produits atteinte")
                    break
                
                is_valid, error_msg, data = CatalogImportManager.validate_and_convert_row(row)
                
                if not is_valid:
                    error_count += 1
                    if len(errors) < 10:  # Afficher max 10 erreurs
                        errors.append(f"Ligne {i}: {error_msg}")
                    continue
                
                try:
                    product = SellerProduct(
                        shop_id=shop.id,
                        name=data['name'],
                        price=data['price'],
                        category=data['category'],
                        description=data['description'],
                        quantity=data['quantity'],
                        compare_price=data['compare_price'],
                        is_active=data['is_active'],
                        is_featured=data['is_featured'],
                    )
                    db.session.add(product)
                    success_count += 1
                    
                    # Log stock initial
                    if data['quantity'] > 0:
                        StockManager.log_stock_change(
                            product_id=None,  # Sera défini après flush
                            user_id=current_admin.id if current_admin else 0,
                            old_quantity=0,
                            new_quantity=data['quantity'],
                            reason="import_initial",
                            user_type="admin"
                        )
                
                except Exception as e:
                    error_count += 1
                    if len(errors) < 10:
                        errors.append(f"Ligne {i}: Erreur BD - {str(e)[:50]}")
            
            db.session.commit()
            
            # Message de confirmation
            flash(f"✅ Import complété: {success_count} produit(s) ajouté(s) au catalogue Tekanayo", "success")
            if errors:
                error_msg = f"⚠️ {error_count} erreur(s):\n" + "\n".join(errors)
                flash(error_msg, "warning")
            
            record_activity(
                f"Import catalogue: {success_count} produits ajoutés",
                actor=current_admin,
                extra=f"errors={error_count}, file={file.filename}"
            )
            
            return redirect(url_for("admin_import_catalog_page"))
        
        except Exception as e:
            flash(f"Erreur lors de l'import: {str(e)}", "error")
            return redirect(url_for("admin_import_catalog_page"))
    
    @app.route("/vendeur/<slug>/import/catalog/page")
    @seller_session_required
    def seller_import_catalog_page(slug):
        """Affiche la page d'import de catalogue (Vendeur)"""
        shop = SellerShop.query.filter_by(slug=slug).first_or_404()
        
        # Vérifier permission
        current_admin = SellerAdmin.query.filter_by(
            id=session.get("seller_admin_id"),
            shop_id=shop.id
        ).first_or_404()
        
        if not (current_admin.is_owner or 'manage_products' in (current_admin.permissions or '').split(',')):
            flash("Permission refusée", "error")
            return redirect(url_for("seller_space", slug=slug))
        
        total_products = SellerProduct.query.filter_by(shop_id=shop.id).count()
        
        return render_template(
            "vendeur/import_catalog.html",
            shop=shop,
            admin=current_admin,
            total_products=total_products,
            active_page="products"
        )
    
    @app.route("/vendeur/<slug>/catalog/import", methods=["POST"])
    @seller_session_required
    def seller_import_catalog(slug):
        """Importe un catalogue (Vendeur)"""
        shop = SellerShop.query.filter_by(slug=slug).first_or_404()
        
        # Vérifier permission
        current_admin = SellerAdmin.query.filter_by(
            id=session.get("seller_admin_id"),
            shop_id=shop.id
        ).first_or_404()
        
        if not (current_admin.is_owner or 'manage_products' in (current_admin.permissions or '').split(',')):
            flash("Permission refusée", "error")
            return redirect(url_for("seller_products_page", slug=slug))
        
        if not request.files.get('file'):
            flash("Aucun fichier sélectionné", "error")
            return redirect(url_for("seller_import_catalog_page", slug=slug))
        
        file = request.files['file']
        if not file.filename:
            flash("Fichier invalide", "error")
            return redirect(url_for("seller_import_catalog_page", slug=slug))
        
        try:
            # Parser le fichier
            headers, rows = CatalogImportManager.parse_file(file)
            if not rows:
                flash("Fichier vide ou format non supporté", "error")
                return redirect(url_for("seller_import_catalog_page", slug=slug))
            
            # Normaliser
            headers, rows = CatalogImportManager.normalize_data(headers, rows)
            
            # Importer
            success_count = 0
            error_count = 0
            errors = []
            
            for i, row in enumerate(rows, 1):
                if success_count >= 5000:  # Limite par vendeur
                    errors.append(f"Limite de 5,000 produits par boutique atteinte")
                    break
                
                is_valid, error_msg, data = CatalogImportManager.validate_and_convert_row(row)
                
                if not is_valid:
                    error_count += 1
                    if len(errors) < 10:
                        errors.append(f"Ligne {i}: {error_msg}")
                    continue
                
                try:
                    product = SellerProduct(
                        shop_id=shop.id,
                        name=data['name'],
                        price=data['price'],
                        category=data['category'],
                        description=data['description'],
                        quantity=data['quantity'],
                        compare_price=data['compare_price'],
                        is_active=data['is_active'],
                        is_featured=data['is_featured'],
                    )
                    db.session.add(product)
                    success_count += 1
                    
                    # Log stock initial
                    if data['quantity'] > 0:
                        StockManager.log_stock_change(
                            product_id=None,
                            user_id=current_admin.id,
                            old_quantity=0,
                            new_quantity=data['quantity'],
                            reason="import_initial",
                            user_type="seller"
                        )
                
                except Exception as e:
                    error_count += 1
                    if len(errors) < 10:
                        errors.append(f"Ligne {i}: Erreur BD - {str(e)[:50]}")
            
            db.session.commit()
            
            # Message de confirmation
            flash(f"✅ Import complété: {success_count} produit(s) ajouté(s) à votre catalogue", "success")
            if errors:
                error_msg = f"⚠️ {error_count} erreur(s):\n" + "\n".join(errors)
                flash(error_msg, "warning")
            
            record_activity(
                f"Import catalogue: {success_count} produits pour {shop.name}",
                actor=current_admin,
                extra=f"errors={error_count}, file={file.filename}"
            )
            
            return redirect(url_for("seller_import_catalog_page", slug=slug))
        
        except Exception as e:
            flash(f"Erreur lors de l'import: {str(e)}", "error")
            return redirect(url_for("seller_import_catalog_page", slug=slug))


# ============================================================================
# AJOUTER CES LIGNES DANS create_app()
# ============================================================================

# Après la création de l'app et l'initialisation, ajouter:
# _setup_catalog_routes(app)
# 
# OU intégrer directement les routes dans la section des routes existantes

# ============================================================================
# ÉTAPES D'INTÉGRATION DANS backend/apps.py
# ============================================================================

"""
1. En haut du fichier, ajouter:
   from backend.catalog_import_manager import CatalogImportManager

2. Copier la fonction _setup_catalog_routes() ci-dessus

3. Dans create_app(), après db.init_app(app):
   _setup_catalog_routes(app)

4. Ajouter les permissions dans ADMIN_PERMISSION_LABELS:
   "manage_import": "Gérer imports",

5. Ajouter dans SELLER_PERMISSION_LABELS:
   "manage_import": "Gérer imports",

6. Mettre à jour les templates de navigation pour ajouter les liens:
   - Pour Admin: /admin/import/catalog/page
   - Pour Vendeur: /vendeur/<slug>/import/catalog/page
"""

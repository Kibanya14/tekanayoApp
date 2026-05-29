# ========================================================================
# ROUTES D'IMPORTATION ET EXPORTATION DE CATALOGUE
# ========================================================================

@app.route("/vendeur/<slug>/products/import", methods=["GET", "POST"])
@seller_session_required
def seller_import_catalog(slug):
    """Page d'import de catalogue pour le vendeur"""
    from backend.catalog_importer import CatalogImporter, CatalogExporter
    
    shop = SellerShop.query.filter_by(slug=slug).first_or_404()
    current_admin = SellerAdmin.query.filter_by(id=session.get("seller_admin_id"), shop_id=shop.id, is_active=True).first()
    
    if not current_admin or (not current_admin.is_owner and not current_admin.has_permission("manage_products")):
        flash("Permission insuffisante pour importer un catalogue.", "error")
        return redirect(url_for("seller_products_page", slug=slug))
    
    import_results = None
    
    if request.method == "POST":
        # Vérifier si un fichier a été uploadé
        if "catalog_file" not in request.files:
            flash("Aucun fichier sélectionné.", "error")
            return redirect(url_for("seller_import_catalog", slug=slug))
        
        file = request.files["catalog_file"]
        
        if file.filename == "":
            flash("Aucun fichier sélectionné.", "error")
            return redirect(url_for("seller_import_catalog", slug=slug))
        
        # Vérifier l'extension du fichier
        allowed_extensions = {".csv", ".xlsx", ".json"}
        file_ext = ""
        if "." in file.filename:
            file_ext = "." + file.filename.rsplit(".", 1)[1].lower()
        
        if file_ext not in allowed_extensions:
            flash("Format de fichier non supporté. Utilisez CSV, XLSX ou JSON.", "error")
            return redirect(url_for("seller_import_catalog", slug=slug))
        
        # Importer le catalogue
        try:
            importer = CatalogImporter(shop)
            import_results = importer.import_file(file)
            
            if import_results["errors"] and import_results["successful"] == 0:
                flash("Erreur lors de l'import : " + import_results["errors"][0], "error")
            else:
                message = f"Import réussi : {import_results['successful']} produit(s) importé(s)"
                if import_results["warnings"]:
                    message += f". {len(import_results['warnings'])} avertissement(s)."
                flash(message, "success")
                
                record_activity(
                    f"Import de catalogue ({import_results['successful']} produits)",
                    actor=current_admin,
                    extra=f"batch_id={import_results['batch_id']}"
                )
        except Exception as e:
            flash(f"Erreur lors de l'import : {str(e)}", "error")
            import_results = None
    
    # Récupérer les résultats d'imports précédents (optionnel)
    recent_imports = (
        SellerProduct.query
        .filter_by(shop_id=shop.id)
        .filter(SellerProduct.import_batch_id != None)
        .order_by(SellerProduct.updated_at.desc())
        .all()
    )
    
    unique_batches = {}
    for product in recent_imports[:100]:
        if product.import_batch_id not in unique_batches:
            unique_batches[product.import_batch_id] = {
                "batch_id": product.import_batch_id,
                "count": 0,
                "created_at": product.updated_at,
            }
        unique_batches[product.import_batch_id]["count"] += 1
    
    import_history = list(unique_batches.values())[:10]
    
    shop_data, admin, context, redirect_response = _seller_page_context(slug)
    if redirect_response:
        return redirect_response
    
    return render_template(
        "vendeur/import_catalog.html",
        shop=shop,
        admin=admin,
        active_page="products",
        import_results=import_results,
        import_history=import_history,
        **context
    )


@app.route("/vendeur/<slug>/products/export", methods=["GET"])
@seller_session_required
def seller_export_catalog(slug):
    """Exporte le catalogue du vendeur"""
    from backend.catalog_importer import CatalogExporter
    
    shop = SellerShop.query.filter_by(slug=slug).first_or_404()
    current_admin = SellerAdmin.query.filter_by(id=session.get("seller_admin_id"), shop_id=shop.id, is_active=True).first()
    
    if not current_admin or (not current_admin.is_owner and not current_admin.has_permission("manage_products")):
        flash("Permission insuffisante pour exporter le catalogue.", "error")
        return redirect(url_for("seller_products_page", slug=slug))
    
    format_type = request.args.get("format", "csv").lower()
    
    if format_type == "json":
        content = CatalogExporter.export_to_json(shop)
        filename = f"catalog_{shop.slug}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        mimetype = "application/json"
    else:
        content = CatalogExporter.export_to_csv(shop)
        filename = f"catalog_{shop.slug}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
        mimetype = "text/csv"
    
    # Enregistrer l'activité
    record_activity(
        f"Export de catalogue ({format_type.upper()})",
        actor=current_admin,
        extra=f"format={format_type}"
    )
    
    return send_file(
        io.BytesIO(content.encode('utf-8')),
        mimetype=mimetype,
        as_attachment=True,
        download_name=filename
    )


@app.route("/vendeur/<slug>/products/import-example", methods=["GET"])
@seller_session_required
def seller_import_example(slug):
    """Télécharge un exemple de fichier d'import"""
    from backend.catalog_importer import CatalogExporter
    
    shop = SellerShop.query.filter_by(slug=slug).first_or_404()
    
    format_type = request.args.get("format", "csv").lower()
    
    # Créer un exemple avec un produit test
    example_products = [
        {
            "name": "Produit Exemple 1",
            "category": "Électronique",
            "description": "Description du produit",
            "price": "19.99",
            "compare_price": "29.99",
            "quantity": "100",
            "sku": "PROD-001",
            "image_url": "",
            "is_promoted": "false",
            "is_active": "true",
            "is_featured": "false",
        },
        {
            "name": "Produit Exemple 2",
            "category": "Mode",
            "description": "Deuxième produit exemple",
            "price": "49.99",
            "compare_price": "",
            "quantity": "50",
            "sku": "PROD-002",
            "image_url": "",
            "is_promoted": "true",
            "is_active": "true",
            "is_featured": "true",
        },
    ]
    
    if format_type == "json":
        content = json.dumps(example_products, indent=2, ensure_ascii=False)
        filename = f"catalog_example_{datetime.utcnow().strftime('%Y%m%d')}.json"
        mimetype = "application/json"
    else:
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=[
            "name", "category", "description", "price", "compare_price",
            "quantity", "sku", "image_url", "is_promoted", "is_active", "is_featured"
        ])
        writer.writeheader()
        writer.writerows(example_products)
        content = output.getvalue()
        filename = f"catalog_example_{datetime.utcnow().strftime('%Y%m%d')}.csv"
        mimetype = "text/csv"
    
    return send_file(
        io.BytesIO(content.encode('utf-8')),
        mimetype=mimetype,
        as_attachment=True,
        download_name=filename
    )


@app.route("/vendeur/<slug>/products/batch/<batch_id>", methods=["GET"])
@seller_session_required
def seller_view_import_batch(slug, batch_id):
    """Affiche les détails d'un batch d'import"""
    shop = SellerShop.query.filter_by(slug=slug).first_or_404()
    current_admin = SellerAdmin.query.filter_by(id=session.get("seller_admin_id"), shop_id=shop.id, is_active=True).first()
    
    if not current_admin or (not current_admin.is_owner and not current_admin.has_permission("manage_products")):
        flash("Permission insuffisante.", "error")
        return redirect(url_for("seller_products_page", slug=slug))
    
    # Récupérer les produits de ce batch
    products = (
        SellerProduct.query
        .filter_by(shop_id=shop.id, import_batch_id=batch_id)
        .order_by(SellerProduct.created_at.desc())
        .all()
    )
    
    if not products:
        flash("Batch d'import non trouvé.", "error")
        return redirect(url_for("seller_import_catalog", slug=slug))
    
    shop_data, admin, context, redirect_response = _seller_page_context(slug)
    if redirect_response:
        return redirect_response
    
    return render_template(
        "vendeur/import_batch_detail.html",
        shop=shop,
        admin=admin,
        batch_id=batch_id,
        products=products,
        active_page="products",
        **context
    )

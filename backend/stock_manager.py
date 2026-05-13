"""
Stock Management Module - Alertes et historique
Intégré avec la base de données
"""

from datetime import datetime
from flask import current_app
from flask_mail import Mail, Message
import os

class StockManager:
    """Gestionnaire de stock avec alertes automatiques"""

    # Seuil d'alerte par défaut
    LOW_STOCK_THRESHOLD = 10

    @classmethod
    def log_stock_change(cls, product_id: int, user_id: int, old_quantity: int, 
                        new_quantity: int, reason: str, user_type: str = 'seller'):
        """
        Enregistrer une modification de stock
        
        Args:
            product_id: ID du produit
            user_id: ID de l'utilisateur (vendeur/admin)
            old_quantity: Ancien stock
            new_quantity: Nouveau stock
            reason: Motif du changement (vente, ajustement, retour, etc.)
            user_type: Type d'utilisateur (seller, admin)
        """
        try:
            from backend.models import db, StockHistory
            
            # Créer l'entrée de stock
            stock_entry = StockHistory(
                product_id=product_id,
                user_id=user_id,
                user_type=user_type,
                old_quantity=old_quantity,
                new_quantity=new_quantity,
                quantity_change=new_quantity - old_quantity,
                reason=reason,
                timestamp=datetime.utcnow()
            )
            
            db.session.add(stock_entry)
            db.session.commit()
            
            print(f"✅ Stock historique enregistré: {reason}")
            
            # Vérifier si alerte nécessaire
            if new_quantity <= cls.LOW_STOCK_THRESHOLD:
                cls.send_low_stock_alert(product_id, new_quantity, user_id)
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur log stock: {str(e)}")
            return False

    @classmethod
    def get_stock_history(cls, product_id: int, limit: int = 50):
        """Obtenir l'historique de stock d'un produit"""
        try:
            from backend.models import StockHistory
            
            history = StockHistory.query \
                .filter_by(product_id=product_id) \
                .order_by(StockHistory.timestamp.desc()) \
                .limit(limit) \
                .all()
            
            return [{
                'id': entry.id,
                'old_quantity': entry.old_quantity,
                'new_quantity': entry.new_quantity,
                'change': entry.quantity_change,
                'reason': entry.reason,
                'timestamp': entry.timestamp.isoformat(),
                'user': f"{entry.user_type}#{entry.user_id}"
            } for entry in history]
            
        except Exception as e:
            print(f"❌ Erreur récupération historique: {str(e)}")
            return []

    @classmethod
    def get_low_stock_products(cls, seller_id: int, threshold: int = None):
        """Obtenir les produits en rupture de stock"""
        try:
            from backend.models import SellerProduct
            
            if threshold is None:
                threshold = cls.LOW_STOCK_THRESHOLD
            
            low_stock = SellerProduct.query \
                .filter(
                    SellerProduct.shop_id == seller_id,
                    SellerProduct.quantity <= threshold,
                    SellerProduct.is_active == True
                ) \
                .all()
            
            return [{
                'id': product.id,
                'name': product.name,
                'quantity': product.quantity,
                'threshold': threshold,
                'warning': 'Rupture de stock imminente ⚠️' if product.quantity == 0 else 'Stock faible'
            } for product in low_stock]
            
        except Exception as e:
            print(f"❌ Erreur low stock products: {str(e)}")
            return []

    @classmethod
    def send_low_stock_alert(cls, product_id: int, current_quantity: int, seller_id: int):
        """Envoyer une alerte de stock faible par email"""
        try:
            from backend.models import SellerProduct, SellerAdmin
            
            # Récupérer le produit et le vendeur
            product = SellerProduct.query.get(product_id)
            seller = SellerAdmin.query.get(seller_id)
            
            if not product or not seller:
                return False

            # Construire le message
            subject = f"⚠️ Alerte stock faible - {product.name}"
            
            if current_quantity == 0:
                message_text = f"""
                ⚠️ RUPTURE DE STOCK!
                
                Produit: {product.name}
                Stock: 0 unités
                
                Veuillez réapprovisionner rapidement pour éviter de perdre des ventes.
                """
            else:
                message_text = f"""
                ⚠️ Stock faible
                
                Produit: {product.name}
                Stock restant: {current_quantity} unités
                Seuil d'alerte: {cls.LOW_STOCK_THRESHOLD} unités
                
                Veuillez prévoir un réapprovisionnement.
                """

            # Envoyer l'email
            try:
                mail = Mail(current_app)
                msg = Message(
                    subject=subject,
                    recipients=[seller.user.email or seller.email],
                    body=message_text
                )
                mail.send(msg)
                print(f"✅ Alerte stock faible envoyée à {seller.user.email or seller.email}")
                return True
            except Exception as mail_error:
                print(f"⚠️ Erreur envoi email: {str(mail_error)}")
                # Continuer même si email échoue - l'alerte est enregistrée
                return True

        except Exception as e:
            print(f"❌ Erreur send_low_stock_alert: {str(e)}")
            return False

    @classmethod
    def get_stock_statistics(cls, seller_id: int):
        """Obtenir les statistiques de stock pour un vendeur"""
        try:
            from backend.models import SellerProduct


            products = SellerProduct.query \
                .filter(SellerProduct.shop_id == seller_id) \
                .all()

            if not products:
                return {
                    'total_products': 0,
                    'total_items': 0,
                    'low_stock_count': 0,
                    'out_of_stock': 0,
                    'estimated_value': 0
                }

            return {
                'total_products': len(products),
                'total_items': sum(p.quantity for p in products),
                'low_stock_count': len([p for p in products if p.quantity <= cls.LOW_STOCK_THRESHOLD]),
                'out_of_stock': len([p for p in products if p.quantity == 0]),
                'estimated_value': sum(p.price * p.quantity for p in products),
                'products': [{
                    'id': p.id,
                    'name': p.name,
                    'quantity': p.quantity,
                    'price': p.price,
                    'category': p.category,
                    'status': '🔴 Rupture' if p.quantity == 0 else '🟡 Alerte' if p.quantity <= cls.LOW_STOCK_THRESHOLD else '🟢 Normal'
                } for p in products]
            }

        except Exception as e:
            print(f"❌ Erreur stock statistics: {str(e)}")
            return {}

    @classmethod
    def bulk_update_stock(cls, product_id: int, new_quantity: int, reason: str, user_id: int):
        """Mettre à jour le stock et enregistrer le changement"""
        try:
            from backend.models import db, SellerProduct
            
            product = SellerProduct.query.get(product_id)
            if not product:
                return False, "Produit non trouvé"

            old_quantity = product.quantity
            product.quantity = max(0, new_quantity)  # Pas de stock négatif
            
            db.session.commit()
            
            # Enregistrer dans l'historique
            cls.log_stock_change(product_id, user_id, old_quantity, product.quantity, reason)
            
            return True, f"Stock mis à jour: {old_quantity} → {product.quantity}"
            
        except Exception as e:
            return False, f"Erreur: {str(e)}"


# Helper pour integration avec les modèles
def create_stock_history_model(db):
    """Créer le modèle StockHistory pour la base de données"""
    
    class StockHistory(db.Model):
        __tablename__ = 'stock_history'
        
        id = db.Column(db.Integer, primary_key=True)
        product_id = db.Column(db.Integer, db.ForeignKey('seller_product.id'), nullable=False)
        user_id = db.Column(db.Integer, nullable=False)
        user_type = db.Column(db.String(20), default='seller')  # seller, admin
        old_quantity = db.Column(db.Integer, default=0)
        new_quantity = db.Column(db.Integer, default=0)
        quantity_change = db.Column(db.Integer)
        reason = db.Column(db.String(255))  # 'sale', 'adjustment', 'return', 'restock'
        timestamp = db.Column(db.DateTime, default=datetime.utcnow)
        
        # Relations
        product = db.relationship('SellerProduct', backref='stock_history')
        
        def __repr__(self):
            return f"<StockHistory {self.product_id}: {self.old_quantity} → {self.new_quantity}>"
        
        def to_dict(self):
            return {
                'id': self.id,
                'product_id': self.product_id,
                'old_quantity': self.old_quantity,
                'new_quantity': self.new_quantity,
                'change': self.quantity_change,
                'reason': self.reason,
                'timestamp': self.timestamp.isoformat()
            }
    
    return StockHistory

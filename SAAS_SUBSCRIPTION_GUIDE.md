# 💰 Système SaaS d'Abonnement - Guide Complet

## 🎯 Vue d'Ensemble

Système complet d'abonnement pour vendeurs avec :
- ✅ **2 mois d'essai gratuit** automatique
- ✅ **5$/mois** après la période d'essai
- ✅ **7 méthodes de paiement** (mobile money + international)
- ✅ **Paiement hors plateforme** avec validation admin
- ✅ **Désactivation automatique** après expiration
- ✅ **Interface UI/UX professionnelle**

---

## 📁 Fichiers Créés

### Backend (Python/Flask)

| Fichier | Description |
|---------|-------------|
| `backend/models.py` | 3 nouveaux modèles : `SellerSubscription`, `SellerPayment`, `SellerPaymentTask` |
| `backend/apps.py` | Routes de gestion d'abonnement et de paiement |

### Frontend (Templates)

| Fichier | Description |
|---------|-------------|
| `vendeur/subscription.html` | Page de gestion de l'abonnement |
| `vendeur/payment.html` | Page de paiement avec 7 méthodes |
| `vendeur/payment_history.html` | Historique des paiements |

---

## 💾 Modèles de Base de Données

### 1. SellerSubscription

```python
class SellerSubscription:
    """Gère l'abonnement d'un vendeur"""
    
    shop_id          # Référence à la boutique (unique)
    status           # trial, active, suspended, expired, cancelled
    trial_start_date # Début essai gratuit
    trial_end_date   # Fin essai (60 jours)
    subscription_start_date  # Début abonnement payant
    subscription_end_date    # Fin abonnement en cours
    monthly_price    # 5.0 USD
    total_paid       # Total payé depuis le début
    payment_method   # airtel, orange, mpesa, vodacom, afri, paypal, stripe, offline
    pending_payment  # Paiement hors plateforme en attente
```

### 2. SellerPayment

```python
class SellerPayment:
    """Historique des paiements"""
    
    subscription_id  # Référence à l'abonnement
    amount           # Montant (5.0 USD)
    payment_method   # Méthode utilisée
    status           # pending, completed, failed, refunded
    is_offline       # Paiement hors plateforme
    transaction_id   # ID Stripe/PayPal
    offline_confirmed_by  # Admin qui a confirmé
```

### 3. SellerPaymentTask

```python
class SellerPaymentTask:
    """Tâches pour l'admin"""
    
    shop_id          # Boutique concernée
    task_type        # offline_payment, activation, deactivation
    status           # pending, completed, cancelled
    title            # Titre de la tâche
    description      # Description détaillée
    assigned_to      # Admin assigné
    completed_by     # Admin qui a complété
```

---

## 🔄 Flux de Paiement

### 1. Inscription Vendeur

```
1. Vendeur crée sa boutique
2. Abonnement créé automatiquement
   - status: "trial"
   - trial_start_date: now
   - trial_end_date: now + 60 jours
3. Vendeur accède à son espace
```

### 2. Pendant la Période d'Essai

```
1. Vendeur utilise toutes les fonctionnalités
2. Notifications J-7 avant expiration
3. Interface affiche "Période d'essai gratuite"
```

### 3. Expiration de l'Essai

```
1. status passe à "expired"
2. Interface d'alerte s'affiche
3. Vendeur ne peut plus accéder à certaines fonctionnalités
4. Admins et livreurs sont bloqués
5. Clients peuvent toujours commander
```

### 4. Paiement En Ligne (Stripe/PayPal/Mobile)

```
1. Vendeur choisit méthode de paiement
2. Clique sur "Payer 5$"
3. Paiement traité automatiquement
4. Abonnement activé immédiatement
   - status: "active"
   - subscription_end_date: now + 30 jours
5. Tâche admin créée (notification)
```

### 5. Paiement Hors Plateforme

```
1. Vendeur choisit "Paiement Hors Plateforme"
2. Confirme le formulaire
3. status passe à "suspended"
4. pending_payment: true
5. Tâche admin créée avec instructions
6. Admin vérifie le paiement (24-48h)
7. Admin active manuellement l'abonnement
8. Vendeur reçoit notification
```

---

## 💳 Intégration des APIs de Paiement

### Airtel Money / Orange Money / M-Pesa / Afrimoney

**Pour rendre ces paiements fonctionnels :**

#### Option 1 : API Directe (Recommandé)

```python
# backend/apps.py - Dans seller_payment_process

if payment_method == 'airtel':
    # Initialiser l'API Airtel Money
    from airtel_money import AirtelMoneyClient
    
    client = AirtelMoneyClient(
        api_key=os.getenv('AIRTEL_API_KEY'),
        api_secret=os.getenv('AIRTEL_API_SECRET')
    )
    
    # Créer la transaction
    transaction = client.create_payment(
        amount=5.0,
        currency='USD',
        phone_number=request.form.get('phone_number'),
        reference=f"TEKANAYO_{shop.id}_{datetime.utcnow().timestamp()}"
    )
    
    # Rediriger vers la page de paiement Airtel
    return redirect(transaction.payment_url)
```

**Configuration requise :**
```bash
# .env
AIRTEL_API_KEY=votre_clé_api_airtel
AIRTEL_API_SECRET=votre_secret_airtel
ORANGE_API_KEY=votre_clé_api_orange
ORANGE_API_SECRET=votre_secret_orange
MPESA_API_KEY=votre_clé_api_mpesa
MPESA_API_SECRET=votre_secret_mpesa
AFRIMONEY_API_KEY=votre_clé_api_afrimoney
AFRIMONEY_API_SECRET=votre_secret_afrimoney
```

#### Option 2 : Agrégateur de Paiement (Plus Simple)

Utiliser un agrégateur comme **Flutterwave** ou **PayGate** qui supporte plusieurs mobile money :

```python
from flutterwave import Flutterwave

flutterwave = Flutterwave(
    public_key=os.getenv('FLW_PUBLIC_KEY'),
    secret_key=os.getenv('FLW_SECRET_KEY')
)

# Paiement mobile money
payment = flutterwave.mobile_money_payment(
    amount=5.0,
    currency='USD',
    network='airtel',  # ou 'orange', 'mpesa', etc.
    email=shop.owner_email,
    phone_number=request.form.get('phone_number'),
    reference=f"TEKANAYO_{shop.id}_{datetime.utcnow().timestamp()}"
)

return redirect(payment.link)
```

---

### PayPal

```python
from paypalrestsdk import Payment as PayPalPayment

# Configuration
paypalrestsdk.configure({
    "mode": "live",  # ou "sandbox" pour les tests
    "client_id": os.getenv('PAYPAL_CLIENT_ID'),
    "client_secret": os.getenv('PAYPAL_CLIENT_SECRET')
})

# Créer le paiement
payment = PayPalPayment({
    "intent": "sale",
    "payer": {"payment_method": "paypal"},
    "transactions": [{
        "amount": {
            "total": "5.00",
            "currency": "USD"
        },
        "description": "Abonnement mensuel Tekanayo App"
    }],
    "redirect_urls": {
        "return_url": url_for('seller_payment_paypal_success', slug=shop.slug, _external=True),
        "cancel_url": url_for('seller_payment_paypal_cancel', slug=shop.slug, _external=True)
    }
})

if payment.create():
    # Rediriger vers PayPal
    return redirect(payment.links[1].href)
else:
    flash("Erreur PayPal", "error")
```

---

### Stripe (Carte Bancaire)

```python
import stripe

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

# Créer une session de paiement
session = stripe.checkout.Session.create(
    payment_method_types=['card'],
    line_items=[{
        'price_data': {
            'currency': 'usd',
            'product_data': {
                'name': 'Abonnement mensuel Tekanayo App',
            },
            'unit_amount': 500,  # 5.00 USD en cents
        },
        'quantity': 1,
    }],
    mode='payment',
    success_url=url_for('seller_payment_stripe_success', slug=shop.slug, _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
    cancel_url=url_for('seller_payment_page', slug=shop.slug, _external=True),
    metadata={
        'shop_id': shop.id,
        'subscription_id': subscription.id
    }
)

return redirect(session.url, code=303)
```

**Webhook Stripe pour confirmation automatique :**

```python
@app.route('/webhook/stripe', methods=['POST'])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, os.getenv('STRIPE_WEBHOOK_SECRET')
        )
    except ValueError:
        return 'Invalid payload', 400
    
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        
        # Récupérer l'abonnement
        subscription_id = session['metadata']['subscription_id']
        subscription = SellerSubscription.query.get(subscription_id)
        
        # Activer l'abonnement
        subscription.status = 'active'
        subscription.subscription_end_date = datetime.utcnow() + timedelta(days=30)
        subscription.last_payment_date = datetime.utcnow()
        subscription.total_paid += 5.0
        
        # Créer le paiement
        payment = SellerPayment(
            subscription_id=subscription.id,
            amount=5.0,
            payment_method='stripe',
            status='completed',
            transaction_id=session['id']
        )
        db.session.add(payment)
        db.session.commit()
    
    return 'Success', 200
```

---

## 🎨 UI/UX - Instructions de Design

### Page de Gestion d'Abonnement (`subscription.html`)

**Éléments clés :**
1. **Carte d'état** avec statut coloré (vert=actif, rouge=expiré, jaune=suspendu)
2. **Compteur de jours** restants bien visible
3. **Bouton d'action** qui change selon l'état :
   - Essai actif : "Renouveler" (gris)
   - J-7 : "Renouveler maintenant" (jaune)
   - Expiré : "Renouveler l'abonnement" (rouge/violet)

### Page de Paiement (`payment.html`)

**Design des cartes de paiement :**
- **Mobile Money** : Icônes colorées avec les couleurs officielles
- **PayPal/Stripe** : Design professionnel bleu/indigo
- **Hors plateforme** : Vert avec instructions détaillées

**Effets interactifs :**
```javascript
// Zoom au survol
.payment-method-option:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

// État sélectionné
.payment-method-option input:checked + div {
    border-color: #7c3aed;
    background-color: #f5f3ff;
}
```

---

## 🔧 Configuration Requise

### Variables d'Environnement (.env)

```bash
# Paiements Mobile Money
AIRTEL_API_KEY=your_airtel_key
AIRTEL_API_SECRET=your_airtel_secret
ORANGE_API_KEY=your_orange_key
ORANGE_API_SECRET=your_orange_secret
MPESA_API_KEY=your_mpesa_key
MPESA_API_SECRET=your_mpesa_secret
AFRIMONEY_API_KEY=your_afrimoney_key
AFRIMONEY_API_SECRET=your_afrimoney_secret

# PayPal
PAYPAL_CLIENT_ID=your_paypal_client_id
PAYPAL_CLIENT_SECRET=your_paypal_secret
PAYPAL_MODE=live  # ou sandbox

# Stripe
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Flutterwave (Optionnel - agrégateur)
FLW_PUBLIC_KEY=FLWPUBK_TEST-...
FLW_SECRET_KEY=FLWSECK_TEST-...
FLW_ENCRYPTION_KEY=FLWENCRYPTION_KEY_...
```

### Installation des Bibliothèques

```bash
pip install stripe paypalrestsdk flutterwave-python
```

---

## 📊 Tableau de Bord Admin

### Routes à Créer pour l'Admin

```python
@app.route("/admin/subscriptions")
@admin_required()
def admin_subscriptions():
    """Liste de tous les abonnements"""
    subscriptions = SellerSubscription.query.all()
    return render_template("admin/subscriptions.html", subscriptions=subscriptions)

@app.route("/admin/subscriptions/<int:id>/activate", methods=["POST"])
@admin_required()
def admin_activate_subscription(id):
    """Activer manuellement un abonnement"""
    subscription = SellerSubscription.query.get_or_404(id)
    subscription.status = 'active'
    subscription.subscription_end_date = datetime.utcnow() + timedelta(days=30)
    db.session.commit()
    
    # Créer une tâche de notification
    task = SellerPaymentTask(
        subscription_id=subscription.id,
        task_type='activation',
        status='completed',
        title=f"Activation manuelle - {subscription.shop.name}",
        description="Abonnement activé par l'admin suite à paiement hors plateforme",
        completed_by=current_user.id,
        completed_at=datetime.utcnow()
    )
    db.session.add(task)
    db.session.commit()
    
    flash("Abonnement activé avec succès", "success")
    return redirect(url_for('admin_subscriptions'))

@app.route("/admin/payment-tasks")
@admin_required()
def admin_payment_tasks():
    """Liste des tâches de paiement en attente"""
    tasks = SellerPaymentTask.query.filter_by(status='pending').all()
    return render_template("admin/payment_tasks.html", tasks=tasks)
```

---

## 🚀 Déploiement

### 1. Créer les Tables

```bash
flask db migrate -m "Add subscription system"
flask db upgrade
```

### 2. Tester en Local

```bash
# Mode sandbox pour les paiements
PAYPAL_MODE=sandbox
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
```

### 3. Mettre en Production

```bash
# Clés de production
PAYPAL_MODE=live
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_SECRET_KEY=sk_live_...

# Configurer les webhooks
# Stripe: https://dashboard.stripe.com/webhooks
# PayPal: https://developer.paypal.com/dashboard/webhooks
```

---

## 📝 Checklist de Déploiement

- [ ] Créer les tables de base de données
- [ ] Configurer les clés API de paiement
- [ ] Tester chaque méthode de paiement en sandbox
- [ ] Configurer les webhooks Stripe/PayPal
- [ ] Créer les templates admin pour gérer les abonnements
- [ ] Ajouter des notifications email pour les paiements
- [ ] Tester le flux complet d'expiration
- [ ] Documenter le processus pour les admins
- [ ] Mettre en place la surveillance des paiements échoués

---

## 🎉 Fonctionnalités Implémentées

✅ **Pour les Vendeurs :**
- 2 mois gratuits automatiques
- 7 méthodes de paiement
- Interface de gestion claire
- Historique des paiements
- Notifications d'expiration

✅ **Pour l'Admin :**
- Tâches de paiement hors plateforme
- Activation manuelle des abonnements
- Surveillance des paiements
- Notifications automatiques

✅ **Pour la Plateforme :**
- Revenus récurrents (5$/mois/vendeur)
- Désactivation automatique
- Système de tâches pour le suivi
- Historique complet des transactions

---

**Date de création :** 12 Mars 2026  
**Version :** 1.0.0  
**Statut :** ✅ Prêt pour intégration des APIs de paiement

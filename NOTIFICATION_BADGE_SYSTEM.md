# 🔔 Système de Notifications et Badges - Guide Complet

## 🎯 Vue d'Ensemble

Système complet de notifications pour les admins avec :
- ✅ **Badges de notification** sur les boutons du menu
- ✅ **Compteur en temps réel** des tâches en attente
- ✅ **Marquer comme vu** automatiquement ou manuellement
- ✅ **Notifications persistantes** jusqu'à lecture
- ✅ **Mise à jour automatique** toutes les 30 secondes

---

## 📁 Fichiers Créés

### Backend (Python/Flask)

| Fichier | Description |
|---------|-------------|
| `backend/models.py` | 2 nouveaux modèles : `AdminNotification`, `SellerPaymentTask` (mis à jour) |
| `backend/apps.py` | 7 nouvelles routes API et gestion des notifications |

### Frontend (Templates)

| Fichier | Description |
|---------|-------------|
| `admin/payment_tasks.html` | Page de gestion des tâches avec badges |

### Migrations

| Fichier | Description |
|---------|-------------|
| `migrations/versions/7b4411ab6a8c_*.py` | Migration du système de notifications |

---

## 💾 Modèles de Base de Données

### 1. AdminNotification

```python
class AdminNotification:
    """Notifications pour les admins"""
    
    id                  # Identifiant unique
    admin_id            # Admin concerné (FK)
    notification_type   # task_pending, payment_completed, etc.
    is_read             # ✅ Lu ou non (déclenche le badge)
    read_at             # Date de lecture
    title               # Titre de la notification
    message             # Message détaillé
    icon                # Icône FontAwesome
    color               # Couleur (blue, green, yellow, red)
    link                # URL vers la page
    reference_type      # task, payment, subscription, shop
    reference_id        # ID de l'entité
```

### 2. SellerPaymentTask (Mis à jour)

```python
class SellerPaymentTask:
    """Tâches de paiement"""
    
    # ... champs existants ...
    
    is_viewed           # ✅ Vu ou non (déclenche le badge)
    viewed_at           # Date de consultation
    viewed_by           # Admin qui a vu
```

---

## 🔄 Fonctionnement du Système de Badges

### 1. Création d'une Tâche

```python
# Quand un vendeur choisit "Paiement Hors Plateforme"
task = SellerPaymentTask(
    shop_id=shop.id,
    task_type='offline_payment',
    status='pending',
    title=f"Paiement hors plateforme - {shop.name}",
    is_viewed=False  # ← Déclenche le badge
)
db.session.add(task)
db.session.commit()
```

**Résultat :**
- Badge rouge apparaît sur le bouton "Tâches"
- Compteur affiche le nombre de tâches en attente

---

### 2. Affichage du Badge

**Dans le template admin/basee.html (menu) :**

```html
<!-- Bouton Tâches avec badge -->
<a href="{{ url_for('admin_payment_tasks') }}" class="relative">
    <i class="fas fa-tasks"></i>
    Tâches
    
    <!-- Badge -->
    <span class="notification-badge absolute -top-2 -right-2 
                 bg-red-500 text-white text-xs rounded-full 
                 px-2 py-0.5 min-w-[20px] text-center">
        {{ pending_tasks_count }}
    </span>
</a>
```

---

### 3. Marquer comme Vu

**Automatiquement :**
```python
# Quand l'admin accède à la page des tâches
@app.route("/admin/payment-tasks")
def admin_payment_tasks():
    pending_tasks = SellerPaymentTask.query.filter_by(status='pending').all()
    
    # Marquer automatiquement comme vues
    for task in pending_tasks:
        if not task.is_viewed:
            task.is_viewed = True
            task.viewed_at = datetime.utcnow()
            task.viewed_by = current_user.id
    
    db.session.commit()
    return render_template("admin/payment_tasks.html", tasks=pending_tasks)
```

**Manuellement (via JavaScript) :**
```javascript
function markAsViewed(taskId) {
    fetch(`/admin/api/tasks/${taskId}/mark-viewed`, {
        method: 'POST',
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Badge disparaît
            location.reload();
        }
    });
}
```

---

### 4. Mise à Jour Automatique du Badge

**JavaScript (toutes les 30 secondes) :**
```javascript
function updateNotificationBadge() {
    fetch('/admin/api/notification-count')
        .then(response => response.json())
        .then(data => {
            const badge = document.querySelector('.notification-badge');
            
            if (data.total > 0) {
                badge.textContent = data.total;
                badge.classList.remove('hidden');
            } else {
                badge.classList.add('hidden');
            }
        });
}

// Mettre à jour toutes les 30 secondes
setInterval(updateNotificationBadge, 30000);
updateNotificationBadge(); // Premier appel immédiat
```

---

## 📊 API Endpoints

### GET `/admin/api/notification-count`

**Description :** Retourne le nombre de notifications non lues et tâches en attente

**Réponse :**
```json
{
    "unread_notifications": 3,
    "pending_tasks": 5,
    "total": 8
}
```

**Utilisation :**
```javascript
fetch('/admin/api/notification-count')
    .then(response => response.json())
    .then(data => {
        console.log(`Vous avez ${data.total} notifications`);
    });
```

---

### POST `/admin/api/notifications/mark-all-read`

**Description :** Marquer toutes les notifications comme lues

**Réponse :**
```json
{
    "success": true
}
```

**Utilisation :**
```javascript
fetch('/admin/api/notifications/mark-all-read', {
    method: 'POST',
})
.then(response => response.json())
.then(data => {
    if (data.success) {
        // Badge disparaît
    }
});
```

---

### POST `/admin/api/tasks/<task_id>/mark-viewed`

**Description :** Marquer une tâche spécifique comme vue

**Réponse :**
```json
{
    "success": true
}
```

**Utilisation :**
```javascript
fetch('/admin/api/tasks/123/mark-viewed', {
    method: 'POST',
})
.then(response => response.json())
.then(data => {
    // Tâche marquée comme vue
});
```

---

## 🎨 UI/UX des Badges

### Design du Badge

```html
<!-- Badge avec animation -->
<span class="notification-badge 
             absolute -top-2 -right-2 
             bg-red-500 text-white 
             text-xs rounded-full 
             px-2 py-0.5 
             min-w-[20px] text-center
             animate-pulse
             font-bold shadow-lg">
    5
</span>
```

### États du Badge

| État | Apparence | Condition |
|------|-----------|-----------|
| **Nouveau** | 🔴 Rouge + Animation pulse | `is_viewed = False` |
| **Vu** | Gris ou invisible | `is_viewed = True` |
| **Multiple** | Nombre (>1) | `count > 1` |
| **Unique** | Point ou "1" | `count = 1` |
| **Aucun** | Caché | `count = 0` |

---

## 📝 Exemples de Scénarios

### Scénario 1 : Nouveau Paiement Hors Plateforme

```
1. Vendeur choisit "Paiement Hors Plateforme"
   ↓
2. Tâche créée avec is_viewed=False
   ↓
3. Badge rouge apparaît sur "Tâches" (admin)
   ↓
4. Admin reçoit notification: "Nouveau paiement en attente"
   ↓
5. Admin clique sur "Tâches"
   ↓
6. Badge disparaît (marqué automatiquement comme vu)
   ↓
7. Admin active l'abonnement
   ↓
8. Tâche marquée comme completed
```

---

### Scénario 2 : Multiple Tâches en Attente

```
1. 3 vendeurs effectuent un paiement hors plateforme
   ↓
2. 3 tâches créées avec is_viewed=False
   ↓
3. Badge affiche "3" sur "Tâches"
   ↓
4. Admin traite la première tâche
   ↓
5. Badge affiche "2"
   ↓
6. Admin traite les 2 autres
   ↓
7. Badge disparaît
```

---

### Scénario 3 : Notification de Système

```
1. Subscription expire dans 7 jours
   ↓
2. Notification créée avec is_read=False
   ↓
3. Badge apparaît sur "Notifications"
   ↓
4. Admin lit la notification
   ↓
5. is_read=True, read_at=now
   ↓
6. Badge disparaît
```

---

## 🔧 Intégration dans l'Interface Admin

### Dans `admin/basee.html` (Menu Principal)

```html
<!-- Navigation avec badges -->
<nav class="admin-nav">
    <!-- Bouton Tâches -->
    <a href="{{ url_for('admin_payment_tasks') }}" class="nav-item relative">
        <i class="fas fa-tasks"></i>
        <span>Tâches</span>
        
        {% set pending_tasks = SellerPaymentTask.query.filter_by(status='pending').count() %}
        {% if pending_tasks > 0 %}
        <span class="notification-badge 
                     absolute -top-2 -right-2 
                     bg-red-500 text-white 
                     text-xs rounded-full 
                     px-2 py-0.5 min-w-[20px] text-center
                     {{ 'animate-pulse' if pending_tasks > 0 else '' }}">
            {{ pending_tasks }}
        </span>
        {% endif %}
    </a>
    
    <!-- Bouton Notifications -->
    <a href="{{ url_for('admin_notifications') }}" class="nav-item relative">
        <i class="fas fa-bell"></i>
        <span>Notifications</span>
        
        {% set unread = AdminNotification.query.filter_by(admin_id=current_user.id, is_read=False).count() %}
        {% if unread > 0 %}
        <span class="notification-badge 
                     absolute -top-2 -right-2 
                     bg-yellow-500 text-white 
                     text-xs rounded-full 
                     px-2 py-0.5 min-w-[20px] text-center">
            {{ unread }}
        </span>
        {% endif %}
    </a>
</nav>

<script>
// Mettre à jour les badges toutes les 30 secondes
setInterval(function() {
    fetch('/admin/api/notification-count')
        .then(r => r.json())
        .then(data => {
            // Mettre à jour les badges
            updateBadges(data);
        });
}, 30000);
</script>
```

---

## 📊 Statistiques et Suivi

### Requêtes SQL Utiles

```sql
-- Nombre de tâches en attente
SELECT COUNT(*) FROM seller_payment_tasks WHERE status = 'pending';

-- Nombre de notifications non lues par admin
SELECT admin_id, COUNT(*) 
FROM admin_notifications 
WHERE is_read = False 
GROUP BY admin_id;

-- Tâches non vues
SELECT COUNT(*) FROM seller_payment_tasks WHERE is_viewed = False;

-- Temps moyen de traitement des tâches
SELECT AVG(julianday(completed_at) - julianday(created_at)) 
FROM seller_payment_tasks 
WHERE status = 'completed';
```

---

## ✅ Checklist d'Implémentation

- [x] Modèles `AdminNotification` et `SellerPaymentTask` créés
- [x] Migration appliquée avec succès
- [x] Routes API créées (`/admin/api/notification-count`, etc.)
- [x] Template `admin/payment_tasks.html` créé
- [x] JavaScript de mise à jour automatique (30s)
- [x] Badges affichés dans le menu admin
- [x] Marquer automatiquement comme vu à l'ouverture
- [x] Marquer manuellement via bouton

---

## 🎉 Fonctionnalités Clés

### Pour les Admins
- ✅ **Badge rouge** sur les boutons avec notifications
- ✅ **Compteur en temps réel** (mise à jour 30s)
- ✅ **Marquage automatique** quand on consulte
- ✅ **Marquage manuel** via bouton
- ✅ **Notifications persistantes** jusqu'à lecture

### Pour la Plateforme
- ✅ **Suivi des actions** admin
- ✅ **Statistiques de traitement**
- ✅ **Audit trail** complet
- ✅ **Notifications contextuelles**

---

**Date de création :** 13 Mars 2026  
**Version :** 1.0.0  
**Statut :** ✅ Opérationnel

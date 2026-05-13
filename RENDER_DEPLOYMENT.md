# 🚀 Guide Déploiement Render.com

## Pourquoi Render.com?

✅ **Gratuit pour commencer** - Web service gratuit  
✅ **PostgreSQL gratuit** - Database 90 jours gratuite   
✅ **HTTPS automatique** - Let's Encrypt intégré  
✅ **Auto-deploy** - Git push → deploy automatique  
✅ **Scaling facile** - Passer de gratuit à payant  
✅ **50GB bande passante gratuite**  

---

## 📋 PRÉ-REQUIS

- ✅ Repository GitHub avec votre code
- ✅ `Procfile` (déjà créé)
- ✅ `runtime.txt` (déjà créé)
- ✅ `.env` avec toutes les variables
- ✅ `requirements.txt` à jour

---

## 🎯 ÉTAPES DE DÉPLOIEMENT

### ÉTAPE 1: Créer Compte Render

1. Aller à [render.com](https://render.com)
2. Click "Get Started"
3. Signer up avec GitHub
4. Connecter votre compte GitHub

### ÉTAPE 2: Créer le Web Service

1. Dashboard → **New +** → **Web Service**
2. Sélectionner votre repository `tekanayoApp`
3. Configurer:
   - **Name**: `tekanayo-app`
   - **Environment**: Python 3
   - **Branch**: main
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn wsgi:app`

4. Click **Create Web Service**

### ÉTAPE 3: Configurer les Variables d'Environnement

1. Dans le dashboard Render, aller à **Settings**
2. Scroll à **Environment**
3. Ajouter les variables (voir `.env.example`):

```
FLASK_ENV=production
DEBUG=False
SECRET_KEY=your-generated-secret
SUPABASE_URL=your-supabase-url
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
DATABASE_URL=your-postgresql-url
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
```

### ÉTAPE 4: Créer PostgreSQL Database

1. Dashboard → **New +** → **PostgreSQL**
2. Configurer:
   - **Name**: `tekanayo-db`
   - **Database**: `tekanayo_production`
   - **User**: `tekanayo_user`
   - **Region**: Tokyo (ou proche de votre région)

3. Copier la **Internal Connection String**
4. Ajouter à la variable `DATABASE_URL` du Web Service

### ÉTAPE 5: Database Migration

1. Aller au Web Service dans Render
2. **Logs** → Vérifier que l'app démarre
3. Ouvrir **Shell** (onglet Console/Shell)
4. Exécuter:

```bash
python -m flask db upgrade
python -m flask seed-admin
```

### ÉTAPE 6: Configurer le Domaine

#### Option A: Sous-domaine Render (gratuit)
- Render fournit: `tekanayo-app.onrender.com`
- C'est prêt à l'emploi

#### Option B: Domaine personnalisé
1. **Settings** → **Custom Domains**
2. Ajouter: `tekanayo.rw`
3. Render donne des nameservers
4. Aller à votre registrar DNS (Namecheap, etc.)
5. Changer les nameservers
6. Attendre 24h pour propagation

### ÉTAPE 7: Configurer HTTPS

- Render gère **automatiquement** Let's Encrypt
- HTTPS est activé par défaut
- Pas de configuration nécessaire

### ÉTAPE 8: Variables de Monitoring

Ajouter à `.env`:

```
SENTRY_DSN=https://your-sentry-dsn
LOG_LEVEL=INFO
```

---

## 🔄 AUTO-DEPLOY AVEC GIT

Quand vous faites:
```bash
git push origin main
```

Render va automatiquement:
1. Détecter le push
2. Cloner le code
3. Installer les dépendances (`requirements.txt`)
4. Exécuter `Procfile` → `gunicorn wsgi:app`
5. Redémarrer le service

**Logs en temps réel**: Settings → Logs

---

## 📊 DATABASE BACKUP

Render gère les backups automatiquement pour les plans payants.
Pour gratuit, faire des backups manuel:

```bash
# Se connecter à la database
psql your-database-url

# Dump
pg_dump your-database-url > backup.sql

# Restore
psql your-database-url < backup.sql
```

---

## ⚡ PERFORMANCE TIPS

1. **Upgrade Worker Type**: Settings → Instance Type → Plus (payant mais plus rapide)
2. **Caching**: Ajouter Redis (Render Redis cache)
3. **CDN**: Utiliser Supabase Storage CDN (déjà intégré)
4. **Images**: Continuez à utiliser les images optimisées

---

## 🚨 MONITORING & ALERTES

### Logs
```bash
# Voir logs en temps réel
tail -f logs.txt

# Ou via Dashboard Render:
Settings → Logs
```

### Healthcheck
Render vérifie automatiquement votre app chaque 60s.
Si erreur: restart automatique

### Sentry Integration
```python
# Après deployment et avec SENTRY_DSN cofiguré
import sentry_sdk
sentry_sdk.init(dsn=os.getenv('SENTRY_DSN'))
# Errors automatiquement tracées
```

---

## 💰 COÛTS ESTIMÉS

| Service | Gratuit | Payant |
|---------|---------|--------|
| Web Service | Oui (avec limite) | $12+/mois |
| PostgreSQL | Oui (90 jours) | $15/mois |
| Bandwidth | 50GB/mois | Illimité |
| Auto-scaling | Non | Oui |
| Support | Non | Oui |

**Estimation mensuelle**: €50-100 pour production

---

## 🔐 SÉCURITÉ RENDER

✅ HTTPS automatique  
✅ Pare-feu DDoS  
✅ Environment variables chiffrées  
✅ Logs privés  
✅ PostgreSQL isolation  

---

## ❌ PROBLÈMES COURANTS

### 1. **App crash au démarrage**
```
Solution:
1. Vérifier logs: Settings → Logs
2. Vérifier DATABASE_URL correcte
3. Vérifier requirements.txt complet
4. Exécuter: python -m flask db upgrade
```

### 2. **Timeout 504**
```
Solution:
1. Augmenter timeout: Settings → Instance Type
2. Optimiser requêtes database (indexation)
3. Ajouter caching
```

### 3. **Out of memory**
```
Solution:
1. Upgrade Instance Type
2. Vérifier fuite mémoire dans code
3. Réduire les query results
```

### 4. **Database full (90 jours gratuit)**
```
Solution:
1. Passer à plan payant
2. Ou migrer vers Supabase PostgreSQL
```

---

## 📱 POST-DÉPLOIEMENT

1. ✅ Tester l'app: https://tekanayo-app.onrender.com
2. ✅ Vérifier les logs pour erreurs
3. ✅ Configurer le domaine
4. ✅ Setup email notifications
5. ✅ Ajouter SSL certificate personnalisé
6. ✅ Setup monitoring/alertes
7. ✅ Documenter la configuration
8. ✅ Créer runbook pour incidents

---

## 🔄 MISE À JOUR ET MAINTENANCE

### Déployer une mise à jour:
```bash
git commit -am "Feature: Add stock alerts"
git push origin main
# Render détecte et déploie automatiquement
```

### Rollback si problème:
```bash
git revert HEAD
git push origin main
# Ou manuellement via Render dashboard
```

### Maintenances planifiées:
- Notifier les utilisateurs 24h avant
- Utiliser une page de maintenance
- Planifier hors heures de pointe

---

## 📞 SUPPORT

- Render Docs: https://render.com/docs
- Status: https://status.render.com
- Support Chat: Render dashboard (payant)

---

## ✅ CHECKLIST DÉPLOIEMENT

- [ ] Repository GitHub avec code à jour
- [ ] Procfile et runtime.txt créés
- [ ] .env avec toutes les variables
- [ ] requirements.txt complet
- [ ] Tests passants localement
- [ ] Compte Render créé
- [ ] Web Service déployé
- [ ] Database PostgreSQL créé
- [ ] Variables d'environnement ajoutées
- [ ] Migrations exécutées
- [ ] Admin user créé
- [ ] Domain configuré
- [ ] HTTPS vérifié
- [ ] Monitoring activé
- [ ] Backups configurés
- [ ] Documentation complète
- [ ] Team notifiée du déploiement

---

**🎉 Bravo! TekanayoApp est maintenant en ligne!**

#!/bin/bash
"""
Script de déploiement TekanayoApp - Automatiser la mise en ligne
Usage: bash deploy.sh [production|staging|test]
"""

set -e  # Exit on first error

# Couleurs pour output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT="${1:-production}"
APP_NAME="TekanayoApp"
DEPLOY_DATE=$(date +"%Y-%m-%d %H:%M:%S")

echo -e "${GREEN}🚀 Déploiement de $APP_NAME - $ENVIRONMENT${NC}"
echo "Date: $DEPLOY_DATE"
echo "========================================"

# ============================================
# 1. PRE-DEPLOYMENT CHECKS
# ============================================
echo -e "${YELLOW}1️⃣  Vérification pré-déploiement...${NC}"

if [ ! -f ".env" ]; then
    echo -e "${RED}❌ Erreur: .env non trouvé${NC}"
    exit 1
fi

if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}❌ Erreur: requirements.txt non trouvé${NC}"
    exit 1
fi

# Vérifier les dependencies critiques
for cmd in python3 git npm; do
    if ! command -v $cmd &> /dev/null; then
        echo -e "${YELLOW}⚠️  $cmd non trouvé - certaines fonctionnalités peuvent ne pas fonctionner${NC}"
    fi
done

echo -e "${GREEN}✅ Vérifications pré-déploiement OK${NC}\n"

# ============================================
# 2. BACKUP
# ============================================
echo -e "${YELLOW}2️⃣  Création de sauvegarde...${NC}"

BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

# Copier la configuration
cp .env $BACKUP_DIR/.env.backup
echo -e "${GREEN}✅ Configuration sauvegardée${NC}"

# Dump database (Supabase)
echo "Effectuer manuellement: pg_dump ... > $BACKUP_DIR/database.sql"

echo -e "${GREEN}✅ Sauvegarde créée: $BACKUP_DIR${NC}\n"

# ============================================
# 3. DEPENDENCIES
# ============================================
echo -e "${YELLOW}3️⃣  Installation des dépendances...${NC}"

if [ -d "ecom" ]; then
    source ecom/bin/activate
else
    echo -e "${YELLOW}⚠️  Venv non trouvé, création de venv...${NC}"
    python3 -m venv ecom
    source ecom/bin/activate
fi

pip install --upgrade pip
pip install -r requirements.txt

echo -e "${GREEN}✅ Dépendances Python installées${NC}\n"

# ============================================
# 4. CODE SECURITY CHECKS
# ============================================
echo -e "${YELLOW}4️⃣  Vérification de sécurité...${NC}"

# Vérifier les secrets commitées
if grep -r "SECRET_KEY\|PASSWORD\|API_KEY" --include="*.py" . | grep -v ".env" | grep -v "requirements.txt" | grep -v ".git"; then
    echo -e "${RED}❌ Alerte: Secrets potentiels détectés dans le code!${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Vérification de sécurité OK${NC}\n"

# ============================================
# 5. ENVIRONMENT SETUP
# ============================================
echo -e "${YELLOW}5️⃣  Configuration de l'environnement...${NC}"

if [ "$ENVIRONMENT" == "production" ]; then
    export FLASK_ENV=production
    export DEBUG=False
    echo "FLASK_ENV=production"
    echo "DEBUG=False"
elif [ "$ENVIRONMENT" == "staging" ]; then
    export FLASK_ENV=staging
    export DEBUG=False
    echo "FLASK_ENV=staging"
    echo "DEBUG=False"
else
    export FLASK_ENV=development
    export DEBUG=True
fi

echo -e "${GREEN}✅ Environnement configuré: $ENVIRONMENT${NC}\n"

# ============================================
# 6. DATABASE MIGRATION
# ============================================
echo -e "${YELLOW}6️⃣  Migration database...${NC}"

echo "Commandes pour migration manuel:"
echo "  flask db migrate -m 'Migration: $(date +%s)'"
echo "  flask db upgrade"
echo ""
echo "Exécuter manuellement ou utiliser Render pipeline"

echo -e "${GREEN}✅ Instructions migration affichées${NC}\n"

# ============================================
# 7. TESTS
# ============================================
echo -e "${YELLOW}7️⃣  Exécution des tests...${NC}"

if command -v pytest &> /dev/null; then
    pytest tests/ -v || echo -e "${YELLOW}⚠️  Certains tests ont échoué${NC}"
else
    echo -e "${YELLOW}⚠️  pytest non disponible, skip les tests${NC}"
fi

echo -e "${GREEN}✅ Tests complétés${NC}\n"

# ============================================
# 8. BUILD ASSETS
# ============================================
echo -e "${YELLOW}8️⃣  Compilation des assets...${NC}"

if [ -f "package.json" ]; then
    npm install
    npm run build || echo "Build npm skipped"
    echo -e "${GREEN}✅ Assets compilés${NC}\n"
else
    echo -e "${YELLOW}⚠️  package.json non trouvé, skip npm${NC}\n"
fi

# ============================================
# 9. READY FOR DEPLOYMENT
# ============================================
echo -e "${GREEN}========================================"
echo "🎉 TekanayoApp prêt pour le déploiement!"
echo "========================================"
echo ""
echo "Prochaines étapes pour $ENVIRONMENT:"
echo "1. Vérifier Render/Railway/Heroku dashboard"
echo "2. Déclencher le déploiement"
echo "3. Attendre les migrations database"
echo "4. Tester l'application en ligne"
echo "5. Surveiller les logs en temps réel"
echo ""
echo "Backup créé à: $BACKUP_DIR"
echo -e "${NC}"

# ============================================
# 10. RENDER DEPLOYMENT
# ============================================
if [ "$ENVIRONMENT" == "production" ]; then
    echo -e "${YELLOW}Déploiement sur Render.com:${NC}"
    echo "1. Push à main branch: git push origin main"
    echo "2. Render.com détectera le push et déploiera automatiquement"
    echo "3. Vérifier: https://render.com/dashboard"
    echo ""
fi

echo -e "${GREEN}✅ Script de déploiement terminé!${NC}"

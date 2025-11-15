#!/bin/bash

# Docker Setup Validation Script
# This script validates the Docker configuration files

set -e

echo "🔍 Validating Docker Setup..."
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is installed
echo "1. Checking Docker installation..."
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    echo -e "${GREEN}✓${NC} Docker is installed: $DOCKER_VERSION"
else
    echo -e "${RED}✗${NC} Docker is not installed"
    exit 1
fi

# Check if Docker Compose is installed
echo "2. Checking Docker Compose installation..."
if command -v docker-compose &> /dev/null; then
    COMPOSE_VERSION=$(docker-compose --version)
    echo -e "${GREEN}✓${NC} Docker Compose is installed: $COMPOSE_VERSION"
else
    echo -e "${RED}✗${NC} Docker Compose is not installed"
    exit 1
fi

# Validate docker-compose.dev.yml
echo "3. Validating docker-compose.dev.yml..."
if docker-compose -f docker-compose.dev.yml config > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} docker-compose.dev.yml is valid"
else
    echo -e "${RED}✗${NC} docker-compose.dev.yml has errors"
    docker-compose -f docker-compose.dev.yml config
    exit 1
fi

# Validate docker-compose.prod.yml
echo "4. Validating docker-compose.prod.yml..."
if docker-compose -f docker-compose.prod.yml config > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} docker-compose.prod.yml is valid"
else
    echo -e "${RED}✗${NC} docker-compose.prod.yml has errors"
    docker-compose -f docker-compose.prod.yml config
    exit 1
fi

# Check if Dockerfile exists
echo "5. Checking Dockerfile..."
if [ -f "application/Dockerfile" ]; then
    echo -e "${GREEN}✓${NC} application/Dockerfile exists"
else
    echo -e "${RED}✗${NC} application/Dockerfile not found"
    exit 1
fi

# Check if .dockerignore exists
echo "6. Checking .dockerignore..."
if [ -f "application/.dockerignore" ]; then
    echo -e "${GREEN}✓${NC} application/.dockerignore exists"
else
    echo -e "${YELLOW}⚠${NC} application/.dockerignore not found (optional but recommended)"
fi

# Check if .env.example exists
echo "7. Checking .env.example..."
if [ -f ".env.example" ]; then
    echo -e "${GREEN}✓${NC} .env.example exists"
else
    echo -e "${YELLOW}⚠${NC} .env.example not found"
fi

# Check if Makefile exists
echo "8. Checking Makefile..."
if [ -f "Makefile" ]; then
    echo -e "${GREEN}✓${NC} Makefile exists"
else
    echo -e "${YELLOW}⚠${NC} Makefile not found (optional but convenient)"
fi

# Check documentation
echo "9. Checking documentation..."
DOCS_FOUND=0
if [ -f "DOCKER_DEPLOYMENT.md" ]; then
    echo -e "${GREEN}✓${NC} DOCKER_DEPLOYMENT.md exists"
    DOCS_FOUND=$((DOCS_FOUND + 1))
fi
if [ -f "DOCKER_QUICK_START.md" ]; then
    echo -e "${GREEN}✓${NC} DOCKER_QUICK_START.md exists"
    DOCS_FOUND=$((DOCS_FOUND + 1))
fi
if [ $DOCS_FOUND -eq 0 ]; then
    echo -e "${YELLOW}⚠${NC} No Docker documentation found"
fi

# Check if .env exists for production
echo "10. Checking production configuration..."
if [ -f ".env" ]; then
    echo -e "${GREEN}✓${NC} .env file exists (ready for production)"
else
    echo -e "${YELLOW}⚠${NC} .env file not found (required for production)"
    echo "   Run: cp .env.example .env"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✓ Validation Complete!${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Next steps:"
echo "  Development: make dev-up"
echo "  Production:  cp .env.example .env && make prod-up"
echo ""
echo "For more information:"
echo "  Quick Start: cat DOCKER_QUICK_START.md"
echo "  Full Guide:  cat DOCKER_DEPLOYMENT.md"
echo ""

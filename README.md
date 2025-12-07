# Odoo 19 Enterprise - VPA Custom Modules

This repository contains VPA custom modules for Odoo 19 Enterprise deployment on Odoo.sh.

## Directory Structure

```
UD-Odoo19-Enterprise/
├── enterprise/           # Odoo Enterprise modules
├── custom_addons/        # GhalaGroup custom modules (Beta branch)
├── data/                 # Odoo data directory
├── postgres_data/        # PostgreSQL data
├── config/               # Odoo configuration
│   └── odoo.conf
├── backup_files/         # Database backup and filestore
│   ├── dump.sql
│   └── filestore/
├── scripts/              # Helper scripts
│   ├── import_db.sh
│   └── start.sh
└── docker-compose.yml
```

## Quick Start

Simply run:

```bash
./scripts/start.sh
```

This will:
1. Start PostgreSQL container
2. Import the database from backup
3. Copy filestore with correct permissions
4. Start Odoo container
5. Open Odoo in your browser

## Services

- **Odoo**: http://localhost:8071
- **PostgreSQL**: localhost:5436

## Credentials

- Database user: `odoo`
- Database password: `odoo`
- Database name: `odoo`

## Manual Operations

### Start services:
```bash
docker-compose up -d
```

### Stop services:
```bash
docker-compose down
```

### View Odoo logs:
```bash
docker-compose logs -f odoo
```

### View PostgreSQL logs:
```bash
docker-compose logs -f db
```

### Restart Odoo:
```bash
docker-compose restart odoo
```

### Import database only:
```bash
./scripts/import_db.sh
```

## Configuration

Odoo configuration is in [config/odoo.conf](config/odoo.conf).

Key settings:
- Enterprise addons: `/mnt/enterprise-addons`
- Custom addons: `/mnt/custom-addons`
- Workers: 4
- Data directory: `/var/lib/odoo`

## Custom Modules

Custom modules from GhalaGroup repository (Beta branch) are located in `custom_addons/`.

To update custom modules:
```bash
cd custom_addons
git pull origin Beta
docker-compose restart odoo
```

## Troubleshooting

### Database connection issues:
```bash
docker-compose logs db
```

### Odoo not starting:
```bash
docker-compose logs odoo
```

### Reset everything:
```bash
docker-compose down -v
sudo rm -rf postgres_data/* data/*
./scripts/start.sh
```

### Check container status:
```bash
docker-compose ps
```

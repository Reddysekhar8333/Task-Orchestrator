# Azure connectivity setup

This project is configured to connect to:
- **Azure SQL Database** for Django data.
- **Azure Blob Storage containers** for uploaded/static files.

## 1) Configure environment variables

Copy `.env.example` to `.env` and set real values:

```bash
cp .env.example .env
```

Required values:
- `USE_AZURE_SQL=True`
- `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASS`
- `AZURE_STORAGE_CONNECTION_STRING` (or `AZURE_ACCOUNT_NAME` + `AZURE_ACCOUNT_KEY`)
- `AZURE_MEDIA_CONTAINER` and `AZURE_STATIC_CONTAINER`

## 2) Create storage containers in Azure

Create the blob containers once in your storage account:
- `media`
- `static`

You can use Azure Portal or Azure CLI:

```bash
az storage container create --name media --connection-string "$AZURE_STORAGE_CONNECTION_STRING"
az storage container create --name static --connection-string "$AZURE_STORAGE_CONNECTION_STRING"
```

## 3) Validate SQL connection

```bash
cd task_manager
python manage.py showmigrations
```

If connection succeeds, migrations are listed from the Azure SQL database.

## 4) Run with Docker

```bash
docker compose up --build
```

Both `web` and `celery` services now receive the Azure SQL and Storage env variables.
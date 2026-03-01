# Making Task-Orchestrator accessible to everyone

Use this checklist to turn your local setup into a public production deployment.

## 1) Run the app on a public server

The repository already includes a Docker Compose stack with:
- `web` (Django + Gunicorn)
- `celery`
- `redis`
- `nginx` exposed on port `80`

On your VM (Azure, AWS, GCP, or any VPS):

```bash
git clone <your-repo-url>
cd Task-Orchestrator
docker compose up -d --build
```

## 2) Set production environment variables

Create a `.env` file before starting Compose. At minimum:

```env
DEBUG=False
SECRET_KEY=<strong-random-secret>
ALLOWED_HOSTS=your-domain.com,www.your-domain.com,<server-public-ip>

USE_AZURE_SQL=True
DB_HOST=<azure-sql-host>
DB_PORT=1433
DB_NAME=<db-name>
DB_USER=<db-user>
DB_PASS=<db-password>

AZURE_STORAGE_CONNECTION_STRING=<connection-string>
AZURE_MEDIA_CONTAINER=media
AZURE_STATIC_CONTAINER=static
```

If you use Azure Key Vault, set `AZURE_VAULT_NAME` and keep DB/storage secrets there.

## 3) Open network access safely

On your cloud firewall / NSG:
- Allow inbound `80` (HTTP)
- Allow inbound `443` (HTTPS) after TLS is enabled
- Keep DB ports private (do not expose Azure SQL publicly to the world)

## 4) Point a domain to your server

Create DNS records:
- `A` record: `your-domain.com` -> server public IP
- `A` record: `www.your-domain.com` -> server public IP

## 5) Enable HTTPS (required for real users)

Recommended options:
- Use a managed edge service (Cloudflare/Azure Front Door/Application Gateway), or
- Install Certbot on the VM and issue Let's Encrypt certificates

Terminate TLS at the edge or nginx and redirect all HTTP traffic to HTTPS.

## 6) Configure browser access (CORS)

If users access the API from a separate frontend domain, configure Django CORS settings for that domain (for example, `https://app.your-domain.com`).

## 7) Verify external access

From a machine outside your VM/network:

```bash
curl -i http://your-domain.com/
curl -i https://your-domain.com/api/
```

Also test login and authenticated task APIs with JWT.

## 8) Keep it reliable

- Add health checks/uptime monitoring
- Use automated backups for Azure SQL
- Ship logs to a centralized system
- Keep CI/CD (Jenkins) deploying tested images only

---

## Notes specific to this repository

- `docker-compose.yml` expects an nginx config at `nginx/default.conf`.
- This repository now includes a baseline reverse-proxy config there.
- Django reads `ALLOWED_HOSTS` from environment variables, so set it explicitly for your domain/IP.
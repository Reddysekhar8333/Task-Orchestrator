# Making Task-Orchestrator accessible to everyone

Use this checklist to turn your local setup into a public production deployment.
### If you see `HYT00 Login timeout expired`

That error means the Django container cannot reach SQL Server. Check these in order:

1. **Make sure Azure SQL is actually intended**
   - For local/dev without Azure SQL, set `USE_AZURE_SQL=False` in `.env`.
2. **Verify host and credentials**
   - `DB_HOST` should be your Azure SQL server FQDN (for example, `myserver.database.windows.net`).
   - `DB_PORT` should be `1433`.
   - Confirm `DB_NAME`, `DB_USER`, `DB_PASS` are correct.
3. **Allow network access from your VM**
   - In Azure SQL Server firewall, add your VM public outbound IP.
   - If using private endpoint/VNet integration, ensure the VM can resolve and route to that private endpoint.
4. **Test connectivity from the host**
   - Example: `nc -vz <azure-sql-host> 1433`
   - If this fails, it's a network/firewall/routing problem (not Django).
5. **ODBC Driver 18 TLS requirements**
   - Driver 18 enforces encryption by default. Keep SSL parameters consistent with your SQL policy.

## 1) Run the app on a public server

The repository already includes a Docker Compose stack with:
- `web` (Django + Gunicorn)
- `celery`
- `redis`
- `nginx` exposed on host port `80` by default (override with `NGINX_HOST_PORT` if port 80 is already in use)

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

# Optional: avoid host-port conflicts on machines where port 80 is already taken
NGINX_HOST_PORT=8080
```

Use Jenkins Global Credentials (or your CI/CD secret manager) to inject these values as environment variables at deploy time.

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

## 9) Troubleshooting: `502 Bad Gateway` with Jenkins on the same VM

Port mapping in this repository is:
- `web` (Django/Gunicorn) listens on container port `8000`.
- `nginx` listens on container port `80` and is published as `${NGINX_HOST_PORT:-80}:80`.

So by default, app nginx uses host port `80` (not `8080`).
A conflict with Jenkins on `8080` only occurs if you explicitly set:

```env
NGINX_HOST_PORT=8080
```

If Jenkins logs show:
- `Failed to bind to 0.0.0.0:8080`
- `java.net.BindException: Address already in use`

then something is already listening on host port `8080`.

Check listeners:

```bash
sudo lsof -iTCP:8080 -sTCP:LISTEN -n -P
sudo ss -ltnp 'sport = :8080'
```

Resolution options:
- Keep Jenkins on `8080` and publish app nginx on a different host port (for example `NGINX_HOST_PORT=8081`), **or**
- Keep app nginx on `8080` and run Jenkins on another port (for example `8081` or `9090`).

After changes, restart services and validate:

```bash
curl -I http://127.0.0.1:<jenkins-or-nginx-port>
curl -I http://<your-domain-or-vm-ip>/
```



---

## Notes specific to this repository

- `docker-compose.yml` expects an nginx config at `nginx/default.conf`.
- This repository now includes a baseline reverse-proxy config there.
- Django reads `ALLOWED_HOSTS` from environment variables, so set it explicitly for your domain/IP.


## 10) Troubleshooting: intermittent `502 Bad Gateway` after container restarts

If nginx starts fine but later begins returning `502 Bad Gateway`, your upstream DNS may be stale after the `web` container is recreated with a new IP.

This repository now configures nginx to re-resolve Docker service DNS (`resolver 127.0.0.11`) and proxies through a variable-based upstream, which prevents stale-IP 502s.

After pulling this change, redeploy/restart nginx:

```bash
docker compose up -d --build nginx web
```
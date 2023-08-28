# CameraTrap 2021

- `docker-compose.yml`: yml file for development
- `docker-compose-initdb.yml`: yml file for development (start from xxx.sql.gz dump file)
- `production.yml` yml file for for production
- `Makefile` for command shortcuts

## Development

### Frontend (Search page)

folder: `frontend-search`
```bash
$ cd frontend-search
```

Setting Environment

`.env` for local development

`.env.prod` for production build

local development setting:
```
MY_ENV=dev
API_URL=http://127.0.0.1:8000/api/
```

Install packages

```bash
$ yarn install
```

Run for development

```bash
$ yarn start
```

### Data Model

- DeploymentJournal: 相機行程
- DeploymentStat: 相機位置工作時數
- `script/import-deployment-stat.py` 計算/匯入工作時數


## Nginx & Let's Encrypt for HTTPS
[Setup referece](https://pentacent.medium.com/nginx-and-lets-encrypt-with-docker-in-less-than-5-minutes-b4b8a60d3a71)

Scripts:
- Nginx config: [nginx-django.conf](./scripts/nginx-django.conf)
- Docker config: [production.yml](./production.yml)
- Initialize let's encrypt: [init-letsencrypt.sh](./init-letsencrypt.sh)

NOTES: 
1. Open port 443 on EC2
2. Link nginx to django in docker config otherwise nginx cannot find correct upstream
3. Make sure to check if data path & docker-compose yml filename in `init-letsencrypt.sh` are correct
4. When developinglocally by docker, https (provided by nginx) will not be available, so login through ORCID will fail.

## Deployment

gunicorn should add `--limit-request-line 8190`, otherwise the search page download api may cause verbose querystring too long error
 

# CameraTrap 2021

`docker-compose.yml`: yml file for development 
`production.yml` yml file for for production
`Makefile` for command shortcuts

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
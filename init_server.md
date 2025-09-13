
## Notes

### Deployment Server Setup

Install docker-compose

```shell
DOCKER_CONFIG=${DOCKER_CONFIG:-$HOME/.docker}
mkdir -p $DOCKER_CONFIG/cli-plugins
curl -SL https://github.com/docker/compose/releases/download/v2.35.1/docker-compose-linux-x86_64 -o $DOCKER_CONFIG/cli-plugins/docker-compose
```

Get Application
```shell
git clone https://github.com/Iyki/alarino.git
cd alarino
```

Deploy Environment file to server (from local machine after ssh setup done)
```shell
 scp .env root@alarino.com:/root/alarino/alarino_backend/.env
```

Build Application
```
sudo apt update
sudo apt install docker.io docker-compose 
sudo docker compose up --build -d
```

Set up certificates
```
sudo systemctl stop nginx
sudo systemctl disable nginx

sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d alarino.com -d www.alarino.com
0 0 * * * certbot renew --webroot -w /var/www/certbot --quiet && docker exec alarino-10-nginx-1 nginx -s reload

```

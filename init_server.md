

## Notes
```

/*

docker compose

DOCKER_CONFIG=${DOCKER_CONFIG:-$HOME/.docker}
mkdir -p $DOCKER_CONFIG/cli-plugins
curl -SL https://github.com/docker/compose/releases/download/v2.35.1/docker-compose-linux-x86_64 -o $DOCKER_CONFIG/cli-plugins/docker-compose



git clone https://github.com/Iyki/alarino.git
cd alarino

sudo apt update
sudo apt install docker.io docker-compose 
sudo docker compose up --build -d


// env file to deploy
 scp .env root@alarino.com:/root/alarino/alarino_backend/.env
*/

sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d alarino.com -d www.alarino.com
0 0 * * * certbot renew --webroot -w /var/www/certbot --quiet && docker exec alarino-10-nginx-1 nginx -s reload

sudo systemctl stop nginx
sudo systemctl disable nginx

```



## Frontend setup [alarino_frontend](./alarino_frontend/)
```
cd alarino-frontend
brew install npm
npm install  // setting up from package lock
npm run dev  

# npm run build // npm run build (Vite) to generate static files in a /build or /dist folder for production.
```
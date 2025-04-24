# alarino

## Backend setup [alarino-backend](alarino_backend/)
```
cd alarino-backend
conda env create alarino
conda activate alarino

conda create --name alarino --file conda-requirements.txt

# or 
# python -m venv .venv
# source .venv/bin/activate
# pip install -r pip-requirements.txt if using python virtual environments
```

### Run backend app
```
python app.py
```
### test the backend
```
pytest
```

## Frontend setup [alarino-frontend](./alarino-frontend/)
```
cd alarino-frontend
brew install npm
npm install  // setting up from package lock
npm run dev  

# npm run build // npm run build (Vite) to generate static files in a /build or /dist folder for production.
```

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
sudo docker-compose up --build -d


// env file to deploy
 scp .env root@alarino.com:/root/alarino/alarino_backend/.env
*/

sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d alarino.com -d www.alarino.com
0 0 * * * certbot renew --quiet && docker exec nginx nginx -s reload

sudo systemctl stop nginx
sudo systemctl disable nginx

```




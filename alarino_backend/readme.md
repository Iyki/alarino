## Backend setup [alarino-backend](alarino_backend/)
```
cd alarino-backend
conda env create alarino
conda activate alarino

# python -m pip list --format=freeze > pip-requirements.txt  --to save python libraries used in conda
# conda list -e > conda-requirements.txt -- save conda libraries

conda create --name alarino --file conda-requirements.txt

# or 
# python -m venv .venv
# source .venv/bin/activate
# pip install -r pip-requirements.txt if using python virtual environments
```
### Run scripts
```
python -m data.seed_data

```

### Run backend app
```
python app.py 
```
or
[docker run instructions](../init_server.md/)

### test the backend
```
pytest
```
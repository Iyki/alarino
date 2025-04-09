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

#### Database setup
```
# export FLASK_APP=app.py
# flask db init

```

### Run backend app
```
python app.py
```
### test the backend
```
pytest
```
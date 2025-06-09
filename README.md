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



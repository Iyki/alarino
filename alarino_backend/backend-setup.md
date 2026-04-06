## Backend setup [alarino-backend](../alarino_backend/)

```
cd alarino_backend
```
### Conda Setup
```
conda create -n alarino python=3.11
conda activate alarino
python -m pip install -e .[dev]

# Optional virtualenv alternative
# python -m venv .venv
# source .venv/bin/activate
# pip install -e .[dev]
```

### Update libraries
```shell
python -m pip install -e .[dev] --upgrade
```

### Run scripts
```
python -m main.app

```

### Run backend app
```
python -m main.app
```
or
[docker run instructions](../init_server.md/)

### test the backend
```
pytest
```

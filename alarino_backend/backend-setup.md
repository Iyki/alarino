## Backend Setup

The canonical project setup guide is [Developer Setup](../docs/developer_setup.md).

### Conda Setup

```bash
cd alarino_backend
conda create -n alarino python=3.11
conda activate alarino
python -m pip install -e .[dev]
```

### Run Backend App

```bash
python -m alarino_backend.app
```

### Run Data Scripts

```bash
python -m alarino_backend.data.generate_sitemap
python -m alarino_backend.data.proverbs_loader
python -m alarino_backend.data.word_translations_loader
```

### Test Backend

```bash
python -m pytest
```

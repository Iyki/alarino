import importlib


def test_package_import_succeeds():
    package = importlib.import_module("alarino_backend")

    assert package.__version__


def test_data_script_modules_import():
    modules = [
        "alarino_backend.data.create_tables",
        "alarino_backend.data.generate_sitemap",
        "alarino_backend.data.proverbs_loader",
        "alarino_backend.data.word_translations_loader",
    ]

    for module in modules:
        assert importlib.import_module(module)

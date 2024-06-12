# bookerics

bookmarks, but for Erics

![screenshot](screenshot.png)

## Running the App

Using Poetry (recommended):

```
poetry install --no-root
poetry run uvicorn --reload src.main:app
```

Or without Poetry:

```
pip install .
uvicorn --reload src.main:app
```

## Running the Tests

Using Poetry (recommended):

```
poetry run pytest
```

Or without Poetry:

```
pytest
```

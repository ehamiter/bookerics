# bookerics

bookmarks, but for Erics

![screenshot](screenshot.png)


## This is a continual work in progress.

Things will definitely break in here, but if you want to tinker around with it, be my guest.

## Import bookmarks

https://github.com/ehamiter/bookerics-importer


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

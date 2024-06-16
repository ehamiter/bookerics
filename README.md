## bookerics

> bookmarks, but for Erics

![screenshot](screenshot.png)

This is like a self-hosted [pinboard.in](https://pinboard.in), but not nearly as nice or feature-rich. It's also only for Erics.


### FAQ

What?
> It's bookmarks, but for Erics. So, bookerics. Get it?

That seems like it's marketed to a very niche group.
> That's not a question.

Can I use this if my name isn't Eric?
> Sure. If you're not lucky enough to be named Eric, you can update the configuration to be Booktoms, Bookzendayas, Bookvolodymyrs, etc. I suppose "Mark" works as well.


### This is a continual work in progress.

Things will definitely break in here, but if you want to tinker around with it, be my guest.


### Import bookmarks

This tool will convert `bookmarks.html` to `bookerics.db`:

https://github.com/ehamiter/bookerics-importer


### Running the App

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

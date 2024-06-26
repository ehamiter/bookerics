## bookerics

> bookmarks, but for Erics

This is like a self-hosted [pinboard.in](https://pinboard.in), but not nearly as nice or feature-rich. It's also only for Erics.

![screenshot](/bookerics/static/images/screenshot.webp)


### FAQ

What?
> It's bookmarks, but for Erics. So, bookerics. Get it?

That seems like it's marketed to a very niche group.
> That's not a question.

Can I use this if my name isn't Eric?
> Sure. If you're not lucky enough to be named Eric, you can update the configuration to be booktoms, bookzendayas, bookvolodymyrs, etc. I suppose "bookmarks" works as well.


### This is a continual work in progress.

Things will definitely break in here, but if you want to tinker around with it, be my guest.


### Import bookmarks

This tool will convert `bookmarks.html` to `bookerics.db`:

https://github.com/ehamiter/bookerics-importer

```
git clone git@github.com:ehamiter/bookerics-importer.git

cargo build --release

ln -s  /path/to/bookerics_importer/target/release/bookerics_importer /usr/local/bin/bookerics_importer

bookerics_importer /path/to/bookmarks.html bookerics.db
```

### Running the App

```
git clone git@github.com:ehamiter/bookerics.git bookyournamehere

mv .env.example .env  # and update it with relevant bits

poetry install

poetry run app
```

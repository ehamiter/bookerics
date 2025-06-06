## bookerics

> bookmarks, but for Erics

This is like a self-hosted [pinboard.in](https://pinboard.in), but not nearly as nice or feature-rich. It's also only for Erics.

Built with Python using the [FastHTML](https://fastht.ml/) web framework and [HTMX](https://htmx.org/) for dynamic frontend interactions.

![screenshot](/bookerics/static/images/screenshot.webp)


### FAQ

What?
> It's bookmarks, but for Erics. So, bookerics. Get it?

That seems like it's marketed to a very niche group.
> That's not a question.

Can I use this if my name isn't Eric?
> Sure. If you're not lucky enough to be named Eric, you can update the configuration to be booktoms, bookzendayas, bookvolodymyrs, etc. I suppose "bookmarks" works as well.


### This is a continual work in progress.

Things will definitely break in here, but if you want to tinker around with it, be my guest. It was recently refactored to use the FastHTML framework.


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

poetry run bookerics
```

### Running the App as a service

##### Create a launch agent configuration file

```
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.bookerics</string>
    <key>ProgramArguments</key>
    <array>
        <string>/opt/homebrew/bin/poetry</string>
        <string>run</string>
        <string>bookerics</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/Users/YOUR_USERNAME/bookerics</string>
    <key>StandardOutPath</key>
    <string>/Users/YOUR_USERNAME/Library/Logs/bookerics.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/YOUR_USERNAME/Library/Logs/bookerics.error.log</string>
    <key>KeepAlive</key>
    <true/>
    <key>RunAtLoad</key>
    <true/>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>
</dict>
</plist>
```

##### Load the service (starts it and enables on boot)

```
launchctl load ~/Library/LaunchAgents/com.bookerics.plist
```

##### Unload the service (stops it and disables on boot)

```
launchctl unload ~/Library/LaunchAgents/com.bookerics.plist
```

##### Check the status

```
launchctl list | grep bookerics
```

##### View logs in real-time

```
tail -f ~/Library/Logs/bookerics.log
tail -f ~/Library/Logs/bookerics.error.log
```

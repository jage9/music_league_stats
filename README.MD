# Music League Stats

This script Generates a static website with detailed stats for one or more [Music Leagues.]((https://musicleague.com/)
Music League is a website/app that allows you to compete against others for supremacy by choosing songs that fit the prompt. This script will use your league data to generate stat pages for:

* Every artist
* Every song submitted
* Round by round history
* Player stats and trends
* And much more

All generated as a static site.

## Quick Start

You will need:

* Python 3.11 or later
* A premium Music League account so you can export the data

1. Put your league data in the /leagues folder. Create a subfolder for each league you would like to include, with the CSV files you download inside that subfolder.
2. If you want to change the page title or description, copy config.sample.json to config.json and update the values.
3. Run the script. It will put the site and all pages in the /site folder.

## Contributing
All ideas welcome. Please submit a PR.

## License
MIT
This repository is not endorsed by or created by Music League.
# Homily Scripts by Shane

A set of Python scripts that I use for managing my writing of homilies. If you're not comfortable with the command line or don't already know what Markdown is, this probably isn't for you. 

## Installation

Only tested/used on a Mac; would probably work on Linux, too? I've run it on Windows and fixed some obvious things to make it work there, but not doing ongoing maintenance of it. 

### Prerequisites
* [Python](https://www.python.org/) (I just use [Homebrew](https://brew.sh/)'s installation these days, but however you want works; `brew install python virtualenv` is my way)
* [Pandoc](https://pandoc.org/) (`brew install pandoc`)
* [Typst](https://github.com/typst/typst) (`brew install typst`)

### Setup
1. Make a new directory for where you want the homilies to go, and initialize a git repository there. Add an empty `archive` directory. Something like:
    ```sh
    mkdir ~/Documents/preaching
    cd ~/Documents/preaching
    mkdir archive
    git init .
    ```
2. Import this project as a submodule for that git repo; I call it `_scripts` but you do you.
    ```sh
    git submodule add git@github.com:sjml/homily-scripts.git _scripts
    git add .gitmodules _scripts
    git commit -m "setting up submodule"
    ```
3. Initialize the Python environment.
   ```sh
   cd _scripts
   virtualenv env
   ./env/bin/pip install -r requirements.txt
   cd ..
   ```

## Usage

All the scripts are set up to be run directly from the parent directory, so you can invoke `./_scripts/new.py` straight instead of having to activate the Python environment. 

* `new.py` --- Create a new empty homily; you'll be prompted to pick the date, and it will fill in appropriate metadata from the USCCB website. You can also specify a location or leave it blank to re-use the most recent one. 
* `wc.py [homily_file]` --- Give a word count of a specific homily along with a time estimate based on preaching speed. You can pass `--watch` as a flag to have this run continuously and update whenever the file changes on disk. 
* `render.py [homily_file]` --- Takes the Markdown file and generates a preaching script. (Large font, numbered pages, doesn't break paragraphs across pages, and has a very large bottom margin so you don't end up looking down too much. Check the Typst template for more details.)
* `concat.py` --- Puts all the homilies together in chronological order in a single file. If you don't specify an output, it will print to stdout.


## TODOs
* make preaching speed configurable for time estimations (right now it's just based on Shane's average speed)
* make the Typst template more easily configurable
* figure out some nice way of making tablet or phone output (maybe a self-contained HTML file?)

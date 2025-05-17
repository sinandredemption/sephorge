# Sephorge - Simple Static Site Generator

Sephorge is a lightweight static site generator that converts markdown files to HTML using a template system.

## Features

- Markdown to HTML conversion with simple template integration
- Automatic rebuild on file changes with a watcher script
- Makefile-like build system for efficient rebuilds
- Simple directory structure: `pages/` for source, `public/` for output

## Directory Structure

```
sephorge/
├── md/                # Markdown source files
├── public/            # Generated HTML output
├── sephorge.py        # Site generator
├── watcher.sh         # File system watcher
└── page.html          # HTML template
```

## Requirements

- Python 3.6+
- Required Python packages: `markdown`, `jinja2`
- For the file watcher: 
  - Linux: `inotify-tools`

## Installation

1. Clone this repository:

2. Install required Python packages:
   ```
   pip install markdown jinja2
   ```

3. Install the file watching tools:
   - On Debian/Ubuntu: `sudo apt-get install inotify-tools`

4. Make the scripts executable:
   ```
   chmod +x sephorge.py md2html.py watcher.sh
   ```

## Usage

1. Place markdown files and other assests in the `pages/` directory:
   ```
   mkdir -p pages 
   echo "# Hello World" > pages/index.md
   ```

2. Start the watcher:
   ```
   ./watcher.sh
   ```

3. Start a http server from `public/` to view the site:
   ```
   cd public && python3 -m http.server
   xdg-open http://localhost:8000  # On Linux
   ```

## Configuration

- Set the `WEBSITE_NAME` environment variable to change the website name (defaults to "Sephorge"):
  ```
  export WEBSITE_NAME="My Website"
  ```

- Modify `page.html` to change the HTML template.

## License

MIT
#!/bin/bash

# Configuration
PAGES_DIR="pages"
SEPHORGE_SCRIPT="./sephorge.py"

# Check if inotifywait command is available (requires inotify-tools)
if ! command -v inotifywait &> /dev/null; then
    echo "Error: inotifywait command not found."
    echo "Please install inotify-tools:"
    echo "  On Debian/Ubuntu: sudo apt-get install inotify-tools"
    echo "  On RedHat/CentOS: sudo yum install inotify-tools"
    echo "  On macOS with Homebrew: brew install fswatch"
    exit 1
fi

# Initialize
echo "==> Initializing Sephorge watcher..."

# First-time: rebuild site
python3 "$SEPHORGE_SCRIPT"

echo "==> Watching for changes in $PAGES_DIR directory..."

# Watch for file changes 
inotifywait -m -r -e modify,create,delete,move "$PAGES_DIR" | while read path action file; do
    echo "==> Change detected: $path$file ($action)"

    eval "$SEPHORGE_SCRIPT"

    echo "==> Site rebuilt successfully!"
done

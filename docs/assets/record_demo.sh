#!/usr/bin/env bash
# Record DevMind demo GIF using asciinema + agg
# Usage: ./record_demo.sh
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
CAST="$DIR/devmind_demo.cast"
GIF="$DIR/devmind_demo.gif"

echo "Recording... Execute commands one by one. Press Ctrl+D when done."
echo ""

asciinema rec "$CAST" --overwrite

echo ""
echo "Converting to GIF..."
agg --fps 15 --rows 30 "$CAST" "$GIF" 2>/dev/null || agg "$CAST" "$GIF"

echo "Done: $GIF"
echo "Size: $(du -h "$GIF" | cut -f1)"

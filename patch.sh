#!/bin/bash
DIR="$(dirname "$0")"
python3 "$DIR/patch_claude.py" "$(npm root -g)/@anthropic-ai/claude-code/cli.js"

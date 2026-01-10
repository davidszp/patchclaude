#!/usr/bin/env pwsh
$cliPath = "$(npm root -g)/@anthropic-ai/claude-code/cli.js"
python "$PSScriptRoot/patch_claude.py" $cliPath

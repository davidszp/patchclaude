#!/usr/bin/env python3
"""
Patch Claude Code cli.js to fix CPU spikes.

Fixes:
  1. Typing '/' for slash commands - NU0 creates new Fuse.js index on every render
  2. Typing '/skill ' (space after skill) - React render loop from new [] references

Usage:
    python3 patch_claude.py <path-to-cli.js>
    python3 patch_claude.py "$(npm root -g)/@anthropic-ai/claude-code/cli.js"
"""

import sys
import re
import shutil
from pathlib import Path


def find_function_end(content: str, start: int) -> int:
    """Find the matching closing brace for a function."""
    pos = content.index('{', start) + 1
    depth = 1
    while depth > 0 and pos < len(content):
        if content[pos] == '{':
            depth += 1
        elif content[pos] == '}':
            depth -= 1
        pos += 1
    return pos


def patch_slash_command_function(content: str) -> tuple[str, bool]:
    """Patch the slash command suggestion function.

    Dynamically finds the function by looking for Fuse.js usage with
    commandName/partKey/aliasKey/descriptionKey keys, then adds caching.
    """
    if '_NU0C' in content:
        print("  Slash commands: Already patched")
        return content, False

    # Find the Fuse.js command search pattern to locate the function
    fuse_pattern = r'commandName.*partKey.*aliasKey.*descriptionKey'
    fuse_match = re.search(fuse_pattern, content)
    if not fuse_match:
        print("  Slash commands: Could not find Fuse.js command pattern")
        return content, False

    # Search backwards to find the enclosing function
    search_start = max(0, fuse_match.start() - 3000)
    preceding = content[search_start:fuse_match.start()]

    func_matches = list(re.finditer(r'function ([A-Za-z0-9_$]+)\(([A-Za-z0-9_$,]+)\)\{', preceding))
    if not func_matches:
        print("  Slash commands: Could not find enclosing function")
        return content, False

    last_match = func_matches[-1]
    func_name = last_match.group(1)
    func_params = last_match.group(2)
    func_start = search_start + last_match.start()

    # Find function end
    func_end = find_function_end(content, func_start)
    original = content[func_start:func_end]

    # Calculate header length: "function <name>(<params>){"
    header = f'function {func_name}({func_params}){{'
    header_len = len(header)
    func_body = original[header_len:-1]  # Remove header and final "}"

    # Get first param name for cache key
    first_param = func_params.split(',')[0]

    patched = (
        'var _NU0C={k:"",v:null};'
        f'function {func_name}({func_params}){{'
        f'var _k={first_param};'
        'if(_NU0C.k===_k&&_NU0C.v!==null)return _NU0C.v;'
        '_NU0C.k=_k;'
        'var _orig=function(){' + func_body + '};'
        'var _r=_orig();'
        '_NU0C.v=_r;'
        'return _r}'
    )

    content = content[:func_start] + patched + content[func_end:]
    print(f"  Slash commands: Patched function '{func_name}' ({len(original)} -> {len(patched)} chars)")
    return content, True


def patch_suggestions_empty_array(content: str) -> tuple[str, bool]:
    """Patch all suggestions:[] to use a constant empty array.

    React uses referential equality to detect state changes. Creating new []
    on every setState call causes infinite render loops because each [] is
    a different object. This patch replaces all suggestions:[] with a constant.
    """
    if '_$ES' in content:
        print("  suggestions:[]: Already patched")
        return content, False

    count = content.count('suggestions:[]')
    if count == 0:
        print("  suggestions:[]: No occurrences found")
        return content, False

    # Insert at the very beginning of the file (after shebang if present)
    # This ensures the constant is at module/global scope
    if content.startswith('#!'):
        # Find end of shebang line
        newline_pos = content.find('\n')
        insert_pos = newline_pos + 1 if newline_pos != -1 else 0
    else:
        insert_pos = 0

    constant_decl = 'var _$ES=[];'

    content = content[:insert_pos] + constant_decl + content[insert_pos:]

    # Replace all suggestions:[] with suggestions:_$ES
    content = content.replace('suggestions:[]', 'suggestions:_$ES')

    print(f"  suggestions:[]: Patched {count} occurrences")
    return content, True


def patch_cli(cli_path: str) -> None:
    cli_path = Path(cli_path)

    if not cli_path.exists():
        print(f"Error: {cli_path} not found")
        sys.exit(1)

    content = cli_path.read_text()
    backup_path = cli_path.with_suffix('.js.bak')

    # Check if already patched (don't overwrite backup with patched version)
    already_patched = '_NU0C' in content and '_$ES' in content
    if already_patched:
        print("Already patched. Run `npm install -g @anthropic-ai/claude-code` to get fresh version, then re-run this script.")
        sys.exit(0)

    # Backup original (refresh each time to handle version updates)
    shutil.copy(cli_path, backup_path)
    print(f"Backup saved: {backup_path}")

    patches_applied = 0
    print("Applying patches...")

    # Patch 1: Slash command suggestions - fixes CPU spike on '/'
    content, patched = patch_slash_command_function(content)
    if patched:
        patches_applied += 1

    # Patch 2: suggestions:[] constant - fixes React render loop on '/skill '
    content, patched = patch_suggestions_empty_array(content)
    if patched:
        patches_applied += 1

    if patches_applied == 0:
        print("\nNo patches applied (already patched or functions not found)")
        sys.exit(0)

    cli_path.write_text(content)

    print(f"\nPatched {patches_applied} function(s) in: {cli_path}")
    print(f"\nTo verify syntax: node --check {cli_path}")
    print(f"To revert: cp {backup_path} {cli_path}")


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <path-to-cli.js>")
        print()
        print("Examples:")
        print(f"  {sys.argv[0]} \"$(npm root -g)/@anthropic-ai/claude-code/cli.js\"")
        sys.exit(1)

    patch_cli(sys.argv[1])

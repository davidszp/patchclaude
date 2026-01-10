# Claude Code CPU Spike Workaround

> **Note**: This repository contains an unofficial, temporary workaround for a known performance issue in Claude Code. It is intended solely for educational and demonstration purposes. This repository will be archived once the issue is resolved upstream.

## Disclaimer

- This project is **not affiliated with, endorsed by, or supported by Anthropic**
- All Claude Code software and intellectual property belong to **Anthropic**
- This code is provided **as-is, for demonstration purposes only**
- **Not recommended for production use** — use at your own risk
- The patches modify Anthropic's bundled code; always keep backups

If you're experiencing this issue, please consider adding your feedback to the official GitHub issue to help prioritize a fix:

- **GitHub Issue**: [#15689](https://github.com/anthropics/claude-code/issues/15689)

---

## Problem

### Symptoms

1. **Slash commands**: When typing `/` to access slash commands, the CPU immediately spikes to 100%+ on one core
2. **Skill arguments**: When typing arguments after a skill (e.g., `/skill ` with a space), the CPU spikes again

### Environment

- Claude Code: npm version (not the compiled binary)
- Tested on: Linux x86-64
- Should work on: macOS, Windows (with Python 3)

---

## Installation

### Prerequisites

- Python 3.6+
- Node.js and npm
- Claude Code installed via npm (not the standalone binary)

### Step 1: Install NPM Version

```bash
# Install npm version globally
npm install -g @anthropic-ai/claude-code

# Verify installation
which claude    # Linux/macOS
where claude    # Windows
```

> **Note**: If you have the standalone binary installed, the npm version should take precedence if your npm bin directory is earlier in PATH. You can check with `which claude` (or `where claude` on Windows).

### Step 2: Apply the Patch

**Linux/macOS:**
```bash
python3 patch_claude.py "$(npm root -g)/@anthropic-ai/claude-code/cli.js"
# Or use: ./patch.sh
```

**Windows (PowerShell):**
```powershell
python patch_claude.py "$(npm root -g)/@anthropic-ai/claude-code/cli.js"
# Or use: .\patch.ps1
```

Expected output:
```
Backup saved: .../cli.js.bak
Applying patches...
  Slash commands: Patched function 'XYZ' (1953 -> 2102 chars)
  suggestions:[]: Patched 8 occurrences

Patched 2 function(s) in: .../cli.js
```

### Step 3: Verify

```bash
# Check syntax is valid
node --check "$(npm root -g)/@anthropic-ai/claude-code/cli.js"

# Test Claude
claude
# Type '/' and verify no CPU spike
# Type '/skill ' (with a trailing space) and verify no CPU spike
```

### Reverting the Patch

Restore from backup or simply reinstall:

```bash
npm install -g @anthropic-ai/claude-code
```

---

## Notes

- The patches will be overwritten when Claude Code updates
- Re-run the patch script after updates if needed
- Please star/comment on [#15689](https://github.com/anthropics/claude-code/issues/15689) to help prioritize an official fix

---

## Contributing to the Official Fix

The best way to help resolve this issue permanently is to engage with Anthropic directly:

1. **Star and comment** on [issue #15689](https://github.com/anthropics/claude-code/issues/15689)
2. **Provide details** about your environment and symptoms
3. **Share reproduction steps** if you've found additional triggers

---

## License

The patch scripts in this repository are provided under the MIT License for educational purposes. This license applies only to the original code in this repository, not to any Anthropic software.

## Acknowledgments

Thank you to the Anthropic team for creating Claude Code. This workaround is offered in the spirit of constructive community feedback, and we look forward to an official fix that makes this repository obsolete.

---

## Technical Details

### Root Cause Analysis

Investigation of the bundled `cli.js` revealed two distinct issues:

#### Issue 1: Slash command suggestions function

The function that computes slash command suggestions:
1. Gets called repeatedly by the React/Ink rendering loop
2. On each call, builds a data structure of all commands
3. When there's text after `/`, creates a **new Fuse.js search index on every keystroke**

#### Issue 2: React state updates with `suggestions:[]`

Multiple places in the code set React state with `suggestions:[]`:
1. Each `[]` creates a **new array object** in JavaScript
2. React uses referential equality (`===`) to detect state changes
3. Since `[] !== []` (different objects), React sees every setState as a change
4. This triggers infinite render loops when entering skill argument mode

### The Patches

#### Patch 1: Slash command suggestions (cache wrapper)

```javascript
// Before (minified):
function XYZ(A,Q){if(!b6A(A))return[];...creates new Fuse.js index...}

// After (with cache):
var _NU0C={k:"",v:null};
function XYZ(A,Q){
  var _k=A;                                          // Cache key: input text
  if(_NU0C.k===_k&&_NU0C.v!==null) return _NU0C.v;   // Cache hit
  _NU0C.k=_k;
  var _orig=function(){...original code...};
  var _r=_orig();
  _NU0C.v=_r;                                        // Store result
  return _r;
}
```

#### Patch 2: suggestions:[] → constant array

```javascript
// Before:
I(()=>({commandArgumentHint:CA,suggestions:[],selectedSuggestion:-1}))
// Each [] is a new object, breaks React's referential equality

// After:
var _$ES=[];  // Constant empty array (defined once at module scope)
I(()=>({commandArgumentHint:CA,suggestions:_$ES,selectedSuggestion:-1}))
// Same array reference every time, React sees no change
```

### Why This Works

- **Slash command cache**: Prevents repeated Fuse.js index creation on every render
- **Constant empty array**: Preserves React's referential equality, stops render loops
- Combined, these eliminate CPU spinning in both slash command and skill argument modes

### Dynamic Detection

The patch script doesn't rely on hardcoded minified function names. Instead:
- **Slash command function**: Found by searching for its unique Fuse.js config pattern (`commandName/partKey/aliasKey/descriptionKey`)
- **suggestions:[]**: Simple string pattern, unlikely to change

This makes the patch resilient to minification changes across Claude Code versions.

### Risk Assessment

| Concern | Risk Level | Explanation |
|---------|------------|-------------|
| **Stale suggestions** | Very Low | Cache invalidates when input changes |
| **Memory leak** | None | Single-entry cache, constant array |
| **Breaking functionality** | Very Low | Original code runs unchanged, just wrapped |
| **Conflicts with updates** | Medium | Anthropic updates will overwrite the patches |

Worst case is slightly stale autocomplete suggestions in rare edge cases — no crashes or data loss possible.

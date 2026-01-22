# Claude Code CPU Spike Workaround

> **ARCHIVED**: This project has been archived. The CPU spike issues have been fixed in **Claude Code 2.1.14**. Simply update to the latest version:
> ```bash
> npm install -g @anthropic-ai/claude-code
> ```

## What This Was

This repository contained an unofficial, temporary workaround for CPU spike bugs in Claude Code that occurred when:
1. Typing `/` to access slash commands (Fuse.js index recreation on every render)
2. Typing arguments after skills like `/skill ` (React render loop from referential inequality)

## Related Issues

These issues appear to be resolved in Claude Code 2.1.14:
- [#9684](https://github.com/anthropics/claude-code/issues/9684) - Infinite rendering loop causing high CPU and memory growth
- [#4895](https://github.com/anthropics/claude-code/issues/4895) - Performance degradation due to infinite React render loop in skills system
- [#4896](https://github.com/anthropics/claude-code/issues/4896) - Severe UI performance regression due to infinite React render loop
- [#15689](https://github.com/anthropics/claude-code/issues/15689) - Original issue this patch was created for

## Disclaimer

This project was **not affiliated with, endorsed by, or supported by Anthropic**. All Claude Code software and intellectual property belong to **Anthropic**.

## License

MIT License (for the patch scripts only, not Anthropic software)

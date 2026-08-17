# pencil-skill

Agent skills for [pen.dev](https://docs.pen.dev/) (Pencil): live-canvas MCP design, and headless CLI generation.

| Skill | Use when |
|-------|----------|
| [`pencil-design`](pencil-design/SKILL.md) | Live Pencil canvas / Pencil MCP / an open `.pen` in the desktop app or IDE extension |
| [`pencil-cli`](pencil-cli/SKILL.md) | `pen` CLI, headless/CI, batch `--tasks`, or design without opening the editor |

The MCP server still registers as `pencil`. The product name is **pen.dev**. CLI package: `@pen.dev/cli` (`pen`).

## Install

Copy or symlink a skill folder into your agent’s skills directory, then restart / resync.

```bash
# example: Claude Code / compatible runtimes
git clone https://github.com/devon-kong/pencil-skill.git
ln -s "$(pwd)/pencil-skill/pencil-design" ~/.claude/skills/pencil-design
ln -s "$(pwd)/pencil-skill/pencil-cli" ~/.claude/skills/pencil-cli
```

Paths differ by runtime (`~/.claude/skills/`, `~/.cursor/skills/`, `~/.codex/skills/`, …). If you use [skillshare](https://github.com/runkids/skillshare), add this repo as a source and sync.

## Docs

- Product: https://docs.pen.dev/
- CLI: https://docs.pen.dev/for-developers/pen-cli
- `.pen` format: https://docs.pen.dev/for-developers/the-pen-format

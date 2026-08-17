# `@pen.dev/cli` — when CLI vs MCP

A command-line tool for working with `.pen` files outside the desktop app or IDE extension. Useful
for headless workflows (CI, batch generation, scripted exports).

**This skill does not auto-fall-back to the CLI.** When MCP is not connected, stop and tell the user
to open the pen.dev app or extension. Only invoke the CLI when the user explicitly directs it or the
context is unambiguously headless.

The full flag/command reference lives in the sibling **`pencil-cli`** skill (`pencil-cli/SKILL.md` and
`pencil-cli/references/cli-reference.md`). Do not invent flags. `pen --help` on the installed version
is authoritative.

## Identity (do not mix these up)

| Thing | Current | Dead / stale |
|-------|---------|--------------|
| npm package | `@pen.dev/cli` | `@pencil.dev/cli` (still on npm at 0.2.9; do not install) |
| Binary | `pen` (also aliased as `pencil`) | — |
| Docs | https://docs.pen.dev/for-developers/pen-cli | https://docs.pencil.dev/… (same site, old hostname) |
| CLI key env | `PEN_CLI_KEY` | `PENCIL_CLI_KEY` |
| Agent key env | `PEN_AGENT_API_KEY` / `ANTHROPIC_API_KEY` | — |
| Interactive MCP tools | `get_app_state`, `execute`, `get_guidelines`, `browser` | `get_editor_state`, `batch_design`, `batch_get`, … |

This machine currently has `@pen.dev/cli@0.3.3`. Official docs last updated 2026-08-12 omit some live
flags (`--agent`, `--effort`, `--repo`, `--list-workspaces`, `PEN_AGENT_API_KEY`). Trust `pen --help`.

## Why this skill does not auto-fall-back

1. **The user's expectation.** Live MCP edits show up in the open editor. A headless CLI run does not.
2. **Auth and config.** The CLI uses `~/.pencil/session-cli.json` and may need `PEN_CLI_KEY` /
   `ANTHROPIC_API_KEY`. The agent should not manage these silently.
3. **Output divergence.** CLI writes a file path; the user's open document does not update.

## When CLI vs MCP

| Situation | Use |
|-----------|-----|
| User has the desktop app / IDE extension open | **MCP** |
| Interactive design session | **MCP** |
| Headless CI, `--tasks` batch, scripted `--export` | **CLI** |
| User says "design this without opening the editor" | **CLI** |
| MCP host is not connected | **Stop and ask** — do not silently launch CLI |

Rule of thumb: if a human is watching the canvas, MCP. If no human is in the loop, CLI.

## Minimal install / auth

```
npm install -g @pen.dev/cli
pen version          # requires Node 18+
pen login            # interactive; ask the user to run it
pen status
```

CI:

```
export PEN_CLI_KEY=pencil_cli_...
export ANTHROPIC_API_KEY=sk-ant-...
pen --out onboarding.pen --prompt "Create a 3-step onboarding flow"
```

Interactive shell (same 4 MCP tools as the app):

```
pen interactive -o output.pen
pen > get_app_state({ include_canvas_design: true, include_schema: true, include_scripts_and_shaders: false })
pen > execute({ input: 'Get((n,c)=>{c.skipChildren();Print(n.id,n.name)})' })
pen > save()
```

See the `pencil-cli` skill for agent-mode flags, batch JSON, models (`pen --list-models`), and
troubleshooting.

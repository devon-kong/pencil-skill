# pen.dev CLI Reference

Full command and flag reference for the `pen` CLI (captured from v0.3.3 `pen --help`; `pen --help` on the installed version is always authoritative). Official docs at https://docs.pen.dev/for-developers/pen-cli (2026-08-12) are slightly behind this live flag list.

Contents: Commands · Agent Mode Flags · Agents & Models · Batch Processing · Workspaces · Previews & Debugging · Environment Variables · CI/CD

## Commands

| Command | Purpose |
|---------|---------|
| `pen login` | Log in interactively (email + password, or email + OTP code) |
| `pen status` | Check authentication status and account details |
| `pen version` | Print the installed CLI version |
| `pen interactive` | Start the interactive tool shell — see `interactive-mode.md` |
| `pen --list-workspaces` | List your organizations and workspaces |
| `pen --workspace <slug>` | Set current **cloud** workspace (e.g. `alice` or `alice/designs`). Official docs sometimes label this a folder path — that is wrong. The local working directory is `--repo, -C`. |
| `pen --list-models` | List available models and exit |
| `pen --help` | Show the flag list for the installed version |

## Agent Mode Flags

Running `pen [options]` (no subcommand) starts an AI agent run.

| Flag | Description |
|------|-------------|
| `--in, -i <path>` | Input `.pen` file (optional — empty canvas if omitted) |
| `--out, -o <path>` | Output `.pen` file path (required unless only exporting) |
| `--prompt, -p <text>` | Prompt for the AI agent (required for generation) |
| `--prompt-file, -f <path>` | Attach a file to send with the prompt (repeatable). Images (png/jpeg/gif/webp) or text files; **not** for loading the prompt text itself |
| `--agent <type>` | Agent to use when `--model` is omitted: `claude`, `codex`, `gemini` (default: `claude`) |
| `--model, -m <id>` | Model to use; the agent is inferred from the model id |
| `--effort <level>` | Reasoning effort |
| `--custom, -c` | Use custom Claude model config (e.g. AWS Bedrock, Vertex AI) |
| `--usage <path>` | Write final token usage and cost as JSON to this path |
| `--tasks, -t <path>` | JSON tasks file for batch operations (see below) |
| `--repo, -C <path>` | Local folder to run the agent in (working directory) |
| `--workspace <slug>` | Select current cloud workspace |
| `--export, -e <path>` | Export an image of the final result |
| `--export-scale <n>` | Export scale factor (default: 1; use 2 for crisp images) |
| `--export-type <type>` | `png` (default), `jpeg`, `webp`, `pdf` |
| `--preview-output <path>` | Where preview PNGs are saved (default: `~/.pencil/latest-preview.png`) |
| `--enable-preview` | Save a preview image after each design change |
| `--max-failed-calls <n>` | Abort the run after this many failed tool calls |
| `--verbose, -v` | Stream model thinking and full tool call input/output |
| `--verbose-mcp` | Include full MCP tool error details in responses |
| `--help, -h` | Show help |

Typical invocations:

```bash
# New design from scratch
pen --out login.pen --prompt "Create a modern login page" --export login.png --export-scale 2

# Modify an existing design
pen --in dashboard.pen --out dashboard-v2.pen --prompt "Add a sidebar navigation" --export dashboard-v2.png --export-scale 2

# Export only, no generation
pen --in design.pen --export hero.pdf --export-type pdf

# Faster/cheaper model for a simple task
pen --out simple.pen --model claude-haiku-4-5 --prompt "Create a simple 404 error page"

# Non-Claude agent
pen --out design.pen --prompt "Create a pricing page" --agent gemini
```

## Agents & Models

- Default agent is `claude`; `--agent` also accepts `codex` and `gemini`. `--model <id>` overrides and implies the agent.
- Model lineup changes over time — run `pen --list-models` (optionally with `--agent <type>`) for what the installed CLI offers. As of 0.3.3: Claude default is `claude-opus-5` (also `claude-fable-5`, `claude-opus-4-8`/`4-7`/`4-6`, `claude-sonnet-5`/`4-6`, `claude-haiku-4-5`); Codex default `gpt-5.5`; Gemini default `gemini-3.6-flash`. Official docs still list `claude-opus-4-6` as default — trust `pen --list-models`.
- The agent needs its own credentials: `PEN_AGENT_API_KEY`, `ANTHROPIC_API_KEY` for Claude agents, or an authenticated Claude Code session. Details in `setup-troubleshooting.md`.

## Batch Processing

Process multiple designs sequentially from a JSON file — each task gets its own editor instance:

```bash
pen --tasks batch.json
```

```json
{
  "tasks": [
    {
      "out": "landing-page.pen",
      "prompt": "Create a SaaS landing page with hero, features, and pricing sections"
    },
    {
      "in": "existing-app.pen",
      "out": "existing-app-v2.pen",
      "prompt": "Add a dark mode toggle to the header"
    },
    {
      "out": "mobile-menu.pen",
      "model": "claude-haiku-4-5",
      "prompt": "Create a mobile hamburger menu component"
    }
  ]
}
```

Per-task fields: `out` (required), `prompt` (required), `in` (optional input file), `model` (optional override).

## Previews & Debugging

- `--enable-preview` writes a preview PNG after each design change (default path `~/.pencil/latest-preview.png`, override with `--preview-output`). Useful for watching progress on long runs.
- `--verbose` streams the agent's thinking and tool calls; `--verbose-mcp` surfaces full MCP error details. Reach for these when a run fails or the output looks wrong.
- `--usage run-usage.json` records token usage and cost per run.

## Environment Variables

| Variable | Description |
|----------|-------------|
| `PEN_CLI_KEY` | CLI API key for CI/CD (takes precedence over stored session) |
| `PEN_AGENT_API_KEY` | API key for the selected agent (takes precedence) |
| `ANTHROPIC_API_KEY` | Anthropic API key for Claude agents |
| `PEN_API_BASE` | Backend API base URL (default: `https://api.pen.dev`) |
| `DEBUG` | Enable debug logging |

## CI/CD

Use a CLI key plus an agent API key so no interactive login is needed:

```bash
export PEN_CLI_KEY=pencil_cli_...
export ANTHROPIC_API_KEY=sk-ant-...
pen --out onboarding.pen --prompt "Create a 3-step onboarding flow"
```

CLI keys are scoped to an organization and are created in the **Developer Keys** section of the org settings on the pen.dev web app. The CLI key always takes precedence over a stored session token.

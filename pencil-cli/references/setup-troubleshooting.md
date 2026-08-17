# Setup, Authentication & Troubleshooting

Read this when `pen` is missing, `pen status` fails, or a run errors out. Contents: Installation · pen.dev Authentication · Agent Authentication · Common Errors · Upgrading

## Installation

```bash
npm install -g @pen.dev/cli
pen version        # verify — requires Node.js 18+
```

If global install fails on permissions, install locally in the project (`npm install @pen.dev/cli`) and invoke via `npx pen` or `./node_modules/.bin/pen`.

## pen.dev Authentication

The CLI requires a pen.dev account before any agent operation.

**Interactive login (humans):**

```bash
pen login
```

Offers email + password or email + OTP code. On success the session token is stored in `~/.pencil/session-cli.json` (separate from the desktop app's session). This command is interactive — if you are an agent, ask the user to run it themselves rather than trying to drive the prompts.

**CLI key (CI/CD and agents):**

```bash
PEN_CLI_KEY=pencil_cli_... pen --out design.pen --prompt "Create a form"
```

Keys are scoped to an organization and created under **Developer Keys** in the org settings of the pen.dev web app. `PEN_CLI_KEY` always takes precedence over a stored session token.

**Check status:**

```bash
pen status
```

Shows the current auth method, verifies the session with the backend, and prints account details. Run this first whenever anything fails.

## Agent Authentication

Authentication with pen.dev is not enough on its own — the CLI drives an AI agent that needs its own credentials:

- **Claude agents (default):** an `ANTHROPIC_API_KEY` env var, or an authenticated Claude Code session (user runs `claude` once and completes the browser login). `PEN_AGENT_API_KEY` takes precedence when set.
- **Other agents (`--agent codex` / `--agent gemini`):** the corresponding provider credentials must be configured.
- `--custom` uses a custom Claude model config (AWS Bedrock, Vertex AI).

Conflicting auth methods are a common failure source: if the user logged in via `claude` CLI but also has a stale `ANTHROPIC_API_KEY` in the environment, errors like "Invalid API key" or "Please run /login" appear. Fix by removing the conflicting env var or doing a clean login. If none of these options are available, present them to the user and help set one up — do not attempt to register accounts yourself.

## Common Errors

| Error | Likely cause | Fix |
|-------|--------------|-----|
| `pen: command not found` | CLI not installed / not on PATH | Install per above; or use `npx pen` from a project that has it |
| Not authenticated / session errors from `pen status` | No login or expired session | User runs `pen login`, or set `PEN_CLI_KEY` |
| "Invalid API key" / "Please run /login" | Conflicting agent auth configs | Clean `claude` login; remove stale `ANTHROPIC_API_KEY`; restart the terminal |
| "Claude Code not connected" | Claude Code not authenticated | User runs `claude` and completes browser login |
| `PEN_CLI_KEY` set but still failing | Key invalid or wrong org | Regenerate in org settings → Developer Keys |
| Run aborts with repeated tool failures | Agent stuck on the design task | Re-run with `--verbose` to see the failing calls; bound with `--max-failed-calls <n>` |
| Exported image doesn't match expectations | Export or render issue | Re-export (`pen --in design.pen --export out.png --export-scale 2`); inspect with `--verbose-mcp` |
| Timeouts in your shell/tooling | Generation legitimately takes minutes | Expected: simple 1–2 min, complex 3–5+ min. Use a ≥10 min timeout or a background task |

General escalation: `pen status` → `DEBUG=1 pen ...` → `pen --verbose ...` → report to the user with the exact error message, CLI version (`pen version`), and platform.

IDE / desktop / MCP host issues (activation email, Cursor Pro, Codex `config.toml` duplication, no auto-save, Windows desktop not available) belong to the product, not this CLI: see https://docs.pen.dev/troubleshooting.

## Upgrading

```bash
npm view @pen.dev/cli version     # latest published
pen version                       # installed
npm install -g @pen.dev/cli       # upgrade
```

Upgrade when flags or behavior don't match this skill, or the user asks. After upgrading, `pen --help` is the authoritative reference for the new version.

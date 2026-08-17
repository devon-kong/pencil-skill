---
name: pencil-cli
description: >
  Generate or iterate `.pen` files with the locally installed pen.dev CLI (`pen`): one-shot `--prompt`, batch `--tasks`, headless `--export`, CI. Use this skill when the user names `pen`, `@pen.dev/cli`, pencil-cli, headless/CI/batch export, "用 CLI 出图", "生成设计原型图" with no editor open, or explicitly wants a design without opening the Pencil app. Do NOT use this skill when the user is editing a live Pencil canvas, mentions the Pencil MCP / `.pen` in an open editor, or has the desktop app or IDE extension connected — that is the pencil-design skill.
---

# pencil-cli — pen.dev Design

Create professional visual designs from natural language using the pen.dev CLI. It generates `.pen` files (structured JSON design documents) and exports them as PNG/JPEG/WEBP/PDF.

This file covers the everyday workflow. For anything beyond the basics, consult the reference files listed at the bottom — they are self-contained, so you should never need to search the web for pen CLI information.

## Workflow at a Glance

1. **Check** — `pen status` (once per session). Not authenticated → Failure modes row 2 (🔴 CHECKPOINT: user runs `pen login`).
2. **Generate** — `pen --out design.pen --prompt "<user's request, verbatim>" --export design.png --export-scale 2`, with a ≥10-minute timeout or as a background task.
3. **Show** — read the exported PNG and present it visually to the user.
4. **Iterate** — same command plus `--in design.pen` and the user's change request.
5. **On failure** — follow Failure modes below. Do not retry the identical command blindly.

## Prerequisites

The user has `pen` installed locally. Verify quickly before the first run of a session:

```bash
pen version   # e.g. 0.3.3 — requires Node.js 18+
pen status    # must show an authenticated pen.dev account
```

- If `pen` is missing or auth fails, follow Failure modes — do not improvise install/auth steps.
- The CLI drives an AI agent (Claude by default) that also needs its own credentials. If `pen status` is fine but generation fails with auth/model errors, see the "Agent authentication" section of that same file.

## Creating a Design

The core command:

```bash
pen --out <output.pen> --prompt "<design description>" --export <output.png> --export-scale 2
```

Key flags for daily use:

- `--out, -o` — where to save the `.pen` file (required)
- `--prompt, -p` — what to design (required)
- `--in, -i` — start from an existing `.pen` file (for iteration)
- `--prompt-file, -f` — attach a reference image or text file to the prompt (repeatable)
- `--export, -e` — export an image of the result; `--export-scale 2` for crisp output; `--export-type` for `jpeg`/`webp`/`pdf`
- `--model, -m` / `--agent` — pick a specific model or agent (see `references/cli-reference.md`)

### Passing the Prompt

Pass the user's request directly as the prompt — do not expand it or add detail beyond what the user actually said. The pen CLI runs its own AI designer agent that handles creative decisions like layout structure, color palettes, typography, spacing, and content. Adding your own design specifics on top of the user's request conflicts with that agent's judgment and produces worse results.

If the user says "make me a landing page for a coffee shop", the prompt is exactly that — not a paragraph with hero sections, color palettes, and font choices you invented.

### Timing Expectations

Generation is not instant — the CLI's agent plans the layout, creates each element, and validates the result visually. Expect:

- **Simple designs** (a card, a single component): 1–2 minutes
- **Medium designs** (an app screen, a landing page section): 2–3 minutes
- **Complex designs** (full landing page, detailed dashboard): 3–5+ minutes

Tell the user upfront that generation takes a few minutes. Use a generous timeout (at least 600000ms / 10 minutes) when running the command, and prefer running it as a background task so the conversation stays responsive.

### Showing the Result

Always show the exported image to the user after creating it — that is the whole point. Read the exported PNG with your image-reading capability so the user sees the visual, not just a file path.

## Iterating on a Design

Load the previous `.pen` file with `--in`; the agent modifies the existing design instead of starting over:

```bash
pen --in design.pen --out design-v2.pen --prompt "Make the header larger and change the accent color to green" --export design-v2.png --export-scale 2
```

Keep a consistent naming pattern for successive iterations: `design.pen` → `design-v2.pen` → `design-v3.pen`, or overwrite in place with `--in design.pen --out design.pen`.

## Exporting Without Regenerating

To re-export an existing `.pen` file (different scale or format), skip the prompt entirely:

```bash
pen --in design.pen --export design@3x.png --export-scale 3
```

## Batch Generation

For several designs in one run, use a JSON tasks file (`pen --tasks batch.json`). Format and examples: `references/cli-reference.md` → "Batch Processing".

## Working Directory

Save design files in the user's current working directory or a subdirectory like `designs/`. Do not use temp directories — the user will want to find and iterate on these files later.

## Failure modes

Trigger → first fix → still failing. Details: `references/setup-troubleshooting.md`.

| Trigger | First fix | Still failing |
|---------|-----------|---------------|
| `pen: command not found` | `npm install -g @pen.dev/cli`, or `npx pen` from a local install | Stop. Do not invent install flags or other package names. |
| `pen status` not authenticated | 🔴 CHECKPOINT: the user runs `pen login` themselves, or sets `PEN_CLI_KEY`. Do not drive the login prompts. | Key rejected → regenerate under org **Developer Keys**. Session expired → user runs `pen login` again. |
| Agent auth error (`Invalid API key`, `Please run /login`) | Follow Agent Authentication in `setup-troubleshooting.md` (clean `claude` login or remove stale `ANTHROPIC_API_KEY`) | Still failing → present the remaining auth options to the user. Do not register accounts. |
| Run killed / timeout | Expected: 1–5+ minutes. Rerun with ≥10 min timeout or as a background task | One `--verbose` rerun, then report the exact error + `pen version`. |
| Output looks wrong | Re-export: `pen --in design.pen --export out.png --export-scale 2` | Inspect with `--verbose` / `--verbose-mcp`. Do not retry the same prompt blindly. |

## Common Mistakes

- **Don't embellish the prompt.** Pass the user's request verbatim; your extra design detail fights the CLI's own designer agent and degrades results.
- **Don't run with a short timeout.** Generation legitimately takes minutes; a default 60s timeout kills healthy runs mid-design.
- **Don't save to temp directories.** `.pen` files are working artifacts the user will iterate on — put them in the working directory.
- **Don't improvise install or auth fixes.** Follow `references/setup-troubleshooting.md`; never register accounts or invent flags.
- **Don't read all reference files preemptively.** Load only the one matching the current task.
- **Don't finish without showing the image.** A file path is not the deliverable — the visual is.

## Reference Files

Read these only when the task calls for them:

| File | When to read |
|------|--------------|
| `references/cli-reference.md` | Full flag/command list, models & agents, env vars, batch tasks, CI/CD usage |
| `references/interactive-mode.md` | Fine-grained control via `pen interactive` shell (MCP tools: `get_app_state`, `execute`, `get_guidelines`, `browser`) — for scripting or surgical edits the AI agent isn't suited to |
| `references/setup-troubleshooting.md` | `pen` not installed, `pen status` fails, auth/model errors, anything broken |
| `references/pen-format.md` | Reading or hand-editing `.pen` JSON directly, understanding components/variables/themes |

## Staying Current

This skill targets the installed `@pen.dev/cli` (currently 0.3.3). Official docs at
https://docs.pen.dev/for-developers/pen-cli (updated 2026-08-12) omit some live flags
(`--agent`, `--effort`, `--repo`, `--list-workspaces`, `PEN_AGENT_API_KEY`) and list a
stale default model. If behavior doesn't match these docs, compare `pen version` against
`npm view @pen.dev/cli version` and upgrade with `npm install -g @pen.dev/cli`. `pen --help`
is the authoritative flag list. Do not install `@pencil.dev/cli` — that is the old package.

---
name: pencil-design
description: Use this skill for any pencil.dev work, such as designing UI in a .pen file, editing an open Pencil canvas, sketching or mocking screens, instantiating components from a .lib.pen library, reading an existing design system from a .pen or .lib.pen file, fixing execute schema errors, recovering from Pencil MCP host-not-connected issues, or exporting a .pen (one frame, whole canvas, or multi-screen flow) as a single PNG/JPEG/PDF/HTML. Pick it on any mention of pencil.dev, .pen, .lib.pen, "the Pencil MCP", "the Pencil canvas", "export the canvas", "export the flow", 导出整图, 流程图导出, or a design-system/ folder in a Pencil context, even when the user phrases it casually, mid-sentence, or doesn't name the tool. This is the canonical skill for all Pencil tasks; reach for it before any general design or frontend skill when Pencil signals are present.
license: MIT
compatibility: Any AI coding tool with the pen.dev MCP server configured (Claude Code, Claude Desktop, Cursor, Windsurf, Codex CLI, Antigravity, OpenCode). The MCP server still registers as `pencil`. Headless workflows use `@pen.dev/cli` (`pen`); see `references/pencil-cli.md`.
metadata:
  version: "0.9.5"
permissions:
  mcp:
    - pencil:get_app_state
    - pencil:get_guidelines
    - pencil:execute
    - pencil:browser
  shell: none
  filesystem: project-only
  network: none
---

# Pencil Design Skill

`.pen` files are JSON (`Document.version` **2.17**). Read and write them only through the pen.dev MCP server: schema validation, live screenshots, editor sync. The format is documented JSON, not encrypted. No auto-save — tell the user to `Cmd/Ctrl+S`. Collaboration is Git-only.

Details live in references. Load them when the task hits that topic — do not pre-read the folder.

## Current MCP surface

Four tools. Older names fail. Cookbook: [`references/mcp-tools.md`](references/mcp-tools.md).

| Call this | Not this |
|-----------|----------|
| `get_app_state({ include_canvas_design, include_schema, include_scripts_and_shaders })` | `get_editor_state` |
| `execute({ input })` or `execute({ editId, edits })` | `batch_design` |
| `Get` / `GetVariables` / `Print` / `TakeScreenshot` / `Export` inside `execute` | `batch_get`, `get_variables`, `get_screenshot`, `snapshot_layout`, `export_nodes`, `export_html` |
| `browser({ action, url?, target?, querySelector? })` | (did not exist) |
| `get_guidelines` | (unchanged) |

Do not pass `filePath`. Product name is **pen.dev**; the MCP server still registers as **`pencil`**.

## Host detection

First call of every conversation:

```
get_app_state({ include_canvas_design: true, include_schema: true, include_scripts_and_shaders: false })
```

The three booleans are required. Later calls can set schema / canvas-design to `false`. Set `include_scripts_and_shaders: true` only for script/shader work.

If it errors (`transport not connected to app: desktop`), follow Failure modes row 1. Do not start the CLI.

🔴 CHECKPOINT — no `.pen` open: `get_app_state` succeeded but there is no active document. There is no `open_document` tool. Stop and ask the user to open or create a `.pen`, then wait. Do not invent a file.

## Discipline (always)

Checklist only — full text: [`references/discipline.md`](references/discipline.md).

- **Name** every node you author (PascalCase, role-bearing). Rename default `Frame` / `Group 2` as you go.
- **`context`** on pages, reusable components, fields, interactive and data-display nodes. Behaviour, not visual specs.
- **Components first.** `Get(n=>n.reusable&&Print(n.id,n.name))`. 🔴 CHECKPOINT — the user named a `.lib.pen` that is not in `imports`: ask them to attach it in the Libraries panel, then wait. After it is attached, the same inventory covers it.
- **`Print(GetVariables())` before `SetVariables`.** Only declare missing keys. Light + dark on every colour. No raw hex on rendered nodes.
- **Breakpoints** (unless the user names others): Mobile 390×844, Tablet 768×1024, Desktop 1440×900.
- **A11y:** contrast AA both modes, 44×44 hits, colour not the only signal, focus states. Deeper: [`accessibility.md`](references/accessibility.md).
- **Cover + sections** on real files. Completeness = states + flows + a11y, not happy-path only.

Source priority: live variables → live components → imported libraries → project `design-system/` → skill defaults.

## Taste

User direction wins. If none was given, apply [`references/aesthetic-foundation.md`](references/aesthetic-foundation.md). Name brand vs product register first. Logos/illustrations: `Generate(frameId, "svg", prompt)`, never hand-built paths.

## Default workflow

1. **Host + context.** `get_app_state` as above. Note open file, selection, schema version.
2. **Direction.** Synthesise type / density / accent / surface from the user's screenshot, brand, URL, or prose. Announce it. No direction → aesthetic-foundation defaults. Skip for throwaway sketches.
3. **Guidelines + inventory.** `get_guidelines()` then load one matching guide (`Web App`, `Mobile App`, `Landing Page`, …). Then `Get(n=>n.reusable&&Print(n.id,n.name))`. Hold the component id list before planning.
4. **Plan** before the first visual `execute`: direction, frame names (states + viewports), component ids, layout shape, which states/breakpoints/faults ship, surrounding flow. 🔴 CHECKPOINT — open-ended request (no tokens, no `design-system/`, no reference): ask who it's for, atmosphere, hard constraints. Ask once, then wait.
5. **Build.** One section per `execute`. 🔴 CHECKPOINT — `GetVariables()` empty and no components: ask once whether to bootstrap tokens now or design first; wait. New top-level frames start `placeholder: true`. Bare assignment for ids (`foo = Insert(...)`). End a finished section with `TakeScreenshot` of the smallest meaningful node. Full grammar: [`references/batch-design-grammar.md`](references/batch-design-grammar.md).
6. **Verify.** Distinctiveness ([`distinctiveness-checklist.md`](references/distinctiveness-checklist.md)); state / viewport / fault / annotation coverage you committed in the plan; a11y five checks; both theme modes. Structural questions: `Get` + `c.bounds` / `c.problems`. Failed `execute`: retry with `editId` + `edits`, never resend `input`.
7. **Report.** One paragraph: frames, states, notes shipped. Stop.

Pre-flight each visual `execute`: name, context, `$variable` colours, `fill_container` not `alignItems: "stretch"`, `placeholder` on new page frames.

## When to load more

| Signal | Read |
|--------|------|
| Unfamiliar component / slots / descendants | [`component-anatomy.md`](references/component-anatomy.md) |
| Building a reusable / variants / `.lib.pen` | [`composition-patterns.md`](references/composition-patterns.md) |
| Cover, sections, split files | [`file-architecture.md`](references/file-architecture.md) |
| Form / wizard / validation | [`forms.md`](references/forms.md), [`flows.md`](references/flows.md) |
| Error / empty / 404 / offline | [`states.md`](references/states.md) |
| Keyboard, hits, focus, toasts | [`interactions.md`](references/interactions.md) |
| Hierarchy / whitespace / generic | [`visual-hierarchy.md`](references/visual-hierarchy.md), [`iteration-patterns.md`](references/iteration-patterns.md) |
| Page archetypes (hero, pricing, settings) | [`layout-patterns.md`](references/layout-patterns.md) |
| Copy | [`microcopy.md`](references/microcopy.md), [`ux-writing.md`](references/ux-writing.md) |
| iOS / Android / sheets | [`mobile-patterns.md`](references/mobile-patterns.md) |
| Icons | [`iconography.md`](references/iconography.md) |
| Charts / KPI | [`data-viz.md`](references/data-viz.md), [`chart-anatomy.md`](references/chart-anatomy.md) |
| Industry | [`industry-patterns.md`](references/industry-patterns.md) |
| Style / palette / fonts (greenfield) | [`style-catalogue.md`](references/style-catalogue.md), [`colour-palettes.md`](references/colour-palettes.md), [`font-pairings.md`](references/font-pairings.md) |
| Shader / script / mesh / arcs | [`advanced-canvas.md`](references/advanced-canvas.md) + `include_scripts_and_shaders: true` |
| Live website / localhost preview | `browser` (`load-page` then `import-to-canvas` / `return-screenshot`) |
| Export / handoff / whole-canvas PNG / flow image / 导出整图 | [`export.md`](references/export.md) — load before any `Export` |
| Headless / CI / `pen` CLI | [`pencil-cli.md`](references/pencil-cli.md) — no auto-fall-back |
| Schema / node types | [`pen-schema.md`](references/pen-schema.md) |
| Worked walkthrough | `examples/example-*.md` matching the task |

## execute essentials

```
Insert / Copy / Update (alias U) / Replace / Move / Delete
SetVariables / GetVariables / Get / Print / FindEmptySpace
TakeScreenshot / Export / Generate   // "ai" | "svg" | "stock"
```

- Never set `id`. Bindings do not survive the next `execute` — reuse the returned literal id.
- Text property is `content`. Text needs `fill`. Stroke is `stroke` + `strokeWidth`, not `{ color, thickness }`.
- Icons: `type: "icon"` + `library` + `icon`. Sizing: `"fill_container"` / `"fit_content"`, never `"100%"`.
- `alignItems`: `start`/`center`/`end`. `justifyContent`: `space_between` / `space_around`.
- On error the whole snippet rolls back. Use `editId` + `edits`.

Crowded canvas: `FindEmptySpace({ width, height, direction, padding, nodeId? })` as the first line.

## Screenshot loop

End a finished visual section with `TakeScreenshot([id])` in the same `execute`. Smallest node that contains the change. Narrate what you see in one or two sentences. Skip screenshots on renames / context / metadata. Three failed iterations on the same issue → ask the user.

## Failure modes

Trigger → first fix → still failing.

| Trigger | First fix | Still failing |
|---------|-----------|---------------|
| `transport not connected` / MCP refused | Stop. Ask the user to open the pen.dev desktop app or IDE extension. | Confirm `pencil` is listed (Cursor: Settings → Tools & MCP; Codex: `/mcp`). Restart the host, then retry `get_app_state`. Do not start `pen` CLI. |
| `get_app_state` ok, no document | 🔴 CHECKPOINT: ask the user to open or create a `.pen`. Wait. | Ping `get_app_state` again. Still empty → they may have the wrong window; ask which file path is focused. |
| `GetVariables()` empty and no reusable components | 🔴 CHECKPOINT: ask once — bootstrap tokens now, or design first? | If they do not answer, design with [`aesthetic-foundation.md`](references/aesthetic-foundation.md) defaults and declare only the tokens you actually bind. Do not ask again. |
| Named `.lib.pen` missing from `imports` | 🔴 CHECKPOINT: ask them to attach it in the Libraries panel. Wait. | File missing on disk → say the path is stale; ask to update the path or create the library. Do not `Update(document)` to invent `imports`. |
| `design-system/` contains code (`package.json`, `.tsx`) | Do not overwrite. Ask where docs should go. | If they do not pick, leave the folder alone and keep tokens in the `.pen` only. |
| `execute` schema / invalid op | Read the error. Retry with `editId` + `edits`. Never resend `input`. | Same `editId`; `find` must match the already-patched snippet. Third fail → stop and quote the error. Common causes: `/` in id, `width: "100%"`, old stroke object, `icon_font`, stale binding. |
| Need a token that already exists | `Print(GetVariables())` first. Only pass absent keys. | If you already overwrote a key, restore from the `GetVariables()` values you read. Never `replace: true`. |

## Don't

- Call dead tools: `get_editor_state`, `batch_design`, `batch_get`, `get_screenshot`, `snapshot_layout`, `get_variables`, `export_nodes`, `export_html`.
- Pass `filePath` on any MCP tool.
- Hand-edit `.pen` JSON with file tools.
- Fall back to `@pen.dev/cli` / `pen` because MCP is down.
- `SetVariables` before `Print(GetVariables())`, or re-declare keys the document already has.
- Build logos / illustrations / mascots from `path` nodes — use `Generate(frameId, "svg", prompt)`.
- Invent a library import via `Update(document, { imports })`.

## Reference index

Always-on details: [`discipline.md`](references/discipline.md), [`aesthetic-foundation.md`](references/aesthetic-foundation.md), [`mcp-tools.md`](references/mcp-tools.md), [`batch-design-grammar.md`](references/batch-design-grammar.md).

On demand (see table above): anatomy, composition, file-architecture, export, forms, flows, states, interactions, layout-patterns, visual-hierarchy, iteration-patterns, microcopy, mobile-patterns, iconography, data-viz, industry-patterns, style/colour/font catalogues, advanced-canvas, pen-schema, pencil-cli.

Examples: `examples/example-login-screen.md`, `example-import-library.md`, `example-error-screen.md`, `example-form-flow.md`, `example-component-deep-dive.md`, and the other `example-*.md` files.

`design-system/` is optional user-facing templates. Do not auto-copy or auto-apply.

Platform wrapper names: [`codex-tools.md`](references/codex-tools.md).

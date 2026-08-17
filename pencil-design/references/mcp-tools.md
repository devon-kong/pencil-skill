# pen.dev MCP tools (current)

Authoritative tool surface as of **docs.pen.dev (2026-08-12)** and the installed **`@pen.dev/cli` 0.3.3**
(`pen interactive --help` + live `get_app_state`). Load this whenever you are about to call a Pencil /
pen.dev MCP tool.

The MCP server still appears in Cursor / Codex as **`pencil`**. The product name is **pen.dev**.

## The only four tools

| Tool | Purpose |
|------|---------|
| `get_app_state` | Host ping, open file, selection, optional schema + canvas rules |
| `get_guidelines` | Built-in task guides and visual style archetypes |
| `execute` | **All** reads and writes: nodes, variables, screenshots, exports, images |
| `browser` | Integrated browser: load a URL, import a page, screenshot, read DOM |

There is **no** `get_editor_state`, `batch_design`, `batch_get`, `get_screenshot`, `snapshot_layout`,
`get_variables`, `export_nodes`, or `export_html`. Those names are dead. If an older example in this
skill uses them, map them with the table below and call the current tool.

| Dead name | Current call |
|-----------|----------------|
| `get_editor_state({ include_schema })` | `get_app_state({ include_canvas_design, include_schema, include_scripts_and_shaders })` |
| `batch_design({ input })` | `execute({ input })` |
| `batch_get({ nodeIds, patterns, readDepth })` | `execute({ input: 'Print(Get(id, {depth: n}))' })` or a `Get` visitor |
| `snapshot_layout({ parentId, problemsOnly })` | `Get(id, (n, c) => c.problems && Print(...), {depth})` — `c.bounds` / `c.problems` |
| `get_screenshot({ nodeId })` | `execute({ input: 'TakeScreenshot(["id"])' })` |
| `get_variables()` | `execute({ input: 'Print(GetVariables())' })` |
| `export_nodes({ nodeIds, outputDir, format })` | `execute({ input: 'Export(["id"], "png", "./exports")' })` |
| `export_html({ nodeIds, outputPath, format })` | `execute({ input: 'Export(["id"], "html-tailwind", "./out.html")' })` |
| `Generate(id, "ai" \| "stock", prompt)` | still inside `execute`; also `"svg"` for logos / illustrations |
| `SetVariables` / `FindEmptySpace` / `Insert` / `Update` | still functions **inside** `execute`, not standalone tools |

Do **not** pass `filePath`. Tools operate on the active document. In `pen interactive`, the path is
injected automatically.

## Connect

### `get_app_state`

**Purpose.** Ping the host. Returns the active `.pen` path (if any), selection, top-level nodes,
reusable components, and whether the integrated browser is open.

**First call of every conversation** — the three booleans are required by the live tool schema:

```
get_app_state({
  include_canvas_design: true,
  include_schema: true,
  include_scripts_and_shaders: false
})
```

| Flag | When to set `true` |
|------|--------------------|
| `include_schema` | First call of the session. Loads the live `.pen` schema. Trust it over `pen-schema.md`. Later calls: `false`. |
| `include_canvas_design` | First call, or whenever you no longer have the `execute` documentation. Carries the live `execute` API. |
| `include_scripts_and_shaders` | Only when the task needs a `script` node or a `shader` fill. |

A succeeding call with **no active document** is not a failure. There is no `open_document` tool; ask
the user to open or create a `.pen` in the editor.

If the call errors with `transport not connected to app: desktop` (or any connection-refused message),
stop. Tell the user to open the pen.dev desktop app or IDE extension. Do not silently fall back to the
CLI.

Official docs examples sometimes write `get_app_state({ include_schema: true })`. The installed CLI
schema requires all three booleans — send them.

## Reference

### `get_guidelines`

**Purpose.** Load pen.dev's built-in guides (task how-tos) and styles (visual archetypes).

```
get_guidelines()
get_guidelines({ category: "guide", name: "Web App" })
get_guidelines({ category: "style", name: "Soft Bento" })
```

1. No args → list current guides and styles.
2. `{ category, name }` → load a guide, or get a style's required `params`.
3. `{ category, name, params }` → load the instantiated style.

**Guides** commonly include: `Code`, `Design System`, `Landing Page`, `Mobile App`, `Slides`, `Table`,
`Tailwind`, `Web App`. **Styles** rotate between releases (`Aerial Gravitas`, `Soft Bento`, …). Always
list first; don't invent names.

Load one or two guides, never a pile. Filter stylistic defaults against the user's direction.

## Write / read / screenshot / export

### `execute`

**Purpose.** Run a JavaScript snippet against the open document. This is the only mutation tool, and
also the only way to read nodes, take screenshots, or write export files.

```
execute({ input: 'page=Insert(document,{type:"frame",name:"LoginPage",width:1440,height:900,clip:true,placeholder:true})\nTakeScreenshot([page])' })
```

On failure the **whole snippet rolls back**. The response includes an `editId`. **Never resend the
snippet in `input`.** Retry with:

```
execute({
  editId: "<id from the failure>",
  edits: [{ find: "the exact failing fragment", replace: "the corrected fragment" }]
})
```

`find` must match the snippet as already patched by earlier edits. Keep using the same `editId` until
the call succeeds.

The full function set lives in [`batch-design-grammar.md`](batch-design-grammar.md) (now the `execute`
grammar). The functions you will use every task:

```
Insert / Copy / Update (alias U) / Replace / Move / Delete
SetVariables / GetVariables / Get / Print / FindEmptySpace
TakeScreenshot / Export / Generate
```

**First visual chunk on a new document:** `SetVariables` (only tokens that `GetVariables()` did not
already return), then `Insert` the page skeleton with `placeholder: true`, end the same call with
`TakeScreenshot` of that frame.

**Reading.** There is no separate read tool.

```
execute({ input: 'Get((n,c)=>{c.skipChildren();Print(n.id,n.name)})' })
execute({ input: 'Get(n=>n.reusable&&Print(n.id,n.name))' })
execute({ input: 'Print(Get("frameId",{depth:3}))' })
execute({ input: 'Print(GetVariables())' })
execute({ input: 'Get(screen,(n,c)=>c.problems&&Print(n.name,"in",c.parentCtx?.node.name,":",c.problems))' })
```

`Get` with a visitor replaces both the old `batch_get` and the old `snapshot_layout`. `c.bounds` is
resolved layout; `c.problems` is `"partially clipped"` / `"fully clipped"`.

**Images.** No `image` node type. Insert a frame/rectangle, then `Generate`:

- `Generate(id, "ai", "detailed prompt")` — async; result arrives after the call returns
- `Generate(id, "stock", "two keywords")` — Unsplash, applied during the call
- `Generate(id, "svg", "detailed prompt")` — logos / illustrations / mascots; **never** assemble artwork
  from `path` nodes by hand. Target must be a `frame`. Poll `Get(id,{depth:0}).placeholder` later;
  do not screenshot until the flag clears.

Official CLI shorthand `G(...)` is the same function as `Generate`.

**Export** (handoff, not review):

```
Export([heroId], "png", "./exports")
Export([pageId], "html-tailwind", "./landing.html")
```

Formats: `png` | `jpeg` | `webp` | `pdf` | `html-tailwind` | `html-css`. Images go to a directory
(one file per node id, except PDF which is one multi-page file). HTML goes to a file path.

**Screenshot cadence.** `TakeScreenshot([id])` attaches images to the same `execute` response. End a
section-completing call with a screenshot of the smallest meaningful node. Do not screenshot the
document root when a section frame will do. Do not screenshot after every 2-op tweak.

## Browser

### `browser`

**Purpose.** Drive the app's integrated browser so you can import a live page, compare a generated
site, or steal structure from a reference URL.

| `action` | What it does |
|----------|----------------|
| `load-page` | Open the browser (if closed) and load `url` (http(s) or `file:`) |
| `import-to-canvas` | Recreate the target as editable canvas layers; response gives the top-level frame id |
| `screenshot-to-canvas` | Place a screenshot of the target on the canvas as an image |
| `return-element` | Return the target's DOM + computed styles as text |
| `return-screenshot` | Return a screenshot for you to look at (does not write the document) |

`target` defaults to `full-page`. Use `query` + `querySelector` or `selection` (the user's picker)
instead of dumping the whole page. Call `load-page` first. After import, treat the result as canvas
nodes and edit with `execute` — do not keep thinking in CSS.

```
browser({ action: "load-page", url: "https://example.com" })
browser({ action: "import-to-canvas", target: "query", querySelector: "header.hero" })
browser({ action: "return-screenshot", target: "query", querySelector: ".pricing-card" })
```

Imported nodes store the source tag (and detected code-component name) in `context`, e.g.
`"Card - div"`.

## Composite recipes

### Greenfield bootstrap

1. `get_app_state({ include_canvas_design: true, include_schema: true, include_scripts_and_shaders: false })`
2. `get_guidelines()` then load the matching guide
3. `execute({ input: 'Print(GetVariables())' })`
4. One `execute`: `SetVariables` (only missing tokens) + `FindEmptySpace` + `Insert` the page
   skeleton (`placeholder: true`) + `TakeScreenshot`
5. Further `execute` calls, one section each, ending a finished section with `TakeScreenshot`
6. `Export` only if the user asked for files

### Inventory components

```
execute({ input: 'Get(n=>n.reusable&&Print(n.id,n.name))' })
```

Imported `.lib.pen` libraries are attached through the editor UI (`document.imports`). There is no
MCP `filePath` to open another file. Live canvas rules: you cannot `ref` a component that lives only
in another file until it is imported or copied in.

### Token audit

```
execute({ input: 'Print(GetVariables())' })
execute({ input: 'Get(page,(n,c)=>Print(n.id,n.name,n.fill))' })
execute({ input: 'for (id of ["a","b","c"]) Update(id,{fill:"$primary"})' })
```

### Failed snippet

Do not rewrite and resend `input`. Use `editId` + `edits`. If it fails again, keep the same
`editId` and make `find` match the already-patched snippet.

## Tool cost

Cheapest → most expensive:

| Call | Cost |
|------|------|
| `GetVariables` / `FindEmptySpace` / short `Update` | Small |
| `Get` visitor with `Print` of compact rows | Small–medium |
| `get_app_state` without schema | Small |
| `get_app_state` with schema + canvas design | Large (once per session) |
| `get_guidelines` | Medium per category |
| `execute` + `TakeScreenshot` | **Expensive** (image) |
| `browser` `return-element` on `body`/`html` | Can overflow context |
| `Generate` `"ai"` / `"svg"` | Slow, async; do other work while it runs |

## Hosts

The MCP server starts with the pen.dev desktop app or IDE extension. Officially supported assistants:
Claude Code, Claude Desktop, Cursor, Windsurf, Codex CLI, Antigravity, OpenCode.

Verify:

- Cursor → Settings → Tools & MCP → `pencil`
- Codex → `/mcp` → `pencil` should appear (backup `config.toml` first; pen.dev may modify it)
- VS Code → MCP configuration

The server is **local**. Design files stay on disk. AI prompts leave the machine only when the
assistant itself calls a model.

## See also

- [`batch-design-grammar.md`](batch-design-grammar.md) — `execute` JavaScript API
- [`pen-schema.md`](pen-schema.md) — `.pen` data model (live schema is 2.17)
- [`pencil-cli.md`](pencil-cli.md) — when to use `@pen.dev/cli` instead of MCP
- Official: [AI Integration](https://docs.pen.dev/getting-started/ai-integration),
  [pen.dev CLI](https://docs.pen.dev/for-developers/pen-cli)

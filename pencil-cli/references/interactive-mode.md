# Interactive Mode — `pen interactive`

The interactive shell calls MCP tools directly on `.pen` files. Use it for scripting, debugging, and
workflows that need fine-grained, deterministic control — the things a one-shot AI agent run is not
suited for. For ordinary "design X for me" requests, prefer agent mode (`pen --out ... --prompt ...`).

Contents: Modes · Shell Basics · Tool Reference · Example Sessions

Captured from **`@pen.dev/cli` 0.3.3** (`pen interactive --help`). Re-run that command if the
installed version differs.

## Modes

**Headless mode** — spins up a local editor without a GUI. `--out` is required; call `save()` to write.

```bash
pen interactive -o output.pen                    # new empty canvas
pen interactive -i input.pen -o output.pen       # edit an existing file
```

**App mode** — connects to a running pen.dev desktop app or IDE extension via WebSocket; changes apply live.

```bash
pen interactive -a desktop -i my-design.pen
```

Extra flags: `--enable-preview` (save a preview PNG after each change), `--preview-output <path>`
(default `~/.pencil/latest-preview.png`).

## Shell Basics

```
tool_name({ key: value })   Call an MCP tool with a JS object of arguments
tool_name()                 Call an MCP tool with no arguments
save()                      Save the document to disk
exit()                      Exit the shell
```

The file path is injected automatically — never pass it yourself.

Recommended opening sequence:

1. `get_app_state({ include_canvas_design: true, include_schema: true, include_scripts_and_shaders: false })`
2. `execute({ input: 'Get((n,c)=>{c.skipChildren();Print(n.id,n.name)})' })`
3. `execute({ input: '...' })` — mutations, `TakeScreenshot`, `Export`
4. `save()`

There are **four** tools. Do not call `get_editor_state`, `batch_design`, `batch_get`,
`get_screenshot`, `snapshot_layout`, `get_variables`, `export_nodes`, or `export_html`.

## Tool Reference

### `get_app_state({ include_canvas_design, include_schema, include_scripts_and_shaders })`

Current canvas, integrated browser, selection, open file. All three booleans are required by the live
schema.

- `include_schema: true` on the first call of a session (live `.pen` schema).
- `include_canvas_design: true` on the first call (live `execute` documentation).
- `include_scripts_and_shaders: true` only when the task needs scripts or shaders.

### `execute({ input })` or `execute({ editId, edits })`

The only read/write tool. `input` is a JavaScript snippet. Functions:

```
Insert / Copy / Update (alias U) / Replace / Move / Delete
SetVariables / GetVariables / Get / Print / FindEmptySpace
TakeScreenshot / Export / Generate   # Generate types: "ai" | "svg" | "stock"
```

On failure the whole snippet rolls back and the response includes an `editId`. **Never resend
`input`.** Retry with `{ editId, edits: [{ find, replace }] }`. Further failures keep the same
`editId`; `find` must match the already-patched snippet.

```
execute({ input: 'Get(n=>n.reusable&&Print(n.id,n.name))' })
execute({ input: 'Print(Get("frameId",{depth:3}))' })
execute({ input: 'hero=Insert(document,{type:"frame",name:"Hero",x:0,y:0,width:1440,height:900,fill:"#0A0A0A",layout:"vertical",clip:true})\nTakeScreenshot([hero])' })
execute({ input: 'Export([hero],"png","./exports")' })
```

If you don't have the `execute` documentation, call `get_app_state` with `include_canvas_design: true`.

### `get_guidelines({ category?, name?, params? })`

1. `get_guidelines()` — list guides and styles
2. `get_guidelines({ category, name })` — load a guide, or get a style's required params
3. `get_guidelines({ category, name, params })` — load with params

### `browser({ action, querySelector?, target?, url? })`

Integrated browser. Actions: `load-page`, `import-to-canvas`, `screenshot-to-canvas`,
`return-element`, `return-screenshot`. Call `load-page` first. Prefer `target: "query"` over
`full-page`. After import, edit the result with `execute` — do not keep thinking in CSS.

## Example Sessions

New design, headless:

```
pen > get_app_state({ include_canvas_design: true, include_schema: true, include_scripts_and_shaders: false })
pen > get_guidelines()
pen > get_guidelines({ category: "guide", name: "Landing Page" })
pen > execute({ input: 'hero=Insert(document,{type:"frame",name:"Hero",x:0,y:0,width:1440,height:900,fill:"#0A0A0A",layout:"vertical",clip:true})' })
pen > execute({ input: 'heading=Insert(hero,{type:"text",content:"Ship faster.",fontSize:72,fontWeight:"bold",fill:"#FFFFFF"})\nTakeScreenshot([hero])' })
pen > execute({ input: 'Export([hero],"png","./exports")' })
pen > save()
```

Editing an existing file:

```
pen > get_app_state({ include_canvas_design: true, include_schema: true, include_scripts_and_shaders: false })
pen > execute({ input: 'Get((n,c)=>{c.skipChildren();Print(n.id,n.name)})' })
pen > execute({ input: 'Get(n=>n.reusable&&Print(n.id,n.name))' })
pen > execute({ input: 'Print(Get("frameId",{depth:3}))' })
pen > execute({ input: 'btn=Insert("frameId",{type:"ref",ref:"ButtonComp",width:"fill_container"})\nU(btn+"/label",{content:"Get Started"})\nTakeScreenshot(["frameId"])' })
pen > save()
pen > exit()
```

Note for agents driving the shell: `pen interactive` is a REPL. Feed commands over stdin (a heredoc
or an interactive session) and end with `save()` + `exit()` — nothing is written to disk until
`save()`.

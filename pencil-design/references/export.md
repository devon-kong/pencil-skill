# Export

How to write image / HTML files from an open `.pen`. This file owns the **whole-canvas / multi-root** recipes. Single-node `Export` syntax lives in [`mcp-tools.md`](mcp-tools.md) and [`batch-design-grammar.md`](batch-design-grammar.md) — do not duplicate it here.

All reads and writes go through MCP `execute`. Do not switch to the `pen` CLI, an OS window screenshot, or HTML-then-browser capture.

## When to load this file

- The user wants a PNG / JPEG / WEBP / PDF / HTML of the open design.
- They say *whole canvas*, *one image*, *flow diagram*, *export the board*, *导出整图*, *流程图*, or want several screens **plus** arrows / notes / overlays in a single file.
- `Export(["document"])` just failed, or a single-node export came back as a blank / incomplete board.

## Pick a path

| What they want | What to do |
|----------------|------------|
| One screen / one frame | `Export` that node's id. Stop. |
| Already one parent that contains everything | `Export` that parent. Do **not** build a board. |
| Several roots that must appear **together** | **Default: Recipe A (`ExportBoard`).** Recipe B (compose) only if the user forbids any canvas edit, Recipe A failed, or they asked to compose. |

Do not run A and B in the same task. `Export` writes **one file per node id** — siblings on the infinite canvas do not composite. `Export(["document"])` fails (`"document"` is not a node id). `TakeScreenshot(["document"])` can *show* the whole canvas in the reply, but it is downsampled (transparent documents often render black). Never hand that screenshot to the user as the deliverable.

---

## HTML Tailwind fidelity — deterministic repair only

`html-tailwind` is a convenience export, not a lossless `.pen` renderer. In
particular it can flatten per-corner radii, turn a declared height into `h-fit`,
or omit `clip`. Do **not** fix those by looking at the page and hand-editing
classes. The only approved route is this inventory-bound pipeline. It changes
the exported HTML only; it never edits the `.pen` JSON.

### Gate 0 — scope and tool availability

- This recipe requires `scripts/fix_pen_html.py` beside this skill and a local
  Python 3 standard library. If either is unavailable, stop after the raw
  export; do not hand-patch HTML.
- Every node must have a non-empty Pencil name. The inventory is a full export
  manifest, not a six-row list of suspected dialogs.
- `dockBottom` is an explicit policy flag. Set it only for an already-known
  bottom sheet family in the source design; never infer it from an HTML image.

### 1. Pick one artifact contract before exporting

Do not mix a buildable page with flow annotations.

| Contract | Allowed roots | Purpose |
|---|---|---|
| `screen-html` | exactly one screen frame | engineering handoff; no titles, notes, arrows, or `Flow Overlay` |
| `flow-html` | screens plus the explicit overlay/title/note roots | design-review flow diagram; annotations are expected |

For a page, export the screen only:

```
Export(["<screen-id>"], "html-tailwind", "./exports/<screen-id>.raw.html")
```

Never use a flow-board HTML as evidence that an individual page is clean. A
global red border or arrow can legitimately cross the canvas near a screen.
Some Pencil versions still append `Flow Overlay` to a one-screen HTML export;
the explicit build-time scope filter below removes that unapproved root, and
the later check proves it is absent from the deliverable.

### 2. Capture the full `.pen` truth inventory for that exact export

Run one `Get` visitor and save its `Print` lines verbatim as
`./exports/inventory.jsonl`. The `path` is required because raw Pencil HTML
has `data-pencil-name` but may not have `data-pencil-id`; duplicate names make
name-only matching unsafe.

Call `Get("<screen-id>", …)` for `screen-html`, or `Get(document, …)` for a
flow export. For a multi-root flow, the `Export` list must stay in document
order. The following path builder is relative to the selected export roots,
not the entire canvas, so a one-screen export still has root path `[0]`.

For a known `Dialog Container` bottom-sheet family, this is the capture
predicate. For another family, replace only the explicit `isDockedSheet`
predicate with the policy already agreed for that design.

```
const paths={}
const nextChild={}
let rootIndex=0
Get((n,c)=>{
  if(!n.name)throw new Error("Every exported node needs a name")
  const parentId=c.parentCtx?.node?.id
  let path
  if(!parentId||!paths[parentId])path=[rootIndex++]
  else {
    const childIndex=nextChild[parentId]??0
    nextChild[parentId]=childIndex+1
    path=[...paths[parentId],childIndex]
  }
  paths[n.id]=path
  const parent=c.parentCtx?.bounds
  const isDockedSheet=n.name==="Dialog Container"&&parent&&typeof n.y==="number"&&n.y+c.bounds.height>=parent.height-2
  Print(JSON.stringify({
    id:n.id,name:n.name,path,
    x:n.x,y:n.y,width:n.width,height:n.height,
    boundsWidth:c.bounds.width,boundsHeight:c.bounds.height,
    parentBoundsHeight:parent?.height,
    cornerRadius:n.cornerRadius,clip:n.clip,padding:n.padding,
    dockBottom:isDockedSheet
  }))
})
```

The script rejects inventories that are not a one-to-one match with every
`data-pencil-name` element in the raw export. This is intentional: an
unmatched node is a failed export, not permission for a manual correction.

### 3. Build, scope-check, and verify without vision

```
python3 <skill-root>/scripts/fix_pen_html.py \
  --html ./exports/raw.html \
  --inventory ./exports/inventory.jsonl \
  --out ./exports/patched.html \
  --expected-root <screen-id> \
  --scope-filter \
  --report ./exports/patched.report.json

python3 <skill-root>/scripts/fix_pen_html.py \
  --html ./exports/patched.html \
  --inventory ./exports/inventory.jsonl \
  --check \
  --expected-root <screen-id> \
  --report ./exports/check.report.json
```

The build prints the injected-ID and changed-node counts. `--check` is
read-only for the HTML and must print `no patches needed`; `--report` is the
only optional write in check mode. The script fails before writing an HTML
artifact when a node is missing, duplicated, unexpected, structurally
mis-mapped, or outside the expected root scope. It is byte-idempotent: a
second build must make no change.

A non-visual model accepts only when both reports have `"ok": true`, the
`roots` list equals the approved scope, every `docked[].ok` is true, and the
second report has an empty `patched` list. These are release gates, not hints.

The repairs are intentionally narrow:

| `.pen` truth | HTML repair |
|---|---|
| `[16,16,0,0]` corner radius | `rounded-tl-[16px] rounded-tr-[16px]` |
| numeric `height` | `h-[Npx]`, replacing `h-fit` |
| explicit `dockBottom:true` | `h-[parentBoundsHeight-y]` |
| `clip:true` | `overflow-hidden` |

Do not add `overflow-hidden` merely because a height was repaired: that would
change a source node whose `clip` is false.

### 4. Optional visual audit

Use this only when a human or visual-capable model is available. It is not a
release prerequisite for a weak model.

1. `TakeScreenshot(["<frame-id>"])` from the open `.pen`.
2. Load the patched local HTML with `browser({ action:"load-page", url:"file:///absolute/patched.html" })`.
3. `return-screenshot` the same node by its injected ID, for example
   `[data-pencil-id="<frame-id>"]`.
4. Compare the sheet's bottom edge and lower corners. A docked sheet must meet
   the frame bottom; only the corner radii recorded in the inventory may be
   present. Check this per frame, not by searching class strings.

No pixel-perfect text assertion is implied by this audit; the machine gates
already validate the geometry this repair owns. A visual mismatch is a reason
to extend the inventory rule or script fixture, never a reason to edit one
HTML page by hand.

---

## Recipe A — `ExportBoard` (default)

Pencil renders a node and its descendants. Arrows in a sibling overlay are invisible when you export a screen, and a screen is invisible when you export the overlay. Copying every root into one white frame lets the renderer composite them.

Use **`Copy`**, not `ref`. Root screens and overlays are almost never `reusable: true`. **`Copy`**, never `Move` — `Move` would rip the originals off the canvas.

### 1. Leftover board?

A previous run may have crashed after `Insert`. If a root named `ExportBoard` exists, `Delete` it first.

```
Get(document,(n,c)=>{if(c.depth===0)Print(n.id,n.name);return},{depth:0})
```

### 2. Build the board and look at it

One `execute`. The response lists `ExportBoard` → a generated id (e.g. `"WrLlx"`). **That literal id is the only handle that survives this call** — do not reuse the JS name `board` in a later `execute`.

```
PAD=40
items=[]
Get(document,(n,c)=>{
  if(c.depth===0&&n.name!=="ExportBoard"){
    items.push({id:n.id,x:n.x??0,y:n.y??0,i:c.index,bx:c.bounds.x,by:c.bounds.y,br:c.bounds.x+c.bounds.width,bb:c.bounds.y+c.bounds.height})
  }
  return
},{depth:0})
items.sort((a,b)=>a.i-b.i)
originX=Math.min(...items.map(t=>t.bx))-PAD
originY=Math.min(...items.map(t=>t.by))-PAD
W=Math.ceil(Math.max(...items.map(t=>t.br))-originX+PAD)
H=Math.ceil(Math.max(...items.map(t=>t.bb))-originY+PAD)
space=FindEmptySpace({width:W,height:H,direction:"right",padding:100})
board=Insert(document,{type:"frame",name:"ExportBoard",x:space.x,y:space.y,width:W,height:H,layout:"none",fill:"#FFFFFF",clip:true})
for(const t of items)Copy(t.id,board,{x:t.x-originX,y:t.y-originY})
Print("board",board,"W",W,"H",H,"count",items.length)
TakeScreenshot([board])
```

- Copy in **document index order** (later = on top) so the overlay lands above the screens.
- Position each copy with **`node.x / node.y` minus the same origin**. Size the board from **`c.bounds`**. Two origins is what makes arrows look off.
- White fill. Overlay frames are usually transparent; without a white board the PNG is a checkerboard or a black field.
- Do **not** set `placeholder: true` (the usual new-frame habit). The board must render as a real frame.
- `FindEmptySpace` so the board does not land on the live art. If it errors, `Insert` at `x = max(items.br) + 100`, `y = 0` instead.

Read the screenshot. If screens, overlay, notes, and title are all there on white, continue. If not, delete the board and stop — do not Export a broken board.

### 3. Export

PNG `outputPath` is a **directory**. The file name is always `{boardId}.png`. Default scale is 2.

- Review / iterate: `{scale: 1}`
- Deliver: `{scale: 2}` when `W*scale ≤ 8192` and `H*scale ≤ 8192`. Otherwise drop to `1.5` or `1`.

```
Export(["<boardId>"], "png", "./exports", {scale: 1})
```

Use `./exports` (or another project-relative directory the user named). Let the MCP host resolve it.

Then copy / rename `{boardId}.png` to the filename the user asked for, using the host's normal file tools.

### 4. Delete the board (mandatory)

Run this even when Export failed.

```
Delete("<boardId>")
Get(document,(n,c)=>{if(c.depth===0)Print(n.id,n.name);return},{depth:0})
```

The printed roots must match step 1 (no `ExportBoard`, original ids unchanged). Tell the user the board was temporary and is gone. The editor may still show unsaved — that is the insert/delete, not a new structure.

---

## Recipe B — Export nodes + compose (fallback)

Use only when Recipe A is off the table. This path does **not** insert anything on the canvas.

**Gate — fail closed.** Before Export or JSON:

1. Confirm the file `scripts/compose_export.py` exists next to this skill's `SKILL.md` (the folder that contains `SKILL.md` is `<skill-root>`).
2. Confirm the host can run a local Python on that file.

If either check fails: **stop Recipe B**. Say so, and use Recipe A (or tell the user the skill copy is missing `scripts/`). Do **not** write PIL / ImageMagick / a second compose script. A checkerboard or transparent board almost always means you skipped this script and saved a raw Overlay PNG.

### 1. Inventory

```
Get(document,(n,c)=>{
  if(c.depth===0&&n.name!=="ExportBoard"){
    Print(JSON.stringify({id:n.id,name:n.name,x:n.x??0,y:n.y??0,i:c.index}))
  }
  return
},{depth:0})
```

Skip any node that already lives *inside* an overlay you are also exporting, or it will paste twice. Sort by `i` and keep that order — it is z-order.

### 2. Export every root in one call

Same scale you will put in the manifest. `outputPath` is a directory; files are `{id}.png`.

```
Export(["id1","id2","…"], "png", "./exports/nodes", {scale: 1})
```

Copy the **absolute directory** from the Export response (the parent of `{id}.png`). That string is `indir`. Do not reconstruct it, and do not use `./exports/nodes` in the manifest — Export resolves relative to the `.pen`, the script does not.

The PNG's pixel size can differ from `c.bounds` by 1px (text nodes by more). The script pastes each file at its **actual** size. Do not put width/height in the manifest.

### 3. Pillow

```
python3 -c "from PIL import Image"
```

If that fails — 🔴 CHECKPOINT, ask once and wait:

> Pillow is missing. Install it globally for this Python, or in a project venv?

Do not install until they answer. Then:

- **Global:** `python3 -m pip install Pillow`. If the host refuses (`externally-managed-environment`), quote the error and ask how they want to proceed. Do not pass `--break-system-packages` or invent a package manager they did not name.
- **Venv:** `python3 -m venv .venv` in the project (or the directory they named), then install with that interpreter (`.venv/bin/python -m pip install Pillow`; Windows: `.venv\Scripts\python.exe -m pip install Pillow`). Run the compose script with **that same** interpreter.

### 4. Manifest + script

Write a JSON file. `indir` and `outfile` **must be absolute**. The script rejects relative paths. Fill `nodes` from step 1 — do not copy example ids.

```json
{
  "scale": 1,
  "pad": 40,
  "indir": "/absolute/dir/printed-by-Export",
  "outfile": "/absolute/path/to/deliverable.png",
  "nodes": [
    {"id": "<id-from-Get>", "x": 0, "y": 0}
  ]
}
```

`nodes` is the step-1 list in index order. `x` / `y` are `node.x` / `node.y`. `scale` must match the `Export` call.

```
<python> <skill-root>/scripts/compose_export.py /absolute/path/to/compose-manifest.json
```

`<python>` is `python3` or the venv interpreter from step 3. The script prints `mode=RGB` and `deliver this file only`. That `outfile` is the only deliverable. Do not post-process. If the host cannot execute the script, go back to the gate — use Recipe A.

---

## Verify the file

1. The file exists at the path you told the user. Recipe B: it is the script `outfile`, not a `{id}.png` from the export directory.
2. Pixel size matches what Recipe A printed as `W`/`H` × scale, or what the compose script printed as `canvas=`. Recipe B: the script line includes `mode=RGB`.
3. Open / read the PNG: every intended root is visible, arrows and notes sit on the screens, **background is opaque white** (no checkerboard), nothing clipped at the edge. Checkerboard = you delivered a raw node export; run the script and deliver `outfile`.
4. Recipe A only: canvas roots still match the pre-export list.

Do not verify by colour-scanning pixels at hardcoded coordinates. Do not treat `TakeScreenshot(["document"])` as the delivered file.

## Don't

- Call dead tools: `export_nodes`, `export_html`, `get_screenshot`.
- `Export(["document"])`.
- `ref` the roots, or `Move` them into the board.
- Leave `ExportBoard` on the canvas.
- Run Recipe A and Recipe B together, or write a second compose script. If `compose_export.py` is missing or Python cannot run, use Recipe A — do not improvise.
- Change overlay path geometry, viewBoxes, or original `x`/`y` "to make export easier".
- Fall back to `@pen.dev/cli` or a desktop window screenshot.
- Pass `filePath` on MCP tools (see SKILL.md).
- Hard-code a node-id table from a previous file.

## Failures

| What happened | What to do |
|---------------|------------|
| `Failed to find a node with id document` | Expected. Use Recipe A or B. |
| `ref` of a screen does nothing useful | Use `Copy` (Recipe A). |
| Screenshot is a white / empty board | Copies did not run, or ids were wrong. `Delete` and rerun A.2. |
| Checkerboard or transparent board | Recipe A: board `fill` was not `#FFFFFF`. Recipe B: you delivered a per-node PNG or skipped the script. Deliver `outfile` only. |
| `compose_export: indir must be absolute` | Put Export's printed directory in `indir`, not `./exports/…`. |
| `compose_export.py` missing / host has no shell | Stop B. Use Recipe A. |
| Arrows shifted relative to screens | Two different origins, or copy/manifest order ≠ document index. Redo from inventory. |
| `Export` succeeded but `ExportBoard` is still a root | You skipped A.4. `Delete` it now. |
| Scale error / enormous bitmap | Lower `scale` so both edges stay ≤ 8192. |
| `compose_export: Pillow is not installed` | Recipe B step 3. Ask global vs venv; wait. |
| `compose_export: missing export: …` | `Export` did not write that id, or `indir` is wrong. |

## Prefer this when authoring a new flow

Put screens, notes, and the overlay **inside one named parent** from the first `Insert`. Later exports are `Export([parentId], "png", "./exports")` with no board and no compose. A and B are workarounds for files that already laid siblings out on the document root.

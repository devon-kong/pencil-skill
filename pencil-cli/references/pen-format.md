# The .pen Format

A `.pen` file is JSON describing an object tree (like HTML/SVG) of graphical entities on an infinite 2D canvas. Read this file when you need to inspect a `.pen` file directly, hand-edit one, or understand what the CLI's tools produce. You rarely need to edit `.pen` JSON by hand — prefer agent mode or `pen interactive` — but understanding the structure helps when reviewing or debugging.

Contents: Basics · Layout · Graphics · Components & Instances · Variables & Themes · Full Schema

## Basics

- Every object has a unique `id` and a `type` (`frame`, `rectangle`, `text`, `ref`, `icon`, `script`, `note`, `prompt`, `context`, …). Live document version is **2.17**. Do not use the old `icon_font` type.
- Top-level objects sit on an infinite canvas with `x`/`y` for the top-left corner. Nested objects are positioned relative to their parent.

## Layout

- A parent can take over sizing/positioning of children with a flexbox-style system: `layout` (`"none"` | `"vertical"` | `"horizontal"`), `gap`, `padding`, `justifyContent`, `alignItems`.
- Sizes can be fixed numbers or dynamic: `"fill_container"` (fill the parent) or `"fit_content"` (fit the children), with optional fallback like `"fit_content(100)"`.
- Children may fill the parent or use fixed `width`/`height`; parents may fit children or use fixed sizes.

## Graphics

- Appearance comes from `fill`, `stroke`, and `effect`.
- A fill is a solid `color` (hex `#RGB`/`#RRGGBB`/`#RRGGBBAA`), a `gradient` (linear/radial/angular), an `image`, or a `mesh_gradient`. Objects can stack multiple fills in document order.
- One stroke per object (the stroke itself can have multiple fills); multiple effects, applied in order.

## Components & Instances

Any object marked `"reusable": true` becomes a component. Type `"ref"` places an instance:

```json
{ "id": "foo", "type": "rectangle", "reusable": true, "x": 0, "y": 0, "width": 100, "height": 100, "fill": "#FF0000" }
{ "id": "bar", "type": "ref", "ref": "foo", "x": 120, "y": 0 }
```

Instances override properties directly, and nested content via the `descendants` map — prefix nested instance IDs with a slash path:

```json
{ "id": "save-alert", "type": "ref", "ref": "alert",
  "descendants": {
    "message": { "content": "You have unsaved changes." },
    "ok-button/label": { "content": "Save" }
  } }
```

A descendant entry containing a `type` replaces the object outright; an entry with only `children` replaces just the children (ideal for container components: panels, cards, sidebars). A frame intended to accept children this way can be marked `"slot": ["round-button", "icon-button"]` to suggest which components fit.

## Variables & Themes

Document-wide variables hold colors and numbers; reference them with a `$` prefix:

```json
{ "variables": { "color.background": { "type": "color", "value": "#FFFFFF" } },
  "children": [ { "id": "landing-page", "type": "frame", "fill": "$color.background" } ] }
```

A variable with multiple values resolves to the last entry whose `theme` is satisfied; `themes` declares the axes (first value is the default), and any node can set `"theme": { "mode": "dark" }` for its subtree:

```json
{ "variables": {
    "color.background": { "type": "color", "value": [
      { "value": "#FFFFFF", "theme": { "mode": "light" } },
      { "value": "#000000", "theme": { "mode": "dark" } }
    ] } },
  "themes": { "mode": ["light", "dark"], "spacing": ["regular", "condensed"] } }
```

This is how light/dark variants, density scales, etc. are encoded — one design, several theme settings.

## Full Schema

The authoritative, exhaustive schema is not reproduced here. To get it for the installed version, run:

```
pen interactive -o scratch.pen
pen > get_app_state({ include_canvas_design: true, include_schema: true, include_scripts_and_shaders: false })
```

The format is live and may introduce breaking changes — trust the schema from the installed CLI over any static documentation.

# Example: import a `.lib.pen` and use its components

User says:

> *"Use the design library at `design/system.lib.pen` and add a login form using the Button and Input components."*

A `.pen` file is already open. The library is **not** currently imported.

---

## Step 1: Detect host

```
get_app_state({ include_canvas_design: true, include_schema: true, include_scripts_and_shaders: false })
```

Succeeds. The active document is open with root id `document`. Note the imports field: it's empty or doesn't contain `design/system.lib.pen`.

## Step 2: Verify the library file exists

Check `design/system.lib.pen` exists in the project (a directory listing, not the MCP). Suppose it does.

## Step 3: Attach the library, then inventory

Current MCP tools have no `filePath`. Attach `./design/system.lib.pen` through the editor's Libraries panel (alias `ds`). Confirm it landed:

```
get_app_state({ include_canvas_design: false, include_schema: false, include_scripts_and_shaders: false })
```

The `imports` field now lists `ds → ./design/system.lib.pen`. Then inventory the open document — imported reusable components appear here:

```
execute({ input: 'Get(n=>n.reusable&&Print(n.id,n.name))' })
```

Result: `ButtonPrimary`, `ButtonSecondary`, `Input`, `Textarea`, `Card`.

## Step 4: Plan and tell the user

> *"Library imported as `ds`. I'll add a 360px form to your current page with email + password `Input` instances and a `ButtonPrimary` instance for submit. The form uses a 1px hairline border and no shadow, consistent with a utility form rather than a marketing card."*

## Step 5: Build the form

```
execute({ input: `
form = Insert(document, { type: "frame", name: "LoginForm", layout: "vertical", gap: "$space-4", padding: "$space-6", width: 360, cornerRadius: 12, fill: "$surface", stroke: "$border", strokeWidth: 1 })
title = Insert(form, { type: "text", content: "Sign in", fontSize: "$text2xl", fontWeight: 700 })
email = Insert(form, { type: "ref", ref: "Input", descendants: { label: { content: "Email" }, input: { placeholder: "you@example.com" } } })
pwd = Insert(form, { type: "ref", ref: "Input", descendants: { label: { content: "Password" }, input: { type: "password" } } })
submit = Insert(form, { type: "ref", ref: "ButtonPrimary", descendants: { label: { content: "Sign in" } } })
` })
```

Five ops. Three non-obvious decisions in this form spec:

- **Width 360px, not 400px or wider.** 360px is the compact utility width for a login form. Wider reads as a landing-page card. The difference is subtle but changes the register.
- **Hairline border, no shadow.** `stroke: "$border", strokeWidth: 1` with no `effect` property. A drop shadow shifts a utility form into the marketing-page register. The generic default adds a shadow; this spec does not.
- **`$text2xl` / 700 for the title, not a display scale.** A login form is a utility action. Display-scale headings make it read as a marketing surface.

## Step 6: Verify (structural-first)

Cheapest first: confirm the refs resolved and bound correctly:

```
execute({ input: 'Print(Get(email,{depth:2}))\nPrint(Get(pwd,{depth:2}))\nPrint(Get(submit,{depth:2}))' })
```

This returns the resolved instance trees. If a `ref` shows as a placeholder (no resolved descendants, original component name missing), the import path is wrong or the component id is misspelled. Fix and retry before screenshotting.

If the refs resolved, take one screenshot scoped to the form:

```
execute({ input: 'TakeScreenshot([form])' })
```

Narrate: verify fonts, the primary colour from the library's variables, and overall rhythm. Confirm the form has the hairline border and no shadow. Don't screenshot the whole page when the form subtree is what changed.

---

## Common pitfalls

- **Component id case sensitivity.** `ButtonPrimary` is not `buttonPrimary` and not `Button-Primary`. Get the id from the library; don't guess.
- **Variable scope.** Variables defined in the library are usable in the importing document, but only after the import is added. Don't reference `$libraryVar` before the library is attached.
- **Path is relative to the importing `.pen`**, not to the project root. `./design/system.lib.pen` works only if the current document is at the project root.

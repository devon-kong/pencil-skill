# Discipline rules

Always-on correctness rules for any Pencil / pen.dev task. SKILL.md keeps the checklist; this file owns the full text.

Load when naming, `context`, tokens, components-first, breakpoints, Cover/sections, or metadata need more than the checklist.

## Contents

- [Naming](#naming)
- [Context](#context)
- [Components first](#components-first)
- [Themes](#themes)
- [Responsive](#responsive)
- [Accessibility baseline](#accessibility-baseline)
- [File architecture](#file-architecture)
- [Design completeness](#design-completeness)
- [Design source priority](#design-source-priority)
- [Metadata and annotations](#metadata-and-annotations)

## Naming

Every node you create gets a meaningful `name`. Default `Frame`, `Group`, `Text` names are bugs.

- PascalCase, semantic, role-bearing: `LoginCard`, `EmailField`, `SubmitButton`. Not `Frame 1`, `wrapper`, `f4`.
- Names should survive the file — a maintainer reading layers later should know what each frame *is*.
- Components named after role, not treatment: `PrimaryButton`, not `BlueButton`.
- Inner wrappers count: `HeroContent`, `FieldStack`. If you cannot name it, you do not need it.
- When you read an existing file, rename default-shaped names (`Frame`, `Group 2`, `Text 4`) with a `U` in the same `execute` where you already touch that area. Do not rename nodes you have not understood.

## Context

Every non-trivial node needs a `context` string: reusable components, page frames, form fields, interactive elements, data-display nodes.

Annotate behaviour, not visual specs. Data source, validation, permission gates, analytics, a11y roles, conditional logic. Do not annotate spacing or colour — `Get` reads those.

Backfill missing `context` with a `U` in the same `execute`. If you cannot tell what a node is for, leave it blank rather than invent.

## Components first

Before primitives, look for an existing component.

```
execute({ input: 'Get(n=>n.reusable&&Print(n.id,n.name))' })
```

Imported `.lib.pen` libraries appear in that inventory after the user attaches them in the Libraries panel. There is no `filePath`. You cannot `ref` a component that only lives in another file.

Inspect an unfamiliar component before instantiating:

```
execute({ input: 'Print(Get("ComponentId",{depth:4,resolveInstances:true}))' })
```

Look for `slot` frames, named children (valid `descendants` keys), and `theme` values. Nested path `a → b → c` is `"a/b/c"`. Full guide: [`component-anatomy.md`](component-anatomy.md).

Build from primitives only when no matching component exists, the user asked for a one-off, or variants cannot bridge the gap — then surface extracting it.

If a name does not quite match (`PrimaryButton` vs `SubmitButton`), use the existing component.

## Themes

Every new document declares `mode` with `light` and `dark`. Every color variable carries both.

Call `Print(GetVariables())` before any token work. Only `SetVariables` keys that are absent. `replace: false` still overwrites keys you pass.

Themed values auto-register the axis. Test both modes before declaring done.

No raw hex on rendered elements — bind `$variableName`. A screenshot that shows `#FFFFFF` / `#000000` / `#3B82F6` on a rendered node is a bug.

## Responsive

Canonical breakpoints unless the user says otherwise:

| Breakpoint | Frame size | Content max-width | Side gutter | Column gap |
|------------|------------|-------------------|-------------|------------|
| Mobile     | 390 × 844  | 358               | 16          | 12         |
| Tablet     | 768 × 1024 | 704               | 32          | 16         |
| Desktop    | 1440 × 900 | 1200              | 120         | 24         |

- Per-breakpoint frames for marketing / dashboards (`LoginPage_Desktop` + `_Mobile`).
- Single fluid frame for app surfaces (`width: "fill_container"`).

Bind content max-width to `$maxContent` (default 1200). Body text never exceeds ~65ch.

## Accessibility baseline

Five checks in the verification pass. Fail any one → not done.

1. Contrast: body ≥ 4.5:1 (WCAG AA); large text (≥ 24px) and UI ≥ 3:1. Both modes.
2. Hit targets ≥ 44 × 44. Icon-only buttons included.
3. Colour is never the only signal.
4. Names map to roles (`PrimaryAction`, `FormError`).
5. Components cover default / hover / focus / disabled (focus can be a 2px outline).

Deeper coverage: [`accessibility.md`](accessibility.md).

## File architecture

Every real `.pen` opens with a top-level `Cover` at origin: owner, status (`Discovery` / `In design` / `Design review` / `Engineering review` / `Ready for build` / `In build` / `QA` / `Shipped` / `Deprecated`), version, date, scope, links. Cover `context`: `"File operating manual: owner, status, version, scope, links."`

Section regions: `SourceOfTruth`, `BuildReady`, `UXStates`, `Responsive`, `Exploration`, `Archive`. `FindEmptySpace` between them. Never park exploration in SourceOfTruth.

Multi-screen names use `/` in `name` only (never in `id`):

```
Reporting / Export / 03 / Configure / ValidationError / Desktop
```

Full patterns: [`file-architecture.md`](file-architecture.md).

## Design completeness

Before done: component states ([`states.md`](states.md)), flows if multi-screen ([`flows.md`](flows.md)), a11y beyond the five checks. Happy-path-only is incomplete.

## Design source priority

Highest → lowest:

1. Live `.pen` variables — `Print(GetVariables())`.
2. Live reusable components — `Get(n=>n.reusable&&Print(n.id,n.name))`.
3. Imported `.lib.pen` — `imports` on `get_app_state`. Attach in the Libraries panel if missing.
4. Project `design-system/` docs — only if 1–3 are empty.
5. Skill defaults — only if 1–4 are empty.

If 1–3 return results, 4 and 5 do not drive tokens or components.

## Metadata and annotations

Interactive nodes carry `metadata`: `{ type: "interactive"|"display"|"static", testId, analytics?, aria?, copy?, validation? }`. Set it in the same `execute` that creates the node.

Screen-level surfaces ship sibling `note` nodes to the right (one concern each): state contract, accessibility contract, validation copy, motion contract, analytics events, i18n, flow context.

`note` accepts TextStyle, not `fill` / `stroke` / `effect`. They do not render in `TakeScreenshot`.

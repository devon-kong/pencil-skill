# Aesthetic foundation

Taste rules when the user has not given a direction. User direction always wins. SKILL.md keeps the precedence rule; this file owns the defaults.

Load when there is no reference image / brand / URL, when a design reads generic, or when colour / type / shadow / microcopy defaults are in play.

## Contents

- [Precedence](#precedence)
- [Register](#register)
- [Negative-space defaults](#negative-space-defaults)
- [Type defaults](#type-defaults)
- [Shadows and radius](#shadows-and-radius)
- [Optical precision](#optical-precision)
- [Microcopy](#microcopy)
- [Self-critique gate](#self-critique-gate)
- [Anti-patterns](#anti-patterns)

## Precedence

1. User direction wins (screenshot, brand, URL, prose). Synthesise type, density, accent, surface, motion and announce it.
2. Defaults below apply only when no direction was given.

## Register

- **Brand** — marketing, landing, campaign. More chroma, larger type, broader rhythm.
- **Product** — app, dashboard, settings. Restrained chroma, tighter rhythm, density that serves the data.

Name the register before aesthetic moves. Cue in the task → file in focus → project convention. If you cannot tell, ask once. Deep guidance: [`brand.md`](brand.md) / [`product.md`](product.md).

## Negative-space defaults

- Two-role colour: 4–5 neutrals + 1–3 accents. At most one competing hue. Saturation under ~80% except status colours.
- Neutrals from one family (Zinc *or* Slate *or* Stone).
- Hue-tint borders/shadows toward a coloured surface.
- Hover / focus / active *increase* contrast, never decrease.
- Never bind raw `#000000` / `#FFFFFF` for surfaces — use off-black / off-white tokens.
- No neon, glow shadows, or purple/blue gradient heading fills unless the brand asks.
- Colour-blind safety: never red/green-only. Charts: [`data-viz.md`](data-viz.md).

## Type defaults

When `tokens.md` does not pin fonts:

- Dashboards: `Geist` + `Geist Mono`, or `Satoshi` + `JetBrains Mono`.
- Marketing: `Cabinet Grotesk` or `Satoshi`; serif only if the brand warrants it.
- Banned by default: `Inter`, generic serifs (`Times`, `Georgia`, `Garamond`).
- Body ≤ ~65ch. Tabular nums on numeric columns. `text-wrap: balance` on multi-line display headings.

Menus: [`style-catalogue.md`](style-catalogue.md), [`colour-palettes.md`](colour-palettes.md), [`font-pairings.md`](font-pairings.md).

## Shadows and radius

Layered pair, not a single 40% drop:

```
0 1px 2px rgba(0, 0, 0, 0.06),
0 4px 12px rgba(0, 0, 0, 0.10)
```

Child `cornerRadius` ≤ parent. Flush child at padding `p` inside parent radius `r` uses `r - p`.

## Optical precision

Nudge icons 1–2px when the bounding box is centred but the glyph is not. Mute icon contrast vs its label. Modals sit slightly above geometric centre (40–45% from top). See [`visual-hierarchy.md`](visual-hierarchy.md).

## Microcopy

Active voice, second person, title case for labels. Numerals for counts. Action-specific buttons (`Save changes`, not `Submit`). Errors state what happened and what to do next. Empty states show what is possible. Full framework: [`microcopy.md`](microcopy.md), cliché list: [`ux-writing.md`](ux-writing.md).

## Self-critique gate

Before done, 60 seconds:

1. Could a non-designer recognise the brand or industry?
2. Where does the eye go first / second / third?
3. What is decorative-only?
4. What single change would make this less AI-generated? Make it.

Rescues: [`iteration-patterns.md`](iteration-patterns.md). Distinctiveness pass: [`distinctiveness-checklist.md`](distinctiveness-checklist.md).

## Anti-patterns

Treat as bugs unless the user opted in: raw `#000`/`#FFF`, `Inter`, neon/glow/gradient headings, default three-equal-card feature grids, fabricated metrics, `John Doe` / `Acme` / lorem, clichés (`Elevate`, `Seamless`, `Unleash`), `LABEL // YEAR`, production emojis, “Scroll to explore”, glassmorphism-by-default, hero-metric template, nested cards, modal-as-first-thought.

Logos / illustrations / mascots: `Generate(frameId, "svg", prompt)` — never hand-built paths.

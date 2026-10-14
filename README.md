# saulno.github.io

Personal site and blog of Saul Neri. Static HTML and CSS, written in
Markdown. One Python script (stdlib only, no dependencies) turns your
`.md` files into pages and rebuilds the index; a GitHub Action runs it
on every push. Push to `main` and GitHub Pages serves it.

## Philosophy

Black and white, serif type, hairline rules, generous whitespace.
Restraint as a design principle: nothing decorative that doesn't carry
meaning. Every page is a document, not an app.

## File map

```
index.html                     Landing page (about + post list)
style.css                      The entire design
md/                            WHERE YOU WRITE (Markdown entries)
tools/build.py                 md/ -> posts/ + index regeneration
posts/                         GENERATED. Do not edit by hand.
.github/workflows/build.yml    Builds md -> html on every push
README.md                      This file
```

---

## Runbook

### Writing an entry (the normal flow)

1. Create a file in `md/`. Name it in short, hyphenated, lowercase
   form — the filename becomes the URL:
   `md/on-slow-software.md` → `/posts/on-slow-software.html`.
2. Start it with front matter, then write Markdown below it:

   ```markdown
   ---
   title: On slow software
   date: 2025-10-11
   description: One sentence for search results and link previews.
   ---

   Most software today is in a hurry. ...
   ```

   - `date` must be `YYYY-MM-DD` (it sorts the index and fills `<time>`).
   - `draft: true` keeps an entry off the site while you work on it.
   - Supported Markdown: paragraphs, `## ` / `### ` subheadings,
     `**bold**`, `*italic*`, `` `code` ``, fenced code blocks,
     `[links](url)`, `- ` bullets, `1. ` numbered lists, `> ` quotes,
     `---` rules. Inline HTML is escaped — write Markdown, not HTML.
3. Build and check locally:

   ```
   python3 tools/build.py
   ```

4. Commit and push. Done.

### Or: push only the .md and let GitHub build it

`.github/workflows/build.yml` runs `tools/build.py` on every push to
`main` and commits the generated `posts/` and `index.html` back, so
GitHub Pages (deploy from branch) serves fresh HTML. The bot's own
commit triggers a second run that finds nothing to change and stops —
no loop. If the action fails (bad front matter, bad date), nothing is
committed; fix the `.md` and push again.

### What the build does, exactly

- `md/<slug>.md` → `posts/<slug>.html`, wrapped in the full page
  template (theme toggle, nav, header, scripts), which lives
  inside `tools/build.py` as the `PAGE` constant. **If you ever
  redesign the post page layout, edit `PAGE` and rebuild.**
- The list in `index.html` between the `<!-- posts:start -->` and
  `<!-- posts:end -->` markers is regenerated from all non-draft
  entries, newest first. Everything outside the markers is untouched.
- Empty `.md` files are skipped with a note; missing or invalid front
  matter is a hard error naming the file.

### Publishing a draft

Set `draft: true` while writing. Remove the line (or set `false`) and
rebuild — the entry appears in the index in date order.

### Editing a published entry

Edit the `.md` file, rebuild, push. Never edit `posts/*.html` directly —
it will be overwritten by the next build.

### Removing an entry

Delete the `.md` file and the matching `posts/<slug>.html`, then push
(the action rebuilds the index without it). The build never deletes
generated pages on its own, on purpose: HTML shouldn't vanish silently.

> If you ever need a one-off hand-made page (say, a static CV), put it
> in `posts/` with no matching `.md` — the build leaves it alone.

### Editing the About section

The About text lives in `index.html` inside `<section class="about">`.
The contact email is the `mailto:` link there. Change both freely —
nothing else references them. (This part is not generated.)

### Editing the masthead

Site name and tagline are in `index.html` under
`<header class="masthead">` (`.site-title`, `.site-sub`). The tagline is
displayed in uppercase via CSS (`text-transform`), so write it in
normal case in the HTML. Post page titles come from the `PAGE` template
in `tools/build.py` (currently `{{TITLE}} — Saul Neri`).

### The theme toggle (do not break)

Every page has, in this order (and the post template in
`tools/build.py` already carries all three):

1. A tiny script in `<head>` that reads `localStorage["theme"]` and sets
   `data-theme="dark|light"` on `<html>` **before** the stylesheet loads
   (prevents a flash of the wrong theme).
2. The toggle `<button class="theme-toggle">` with an inline SVG
   (brush circle + hatched half) right after `<body>`.
3. A script before `</body>` that flips `data-theme` on click and
   persists it to `localStorage`.

Rules when editing pages:

- Keep all three pieces. If you add a hand-made page, copy them from
  any existing page.
- The SVG contains `<defs><pattern id="hatch">` and a
  `<filter id="f-tm">`. IDs must be unique per page; one instance per
  page is fine. Never put a second copy on the same page.
- The classes `tm-stroke`, `tm-hatch`, `tm-half-r`, `tm-half-l` are
  styled in `style.css`. Don't rename them.
- Deleting `localStorage` support is fine (the toggle still works per
  page view); deleting the `<head>` script is not — the theme will
  flash.

### Tuning the look

| Want to change | Where |
|---|---|
| Colors, light & dark | `:root` and `:root[data-theme="dark"]` blocks at the top of `style.css` |
| Font | `body { font: ... }` in `style.css` |
| Page width | `body { max-width: 38rem }` |
| Toggle size | `.theme-toggle { width / height }` |
| Hatch density / pressure / wobble (toggle) | The SVGs in each hand-made page **and in the `PAGE` template in `tools/build.py`** — both, or a rebuild will revert your change |
| Post page layout | `PAGE` constant in `tools/build.py`, then rebuild |
| Markdown element styles | `article h2/h3`, `article pre`, `article blockquote`, `article ul/ol`, `article hr` in `style.css` |

Remember: `posts/*.html` is generated. A cosmetic change made only
there is lost on the next build — change the template or `style.css`,
then rebuild.

### Local preview

```
python3 tools/build.py && python3 -m http.server 8000
```

then open <http://localhost:8000>.

### Deployment

GitHub Pages serves this repository from `main` (Settings → Pages →
Deploy from branch → main / root). The `build` workflow commits
generated pages before Pages picks them up. No other infrastructure
exists or is needed.

---

## The stylesheet, semantically

`style.css` is organized as: **tokens → elements → landmarks →
components → states**. Almost no utility classes; selectors describe
*what things are*, not what they should look like.

### 1. Design tokens (`:root`)

The entire palette is four custom properties:

| Token | Meaning | Light | Dark |
|---|---|---|---|
| `--ink` | text, borders, fills — everything "drawn" | `#1a1a1a` | `#e8e8e8` |
| `--paper` | background | `#fff` | `#161616` |
| `--faded` | secondary text (dates, tagline, footer) | `#6b6b6b` | `#9a9a9a` |
| `--rule` | hairlines, link underlines | `#d4d4d4` | `#3a3a3a` |

No other rule uses a raw color — everything reads `var(--ink)` etc.
Consequences:

- **Re-theming = editing four lines** (twice each for dark — see below).
- `::selection` and the focus ring invert automatically because they use
  the same tokens.
- Dark values are deliberately *not* a pure inversion: slightly softened
  (`#1a1a1a`/`#e8e8e8`, not `#000`/`#fff`) to avoid halation; the grays
  are tuned per theme to keep contrast above WCAG AA in both.

### 2. Dark mode: three-state resolution

Theme resolution, in order of precedence:

1. `:root[data-theme="dark"]` → dark tokens (explicit choice, from the
   toggle / `localStorage`)
2. `@media (prefers-color-scheme: dark) :root:not([data-theme="light"])`
   → dark tokens (system default, untouched)
3. base `:root` → light tokens

`data-theme="light"` wins even on a dark-OS device; no attribute means
"follow the system". The dark token block is duplicated across rules 1
and 2 on purpose — **when you change a dark color, change it in both
places.**

### 3. Typography scale

Deliberately small — four sizes:

- `body`: 17px serif (Iowan/Palatino/Georgia stack), 1.7 line height
- `article h1`: 1.75rem, weight normal
- `.site-title`: 1.375rem
- everything "meta" (tagline, dates, footer): 0.75–0.8125rem, uppercase
  or monospace

Dates use a monospace stack (`ui-monospace, SF Mono, Menlo`) at 0.75rem
with slight letter-spacing — a quiet machine-printed contrast to the
serif.

### 4. Layout model

No grid, no flex framework:

- `body`: `max-width: 38rem; margin: 0 auto` — one centered column
  (~70 characters per line, a good reading measure)
- `.post-list li`: the one flex row on the site (title left, date
  right), collapsing to a column under 30rem
- `.theme-toggle`: the only absolutely-positioned element (top-right)
- vertical rhythm: `rem` margins — `4.5rem` between major sections,
  `1.25rem` between paragraphs (`p + p`)

### 5. Components (the complete class inventory)

| Class | Role |
|---|---|
| `.masthead` | centered site header block |
| `.site-title` | name line |
| `.site-sub` | tagline (uppercased via CSS) |
| `.about` | landing about section spacing |
| `.post-list` | the `<ol>` of entries |
| `.date` | timestamp under a post title |
| `.theme-toggle` | the theme button |
| `.tm-*` | SVG parts of the toggle (stroke, hatch, halves) |

(`.writing` on the landing page is a semantic landmark with no CSS —
it exists for structure and a possible future hook.)

Everything else — `article`, `nav`, `footer`, `h2`, `a`, `time` — is
selected **by element/semantic role**, not class. Same HTML structure,
same look, zero new CSS.

### 5b. Markdown element styles

Generated posts can contain subheadings, code, quotes, lists and rules,
so `style.css` styles them under the `article` scope (they never leak
into the landing page):

- `article h2/h3` — quiet subheadings: ink color, normal case, no
  border (the label-style `h2` is reserved for section headers)
- `article pre` — monospace, hairline left border, horizontal scroll
- `article code` — monospace at 85% of text size
- `article blockquote` — faded, italic, hairline left border
- `article ul/ol/li` — indented lists with tight internal spacing
- `article hr` — a short (6rem) centered hairline, a pause not a slash

### 6. Links and focus

- Links inherit the text color (no blue) and underline in `--rule`
  gray, darkening to `--ink` on hover — visible but quiet.
- `:focus-visible` draws a 2px `--ink` outline on every interactive
  element. Never remove this.
- Underlines use `text-underline-offset` for comfortable scanning.

### 7. The theme-toggle SVG anatomy

The button's SVG, bottom to top:

1. `<pattern id="hatch">` — diagonal pencil lines (spacing `2.6`,
   pressure `0.95`), colored `currentColor` so they follow the theme.
2. `<filter id="f-tm">` — `feTurbulence` + `feDisplacementMap`
   (`scale 1.4`) that wobbles whatever it touches, making it look
   hand-drawn.
3. Two half-disc paths (`.tm-half-r`, `.tm-half-l`), hatched and
   filtered. CSS shows exactly one: right half in light theme, left
   half in dark — the "moon phase" flip.
4. The `.tm-stroke` ensō arc on top — an open circle that reads as a
   brush stroke.

State is driven purely by the same three-state theme resolution as the
colors; there is no toggle-specific JavaScript beyond setting
`data-theme`.

### 8. Accessibility checklist (already satisfied)

- Landmarks: `header`, `nav[aria-label]`, `main`, `article`, `footer`
- One `h1` per page; `h2`s introduce sections; no heading skips
- The post list is a real `<ol>` — screen readers announce "list, N items"
- `<time datetime>` on every date, in the list and in posts
- The toggle is a `<button>` with `aria-label` and live `aria-pressed`
- Visible focus ring on all interactive elements
- Contrast ≥ AA in both themes; no color used to convey state (the
  hatch flip also changes position)
- `prefers-color-scheme` respected by default
- No animation, no layout shift (the head script sets the theme before
  first paint)

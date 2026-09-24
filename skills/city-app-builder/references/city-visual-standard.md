# City Data Web Application Visual System

Use this document to create a City of Sacramento data application with a consistent civic look and feel. It is deliberately framework agnostic. Preserve the semantic structure, visual measurements, states, and behavior described here whether the implementation uses server-rendered templates, a component framework, a reactive notebook system, or plain HTML.

The shell is a contract. Page content can change with the subject matter, but the header, portal link, City signature and application title group, minimum navigation, and footer signature must remain recognizable and geometrically consistent.

## Included identity asset

Use the supplied white City signature on cobalt shell surfaces:

![City of Sacramento signature](../assets/starter/www/assets/city-of-sacramento-signature-white.png)

- File: `assets/city-of-sacramento-signature-white.png`
- Intrinsic size: 210 by 51 pixels
- SHA-256: `4880B4F0ED7B77881A6E98134E1361C89A318791A7C36445F35C6E593DC7C295`
- Alternative text: `City of Sacramento`
- Do not recreate the signature with text.
- Do not crop, recolor, distort, rotate, stretch, rearrange, or animate its internal elements.
- Preserve its aspect ratio and at least 16 pixels of practical clear space.
- Keep the application title outside the image. The City seal is not an application logo and is not a substitute.
- Confirm current City communications approval and asset permissions before public release. The asset is included here as a local implementation reference, not as a grant of publication rights.

## Non-negotiable application contract

Every application must provide all of the following:

1. A sticky cobalt header that is 64 pixels tall on desktop and 60 pixels tall below 768 pixels.
2. A left-aligned `Portal` link preceded by the exact diagonal up-left arrow glyph `↖` (`U+2196 NORTH WEST ARROW`). The glyph and its direction are required; do not substitute a left arrow, chevron, curved back arrow, custom SVG, or icon-library symbol.
3. A centered identity group containing the white City signature, a vertical divider, and the application title.
4. Right-aligned primary navigation on wide screens and a 40 by 40 pixel menu control on narrower screens.
5. At least two addressable destinations: `Home` and `About`.
6. The same destination list and active state in desktop and mobile navigation.
7. A full-width cobalt footer with the centered white City signature.
8. A single `main` landmark, a keyboard-visible skip link, visible focus states, and no horizontal page overflow.

`Portal` and the application home are different destinations. The portal link returns to the parent City portal. The centered identity group links to the data application's home.

## Two supported adoption modes

This visual system supports both of these workflows:

### New application

Build the shell and page primitives together, then compose Home, About, and any additional data views from the components in this guide.

### Existing-application retrofit

Keep the existing application's body structure, content, data logic, state, controls, charts, tables, and user workflows intact. Replace or restyle only the header and footer, then apply an approved color and typography theme to the body.

The retrofit is successful when the application gains the shared City identity without being redesigned internally.

## Existing-application visual retrofit

### Protected body boundary

Treat everything between the existing header and footer as a protected functional region. Do not reorganize it merely to make the new shell easier to implement.

The following body characteristics are protected unless the user explicitly expands the scope:

- Page and component order.
- Existing routes, tabs, views, and deep links.
- Data loading, transformation, filtering, sorting, and export behavior.
- Form fields, control labels, defaults, validation, and selection state.
- Chart types, table columns, calculations, annotations, and interactions.
- Card, grid, panel, sidebar, modal, and drawer structure.
- Content wording, headings, imagery, and explanatory sections.
- Existing spacing, sizing, and responsive layout rules.
- Stable element identifiers, test hooks, analytics hooks, and accessibility relationships.

The body may receive these visual changes:

- Body and heading font families.
- Text, heading, link, border, background, panel, and focus colors.
- Font rendering features and tabular numerals.
- Theme variables consumed by existing components.
- Chart colors when semantic meaning, contrast, and series identity are preserved.
- A small compatibility rule needed to prevent the new header or footer from overlapping the body.

Changing a font can change wrapping and element height. A font-only change must not be treated as risk free. Verify long labels, fixed-height controls, card titles, tables, chart annotations, and narrow viewports after the change.

### Allowed-change matrix

| Surface | Allowed by default | Protected by default |
| --- | --- | --- |
| Header | Replace markup, styles, identity, navigation presentation, active state, mobile menu, and sticky behavior | Existing route destinations and route semantics |
| Footer | Replace markup, styles, identity, source/about links, and metadata presentation | Required legal, source, accessibility, privacy, and ownership content |
| Body typography | Change global font tokens and text colors | Wording, hierarchy, component order, and text content |
| Body palette | Remap theme variables and compatible chart colors | Data meaning, warnings, selection meaning, contrast, and non-color cues |
| Body layout | Add only a shell-offset or overflow compatibility fix | Grids, cards, widths, spacing, order, and responsive composition |
| Body behavior | None unless required to connect existing routes to the new navigation | Filtering, data state, forms, charts, tables, modals, and exports |

### Retrofit architecture

Use a shell adapter around the existing body:

```html
<div class="city-app-shell">
  <!-- New shared header -->
  <header class="city-header">...</header>

  <!-- Existing application body, unchanged -->
  <main id="main" class="existing-app-body">...</main>

  <!-- New shared footer -->
  <footer class="city-footer">...</footer>
</div>
```

If the existing application already owns the single `main` landmark, keep it. Do not wrap it in a second `main`. If the framework controls the root layout, mount the header before its existing content outlet and the footer after it without moving the outlet's children.

Prefer these integration patterns, in order:

1. Replace the existing shell component while leaving its body slot or route outlet untouched.
2. Provide a layout wrapper that receives the existing body as an opaque child.
3. Inject header and footer through framework-supported layout regions.
4. As a last resort, add sibling shell elements around the existing root without reparenting interactive body nodes after startup.

Do not copy the existing body into a new template by hand. That approach commonly drops event bindings, reactive state, generated identifiers, focus restoration, or framework ownership.

### Navigation mapping

Create one navigation model from the application's existing routes. Render both desktop and mobile links from that model.

```text
existing route or view ID -> displayed label -> destination URL -> active-state test
```

Rules:

- Preserve every existing destination that remains in scope.
- Add or identify a Home destination.
- Add or identify an About destination. An existing source, methods, help, documentation, or project-information view may serve as About if it fulfills the trust and interpretation role.
- Do not rename a destination when the label has domain or user-workflow meaning unless the user requests it.
- Preserve query parameters, hash state, bookmarks, browser Back and Forward behavior, and deep links.
- Apply `aria-current="page"` from the actual router or view state, not from click styling alone.
- Map the centered City identity group to the existing application home.
- Map `Portal` to the parent City portal, never to an internal application route.

If the application has no About-equivalent destination, adding one is the only default body-content exception because it is part of the shared shell contract. Keep that new destination isolated and do not restructure existing views.

### CSS isolation

Scope shell rules to the shell classes in this guide. Avoid broad descendant selectors that can leak into existing components.

Good:

```css
.city-header .city-nav__link { ... }
.city-footer .city-footer__source { ... }
.existing-app-body { color: var(--app-body-ink); }
```

Avoid:

```css
header a { ... }
footer p { ... }
.city-app-shell button { ... }
.city-app-shell nav a { ... }
```

Do not keep an old header hidden underneath the new header. Remove or disable the old shell at its owning component. Two mounted shells create duplicate landmarks, duplicate navigation, focus problems, and unpredictable sticky offsets.

Update existing owning CSS rules or theme variables when practical. Do not append a long chain of increasingly specific overrides. After the retrofit, there should be one clear owner for header rules, one for footer rules, and one for body theme tokens.

### Body theme adapter

Keep shell identity tokens separate from body theme tokens. This lets a subject-specific application use a compatible body palette without changing the non-negotiable cobalt shell.

```css
:root {
  /* Fixed shell */
  --city-identity-cobalt: #2a3b66;

  /* Body theme adapter */
  --app-body-bg: #ffffff;
  --app-body-ink: #0f172a;
  --app-body-muted: #64748b;
  --app-body-heading: #003c71;
  --app-body-link: #003c71;
  --app-body-accent: #0072ce;
  --app-body-border: #e2e6ed;
  --app-body-panel: #f4f6fa;
  --app-body-font: Inter, ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  --app-heading-font: "Josefin Sans", "Century Gothic", Futura, system-ui, sans-serif;
}

.existing-app-body {
  background: var(--app-body-bg);
  color: var(--app-body-ink);
  font-family: var(--app-body-font);
}
.existing-app-body :is(h1, h2, h3, h4, h5, h6) {
  color: var(--app-body-heading);
  font-family: var(--app-heading-font);
}
.existing-app-body a { color: var(--app-body-link); }
```

Map existing framework variables to these values instead of restyling every generated element. For example, change a framework's primary, body, heading, border, and focus tokens at the theme layer. Keep component-specific overrides only when the framework has no suitable token.

When recoloring charts:

- Preserve the mapping between series and colors across views.
- Preserve positive, negative, warning, selected, and disabled meaning.
- Retain labels, patterns, icons, or text so meaning is not color-only.
- Recheck contrast against the new panel and page backgrounds.
- Do not change calculations, scales, bins, sort order, or annotations.

### Header and footer replacement sequence

1. Capture before screenshots at 1440, 800, and 390 pixels wide.
2. Record existing routes, active-state logic, header height, sticky offsets, footer links, and body top/bottom spacing.
3. Identify the component or template that owns the existing shell.
4. Extract the existing navigation destinations into one shared model without changing the destinations.
5. Replace the header with the City shell and connect it to the existing router or view state.
6. Replace the footer while preserving required site-specific information and links.
7. Add the body theme adapter for allowed color and typography changes.
8. Remove obsolete shell CSS and behavior after confirming nothing in the body depends on it.
9. Verify the body before and after using the same route, filters, data state, and viewport.
10. Capture after screenshots and compare body geometry as well as shell geometry.

### Retrofit acceptance checks

- The body starts at the same logical content point and has not been reordered.
- Existing filters, charts, tables, forms, exports, drawers, and modals behave exactly as before.
- Existing deep links, bookmarks, Back and Forward behavior, and query state still work.
- Body screenshots show only intended color, font, and unavoidable text-wrap differences.
- No duplicate header, footer, navigation, `main`, or content-information landmarks exist.
- Sticky body elements use the correct offset for the 64px desktop and 60px mobile header.
- In-page anchors are not hidden behind the sticky header.
- New font metrics do not clip controls, chart labels, table cells, or fixed-height content.
- The footer follows the body normally and does not cover loading states or short pages.
- Application tests and browser console remain clean.

## Visual tokens

Treat these values as the common design vocabulary. Expose equivalent variables or theme tokens in the chosen framework.

```css
:root {
  color-scheme: light;

  /* Shell identity */
  --city-identity-cobalt: #2a3b66;

  /* Application palette */
  --city-cobalt: #003c71;
  --city-sky: #0072ce;
  --city-gold: #c99a3b;
  --city-green: #4a7c2a;
  --city-ink: #0f172a;
  --city-muted: #64748b;
  --city-line: #e2e6ed;
  --city-alt: #f4f6fa;
  --city-panel: #eaeff5;
  --city-white: #ffffff;

  /* Measures */
  --measure-narrative: 48rem;
  --measure-standard: 64rem;
  --measure-wide: 70rem;
  --measure-analysis: 90rem;
  --measure-shell: 120rem;

  /* Spacing */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-5: 24px;
  --space-6: 32px;
  --space-7: 48px;
  --space-8: 64px;

  /* Shape and motion */
  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 14px;
  --shadow-soft: 0 10px 24px rgb(15 23 42 / 0.07);
  --transition: 160ms ease;

  /* Type */
  --font-heading: "Josefin Sans", "Century Gothic", Futura, system-ui, sans-serif;
  --font-body: Inter, ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  --font-editorial: Georgia, "Times New Roman", serif;
}
```

The shell cobalt is the official identity anchor. The brighter blue, gold, green, neutral ink, panels, and borders belong to the application layer. Use them for hierarchy and data meaning, not as replacements for the official identity color.

## Typography

Use a restrained three-voice system:

| Role | Family | Typical specification |
| --- | --- | --- |
| Body, controls, tables, navigation title | Inter | 16px body, 1.6 line-height |
| Headings, labels, portal link, compact display values | Josefin Sans | weight 600, 1.1 to 1.3 line-height |
| Optional editorial opening headline | Georgia | weight 400, approximately 48 to 54px on wide screens |

Base rules:

```css
*, *::before, *::after { box-sizing: border-box; }
html { background: #fff; color: var(--city-ink); scroll-behavior: smooth; }
body {
  margin: 0;
  overflow-x: hidden;
  background: #fff;
  font-family: var(--font-body);
  font-size: 16px;
  font-feature-settings: "ss01", "cv11";
  line-height: 1.6;
}
h1, h2, h3, h4, h5, h6 {
  margin: 0;
  color: var(--city-cobalt);
  font-family: var(--font-heading);
  letter-spacing: -0.01em;
  line-height: 1.15;
}
p { margin: 0; }
button, input, select, textarea { font: inherit; }
.tabular { font-variant-numeric: tabular-nums; }
```

Recommended scale:

- Page title: `clamp(2rem, 4vw, 3rem)`.
- Section title: `clamp(1.5rem, 3vw, 2.25rem)`.
- Page lede: 17.28px with a 1.65 line-height and a maximum width of 46rem.
- Eyebrow: 11.2px Josefin Sans, weight 600, uppercase, `0.23em` letter spacing, sky blue.
- Card heading: approximately 17.6px.
- Compact uppercase label: 11.2px, weight 600, `0.14em` to `0.16em` letter spacing.
- Supporting copy: 12.8px to 14px in muted ink.
- Large numeric value: 24px to 36px, weight 600, with tabular numerals.

Do not scale compact control or card text directly with viewport width. Keep labels and values stable so they do not collide or escape their containers.

## Header and navigation

### Geometry

The reliable centering pattern is a three-column grid:

```text
| minmax(0, 1fr): Portal | auto: City signature + title | minmax(0, 1fr): navigation |
```

This keeps the identity group at the true viewport center even when the left and right content have different widths.

| Property | Desktop | Mobile below 768px |
| --- | --- | --- |
| Header height | 64px | 60px |
| Shared vertical axis | 32px from top | 30px from top |
| Shell maximum width | 120rem | full width |
| Horizontal gutter | 24px | 12px |
| City signature width | 110px | 84px |
| Signature vertical correction | `translateY(-3.7px)` | `translateY(-2.8px)` |
| Divider | 1 by 24px | 1 by 18px |
| Identity group gap | 16px | 12px |
| Application title | 13.6px, 600 | 9.92px, 600 |
| Portal label | 11.2px, 600 | 8px, 600 |
| Menu control | not shown at 1280px and wider | 40 by 40px |

The full desktop navigation is shown at 1280 pixels and wider. Below 1280 pixels, replace it with the menu control. Do not squeeze all links into a tablet header.

### Portal arrow

Render the Portal arrow as the literal text character `↖` (`U+2196 NORTH WEST ARROW`) immediately before the `Portal` label. This is a normative identity detail, not an illustrative icon choice.

- Use the exact `↖` character as a text node. Font rendering may vary slightly by platform, but the Unicode code point, diagonal up-left direction, and basic arrow shape must remain unchanged.
- Do not replace it with `←`, `<`, `‹`, a left-pointing chevron, a curved undo or back arrow, an emoji-style arrow, a custom SVG path, or an icon-library component.
- Keep the arrow inside the Portal link, set `aria-hidden="true"` on its wrapper, and give the link the accessible label `Return to portal`.
- Render it at `16px` with a `1` line-height as shown in the reference styling. Do not rotate, mirror, outline, or animate it.

### Semantic structure

Use this DOM topology or its exact semantic equivalent. Generate desktop and mobile links from one shared destination list.

```html
<header class="city-header">
  <a class="skip-link" href="#main">Skip to content</a>

  <div class="city-header__inner">
    <a class="portal-link" href="PORTAL_URL" aria-label="Return to portal">
      <span class="portal-link__icon" aria-hidden="true">↖</span>
      <span class="portal-link__label">Portal</span>
    </a>

    <a class="city-brand-link" href="HOME_URL" aria-label="City of Sacramento APPLICATION_TITLE home">
      <img
        class="city-brand-logo"
        src="assets/city-of-sacramento-signature-white.png"
        width="210"
        height="51"
        alt="City of Sacramento"
      >
      <span class="city-brand-separator" aria-hidden="true"></span>
      <span class="city-app-identity">APPLICATION_TITLE</span>
    </a>

    <nav class="city-nav" aria-label="Application sections">
      <a class="city-nav__link is-active" href="HOME_URL" aria-current="page">Home</a>
      <a class="city-nav__link" href="ABOUT_URL">About</a>
    </nav>

    <details class="city-mobile-nav__details">
      <summary class="city-mobile-nav__summary">
        <span aria-hidden="true">☰</span>
        <span class="sr-only">Open page menu</span>
      </summary>
      <nav class="city-mobile-nav" aria-label="Application sections">
        <a class="city-mobile-nav__link is-active" href="HOME_URL" aria-current="page">Home</a>
        <a class="city-mobile-nav__link" href="ABOUT_URL">About</a>
      </nav>
    </details>
  </div>
</header>
```

### Reference styling

```css
.city-header {
  position: sticky;
  top: 0;
  z-index: 40;
  height: 64px;
  border-bottom: 1px solid rgb(255 255 255 / 0.16);
  background: var(--city-identity-cobalt);
  opacity: 1;
  transform: translateY(0);
  transition: opacity 160ms ease, transform 180ms ease;
}
.city-header.is-scroll-hidden {
  opacity: 0;
  pointer-events: none;
  transform: translateY(calc(-100% - 1px));
}
.city-header__inner {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr);
  align-items: center;
  width: 100%;
  max-width: var(--measure-shell);
  height: 64px;
  margin: 0 auto;
  padding-inline: 24px;
}
.portal-link {
  display: inline-flex;
  grid-column: 1;
  align-items: center;
  align-self: center;
  justify-self: start;
  gap: 7.2px;
  min-width: max-content;
  padding: 4px 3.2px;
  color: #fff;
  font: 600 11.2px/1 var(--font-heading);
  letter-spacing: 0.16em;
  text-decoration: none;
  text-transform: uppercase;
  white-space: nowrap;
}
.portal-link:hover { color: var(--city-gold); }
.portal-link__icon { font-size: 16px; line-height: 1; }

.city-brand-link {
  display: flex;
  grid-column: 2;
  align-items: center;
  align-self: center;
  justify-self: center;
  gap: 16px;
  color: #fff;
  text-decoration: none;
}
.city-brand-logo {
  display: block;
  width: 110px;
  height: auto;
  object-fit: contain;
  transform: translateY(-3.7px);
}
.city-brand-separator {
  flex: 0 0 1px;
  width: 1px;
  height: 24px;
  background: rgb(255 255 255 / 0.48);
}
.city-app-identity {
  color: #fff;
  font: 600 13.6px/1 var(--font-body);
  white-space: nowrap;
}

.city-nav {
  display: flex;
  grid-column: 3;
  align-items: center;
  align-self: center;
  justify-self: end;
  gap: 14.4px;
}
.city-nav__link {
  color: rgb(255 255 255 / 0.84);
  font-size: 12.32px;
  font-weight: 500;
  line-height: 1.6;
  text-decoration: none;
  white-space: nowrap;
}
.city-nav__link:hover,
.city-nav__link.is-active { color: #fff; }
.city-nav__link.is-active { font-weight: 700; }

.city-mobile-nav__details {
  position: relative;
  display: none;
  grid-column: 3;
  align-self: center;
  justify-self: end;
}
.city-mobile-nav__summary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border: 1px solid rgb(255 255 255 / 0.42);
  border-radius: 6px;
  color: #fff;
  cursor: pointer;
  list-style: none;
  font-size: 18.4px;
}
.city-mobile-nav__summary::-webkit-details-marker { display: none; }
.city-mobile-nav {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  display: grid;
  width: 224px;
  padding: 8px;
  border: 1px solid var(--city-line);
  border-radius: 8px;
  background: #fff;
  box-shadow: var(--shadow-soft);
}
.city-mobile-nav__link {
  padding: 10px 12px;
  border-radius: 6px;
  color: var(--city-ink);
  font-size: 14px;
  text-decoration: none;
}
.city-mobile-nav__link:hover,
.city-mobile-nav__link.is-active {
  background: var(--city-alt);
  color: var(--city-cobalt);
}
.city-mobile-nav__link.is-active { font-weight: 700; }

@media (max-width: 1279px) {
  .city-nav { display: none; }
  .city-mobile-nav__details { display: block; }
}
@media (max-width: 767px) {
  .city-header,
  .city-header__inner { height: 60px; }
  .city-header__inner { padding-inline: 12px; }
  .city-brand-link { gap: 12px; }
  .city-brand-logo { width: 84px; transform: translateY(-2.8px); }
  .city-brand-separator { height: 18px; }
  .city-app-identity { font-size: 9.92px; }
  .portal-link { gap: 4px; font-size: 8px; letter-spacing: 0.08em; }
}
```

### Navigation behavior

- Keep `Home` and `About` visible as first-class destinations. More destinations may be inserted between them or grouped under `Resources`, but do not omit either.
- Use real routes or stable hash destinations. The technique is framework-specific; the addressability, history behavior, and active state are not.
- Set `aria-current="page"` on exactly one desktop link and its mobile equivalent.
- Close the mobile menu after a destination is selected.
- The menu must be operable with keyboard and touch. Keep its summary or button at least 40 by 40 pixels.
- Keep link labels, order, targets, and active state identical across desktop and mobile.
- Never use the City signature as the portal link. The signature plus application title returns home.

### Directional sticky behavior

The header begins visible. It fades and slides away while scrolling down, then returns when any of these conditions is true:

- The page is within 16 pixels of the top.
- The user scrolls upward.
- Focus is inside the header.
- A header `details` menu is open.

Hide only after the page is more than 96 pixels from the top and the current scroll delta is positive. Schedule updates with `requestAnimationFrame`. Remove the motion for users who prefer reduced motion.

## Page destinations

### Home

The home destination should answer four questions without requiring an initial click:

1. What is this dataset or service about?
2. How fresh and complete is it?
3. What are the most important current values or patterns?
4. How can the user inspect or verify the underlying information?

Recommended order:

1. Source or freshness status and utility actions.
2. Page eyebrow, clear H1, and concise lede.
3. Primary documentary image or restrained civic illustration when appropriate.
4. Filters and active-filter chips.
5. Two to four key values.
6. A primary chart with exact-data disclosure and a source line.
7. Supporting comparisons, ranked changes, or category summaries.
8. Links to related views and the About destination.

The opening can use a two-column editorial and analytical stage at wide widths. Keep the page inside a 120rem maximum canvas with at least 24px outside gutters and approximately 40px of interior inset for a major tinted analytical region.

### About

The About destination is a trust and interpretation surface, not marketing filler. Include the items that apply to the site:

- What the source is and who maintains it.
- Last successful update, refresh policy, time coverage, and record coverage.
- Definitions for transformed or derived fields.
- Data validation and reconciliation checks.
- A field dictionary or compact data contract.
- Known gaps, exclusions, and interpretation limits.
- Accessibility, contact, or ownership information.
- Methodology and download links when available.

A useful layout is a page intro followed by a status callout, four compact metadata cards, two-column source and validation panels, a horizontally scrollable field dictionary, and a final limitations callout.

## Layout system

Use one shared container primitive with named measures:

```css
.city-container {
  width: 100%;
  min-width: 0;
  margin: 0 auto;
  padding-inline: 24px;
}
.city-container--narrow { max-width: var(--measure-narrative); }
.city-container--standard { max-width: var(--measure-standard); }
.city-container--wide { max-width: var(--measure-wide); }
.city-container--analysis { max-width: var(--measure-analysis); }
.city-container--shell { max-width: var(--measure-shell); }

.city-page-flow {
  display: grid;
  min-width: 0;
  gap: 32px;
}
.city-section {
  min-width: 0;
  padding-block: 32px;
  scroll-margin-top: 96px;
}
.city-grid { display: grid; gap: 20px; }
.city-grid--2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.city-grid--3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.city-grid--4 { grid-template-columns: repeat(4, minmax(0, 1fr)); }

@media (max-width: 1023px) {
  .city-grid--4 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 767px) {
  .city-container { padding-inline: 16px; }
  .city-grid--2,
  .city-grid--3 { grid-template-columns: 1fr; }
  .city-section { padding-block: 24px; }
}
@media (max-width: 389px) {
  .city-container { padding-inline: 12px; }
  .city-grid--4 { grid-template-columns: 1fr; }
}
```

Always use `minmax(0, 1fr)` for equal grid tracks and `min-width: 0` on grid or flex children. This prevents long values, controls, charts, and generated framework wrappers from forcing horizontal overflow.

## Component patterns

### Page intro

- Eyebrow above the H1.
- H1 in City cobalt.
- Lede in `#334155`, no wider than 46rem.
- Default page-intro padding: 32px above and 24px below.
- Use the optional Georgia voice only for a major editorial opening, not for every heading.

### Utility toolbar

- Place freshness or source status on the left and actions on the right.
- Use 13px supporting text and a small status icon.
- Allow actions to wrap.
- On mobile, stack the status, actions, and explanation vertically.
- Do not let the toolbar become a second navigation system.

### Filters

- Group related controls on a light alternate surface.
- Use 16px padding, 24px gap, 1px border, and an 8px radius.
- Labels are compact uppercase Josefin Sans in City cobalt.
- Inputs are at least 38px high with a white surface, 1px border, and 6px radius.
- Show active selections as readable chips and provide a clear reset action.
- Put interpretation notes next to the controls when the meaning of values could be misunderstood.

### Buttons

- Primary: City cobalt background, white label, 1px cobalt border, 6px radius, at least 38px high.
- Primary hover: `#002c53`.
- Secondary: white background, City cobalt text, neutral border.
- Disabled: opacity near 0.56 and a not-allowed cursor.
- Focus: a visible 2px sky-blue outline with 3px offset. Interactive cards may use a 3px translucent sky ring.

### KPI or metadata card

```css
.city-stat-card {
  min-width: 0;
  padding: 20px;
  border: 1px solid var(--city-line);
  border-left: 4px solid var(--city-sky);
  border-radius: 10px;
  background: var(--city-panel);
}
.city-stat-card__label {
  color: var(--city-muted);
  font: 600 11.2px/1.3 var(--font-heading);
  letter-spacing: 0.16em;
  text-transform: uppercase;
}
.city-stat-card__value {
  margin-top: 6.4px;
  color: var(--city-cobalt);
  font: 600 clamp(24.8px, 3vw, 36px)/1.1 var(--font-heading);
}
.city-stat-card__detail {
  margin-top: 8.8px;
  color: var(--city-muted);
  font-size: 12.8px;
}
```

Use the left border as a restrained category accent. Sky, gold, green, and cobalt are acceptable, but always pair color with a label or state.

### Card and analytical surface

- Basic surface: white, 1px neutral border, 8px radius.
- Repeated card: 20px to 24px padding and 10px radius.
- Major workspace: alternate background, 1px border, 14px radius, 24px padding.
- Elevated surfaces use the soft shadow only when hierarchy requires it.
- Interactive hover may lift by 1px with `0 8px 20px rgb(15 23 42 / 0.08)`.
- Avoid nested decorative cards. Prefer spacing, rules, and subtle background changes.

### Charts

- Give chart frames stable dimensions to prevent layout shift.
- Put the chart title above the visualization in compact uppercase type.
- Keep the palette small and meaningful.
- Include a short plain-language summary directly below the chart.
- Provide an exact-data table, disclosure, or download path.
- End with a visible source line in muted uppercase text.
- Never rely on hover alone for essential values.

### Tables

- Put wide tables in a container with `overflow-x: auto` rather than allowing page overflow.
- Use a minimum table width near 36rem when the columns need it.
- Keep headers sticky where useful.
- Use 10px by 12px cell padding and neutral row rules.
- Style headers in City cobalt, Josefin Sans, uppercase, with modest positive tracking.
- Provide a caption that explains the table's role.

### Callouts and states

- Standard callout: 16px by 20px padding with a 4px left rule.
- Use gold for caution or interpretation notes and sky for explanatory or exploratory notes.
- Loading, empty, stale, and error states must reserve stable space and explain what the user can do next.
- If a successful prior snapshot remains available during refresh, show it instead of replacing the whole page with a spinner.

## Footer

The full-width cobalt footer and centered City signature are non-negotiable. The explanatory content below the signature should be adapted to the site.

Recommended semantic structure:

```html
<footer class="city-footer">
  <div class="city-container city-container--wide city-footer__inner">
    <div class="city-footer__logo-panel">
      <img
        class="city-footer-logo"
        src="assets/city-of-sacramento-signature-white.png"
        width="210"
        height="51"
        alt="City of Sacramento"
      >
    </div>

    <p class="city-footer__source">
      SITE-SPECIFIC SOURCE, OWNERSHIP, OR PURPOSE STATEMENT.
      <a href="ABOUT_URL">Read the methodology and limitations</a>.
    </p>

    <div class="city-footer__meta">
      <span>DATA OR CONTENT SNAPSHOT · DATE</span>
      <span>REFRESH OR REVIEW CADENCE</span>
    </div>
  </div>
</footer>
```

```css
.city-footer {
  background: var(--city-identity-cobalt);
  color: #fff;
}
.city-footer__inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 32px;
  padding-block: 64px;
  text-align: center;
}
.city-footer__logo-panel {
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.city-footer-logo {
  display: block;
  width: 210px;
  height: auto;
}
.city-footer__source {
  max-width: 42rem;
  color: rgb(255 255 255 / 0.85);
  font-size: 14px;
  line-height: 1.65;
}
.city-footer__source a {
  color: #fff;
  text-decoration-color: var(--city-gold);
  text-decoration-thickness: 2px;
  text-underline-offset: 4px;
}
.city-footer__source a:hover { color: var(--city-gold); }
.city-footer__meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
  color: rgb(255 255 255 / 0.60);
  font: 12px/1.3 var(--font-body);
  letter-spacing: 0.2em;
  text-transform: uppercase;
}
@media (max-width: 767px) {
  .city-footer__inner { padding-block: 48px; }
  .city-footer-logo { width: 184px; }
}
```

Good footer content is short and verifiable. Prefer a source or ownership statement, a link to About or methodology, a snapshot or review date, and a refresh or review cadence. Contact, privacy, accessibility, and licensing links may be added when required.

## Accessibility contract

### Legal baseline for City of Sacramento applications

This contract states the minimum delivery baseline for City web applications. It is implementation guidance, not a legal opinion or a declaration that an application is compliant.

- Title II of the Americans with Disabilities Act applies to the services, programs, and activities that state and local governments provide through websites and mobile applications. It also covers content and applications supplied through contractors, vendors, licensing, or other arrangements.
- The required federal technical standard is [WCAG 2.1 Level A and Level AA](https://www.w3.org/TR/WCAG21/). Treat every applicable Level A and AA success criterion as a release requirement, not merely a design recommendation.
- Under the Department of Justice's April 2026 interim extension, the compliance date for a public entity with a population of 50,000 or more, including the City of Sacramento, is **April 26, 2027**. The extension does not suspend the City's existing Title II duties to provide effective communication, reasonable modifications, and equal opportunity before that date. See the [DOJ Title II web and mobile application compliance guide](https://www.ada.gov/resources/small-entity-compliance-guide/).
- Regulatory exceptions are narrow and must not be assumed during design or development. Archived material, some preexisting documents, qualifying third-party posts, individualized password-protected documents, and preexisting social-media posts may be treated differently only when the rule's specific conditions are satisfied. Even when an exception applies, the City may still need to provide effective communication in an accessible format upon request.
- A vendor product, embedded service, dashboard, document viewer, map, chart library, or other third-party component is not exempt merely because the City did not build it. Procurement and project contracts must assign accessibility testing, defect correction, complaint response, and ongoing maintenance responsibilities.
- California Government Code sections [11135](https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=GOV&sectionNum=11135.) and [7405](https://leginfo.legislature.ca.gov/faces/codes_displaySection.xhtml?lawCode=GOV&sectionNum=7405) may add requirements when a program or activity is conducted by the State, receives State financial assistance, uses State funds for electronic or information technology, or falls within a covered contract. Confirm applicability with the City Attorney or designated ADA authority rather than assuming these provisions apply to every municipal application.
- The City's current [web accessibility policy](https://www.cityofsacramento.gov/city-government/web-policies) uses universal-design principles. The City's web-governance policy also calls for Section 508 accessibility, accessibility-problem reporting, and review of department or vendor-developed web applications. A City application must provide a discoverable way to report an accessibility barrier and request assistance.

### Required product behavior

- Keep exactly one `main` landmark with `id="main"`.
- Place the skip link first in the header. It remains offscreen until focused.
- Give desktop and mobile navigation distinct, useful `aria-label` values.
- Use `aria-current="page"` for the active destination.
- Keep logo alternative text concise. Decorative images use empty alternative text.
- Preserve complete keyboard operation for links, menus, disclosures, filters, tables, dialogs, downloads, and every interaction exposed through a chart or map. Do not add a focusable chart container that has no keyboard action.
- Give each data visualization an accessible name and concise description. Provide the same data and material actions through an accessible table or an equivalent keyboard-operable interface; do not rely on the chart's visual marks alone.
- Use a focus indicator at least 2px thick with a 3px offset. Its color must have at least 3:1 contrast against adjacent colors in every location; use a separate high-contrast token on the cobalt header when `#0072ce` does not meet that threshold.
- Do not use color alone for active, selected, warning, increase, decrease, or validation states.
- Maintain at least 4.5:1 contrast for normal text, 3:1 for qualifying large text, and 3:1 for meaningful graphical objects, control boundaries, and component states.
- Do not clip text at 200% text zoom or require two-dimensional page scrolling at 400% browser zoom. Allow wrapping in labels, values, breadcrumbs, titles, tables, and status messages.
- Associate every form control with a programmatic name, instructions, and accessible error feedback. Preserve entered values when validation fails.
- Announce important asynchronous loading, success, stale-data, empty, and error states without moving focus. Keep live regions targeted so routine reactive updates do not cause large tables or option lists to be announced repeatedly.
- Use native HTML semantics before ARIA. Dialogs must have an accessible name, contain focus while open, close with `Escape`, and return focus to the control that opened them.
- Provide text alternatives for informative images and accessible equivalents for downloadable documents, audio, and video. Decorative media must be hidden from assistive technology.
- Respect `prefers-reduced-motion` and disable smooth scrolling, transitions, and decorative animation.
- Provide an accessibility contact or issue-reporting path in the application shell or a clearly linked City page. Do not make that reporting path depend on the inaccessible feature being reported.

```css
button, a, summary, input, select, textarea { outline-offset: 3px; }
:where(button, a, summary, input, select, textarea):focus-visible {
  outline: 2px solid var(--focus-color, var(--city-sky));
  outline-offset: 3px;
}
.city-header {
  --focus-color: #fff;
}
.skip-link {
  position: absolute;
  top: -48px;
  left: 16px;
  z-index: 60;
  padding: 8px 16px;
  border-radius: 6px;
  background: var(--city-cobalt);
  color: #fff;
  text-decoration: none;
}
.skip-link:focus { top: 16px; }
@media (prefers-reduced-motion: reduce) {
  html { scroll-behavior: auto; }
  *, *::before, *::after {
    animation-duration: 0.001ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.001ms !important;
  }
}
```

### Accessibility acceptance gate

Before release, test the rendered application rather than relying on source review alone:

1. Run an automated WCAG scan on every route and representative application state. Automated results are a starting point, not proof of conformance.
2. Complete every task using only the keyboard, including filters, tables, chart-equivalent actions, dialogs, downloads, validation recovery, and navigation.
3. Check text, focus indicators, controls, status colors, and visualization marks with a contrast-measurement tool.
4. Verify reflow at 320 CSS pixels, 200% text zoom, and 400% browser zoom without loss of information or operation.
5. Test with at least one desktop screen reader in a supported browser. For City Windows environments, include NVDA with Chrome or Edge; add JAWS testing when it is part of the supported environment.
6. Verify reduced motion, high-contrast or forced-colors behavior, loading and error states, stale data, empty results, long labels, and unusually large or negative values.
7. Record the test date, routes and states covered, tools and assistive technologies used, defects found, remediation owner, and retest result.

Do not label an application "ADA compliant" solely because an automated scanner reports no errors. A release passes this contract only when no known WCAG 2.1 Level A or AA blocker remains, equivalent access has been verified for the application's material information and actions, and any claimed exception has written review and approval from the appropriate City legal or ADA authority.

## New-application implementation sequence

1. Define the route or view model. Include `Home` and `About` before building page content.
2. Build the semantic shell with skip link, portal link, centered identity group, desktop navigation, mobile navigation, one main landmark, and footer.
3. Load the official signature from this folder. Do not redraw it.
4. Establish tokens and font fallbacks. Obtain fonts through a lawful project-approved source.
5. Implement the header geometry before adding analytical modules.
6. Generate desktop and mobile links from one navigation data structure.
7. Implement active state, history behavior, menu closing, and directional sticky behavior.
8. Add the shared container, page-flow, grid, surface, control, state, chart, and table primitives.
9. Compose Home for immediate comprehension and About for trust and interpretation.
10. Add the footer statement, About link, date, and cadence appropriate to the site.
11. Verify real data states: loading, success, stale, empty, error, very long labels, and unusually large or negative values.
12. Run visual, responsive, keyboard, contrast, and overflow checks before handoff.

## Visual QA matrix

Inspect the rendered application in Chromium or Edge at these widths. A source-code review is not a substitute for a rendered check.

| Viewport | Required checks |
| --- | --- |
| 2048px wide | Shell and major analytical canvas use space without touching edges; identity remains truly centered |
| 1440px wide | Full desktop navigation fits; portal, identity, and nav centers are at y = 32px |
| 800px wide | Desktop links are replaced by the menu; identity remains centered; no overlap or overflow |
| 390px wide | Header is 60px; signature is 84px; title and Portal remain readable; menu panel fits |
| 320 to 374px wide | No horizontal overflow; labels wrap or compress without hiding the required identity elements |

For each width, verify:

- Header background is `#2A3B66`.
- Portal is the first visible item and aligns to the left grid edge.
- Portal is preceded by the literal diagonal up-left arrow `↖` (`U+2196`), not a left arrow, chevron, curved arrow, SVG, or icon-library substitute.
- City signature is neither distorted nor recreated.
- Divider and application title form one centered identity group.
- Navigation or menu aligns to the right grid edge.
- Exactly one navigation destination is active.
- Home and About are both reachable with keyboard and pointer.
- Mobile navigation opens, stays within the viewport, and closes after selection.
- Downward scrolling hides the header; upward scrolling, focus, or an open menu reveals it.
- Main content has no horizontal page overflow.
- Controls, charts, cards, tables, and footer text do not clip.
- Footer signature is 210px wide on desktop and 184px on mobile.
- Focus indicators are visible against white and cobalt surfaces.
- Reduced-motion mode removes nonessential motion.
- Browser console shows no application errors.

## Definition of done

A new or retrofitted data application belongs to this family when a user can recognize the City shell immediately, understand the app's purpose and data freshness from Home, verify its source and limits on About, move through the interface by keyboard or touch, and reach the underlying evidence without visual or semantic breakage. In a retrofit, the existing body's structure and behavior must remain intact apart from the explicitly allowed color, typography, and shell-compatibility changes.

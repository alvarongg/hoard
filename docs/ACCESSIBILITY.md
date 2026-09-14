# Accessibility

Hoard targets **WCAG 2.1 AA**. Accessibility is enforced in three layers:

## Automated checks (in CI)

- **Component-level axe-core**: every new React component ships a `jest-axe`
  test asserting zero violations (`expect(await axe(container)).toHaveNoViolations()`).
- **Theme contrast**: `frontend/tests/accessibility/theme.a11y.test.tsx` runs axe
  over the app in both light and dark themes, requiring zero contrast violations.
- **Keyboard & ARIA**: interactive components (dialogs, toggles, tables, forms)
  are tested for `role`, `aria-*` attributes, focus behaviour, and keyboard
  operation (Tab, Enter, Escape, arrow keys).

## Design primitives

- **Never color alone**: status is always conveyed with text and/or an icon in
  addition to color (see `Badge`, `StockBadge`, ROI shown as "no data" not "0%").
- **Live regions**: async results and mode changes are announced through an
  `aria-live` region (`LiveRegion`, `OfflineBanner`, search result counts).
- **Skip link**: `SkipLink` is the first focusable element and jumps to
  `#main-content`.
- **Reduced motion**: animations respect `prefers-reduced-motion`.
- **Charts**: SVG charts are `aria-hidden` and paired with an equivalent
  `ChartDataTable` inside a keyboard-reachable `<details>` disclosure.
- **Zoom to 200%**: layouts use `rem`-based max widths; wide tables get their
  own horizontal scroll container to avoid two-dimensional page scrolling.

## Scope and limits

The automated audit described above covers the 6 Phase-1 pages and the 9 pages
added in Phase 2/3, in both themes. **Automated testing is necessary but not
sufficient.** Full WCAG 2.1 AA conformance also requires manual testing with
assistive technologies (screen readers such as NVDA/VoiceOver, keyboard-only
navigation, and expert review), which the automated suite does not replace.

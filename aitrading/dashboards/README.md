# Dashboards

Every dashboard in the project, in one place. All of them are self-contained single
files — open one in a browser, no build step, no dependencies, no server.

| File | Question it answers | Reads from |
|---|---|---|
| `project-dashboard.html` | Are the strategies any good? | SEPA matrix run, 2026-09-04 |
| `learning-dashboard.html` | Am I getting better? | `../moondev-zoom/sessions/` |

Keep those two questions apart. It is entirely possible to make progress on one and
none on the other, and a single page that mixed them would hide exactly that.

## Conventions for anything added here

- **One file, no build.** Everything inline. It has to still open in four years, from a
  USB stick, with no toolchain. That constraint is why these are plain HTML.
- **Shared design system.** Same tokens as the others: IBM Plex Mono / Public Sans /
  Source Serif 4, a left rail of panes, `--paper`/`--ink`/`--rule` variables, and both
  light and dark defined on `:root` plus `[data-theme]`. Copy the `:root` block from an
  existing file rather than inventing a new palette.
- **A distinct accent per dashboard.** `--acc` is the one token that differs — navy for
  the project page, purple for the learning page. It is what stops you misreading which
  page you have open when they otherwise look identical.
- **State goes in `localStorage`, under its own key.** Ticks are per-browser and
  per-device, and none of it is a source of truth. Anything that matters belongs in a
  file in the repo, not in a checkbox.
- **Name it for its question,** not its format: `<subject>-dashboard.html`.

## Note

These are reporting surfaces, not systems of record. Every figure on the project
dashboard is generated from a run; every tick on the learning dashboard is a note to
yourself. Nothing here is live, nothing here trades, and nothing here holds a key.

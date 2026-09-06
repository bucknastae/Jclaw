# Source

| Field | Value |
|---|---|
| URL | `<paste>` |
| Video ID | `<id>` |
| Title | |
| Streamed | |
| Duration | |
| Watched on | |
| Transcript captured | no |

## Capture the transcript first

Livestreams get trimmed, unlisted, or pulled. Do this before you watch, not after.

**From the browser (no tools, always works):** open the video → `...` under the player →
*Show transcript* → click into the panel, select all, paste below. Turn off timestamps
with the toggle in that panel if you want it clean.

**From the command line:**

```sh
yt-dlp --skip-download --write-auto-subs --sub-lang en --convert-subs srt "<url>"
```

Save the raw text under `transcript/` in this folder. Keep it verbatim — your
interpretation goes in `01-notes.md`, not here.

## Chapters / timestamps

<!-- paste the chapter list, or build one as you watch: 00:00 topic -->

## Transcript

<!-- paste, or note the path to transcript/ -->

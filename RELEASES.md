# TermDeck 0.3.2

## What's New

### Inline Images in Slides (0.2.0)
- Render images directly in Markdown slides: `![diagram](path.png)`
- Best available terminal graphics: Kitty TGP, Sixel, iTerm2, or half-block fallback
- Supported formats: PNG, JPG, JPEG, GIF, WEBP, BMP
- Images stay crisp even when zooming terminal font

### Image Controls (0.2.1)
| Key | Action |
|---|---|
| `f` | Toggle fullscreen image view |
| `o` | Open image in system default viewer |
| `Esc` | Exit fullscreen |

### Dark Mode Toggle (0.2.1)
- Press `d` to toggle between light and dark themes in-session

### Presenter Notes Companion (0.3.0)
```bash
termdeck ./my-deck          # main deck
termdeck --notes ./my-deck  # notes companion
```
- **Bidirectional sync** — navigate from either window with arrow keys
- Live timer (total + per-slide)
- Shows next slide filename
- No networking; syncs via atomic temp file

### Multiline Notes (0.3.1)
```markdown
# My Slide

Some content.

<!-- note:
- Mention the 3x speedup
- Ask if anyone has questions
- Transition to demo
-->

More content.
```
- Supports full Markdown formatting in notes
- Multiple `<!-- note: ... -->` blocks per slide accumulate

### Proportional Image Sizing (0.3.2)
- Images auto-size with 15-cell height cap
- Tall images shrink proportionally instead of being cropped
- Small images stay small
- Explicit `<img width="50">` tags still respected

### Customization (0.2.1)
- Add a `deck.tcss` file in your deck folder to override default styles
- Force image renderer: `TERMDECK_IMAGE_PROTOCOL=kitty termdeck ./my-deck`

## Installation
```bash
pip install termdeck
# or with music extras
pip install "termdeck[music]"
```

## Requirements
- Python 3.10+

---

**Full Changelog**: `0.1.0...0.3.2`

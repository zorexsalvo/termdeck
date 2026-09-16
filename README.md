# TermDeck

Terminal presentations, written in Markdown or Python. Built on [Textual](https://github.com/Textualize/textual).

Each file in a deck folder is one slide. Navigate with the arrow keys.

## Install

```bash
pip install termdeck
```

Optional extras:

```bash
pip install "termdeck[music]"   # interactive music-pad slides
```

Requires Python 3.10 or newer.

## Usage

```bash
termdeck                # play the bundled sample deck
termdeck ./my-deck      # play your own deck
python -m termdeck      # same thing
```

Navigate with **← / →** arrow keys.

While viewing a slide that contains an image:

- **f** — toggle fullscreen image view
- **o** — open the image in your system default image viewer
- **Esc** — exit fullscreen
- **Ctrl+C** — quit

### Presenter notes

Add notes to any Markdown slide with block-level HTML comments:

```markdown
# My title

- a bullet
- another bullet

<!-- note: Remember to mention the 3x speedup -->
```

Open a notes companion in a second terminal:

```bash
termdeck --notes ./my-deck
```

The notes window shows the current slide’s notes, a running timer, and the next slide filename. It syncs automatically as you navigate the main deck.

## Writing a deck

A deck is a folder of slide files. Files are sorted by name.

### Markdown slides

```markdown
# My title

- a bullet
- another bullet

![diagram](diagram.png)
```

Image paragraphs (`![alt](path)`) are rendered as images. Relative paths are resolved from the slide file's directory.

Images are rendered using the best available terminal graphics method: Kitty graphics protocol, Sixel, iTerm2 inline images, or a colored half-block fallback. This means images stay crisp even when you zoom the terminal font to make text readable.

Supported formats: `png`, `jpg`, `jpeg`, `gif`, `webp`, `bmp`.

Images are horizontally centered. By default `![alt](path)` images render at a fixed width of 60 cells. To control an individual image's size, use a standard HTML `<img>` tag:

```markdown
<img src="diagram.png" width="80%">
<img src="diagram.png" width="60" height="auto">
```

To change the default size or alignment for all images in a deck, add a `deck.tcss` file in your deck folder:

```css
/* Default: 60 cells wide, centered */
#markdown-slide ImageWidget {
    width: 60;
    height: auto;
    margin: 0 10;
}
```

If image auto-detection misbehaves in your terminal, force a specific renderer:

```bash
TERMDECK_IMAGE_PROTOCOL=kitty termdeck ./my-deck     # Kitty TGP
TERMDECK_IMAGE_PROTOCOL=sixel termdeck ./my-deck     # Sixel
TERMDECK_IMAGE_PROTOCOL=halfcell termdeck ./my-deck  # colored half blocks
TERMDECK_IMAGE_PROTOCOL=unicode termdeck ./my-deck   # unicode characters
```

### Python slides

A Python slide is a [Textual `Screen`](https://textual.textualize.io/api/screen/). It must expose a `Slide` class:

```python
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Button

class Slide(Screen):
    def compose(self) -> ComposeResult:
        yield Button("Hello")
```

The screen's widgets are styled by `styles/default.tcss`. You can add a `deck.tcss`
file in your deck folder to override styles. All Textual functionality is available
for rich, interactive slides.

## Development

```bash
pip install -e ".[dev]"
python test.py
python -m build
```

## License

MIT

Terminal graphics rendering is provided by [textual-image](https://github.com/lnqs/textual-image) (LGPL-3.0-or-later).

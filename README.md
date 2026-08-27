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

## Usage

```bash
termdeck                # play the bundled sample deck
termdeck ./my-deck      # play your own deck
python -m termdeck      # same thing
```

Navigate with **← / →** arrow keys; quit with **Ctrl+C**.

## Writing a deck

A deck is a folder of slide files. Files are sorted by name.

### Markdown slides

```markdown
# My title

- a bullet
- another bullet
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

The screen's widgets are styled by `styles/default.tcss`, which you can override in
your deck if you want. All Textual functionality is available for rich,
interactive slides.

## Development

```bash
pip install -e ".[dev]"
python test.py
python -m build
```

## License

MIT

from pathlib import Path

from textual import events
from textual.app import App
from textual.widgets import Footer, Header

from termdeck.deck import load_deck


class TermDeck(App):
    """A terminal presentation app: arrow keys walk through a deck of slides."""

    title = "TermDeck"
    CSS_PATH = str(Path(__file__).parent / "styles" / "default.tcss")

    def __init__(self, deck_dir: Path, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.slide_number = 0
        self.names = [name for name, _ in load_deck(deck_dir)]
        for name, cls in load_deck(deck_dir):
            self.install_screen(cls, name)

    def on_key(self, event: events.Key) -> None:
        names = self.names
        if not names:
            return

        if event.key == "right" and self.slide_number < len(names) - 1:
            self.slide_number += 1
        elif event.key == "left" and self.slide_number > 0:
            self.slide_number -= 1
        else:
            return

        self.push_screen(names[self.slide_number])

    def compose(self):
        yield Header()
        yield Footer()


if __name__ == "__main__":
    TermDeck(Path("slides")).run()

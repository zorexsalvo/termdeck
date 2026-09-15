import subprocess
import sys
from pathlib import Path

from textual import events
from textual.app import App
from textual.widgets import Footer, Header

from termdeck.deck import ImageFullscreen, ImageWidget, load_deck


def _open_image(path: Path) -> None:
    """Open an image file with the system default viewer."""
    if sys.platform == "darwin":
        subprocess.run(["open", str(path)], check=False)
    elif sys.platform == "win32":
        subprocess.run(["start", str(path)], shell=True, check=False)
    else:
        subprocess.run(["xdg-open", str(path)], check=False)


class TermDeck(App):
    """A terminal presentation app: arrow keys walk through a deck of slides."""

    title = "TermDeck"
    CSS_PATH = str(Path(__file__).parent / "styles" / "default.tcss")
    BINDINGS = [("d", "toggle_dark", "Toggle dark mode")]

    def __init__(self, deck_dir: Path, *args, **kwargs):
        default_css = Path(__file__).parent / "styles" / "default.tcss"
        custom_css = Path(deck_dir) / "deck.tcss"
        self.CSS_PATH = [str(default_css)]
        if custom_css.is_file():
            self.CSS_PATH.append(str(custom_css))
        super().__init__(*args, **kwargs)
        self.slide_number = 0
        self.names = [name for name, _ in load_deck(deck_dir)]
        for name, cls in load_deck(deck_dir):
            self.install_screen(cls, name)

    def _current_image_path(self) -> Path | None:
        """Return the image path of the current screen, or None."""
        from textual.css.query import NoMatches

        screen = self.screen
        if isinstance(screen, ImageFullscreen):
            return screen.path
        try:
            image = screen.query_one(ImageWidget)
        except NoMatches:
            return None
        return image.path

    def _toggle_fullscreen(self) -> None:
        """Push or pop the fullscreen image view."""
        if isinstance(self.screen, ImageFullscreen):
            self.pop_screen()
            return

        path = self._current_image_path()
        if path is not None:
            self.push_screen(ImageFullscreen(path))

    def _go_to_slide(self, index: int) -> None:
        """Navigate to the slide at index, exiting fullscreen if needed."""
        if isinstance(self.screen, ImageFullscreen):
            self.pop_screen()
        self.slide_number = index
        self.push_screen(self.names[index])

    def on_key(self, event: events.Key) -> None:
        names = self.names
        if not names:
            return

        if event.key == "right" and self.slide_number < len(names) - 1:
            self._go_to_slide(self.slide_number + 1)
        elif event.key == "left" and self.slide_number > 0:
            self._go_to_slide(self.slide_number - 1)
        elif event.key == "o":
            path = self._current_image_path()
            if path is not None:
                _open_image(path)
        elif event.key == "f":
            self._toggle_fullscreen()
        elif event.key == "escape" and isinstance(self.screen, ImageFullscreen):
            self.pop_screen()
        else:
            return

    def on_mount(self) -> None:
        if self.names:
            self.push_screen(self.names[0])

    def compose(self):
        yield Header()
        yield Footer()


if __name__ == "__main__":
    TermDeck(Path("slides")).run()

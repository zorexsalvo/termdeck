from pathlib import Path

from termdeck.deck import load_deck, load_slide

SAMPLE = Path(__file__).parent / "termdeck" / "sample"


def test_load_slide_markdown():
    cls = load_slide(SAMPLE / "p01_intro.md")
    assert cls.__name__ == "Slide"


def test_load_slide_python(tmp_dir):
    py = tmp_dir / "slide.py"
    py.write_text("from textual.screen import Screen\nclass Slide(Screen): pass\n")
    cls = load_slide(py)
    assert issubclass(cls, __import__("textual.screen", fromlist=["Screen"]).Screen)


def test_load_deck_sorted():
    slides = load_deck(SAMPLE)
    names = [name for name, _ in slides]
    assert names == sorted(names)
    assert len(slides) == 2
    assert all(name.endswith((".md", ".MD", ".py")) for name in names)


def test_navigation():
    from pathlib import Path

    from textual.events import Key

    from termdeck.app import TermDeck

    async def _run():
        app = TermDeck(Path(__file__).parent / "termdeck" / "sample")
        async with app.run_test() as pilot:
            assert len(app.names) == 2
            app.on_key(Key("right", "right"))
            await pilot.pause()
            assert app.slide_number == 1
            app.on_key(Key("left", "left"))
            await pilot.pause()
            assert app.slide_number == 0

    import asyncio

    asyncio.run(_run())


def main():
    test_load_slide_markdown()
    test_load_deck_sorted()
    test_navigation()

    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as tmp:
        test_load_slide_python(Path(tmp))

    print("All tests passed.")


if __name__ == "__main__":
    main()

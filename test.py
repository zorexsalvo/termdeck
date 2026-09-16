from pathlib import Path
from unittest import mock

from PIL import Image as PILImage
from textual.widgets import Markdown

from termdeck.deck import ImageFullscreen, load_deck, load_slide

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
    names = [name for name, _, _ in slides]
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


def test_markdown_inline_image(tmp_dir):
    from termdeck.app import TermDeck

    img_path = tmp_dir / "diagram.png"
    PILImage.new("RGB", (20, 10), color="blue").save(img_path)

    md = tmp_dir / "slide.md"
    md.write_text("# Title\n\n![diagram](diagram.png)\n")

    async def _run():
        app = TermDeck(tmp_dir)
        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.pause()
            image_widget = app.screen.query_one("ImageWidget")
            # 20x10 pixel image → 2x1 cells, centered in 80-col terminal
            assert image_widget.region.width == 2
            assert image_widget.region.height == 1
            assert image_widget.region.x == 39
            renderable = image_widget.render()
            assert renderable is not None

    import asyncio

    asyncio.run(_run())


def test_markdown_without_images(tmp_dir):
    from termdeck.app import TermDeck

    md = tmp_dir / "slide.md"
    md.write_text("# Title\n\nSome text.\n")

    async def _run():
        app = TermDeck(tmp_dir)
        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.pause()
            assert len(list(app.screen.query("ImageWidget").results())) == 0

    import asyncio

    asyncio.run(_run())


def test_fullscreen_image(tmp_dir):
    from textual.events import Key

    from termdeck.app import TermDeck

    img_path = tmp_dir / "diagram.png"
    PILImage.new("RGB", (20, 10), color="blue").save(img_path)

    md = tmp_dir / "slide.md"
    md.write_text("# Title\n\n![diagram](diagram.png)\n")

    async def _run():
        app = TermDeck(tmp_dir)
        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.pause()
            app.on_key(Key("f", "f"))
            await pilot.pause()
            assert isinstance(app.screen, ImageFullscreen)
            app.on_key(Key("escape", "escape"))
            await pilot.pause()
            assert not isinstance(app.screen, ImageFullscreen)

    import asyncio

    asyncio.run(_run())


def test_open_image_externally(tmp_dir):
    from textual.events import Key

    from termdeck.app import TermDeck

    img_path = tmp_dir / "diagram.png"
    PILImage.new("RGB", (20, 10), color="blue").save(img_path)

    md = tmp_dir / "slide.md"
    md.write_text("# Title\n\n![diagram](diagram.png)\n")

    async def _run():
        app = TermDeck(tmp_dir)
        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.pause()
            with mock.patch("termdeck.app.subprocess.run") as run:
                app.on_key(Key("o", "o"))
                await pilot.pause()
                run.assert_called_once()
                args = run.call_args[0][0]
                assert str(img_path) in args

    import asyncio

    asyncio.run(_run())


def test_html_img_tag_with_size(tmp_dir):
    from termdeck.app import TermDeck

    img_path = tmp_dir / "diagram.png"
    PILImage.new("RGB", (200, 100), color="blue").save(img_path)

    md = tmp_dir / "slide.md"
    md.write_text('# Title\n\n<img src="diagram.png" width="50%">\n')

    async def _run():
        from textual.css.scalar import Unit

        app = TermDeck(tmp_dir)
        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.pause()
            image_widget = app.screen.query_one("ImageWidget")
            assert image_widget.styles.width.unit == Unit.WIDTH
            assert image_widget.styles.width.value == 50
            renderable = image_widget.render()
            assert renderable is not None

    import asyncio

    asyncio.run(_run())


def test_extract_notes():
    from termdeck.deck import _extract_notes

    content = "# Title\n\n<!-- note: first note -->\n\nSome text.\n\n<!-- note: second note -->\n"
    notes = _extract_notes(content)
    assert notes == "first note\n\nsecond note"

    multiline = "# Title\n\n<!-- note:\n- Mention the 3x speedup\n- Ask if anyone has questions\n-->\n"
    notes = _extract_notes(multiline)
    assert notes == "- Mention the 3x speedup\n- Ask if anyone has questions"

    assert _extract_notes("# Title\n\nNo notes here.") == ""
    assert _extract_notes("<!-- NOTE:   spaced out   -->") == "spaced out"


def test_state_file_written(tmp_dir):
    from textual.events import Key

    from termdeck.app import TermDeck
    from termdeck.deck import _get_state_path

    img_path = tmp_dir / "diagram.png"
    PILImage.new("RGB", (20, 10), color="blue").save(img_path)

    md = tmp_dir / "slide.md"
    md.write_text("# Title\n\n<!-- note: remember to smile -->\n")

    state_path = _get_state_path(tmp_dir)
    if state_path.exists():
        state_path.unlink()

    async def _run():
        app = TermDeck(tmp_dir)
        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.pause()
            assert state_path.exists()
            import json

            data = json.loads(state_path.read_text())
            assert data["slide"] == 0
            assert data["name"] == "slide.md"

            app.on_key(Key("right", "right"))
            await pilot.pause()
            data = json.loads(state_path.read_text())
            assert data["slide"] == 0  # only one slide, can't advance

    import asyncio

    asyncio.run(_run())


def test_notes_app_display(tmp_dir):
    import json

    from termdeck.deck import _get_state_path
    from termdeck.notes_app import TermDeckNotes

    md = tmp_dir / "slide.md"
    md.write_text("# Title\n\n<!-- note: hello notes -->\n")

    state_path = _get_state_path(tmp_dir)
    state_path.write_text(
        json.dumps({
            "slide": 0,
            "name": "slide.md",
            "total_start_time": 0.0,
            "slide_start_time": 0.0,
        }),
        encoding="utf-8",
    )

    async def _run():
        app = TermDeckNotes(tmp_dir)
        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.pause()
            assert app.slide_index == 0
            assert app.query_one("#notes-content") is not None

    import asyncio

    asyncio.run(_run())


def test_main_deck_polls_state(tmp_dir):
    import json
    import time

    from termdeck.app import TermDeck
    from termdeck.deck import _get_state_path, _write_state

    md1 = tmp_dir / "01_slide.md"
    md1.write_text("# Slide 1\n")
    md2 = tmp_dir / "02_slide.md"
    md2.write_text("# Slide 2\n")

    state_path = _get_state_path(tmp_dir)
    if state_path.exists():
        state_path.unlink()

    async def _run():
        app = TermDeck(tmp_dir)
        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.pause()
            assert app.slide_number == 0

            _write_state(state_path, 1, "02_slide.md", time.time(), time.time())
            import asyncio
            await asyncio.sleep(0.3)
            assert app.slide_number == 1

    import asyncio

    asyncio.run(_run())


def test_notes_app_navigates_and_writes_state(tmp_dir):
    import json

    from textual.events import Key

    from termdeck.deck import _get_state_path
    from termdeck.notes_app import TermDeckNotes

    md1 = tmp_dir / "01_slide.md"
    md1.write_text("# Slide 1\n\n<!-- note: first -->\n")
    md2 = tmp_dir / "02_slide.md"
    md2.write_text("# Slide 2\n\n<!-- note: second -->\n")

    state_path = _get_state_path(tmp_dir)
    state_path.write_text(
        json.dumps({
            "slide": 0,
            "name": "01_slide.md",
            "total_start_time": 0.0,
            "slide_start_time": 0.0,
        }),
        encoding="utf-8",
    )

    async def _run():
        app = TermDeckNotes(tmp_dir)
        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.pause()
            assert app.slide_index == 0

            app.on_key(Key("right", "right"))
            await pilot.pause()
            assert app.slide_index == 1
            data = json.loads(state_path.read_text())
            assert data["slide"] == 1
            assert data["name"] == "02_slide.md"

    import asyncio

    asyncio.run(_run())


def test_tall_image_shrinks(tmp_dir):
    from PIL import Image as PILImage

    from termdeck.app import TermDeck

    # Create a very tall image (20x400 pixels)
    img_path = tmp_dir / "tall.png"
    PILImage.new("RGB", (20, 400), color="blue").save(img_path)

    md = tmp_dir / "slide.md"
    md.write_text("# Title\n\n![tall](tall.png)\n")

    async def _run():
        app = TermDeck(tmp_dir)
        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.pause()
            image_widget = app.screen.query_one("ImageWidget")
            # Height should be capped at DEFAULT_MAX_HEIGHT (15)
            assert image_widget.region.height <= 15
            # Width should be shrunk proportionally (much less than 60)
            assert image_widget.region.width < 10

    import asyncio

    asyncio.run(_run())


def main():
    test_load_slide_markdown()
    test_load_deck_sorted()
    test_navigation()

    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as tmp:
        path = Path(tmp)
        test_load_slide_python(path)
        test_markdown_inline_image(path)
        test_markdown_without_images(path)
        test_fullscreen_image(path)
        test_open_image_externally(path)
        test_html_img_tag_with_size(path)
        test_extract_notes()

    with TemporaryDirectory() as tmp:
        path = Path(tmp)
        test_state_file_written(path)

    with TemporaryDirectory() as tmp:
        path = Path(tmp)
        test_notes_app_display(path)

    with TemporaryDirectory() as tmp:
        path = Path(tmp)
        test_main_deck_polls_state(path)

    with TemporaryDirectory() as tmp:
        path = Path(tmp)
        test_notes_app_navigates_and_writes_state(path)

    with TemporaryDirectory() as tmp:
        path = Path(tmp)
        test_tall_image_shrinks(path)

    print("All tests passed.")


if __name__ == "__main__":
    main()

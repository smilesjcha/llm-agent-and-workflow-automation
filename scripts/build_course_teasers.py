"""Build 45-second animated course teasers from verified browser captures."""

from __future__ import annotations

from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
ASSET_DIR = ROOT / "assets/demo-videos"
SCENES = ("overview", "pipeline", "result", "boundary")
DURATIONS_MS = (9_000, 11_000, 11_000, 14_000)


def build_teaser(day: int) -> Path:
    frames: list[Image.Image] = []
    for scene in SCENES:
        source = ASSET_DIR / f"day{day}_{scene}.png"
        if not source.is_file():
            raise FileNotFoundError(f"DEMO_CAPTURE_NOT_FOUND:{source}")
        with Image.open(source) as image:
            frames.append(image.convert("P", palette=Image.Palette.ADAPTIVE, colors=192))

    output = ASSET_DIR / f"day{day}_service_teaser.gif"
    frames[0].save(
        output,
        save_all=True,
        append_images=frames[1:],
        duration=DURATIONS_MS,
        loop=0,
        optimize=True,
        disposal=2,
    )
    return output


def main() -> None:
    for day in (2, 3, 4, 5):
        output = build_teaser(day)
        print(output.relative_to(ROOT))


if __name__ == "__main__":
    main()

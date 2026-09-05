from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
SIZE = 512


def scaled(value: int) -> int:
    return value * SIZE // 256


def create_icon() -> Image.Image:
    image = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle(
        (scaled(12), scaled(12), scaled(244), scaled(244)),
        radius=scaled(52),
        fill="#3660F4",
    )
    draw.rounded_rectangle(
        (scaled(67), scaled(42), scaled(184), scaled(207)),
        radius=scaled(16),
        fill="#FFFFFF",
    )
    draw.polygon(
        [(scaled(151), scaled(42)), (scaled(184), scaled(75)), (scaled(151), scaled(75))],
        fill="#C9D5FF",
    )
    # The mark is a compact geometric rendering of "廾" so it stays legible at 16px.
    mark = "#3660F4"
    draw.rounded_rectangle(
        (scaled(88), scaled(105), scaled(104), scaled(165)), radius=scaled(7), fill=mark
    )
    draw.rounded_rectangle(
        (scaled(148), scaled(105), scaled(164), scaled(165)), radius=scaled(7), fill=mark
    )
    draw.rounded_rectangle(
        (scaled(83), scaled(117), scaled(169), scaled(133)), radius=scaled(7), fill=mark
    )
    draw.rounded_rectangle(
        (scaled(116), scaled(86), scaled(132), scaled(179)), radius=scaled(7), fill=mark
    )
    # Local conversion accent: a small green forward arrow with strong contrast.
    accent = "#09B42C"
    draw.rounded_rectangle(
        (scaled(156), scaled(166), scaled(210), scaled(184)), radius=scaled(9), fill=accent
    )
    draw.polygon(
        [(scaled(205), scaled(153)), (scaled(226), scaled(175)), (scaled(205), scaled(197))],
        fill=accent,
    )
    return image


def main() -> None:
    ASSETS.mkdir(exist_ok=True)
    image = create_icon()
    image.save(ASSETS / "app-icon.png")
    image.save(
        ASSETS / "app-icon.ico",
        sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )


if __name__ == "__main__":
    main()

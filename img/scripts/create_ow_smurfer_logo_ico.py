from __future__ import annotations

import argparse
import struct
import sys
from pathlib import Path

from PySide6.QtCore import QByteArray, QBuffer, QIODevice, Qt
from PySide6.QtGui import QImage, QPainter

DEFAULT_ICON_SIZES = (16, 20, 24, 32, 40, 48, 64, 72, 96, 128, 256)


def parse_args() -> argparse.Namespace:
    script_dir = Path(__file__).resolve().parent
    img_dir = script_dir.parent

    parser = argparse.ArgumentParser(
        description="Create a Windows .ico file with multiple embedded sizes."
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=img_dir / "OW_Smurfer_logo.png",
        help="Source PNG file.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=img_dir / "OW_Smurfer_logo.ico",
        help="Output ICO file.",
    )
    parser.add_argument(
        "--sizes",
        type=int,
        nargs="+",
        default=list(DEFAULT_ICON_SIZES),
        help="Icon sizes to embed in the ICO file.",
    )
    return parser.parse_args()


def normalize_sizes(raw_sizes: list[int]) -> list[int]:
    sizes = sorted({size for size in raw_sizes if 1 <= size <= 256})
    if not sizes:
        raise ValueError("At least one icon size between 1 and 256 is required.")
    return sizes


def load_png(source_path: Path) -> QImage:
    image = QImage(str(source_path))
    if image.isNull():
        raise FileNotFoundError(f"Could not load source image: {source_path}")
    return image


def render_square_icon(source: QImage, size: int) -> QImage:
    scaled = source.scaled(
        size,
        size,
        Qt.KeepAspectRatio,
        Qt.SmoothTransformation,
    )

    canvas = QImage(size, size, QImage.Format_ARGB32)
    canvas.fill(Qt.transparent)

    painter = QPainter(canvas)
    x = (size - scaled.width()) / 2
    y = (size - scaled.height()) / 2
    painter.drawImage(x, y, scaled)
    painter.end()

    return canvas


def image_to_png_bytes(image: QImage) -> bytes:
    data = QByteArray()
    buffer = QBuffer(data)
    if not buffer.open(QIODevice.WriteOnly):
        raise RuntimeError("Could not open an in-memory buffer for PNG encoding.")
    if not image.save(buffer, "PNG"):
        raise RuntimeError("Could not encode icon image as PNG.")
    return bytes(data)


def build_ico(images: list[tuple[int, bytes]]) -> bytes:
    header = struct.pack("<HHH", 0, 1, len(images))
    directory = bytearray()
    payload = bytearray()
    offset = 6 + (16 * len(images))

    for size, png_bytes in images:
        ico_dimension = 0 if size == 256 else size
        directory.extend(
            struct.pack(
                "<BBBBHHII",
                ico_dimension,
                ico_dimension,
                0,
                0,
                1,
                32,
                len(png_bytes),
                offset,
            )
        )
        payload.extend(png_bytes)
        offset += len(png_bytes)

    return header + directory + payload


def create_icon(source_path: Path, output_path: Path, sizes: list[int]) -> list[int]:
    source_image = load_png(source_path)
    icon_images = []

    for size in sizes:
        resized = render_square_icon(source_image, size)
        icon_images.append((size, image_to_png_bytes(resized)))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(build_ico(icon_images))
    return sizes


def main() -> int:
    args = parse_args()

    try:
        sizes = normalize_sizes(args.sizes)
        embedded_sizes = create_icon(args.source.resolve(), args.output.resolve(), sizes)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    size_list = ", ".join(str(size) for size in embedded_sizes)
    print(f"ICO created: {args.output.resolve()} ({size_list})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""
Sprite Sheet Processor V2 for Desktop Pet

Fixes the two main problems in the original script:
1. Uses a fixed grid instead of inferring split lines from magenta gaps.
2. Uses a consistent scale and bottom baseline per row so frames do not jitter.

Usage:
    python3 desktop-pet/scripts/process-spritesheet-v2.py INPUT.png \
      -o desktop-pet/public/sprites/tappy_cat_v2.png \
      --cols 8 --rows 9 --target 128 --name "TappyCat V2"
"""

import argparse
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image


@dataclass
class CellFrame:
    image: Image.Image | None
    width: int = 0
    height: int = 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Process a magenta-background sprite sheet")
    parser.add_argument("input", help="Input PNG/JPG sprite sheet")
    parser.add_argument("-o", "--output", required=True, help="Output PNG path")
    parser.add_argument("--name", default="Unnamed Sprite", help="Human-readable sprite name")
    parser.add_argument("--cols", type=int, default=8, help="Number of columns in source sheet")
    parser.add_argument("--rows", type=int, required=True, help="Number of rows in source sheet")
    parser.add_argument("--target", type=int, default=128, help="Output frame size in pixels")
    parser.add_argument("--margin", type=int, default=6, help="Outer margin inside each output frame")
    parser.add_argument("--padding", type=int, default=6, help="Padding added around trimmed content")
    parser.add_argument("--inner", type=float, default=70.0, help="Distance to background for full transparency")
    parser.add_argument("--outer", type=float, default=190.0, help="Distance to background for soft edge opacity")
    parser.add_argument("--alpha-threshold", type=int, default=12, help="Alpha threshold used to trim content")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    img = Image.open(input_path).convert("RGBA")
    arr = np.array(img)
    height, width = arr.shape[:2]

    print(f"Name: {args.name}")
    print(f"Source: {input_path}")
    print(f"Size: {width}x{height}")
    print(f"Grid: {args.cols}x{args.rows}")

    keyed = chroma_key(arr, inner=args.inner, outer=args.outer)
    x_edges = grid_edges(width, args.cols)
    y_edges = grid_edges(height, args.rows)

    rows: list[list[CellFrame]] = []
    for row in range(args.rows):
      row_frames: list[CellFrame] = []
      for col in range(args.cols):
        x0, x1 = x_edges[col], x_edges[col + 1]
        y0, y1 = y_edges[row], y_edges[row + 1]
        cell = Image.fromarray(keyed[y0:y1, x0:x1], mode="RGBA")
        trimmed = trim_with_padding(cell, padding=args.padding, alpha_threshold=args.alpha_threshold)
        if trimmed is None:
          row_frames.append(CellFrame(image=None))
        else:
          row_frames.append(CellFrame(image=trimmed, width=trimmed.width, height=trimmed.height))
      rows.append(row_frames)

    out = Image.new("RGBA", (args.target * args.cols, args.target * args.rows), (0, 0, 0, 0))

    for row_idx, row_frames in enumerate(rows):
      max_w = max((frame.width for frame in row_frames), default=0)
      max_h = max((frame.height for frame in row_frames), default=0)
      if max_w == 0 or max_h == 0:
        print(f"  Row {row_idx}: empty")
        continue

      scale = min(
        (args.target - args.margin * 2) / max_w,
        (args.target - args.margin * 2) / max_h,
      )
      baseline_y = row_idx * args.target + args.target - args.margin
      print(f"  Row {row_idx}: max content {max_w}x{max_h}, scale {scale:.3f}")

      for col_idx, frame in enumerate(row_frames):
        if frame.image is None:
          continue

        resized = resize_frame(frame.image, scale)
        left = col_idx * args.target + (args.target - resized.width) // 2
        top = baseline_y - resized.height
        out.alpha_composite(resized, (left, top))

    out.save(output_path)
    print(f"Saved: {output_path}")
    print(f"Output size: {out.width}x{out.height}")


def grid_edges(total: int, count: int) -> list[int]:
    return [round(i * total / count) for i in range(count + 1)]


def chroma_key(arr: np.ndarray, inner: float, outer: float) -> np.ndarray:
    bg = np.array([255.0, 0.0, 255.0], dtype=np.float32)
    rgb = arr[:, :, :3].astype(np.float32)
    dist = np.sqrt(np.sum((rgb - bg) ** 2, axis=2))

    out = arr.copy()
    out[dist <= inner, 3] = 0

    transition = (dist > inner) & (dist < outer)
    t = (dist[transition] - inner) / (outer - inner)
    out[transition, 3] = (t * out[transition, 3]).astype(np.uint8)
    return out


def trim_with_padding(img: Image.Image, padding: int, alpha_threshold: int) -> Image.Image | None:
    arr = np.array(img)
    alpha = arr[:, :, 3]
    mask = alpha > alpha_threshold
    if not np.any(mask):
        return None

    rows = np.any(mask, axis=1)
    cols = np.any(mask, axis=0)

    y0 = int(np.argmax(rows))
    y1 = int(len(rows) - np.argmax(rows[::-1]))
    x0 = int(np.argmax(cols))
    x1 = int(len(cols) - np.argmax(cols[::-1]))

    x0 = max(0, x0 - padding)
    y0 = max(0, y0 - padding)
    x1 = min(img.width, x1 + padding)
    y1 = min(img.height, y1 + padding)

    if x1 <= x0 or y1 <= y0:
        return None

    return img.crop((x0, y0, x1, y1))


def resize_frame(img: Image.Image, scale: float) -> Image.Image:
    new_w = max(1, int(round(img.width * scale)))
    new_h = max(1, int(round(img.height * scale)))
    return img.resize((new_w, new_h), Image.LANCZOS)


if __name__ == "__main__":
    main()

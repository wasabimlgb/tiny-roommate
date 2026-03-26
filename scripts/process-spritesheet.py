#!/usr/bin/env python3
"""
Sprite Sheet Processor for Desktop Pet

Takes a sprite sheet with magenta (#FF00FF) background and square cells,
removes the background, and outputs a clean sprite sheet.

Assumes the source grid has square cells — auto-detects cell size from
the image width and column count.

Usage:
    python3 scripts/process-spritesheet.py source.png -o output.png
    python3 scripts/process-spritesheet.py source.png -o output.png --cols 8 --target 128
"""

import argparse
import numpy as np
from PIL import Image
from scipy.ndimage import minimum_filter


def main():
    parser = argparse.ArgumentParser(description='Process sprite sheet for desktop pet')
    parser.add_argument('input', help='Input PNG with magenta background')
    parser.add_argument('-o', '--output', required=True, help='Output PNG path')
    parser.add_argument('--cols', type=int, default=8, help='Number of columns (default: 8)')
    parser.add_argument('--target', type=int, default=128, help='Output frame size in px (default: 128)')
    parser.add_argument('--erode', type=int, default=4, help='Alpha erosion px — use 0-1 for cartoon/outlined styles (default: 4)')
    args = parser.parse_args()

    img = Image.open(args.input).convert('RGBA')
    arr = np.array(img)
    h, w = arr.shape[:2]

    bg = np.array([255.0, 0.0, 255.0])
    dist = np.sqrt(np.sum((arr[:, :, :3].astype(np.float32) - bg) ** 2, axis=2))

    # Square cells: cell size = image width / cols, rows = height / cell size
    cell_size = w / args.cols
    rows = round(h / cell_size)

    print(f'Source: {w}x{h}, cell ~{cell_size}px, grid {args.cols}x{rows}')

    # Chroma key the full image
    keyed = chroma_key(arr, dist, erode=args.erode)

    # Slice uniform grid, trim, scale
    TARGET = args.target
    out = Image.new('RGBA', (TARGET * args.cols, TARGET * rows), (0, 0, 0, 0))

    for r in range(rows):
        for c in range(args.cols):
            x0 = round(c * w / args.cols)
            x1 = round((c + 1) * w / args.cols)
            y0 = round(r * h / rows)
            y1 = round((r + 1) * h / rows)

            cell = Image.fromarray(keyed[y0:y1, x0:x1])
            cell = cell.resize((TARGET, TARGET), Image.LANCZOS)
            out.paste(cell, (c * TARGET, r * TARGET), cell)

        print(f'  Row {r}/{rows - 1} done')

    out.save(args.output)
    print(f'\nSaved: {args.output} ({out.size[0]}x{out.size[1]})')



def chroma_key(arr, dist, threshold=150, erode=4):
    """Remove magenta background + erode alpha edges to kill fringe."""
    out = arr.copy()
    out[dist < threshold, 3] = 0

    # Erode alpha to remove anti-aliased pink fringe
    if erode > 0:
        alpha = out[:, :, 3].astype(np.float32)
        alpha = minimum_filter(alpha, size=erode * 2 + 1)
        out[:, :, 3] = alpha.astype(np.uint8)

    return out


def trim_to_content(img, alpha_threshold=10):
    """Trim to bounding box of non-transparent pixels."""
    arr = np.array(img)
    alpha = arr[:, :, 3]
    has_content = alpha > alpha_threshold
    rows = np.any(has_content, axis=1)
    cols = np.any(has_content, axis=0)

    if not np.any(rows):
        return img

    y0 = int(np.argmax(rows))
    y1 = int(len(rows) - np.argmax(rows[::-1]))
    x0 = int(np.argmax(cols))
    x1 = int(len(cols) - np.argmax(cols[::-1]))

    return img.crop((x0, y0, x1, y1))


if __name__ == '__main__':
    main()

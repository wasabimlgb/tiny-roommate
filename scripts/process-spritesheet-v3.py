#!/usr/bin/env python3
"""
Sprite Sheet Processor V3 for Desktop Pet

This version keeps each source cell's original framing intact.
Instead of trimming and re-centering the subject, it:
1. slices a fixed grid,
2. removes only the border-connected magenta background in each cell,
3. lightly de-spills magenta edges,
4. rescales the full cell into the target output frame.

This works better for AI-generated sheets where the model already
laid out each pose intentionally inside its own cell.

Usage:
    python3 desktop-pet/scripts/process-spritesheet-v3.py INPUT.png \
      -o desktop-pet/public/sprites/tappy_cat_v2.png \
      --cols 8 --rows 9 --target 128 --name "TappyCat V2"
"""

from __future__ import annotations

import argparse
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Process a magenta-background sprite sheet")
    parser.add_argument("input", help="Input PNG/JPG sprite sheet")
    parser.add_argument("-o", "--output", required=True, help="Output PNG path")
    parser.add_argument("--name", default="Unnamed Sprite", help="Human-readable sprite name")
    parser.add_argument("--cols", type=int, default=8, help="Number of columns in source sheet")
    parser.add_argument("--rows", type=int, required=True, help="Number of rows in source sheet")
    parser.add_argument("--target", type=int, default=128, help="Output frame size in pixels")
    parser.add_argument(
        "--bg-score",
        type=float,
        default=22.0,
        help="Minimum magenta score for a pixel to count as background",
    )
    parser.add_argument(
        "--bg-gap",
        type=float,
        default=10.0,
        help="Required red/blue dominance over green for background flood fill",
    )
    parser.add_argument(
        "--bg-min-brightness",
        type=float,
        default=118.0,
        help="Minimum average red/blue brightness for a pixel to qualify as magenta background",
    )
    parser.add_argument(
        "--bg-max-rb-delta",
        type=float,
        default=90.0,
        help="Maximum allowed red/blue difference for magenta background detection",
    )
    parser.add_argument(
        "--despill-threshold",
        type=float,
        default=14.0,
        help="Minimum magenta spill score before edge cleanup kicks in",
    )
    parser.add_argument(
        "--hard-purge-score",
        type=float,
        default=24.0,
        help="Fully remove any remaining strong magenta after layout",
    )
    parser.add_argument(
        "--soft-purge-score",
        type=float,
        default=14.0,
        help="Fade medium magenta after layout to catch leftover contamination",
    )
    parser.add_argument(
        "--edge-search",
        type=int,
        default=25,
        help="Pixels to search around each nominal grid edge to find the emptiest gutter",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    img = Image.open(input_path).convert("RGBA")
    width, height = img.size
    rgb = np.array(img[:, :, :3] if isinstance(img, np.ndarray) else img)[..., :3]
    x_edges = refined_grid_edges(
        rgb,
        count=args.cols,
        axis=1,
        bg_score=args.bg_score,
        bg_gap=args.bg_gap,
        bg_min_brightness=args.bg_min_brightness,
        bg_max_rb_delta=args.bg_max_rb_delta,
        search_radius=args.edge_search,
    )
    y_edges = refined_grid_edges(
        rgb,
        count=args.rows,
        axis=0,
        bg_score=args.bg_score,
        bg_gap=args.bg_gap,
        bg_min_brightness=args.bg_min_brightness,
        bg_max_rb_delta=args.bg_max_rb_delta,
        search_radius=args.edge_search,
    )

    print(f"Name: {args.name}")
    print(f"Source: {input_path}")
    print(f"Size: {width}x{height}")
    print(f"Grid: {args.cols}x{args.rows}")
    print(f"X edges: {x_edges}")
    print(f"Y edges: {y_edges}")

    out = Image.new("RGBA", (args.cols * args.target, args.rows * args.target), (0, 0, 0, 0))

    for row in range(args.rows):
        for col in range(args.cols):
            x0, x1 = x_edges[col], x_edges[col + 1]
            y0, y1 = y_edges[row], y_edges[row + 1]
            cell = img.crop((x0, y0, x1, y1))
            processed = process_cell(
                cell,
                target=args.target,
                bg_score=args.bg_score,
                bg_gap=args.bg_gap,
                bg_min_brightness=args.bg_min_brightness,
                bg_max_rb_delta=args.bg_max_rb_delta,
                despill_threshold=args.despill_threshold,
            )
            out.alpha_composite(processed, (col * args.target, row * args.target))

        print(f"  Row {row + 1}/{args.rows} done")

    out = purge_remaining_magenta(
        out,
        hard_score=args.hard_purge_score,
        soft_score=args.soft_purge_score,
    )
    out.save(output_path)
    print(f"Saved: {output_path}")
    print(f"Output size: {out.width}x{out.height}")


def grid_edges(total: int, count: int) -> list[int]:
    return [round(i * total / count) for i in range(count + 1)]


def refined_grid_edges(
    rgb: np.ndarray,
    *,
    count: int,
    axis: int,
    bg_score: float,
    bg_gap: float,
    bg_min_brightness: float,
    bg_max_rb_delta: float,
    search_radius: int,
) -> list[int]:
    total = rgb.shape[1] if axis == 1 else rgb.shape[0]
    nominal = grid_edges(total, count)
    bg_like = background_candidate_mask(
        rgb,
        bg_score=bg_score,
        bg_gap=bg_gap,
        bg_min_brightness=bg_min_brightness,
        bg_max_rb_delta=bg_max_rb_delta,
    )
    content = ~bg_like
    density = content.sum(axis=0 if axis == 1 else 1)

    edges = [0]
    for i in range(1, count):
        center = nominal[i]
        lo = max(edges[-1] + 1, center - search_radius)
        hi = min(total - 1, center + search_radius)
        window = list(range(lo, hi + 1))
        min_density = min(int(density[idx]) for idx in window)
        candidates = [idx for idx in window if int(density[idx]) == min_density]
        best = min(candidates, key=lambda idx: abs(idx - center))
        edges.append(best)
    edges.append(total)
    return edges


def background_candidate_mask(
    rgb: np.ndarray,
    *,
    bg_score: float,
    bg_gap: float,
    bg_min_brightness: float,
    bg_max_rb_delta: float,
) -> np.ndarray:
    rgb16 = rgb.astype(np.int16)
    r = rgb16[:, :, 0]
    g = rgb16[:, :, 1]
    b = rgb16[:, :, 2]
    score = ((r + b) / 2.0) - g
    rb_mean = (r + b) / 2.0
    rb_delta = np.abs(r - b)
    return (
        (score >= bg_score)
        & ((np.minimum(r, b) - g) >= bg_gap)
        & (rb_mean >= bg_min_brightness)
        & (rb_delta <= bg_max_rb_delta)
    )


def process_cell(
    cell: Image.Image,
    *,
    target: int,
    bg_score: float,
    bg_gap: float,
    bg_min_brightness: float,
    bg_max_rb_delta: float,
    despill_threshold: float,
) -> Image.Image:
    arr = np.array(cell, dtype=np.uint8)
    bg = border_connected_background(
        arr[:, :, :3],
        bg_score=bg_score,
        bg_gap=bg_gap,
        bg_min_brightness=bg_min_brightness,
        bg_max_rb_delta=bg_max_rb_delta,
    )
    arr[bg, 3] = 0
    arr = despill_edges(arr, bg, threshold=despill_threshold)
    return Image.fromarray(arr, mode="RGBA").resize((target, target), Image.LANCZOS)


def border_connected_background(
    rgb: np.ndarray,
    *,
    bg_score: float,
    bg_gap: float,
    bg_min_brightness: float,
    bg_max_rb_delta: float,
) -> np.ndarray:
    h, w = rgb.shape[:2]
    bg = np.zeros((h, w), dtype=bool)
    queue: deque[tuple[int, int]] = deque()

    def candidate(x: int, y: int) -> bool:
        pixel = rgb[y, x].astype(np.int16)
        r, g, b = int(pixel[0]), int(pixel[1]), int(pixel[2])
        score = ((r + b) / 2.0) - g
        rb_mean = (r + b) / 2.0
        rb_delta = abs(r - b)
        return (
            score >= bg_score
            and min(r, b) - g >= bg_gap
            and rb_mean >= bg_min_brightness
            and rb_delta <= bg_max_rb_delta
        )

    def push(x: int, y: int) -> None:
        if 0 <= x < w and 0 <= y < h and not bg[y, x] and candidate(x, y):
            bg[y, x] = True
            queue.append((x, y))

    for x in range(w):
        push(x, 0)
        push(x, h - 1)
    for y in range(h):
        push(0, y)
        push(w - 1, y)

    while queue:
        x, y = queue.popleft()
        push(x + 1, y)
        push(x - 1, y)
        push(x, y + 1)
        push(x, y - 1)

    return bg


def despill_edges(arr: np.ndarray, bg: np.ndarray, *, threshold: float) -> np.ndarray:
    out = arr.copy()
    alpha = out[:, :, 3]
    fg = alpha > 0
    if not np.any(fg):
        return out

    neighbor_bg = np.zeros_like(bg)
    neighbor_bg[1:, :] |= bg[:-1, :]
    neighbor_bg[:-1, :] |= bg[1:, :]
    neighbor_bg[:, 1:] |= bg[:, :-1]
    neighbor_bg[:, :-1] |= bg[:, 1:]

    edge = fg & neighbor_bg
    if not np.any(edge):
        return out

    rgb = out[:, :, :3].astype(np.uint8)
    score = magenta_score(rgb)
    borrow = edge & ((score > threshold * 0.2) | (alpha < 235))
    if not np.any(borrow):
        return out

    clean = fg & (score < threshold * 0.45)
    out = borrow_clean_edge_colors(out, spill=borrow, clean=clean, bg=bg, threshold=threshold)

    rgb = out[:, :, :3].astype(np.uint8)
    score = magenta_score(rgb)
    spill = edge & (score > threshold * 0.5)
    amount = np.clip((score - threshold * 0.5) / 65.0, 0.0, 1.0)
    alpha_drop = np.where(amount > 0.7, 120, 42).astype(np.uint8)
    rgb16 = out[:, :, :3].astype(np.int16)
    rgb16[:, :, 0][spill] = np.maximum(rgb16[:, :, 0][spill] - (amount[spill] * 36).astype(np.int16), 0)
    rgb16[:, :, 2][spill] = np.maximum(rgb16[:, :, 2][spill] - (amount[spill] * 36).astype(np.int16), 0)
    out[:, :, :3] = rgb16.astype(np.uint8)
    new_alpha = alpha.copy()
    new_alpha[spill] = np.maximum(alpha[spill].astype(np.int16) - alpha_drop[spill].astype(np.int16), 0)
    out[:, :, 3] = new_alpha.astype(np.uint8)
    return out


def magenta_score(rgb: np.ndarray) -> np.ndarray:
    rgb16 = rgb.astype(np.int16)
    r = rgb16[:, :, 0].astype(np.float32)
    g = rgb16[:, :, 1].astype(np.float32)
    b = rgb16[:, :, 2].astype(np.float32)
    return ((r + b) / 2.0) - g


def borrow_clean_edge_colors(
    arr: np.ndarray,
    *,
    spill: np.ndarray,
    clean: np.ndarray,
    bg: np.ndarray,
    threshold: float,
) -> np.ndarray:
    out = arr.copy()
    h, w = spill.shape
    ys, xs = np.nonzero(spill)

    for y, x in zip(ys.tolist(), xs.tolist()):
        candidates: list[np.ndarray] = []
        for radius in (1, 2, 3):
            y0 = max(0, y - radius)
            y1 = min(h, y + radius + 1)
            x0 = max(0, x - radius)
            x1 = min(w, x + radius + 1)

            region_clean = clean[y0:y1, x0:x1]
            if np.any(region_clean):
                local = out[y0:y1, x0:x1, :3][region_clean]
                local_scores = magenta_score(local.reshape((-1, 1, 3))).reshape(-1)
                local = local[local_scores < threshold * 0.35]
                if len(local) > 0:
                    candidates.append(local)
                    break

        if not candidates:
            continue

        source = np.concatenate(candidates, axis=0).astype(np.float32)
        replacement = np.median(source, axis=0)
        original = out[y, x, :3].astype(np.float32)

        # Keep some local contrast while removing the magenta contamination.
        blended = replacement * 0.92 + original * 0.08
        out[y, x, :3] = np.clip(blended, 0.0, 255.0).astype(np.uint8)

        # If the edge is still hugging the keyed-out background, fade it a touch.
        if touches_background(bg, x, y):
            out[y, x, 3] = max(int(out[y, x, 3]) - 28, 0)

    return out


def touches_background(bg: np.ndarray, x: int, y: int) -> bool:
    h, w = bg.shape
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nx = x + dx
        ny = y + dy
        if 0 <= nx < w and 0 <= ny < h and bg[ny, nx]:
            return True
    return False


def purge_remaining_magenta(img: Image.Image, *, hard_score: float, soft_score: float) -> Image.Image:
    arr = np.array(img, dtype=np.uint8)
    score = magenta_score(arr[:, :, :3])
    alpha = arr[:, :, 3]
    r = arr[:, :, 0].astype(np.int16)
    b = arr[:, :, 2].astype(np.int16)
    rb_mean = (r + b) / 2.0
    rb_delta = np.abs(r - b)

    strong = (alpha > 0) & (score > hard_score) & (rb_mean > 138) & (rb_delta < 92)
    medium = (alpha > 0) & (score > soft_score) & (rb_mean > 112) & (rb_delta < 100) & (~strong)

    arr[strong, 3] = 0
    if np.any(medium):
        arr[medium, 3] = np.minimum(arr[medium, 3], 110)

    return Image.fromarray(arr, mode="RGBA")


if __name__ == "__main__":
    main()

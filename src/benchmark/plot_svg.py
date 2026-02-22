from __future__ import annotations

from html import escape
from pathlib import Path


def _nice_step(max_value: float, tick_count: int = 6) -> float:
    if max_value <= 0:
        return 1.0

    rough = max_value / tick_count
    magnitude = 10 ** int(len(str(int(rough))) - 1) if rough >= 1 else 0.1
    normalized = rough / magnitude

    if normalized <= 1:
        nice = 1
    elif normalized <= 2:
        nice = 2
    elif normalized <= 5:
        nice = 5
    else:
        nice = 10

    return nice * magnitude


def _build_y_ticks(max_value: float) -> list[float]:
    step = _nice_step(max_value)
    tick_max = step
    while tick_max < max_value:
        tick_max += step

    ticks: list[float] = []
    current = 0.0
    while current <= tick_max + (step * 0.001):
        ticks.append(round(current, 6))
        current += step

    return ticks


def _build_x_ticks(max_users: int, target_ticks: int = 8) -> list[int]:
    if max_users <= 1:
        return [1]

    step = max(1, round(max_users / target_ticks))
    ticks = list(range(1, max_users + 1, step))

    if ticks[-1] != max_users:
        ticks.append(max_users)

    return ticks


def write_latency_chart_svg(
    *,
    users: list[int],
    avg_latency_ms: list[float],
    output_path: Path,
    title: str,
    failure_index: int | None,
) -> None:
    if len(users) != len(avg_latency_ms):
        raise ValueError("users and avg_latency_ms must have the same length")

    if not users:
        raise ValueError("at least one data point is required")

    width = 1100
    height = 680
    margin_left = 90
    margin_right = 40
    margin_top = 70
    margin_bottom = 90

    chart_x = margin_left
    chart_y = margin_top
    chart_w = width - margin_left - margin_right
    chart_h = height - margin_top - margin_bottom

    x_min = min(users)
    x_max = max(users)
    y_max = max(avg_latency_ms) * 1.1
    y_ticks = _build_y_ticks(y_max)
    y_display_max = y_ticks[-1]
    x_ticks = _build_x_ticks(x_max)

    def x_to_px(x: int) -> float:
        if x_max == x_min:
            return chart_x + (chart_w / 2)
        ratio = (x - x_min) / (x_max - x_min)
        return chart_x + ratio * chart_w

    def y_to_px(y: float) -> float:
        if y_display_max <= 0:
            return chart_y + chart_h
        ratio = y / y_display_max
        return chart_y + chart_h - (ratio * chart_h)

    polyline_points = " ".join(
        f"{x_to_px(x):.2f},{y_to_px(y):.2f}" for x, y in zip(users, avg_latency_ms)
    )

    lines: list[str] = []
    lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    lines.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
    )
    lines.append(
        '<rect x="0" y="0" width="100%" height="100%" fill="#fbfbf8" stroke="#d9d9cf"/>'
    )
    lines.append(
        f'<text x="{width / 2:.0f}" y="36" text-anchor="middle" font-size="24" font-family="Georgia, serif" fill="#1f2b2d">{escape(title)}</text>'
    )

    for y_tick in y_ticks:
        y_px = y_to_px(y_tick)
        lines.append(
            f'<line x1="{chart_x}" y1="{y_px:.2f}" x2="{chart_x + chart_w}" y2="{y_px:.2f}" stroke="#e6e6de" stroke-width="1"/>'
        )
        lines.append(
            f'<text x="{chart_x - 12}" y="{y_px + 4:.2f}" text-anchor="end" font-size="12" font-family="Menlo, monospace" fill="#4f5b62">{y_tick:.0f}</text>'
        )

    for x_tick in x_ticks:
        x_px = x_to_px(x_tick)
        lines.append(
            f'<line x1="{x_px:.2f}" y1="{chart_y}" x2="{x_px:.2f}" y2="{chart_y + chart_h}" stroke="#efefe7" stroke-width="1"/>'
        )
        lines.append(
            f'<text x="{x_px:.2f}" y="{chart_y + chart_h + 24}" text-anchor="middle" font-size="12" font-family="Menlo, monospace" fill="#4f5b62">{x_tick}</text>'
        )

    lines.append(
        f'<line x1="{chart_x}" y1="{chart_y + chart_h}" x2="{chart_x + chart_w}" y2="{chart_y + chart_h}" stroke="#2f3d40" stroke-width="1.5"/>'
    )
    lines.append(
        f'<line x1="{chart_x}" y1="{chart_y}" x2="{chart_x}" y2="{chart_y + chart_h}" stroke="#2f3d40" stroke-width="1.5"/>'
    )

    lines.append(
        f'<polyline fill="none" stroke="#2a9d8f" stroke-width="3" points="{polyline_points}"/>'
    )

    for index, (x, y) in enumerate(zip(users, avg_latency_ms)):
        is_failure_point = failure_index is not None and index == failure_index
        color = "#c1121f" if is_failure_point else "#1d3557"
        radius = 6 if is_failure_point else 4
        lines.append(
            f'<circle cx="{x_to_px(x):.2f}" cy="{y_to_px(y):.2f}" r="{radius}" fill="{color}"/>'
        )

    lines.append(
        f'<text x="{chart_x + chart_w / 2:.2f}" y="{height - 26}" text-anchor="middle" font-size="14" font-family="Georgia, serif" fill="#1f2b2d">Concurrent connections</text>'
    )
    lines.append(
        f'<text x="26" y="{chart_y + chart_h / 2:.2f}" text-anchor="middle" font-size="14" font-family="Georgia, serif" fill="#1f2b2d" transform="rotate(-90 26 {chart_y + chart_h / 2:.2f})">Average response time (ms)</text>'
    )

    lines.append("</svg>")

    output_path.write_text("\n".join(lines), encoding="utf-8")

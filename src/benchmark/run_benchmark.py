from __future__ import annotations

import argparse
import asyncio
import csv
import importlib
import json
import math
import os
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from time import perf_counter
from typing import Any

import httpx


@dataclass
class RequestResult:
    latency_ms: float
    status_code: int | None
    ok: bool
    error: str | None


@dataclass
class LevelMetrics:
    users: int
    total_requests: int
    success_count: int
    failure_count: int
    error_rate_pct: float
    avg_latency_ms: float
    p95_latency_ms: float
    min_latency_ms: float
    max_latency_ms: float
    throughput_rps: float
    elapsed_seconds: float
    is_failure: bool
    failure_reasons: list[str]


@dataclass
class BenchmarkConfig:
    base_url: str
    path: str
    start_users: int
    step_users: int
    max_users: int
    requests_per_level: int
    timeout_seconds: float
    avg_latency_fail_ms: float
    p95_latency_fail_ms: float
    error_rate_fail_pct: float
    warmup_requests: int
    in_process: bool
    app_import_path: str
    allow_unfiltered_sections: bool


def _ensure_src_on_path() -> None:
    project_root = Path(__file__).resolve().parents[2]
    src_path = project_root / "src"

    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))


def _parse_app_import_path(import_path: str) -> tuple[str, str]:
    if ":" not in import_path:
        raise ValueError("app import path must look like 'module.path:app_variable'")
    module_name, app_name = import_path.split(":", 1)
    if not module_name or not app_name:
        raise ValueError("app import path must look like 'module.path:app_variable'")
    return module_name, app_name


def _load_asgi_app(import_path: str) -> Any:
    _ensure_src_on_path()
    os.environ.setdefault("ENV", "PROD")
    module_name, app_name = _parse_app_import_path(import_path)
    module = importlib.import_module(module_name)
    return getattr(module, app_name)


def _load_chart_writer() -> Any:
    module_name = "benchmark.plot_svg" if __package__ else "plot_svg"
    module = importlib.import_module(module_name)
    return module.write_latency_chart_svg


def _p95(values: list[float]) -> float:
    if not values:
        return 0.0
    sorted_values = sorted(values)
    index = max(0, math.ceil(len(sorted_values) * 0.95) - 1)
    return sorted_values[index]


def _safe_mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


async def _send_request(*, client: httpx.AsyncClient, path: str) -> RequestResult:
    start = perf_counter()
    try:
        response = await client.get(path)
        latency_ms = (perf_counter() - start) * 1000
        ok = 200 <= response.status_code < 300
        return RequestResult(
            latency_ms=latency_ms,
            status_code=response.status_code,
            ok=ok,
            error=None if ok else f"http_{response.status_code}",
        )
    except Exception as exc:
        latency_ms = (perf_counter() - start) * 1000
        return RequestResult(
            latency_ms=latency_ms,
            status_code=None,
            ok=False,
            error=type(exc).__name__,
        )


async def _run_level(
    *,
    users: int,
    total_requests: int,
    client: httpx.AsyncClient,
    path: str,
    avg_latency_fail_ms: float,
    p95_latency_fail_ms: float,
    error_rate_fail_pct: float,
) -> LevelMetrics:
    semaphore = asyncio.Semaphore(users)

    async def worker() -> RequestResult:
        async with semaphore:
            return await _send_request(client=client, path=path)

    start = perf_counter()
    tasks = [asyncio.create_task(worker()) for _ in range(total_requests)]
    results = await asyncio.gather(*tasks)
    elapsed_seconds = perf_counter() - start

    latencies = [result.latency_ms for result in results]
    success_count = sum(1 for result in results if result.ok)
    failure_count = total_requests - success_count
    error_rate_pct = (failure_count / total_requests) * 100 if total_requests else 0.0

    avg_latency_ms = _safe_mean(latencies)
    p95_latency_ms = _p95(latencies)
    min_latency_ms = min(latencies) if latencies else 0.0
    max_latency_ms = max(latencies) if latencies else 0.0
    throughput_rps = (total_requests / elapsed_seconds) if elapsed_seconds > 0 else 0.0

    failure_reasons: list[str] = []
    if avg_latency_ms > avg_latency_fail_ms:
        failure_reasons.append(
            f"average latency {avg_latency_ms:.1f}ms > {avg_latency_fail_ms:.1f}ms"
        )
    if p95_latency_ms > p95_latency_fail_ms:
        failure_reasons.append(
            f"p95 latency {p95_latency_ms:.1f}ms > {p95_latency_fail_ms:.1f}ms"
        )
    if error_rate_pct > error_rate_fail_pct:
        failure_reasons.append(
            f"error rate {error_rate_pct:.2f}% > {error_rate_fail_pct:.2f}%"
        )

    return LevelMetrics(
        users=users,
        total_requests=total_requests,
        success_count=success_count,
        failure_count=failure_count,
        error_rate_pct=error_rate_pct,
        avg_latency_ms=avg_latency_ms,
        p95_latency_ms=p95_latency_ms,
        min_latency_ms=min_latency_ms,
        max_latency_ms=max_latency_ms,
        throughput_rps=throughput_rps,
        elapsed_seconds=elapsed_seconds,
        is_failure=bool(failure_reasons),
        failure_reasons=failure_reasons,
    )


async def _build_client(
    config: BenchmarkConfig,
    users: int,
    app: Any | None,
) -> httpx.AsyncClient:
    timeout = httpx.Timeout(config.timeout_seconds)

    if config.in_process:
        if app is None:
            raise RuntimeError("in-process mode requires a loaded ASGI app")
        return httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://benchmark.local",
            timeout=timeout,
            follow_redirects=True,
        )

    limits = httpx.Limits(
        max_connections=max(100, users * 2),
        max_keepalive_connections=max(20, users),
    )
    return httpx.AsyncClient(
        base_url=config.base_url,
        timeout=timeout,
        limits=limits,
        follow_redirects=True,
    )


async def _wait_until_server_ready(config: BenchmarkConfig) -> None:
    if config.in_process:
        return

    timeout = httpx.Timeout(config.timeout_seconds)
    async with httpx.AsyncClient(base_url=config.base_url, timeout=timeout) as client:
        retries = 8
        for attempt in range(1, retries + 1):
            try:
                response = await client.get("/health")
                if response.status_code == 200:
                    return
            except Exception:
                pass

            await asyncio.sleep(min(0.4 * attempt, 2.0))

    raise RuntimeError(
        "Server is not reachable at /health. Start FastAPI first or use --in-process."
    )


def _format_row(level: LevelMetrics) -> str:
    status = "FAIL" if level.is_failure else "OK"
    return (
        f"users={level.users:>4} | avg={level.avg_latency_ms:>8.2f}ms | "
        f"p95={level.p95_latency_ms:>8.2f}ms | err={level.error_rate_pct:>6.2f}% | "
        f"rps={level.throughput_rps:>7.2f} | {status}"
    )


def _create_results_dir() -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_dir = Path(__file__).resolve().parent / "results" / timestamp
    result_dir.mkdir(parents=True, exist_ok=True)
    return result_dir


def _write_csv(levels: list[LevelMetrics], output_path: Path) -> None:
    fieldnames = [
        "users",
        "total_requests",
        "success_count",
        "failure_count",
        "error_rate_pct",
        "avg_latency_ms",
        "p95_latency_ms",
        "min_latency_ms",
        "max_latency_ms",
        "throughput_rps",
        "elapsed_seconds",
        "is_failure",
        "failure_reasons",
    ]

    with output_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

        for level in levels:
            row = asdict(level)
            row["failure_reasons"] = " | ".join(level.failure_reasons)
            writer.writerow(row)


def _write_json(
    *,
    config: BenchmarkConfig,
    levels: list[LevelMetrics],
    output_path: Path,
    started_at: str,
    ended_at: str,
) -> None:
    payload = {
        "started_at": started_at,
        "ended_at": ended_at,
        "config": asdict(config),
        "levels": [asdict(level) for level in levels],
        "failure_users": next(
            (level.users for level in levels if level.is_failure), None
        ),
    }
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


async def _run_benchmark(config: BenchmarkConfig) -> tuple[list[LevelMetrics], Path]:
    await _wait_until_server_ready(config)

    app: Any | None = None
    if config.in_process:
        app = _load_asgi_app(config.app_import_path)

    levels: list[LevelMetrics] = []

    warmup_total = max(config.warmup_requests, 0)
    if warmup_total > 0:
        async with await _build_client(
            config=config, users=1, app=app
        ) as warmup_client:
            _ = await _run_level(
                users=1,
                total_requests=warmup_total,
                client=warmup_client,
                path=config.path,
                avg_latency_fail_ms=float("inf"),
                p95_latency_fail_ms=float("inf"),
                error_rate_fail_pct=float("inf"),
            )

    users = config.start_users
    while users <= config.max_users:
        total_requests = max(config.requests_per_level, users)
        async with await _build_client(config=config, users=users, app=app) as client:
            level = await _run_level(
                users=users,
                total_requests=total_requests,
                client=client,
                path=config.path,
                avg_latency_fail_ms=config.avg_latency_fail_ms,
                p95_latency_fail_ms=config.p95_latency_fail_ms,
                error_rate_fail_pct=config.error_rate_fail_pct,
            )

        levels.append(level)
        print(_format_row(level))

        if level.is_failure:
            break

        users += config.step_users

    result_dir = _create_results_dir()
    return levels, result_dir


def _normalize_path(path: str) -> str:
    if not path:
        return "/"
    return path if path.startswith("/") else f"/{path}"


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run a concurrency ramp benchmark against the FastAPI API until latency or errors exceed thresholds."
        )
    )
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--path", default="/sections/1")

    parser.add_argument("--start-users", type=int, default=1)
    parser.add_argument("--step-users", type=int, default=5)
    parser.add_argument("--max-users", type=int, default=200)
    parser.add_argument("--requests-per-level", type=int, default=80)

    parser.add_argument("--timeout-seconds", type=float, default=12.0)
    parser.add_argument("--avg-latency-fail-ms", type=float, default=2000.0)
    parser.add_argument("--p95-latency-fail-ms", type=float, default=3500.0)
    parser.add_argument("--error-rate-fail-pct", type=float, default=5.0)
    parser.add_argument("--warmup-requests", type=int, default=5)

    parser.add_argument(
        "--in-process",
        action="store_true",
        help="Benchmark in-process ASGI app instead of an external HTTP server.",
    )
    parser.add_argument(
        "--app-import-path",
        default="api.app:app",
        help="ASGI app import path when using --in-process.",
    )
    parser.add_argument(
        "--allow-unfiltered-sections",
        action="store_true",
        help="Allow using /sections/ without query parameters.",
    )

    return parser


def _validate_config(config: BenchmarkConfig) -> None:
    if config.start_users < 1:
        raise ValueError("--start-users must be >= 1")
    if config.step_users < 1:
        raise ValueError("--step-users must be >= 1")
    if config.max_users < config.start_users:
        raise ValueError("--max-users must be >= --start-users")
    if config.requests_per_level < 1:
        raise ValueError("--requests-per-level must be >= 1")
    if config.timeout_seconds <= 0:
        raise ValueError("--timeout-seconds must be > 0")

    normalized_path = config.path.rstrip("/")
    if (
        normalized_path == "/sections"
        and "?" not in config.path
        and not config.allow_unfiltered_sections
    ):
        raise ValueError(
            "Use /sections/ with query params (for example /sections/?course=science) "
            "or use /sections/{section_id}. Pass --allow-unfiltered-sections to override."
        )


async def _async_main(config: BenchmarkConfig) -> int:
    started_at = datetime.now().isoformat(timespec="seconds")
    levels, result_dir = await _run_benchmark(config)
    ended_at = datetime.now().isoformat(timespec="seconds")

    if not levels:
        print("No benchmark levels were executed.")
        return 1

    csv_path = result_dir / "metrics.csv"
    json_path = result_dir / "metrics.json"
    svg_path = result_dir / "latency_vs_concurrency.svg"

    _write_csv(levels, csv_path)
    _write_json(
        config=config,
        levels=levels,
        output_path=json_path,
        started_at=started_at,
        ended_at=ended_at,
    )

    failure_index = next(
        (i for i, level in enumerate(levels) if level.is_failure), None
    )
    write_latency_chart_svg = _load_chart_writer()
    write_latency_chart_svg(
        users=[level.users for level in levels],
        avg_latency_ms=[level.avg_latency_ms for level in levels],
        output_path=svg_path,
        title="FastAPI benchmark: average response time vs concurrent connections",
        failure_index=failure_index,
    )

    print("")
    print(f"Saved benchmark artifacts to: {result_dir}")
    print(f"- {csv_path.name}")
    print(f"- {json_path.name}")
    print(f"- {svg_path.name}")

    if failure_index is None:
        print(
            "No failure threshold reached. Increase --max-users or tighten fail thresholds if needed."
        )
    else:
        level = levels[failure_index]
        reasons = "; ".join(level.failure_reasons)
        print(f"Failure reached at {level.users} concurrent users: {reasons}")

    return 0


def main() -> int:
    parser = _build_arg_parser()
    args = parser.parse_args()

    config = BenchmarkConfig(
        base_url=args.base_url.rstrip("/"),
        path=_normalize_path(args.path),
        start_users=args.start_users,
        step_users=args.step_users,
        max_users=args.max_users,
        requests_per_level=args.requests_per_level,
        timeout_seconds=args.timeout_seconds,
        avg_latency_fail_ms=args.avg_latency_fail_ms,
        p95_latency_fail_ms=args.p95_latency_fail_ms,
        error_rate_fail_pct=args.error_rate_fail_pct,
        warmup_requests=args.warmup_requests,
        in_process=args.in_process,
        app_import_path=args.app_import_path,
        allow_unfiltered_sections=args.allow_unfiltered_sections,
    )

    try:
        _validate_config(config)
        return asyncio.run(_async_main(config))
    except KeyboardInterrupt:
        print("Interrupted.")
        return 130
    except Exception as exc:
        print(f"Benchmark failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

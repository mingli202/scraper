# API Benchmark

This folder contains a concurrency ramp benchmark for the FastAPI backend.

## What it does

- Targets an API route (default: `GET /sections/{section_id}`)
- Starts with a small number of concurrent users
- Increases concurrency step-by-step
- Stops when the API becomes too slow (or error rate is too high)
- Exports a graph of average response time vs concurrent users

## Run against a running server (recommended)

1) Start your API server in another terminal:

```bash
fastapi run src/api/app.py --host 127.0.0.1 --port 8000
```

2) Run benchmark:

```bash
python src/benchmark/run_benchmark.py --base-url http://127.0.0.1:8000 --path /sections/1
```

## Run in-process (no external server)

```bash
python src/benchmark/run_benchmark.py --in-process --path /sections/1
```

This mode benchmarks ASGI request handling inside one Python process. It is useful for quick local checks, but external mode gives more realistic network behavior.

## Useful options

- `--start-users` (default `1`)
- `--step-users` (default `5`)
- `--max-users` (default `200`)
- `--requests-per-level` (default `80`)
- `--timeout-seconds` (default `12`)
- `--avg-latency-fail-ms` (default `2000`)
- `--p95-latency-fail-ms` (default `3500`)
- `--error-rate-fail-pct` (default `5`)

Example tuned run:

```bash
python src/benchmark/run_benchmark.py \
  --base-url http://127.0.0.1:8000 \
  --path '/sections/?course=science&domain=biology' \
  --start-users 1 \
  --step-users 10 \
  --max-users 300 \
  --requests-per-level 120
```

Note: `/sections/` without query params is blocked by default to avoid benchmarking an unrealistic full table fetch. Use query params for filtering, or benchmark `GET /sections/{section_id}`. You can bypass this guard with `--allow-unfiltered-sections`.

## Output

Each run writes artifacts to a timestamped folder:

`src/benchmark/results/YYYYMMDD_HHMMSS/`

- `metrics.csv`: per-level metrics
- `metrics.json`: full structured output + config
- `latency_vs_concurrency.svg`: graph of average response time by concurrent users

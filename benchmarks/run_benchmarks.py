"""Load & latency benchmarks for /chat.

Runs the real server (uvicorn subprocess) and measures:
  - p50/p95/p99 latency and throughput at concurrency levels 1/5/10/25
    (app-layer: deterministic LLM bypass, real retrieval + rate limiting + logging)
  - the latency cost of the RAG layer (retrieval ON vs OFF at concurrency 10)
  - burst behavior with a tight rate limit (429s vs 200s — graceful degradation)
  - optional real end-to-end latency incl. the LLM round trip (10 sequential calls, needs key)

All numbers are written to benchmarks/results/load_results.json.

Usage:
    python benchmarks/run_benchmarks.py            # app-layer + burst (+ real e2e if key)
    python benchmarks/run_benchmarks.py --skip-real
"""

import argparse
import asyncio
import json
import os
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import httpx

BENCH_DIR = Path(__file__).resolve().parent
REPO_ROOT = BENCH_DIR.parent
RESULTS_DIR = BENCH_DIR / "results"

BASE_PORT = 9101
CONCURRENCY_LEVELS = [1, 5, 10, 25]
REQUESTS_PER_WORKER = 20
BYTE_OFFSETS = {"on": 0, "off": 1, "burst": 2, "real": 3}


def percentile(values, p):
    if not values:
        return None
    s = sorted(values)
    idx = min(len(s) - 1, max(0, int(round(p / 100 * (len(s) - 1)))))
    return s[idx]


class Server:
    """Starts a real uvicorn subprocess with a project-local env file.

    The app reads settings from APP_ENV_FILE (see app/config.py); we write a
    temp env file seeded from the repo's .env plus the benchmark overrides so
    machine-wide environment variables never interfere.
    """

    def __init__(self, port: int, env_overrides: dict):
        self.port = port
        env = os.environ.copy()

        self._tmpdir = tempfile.mkdtemp(prefix="vlab_bench_")
        self._env_path = os.path.join(self._tmpdir, ".env")
        self._write_env_file(env_overrides)
        env["APP_ENV_FILE"] = self._env_path

        self.proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "chatbot:app",
             "--host", "127.0.0.1", "--port", str(port), "--log-level", "warning"],
            cwd=str(REPO_ROOT), env=env,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        self.base = f"http://127.0.0.1:{port}"

    def _write_env_file(self, overrides: dict):
        lines = []
        repo_env = REPO_ROOT / ".env"
        if repo_env.exists():
            lines = repo_env.read_text(encoding="utf-8").splitlines()
        merged = {}
        for line in lines:
            if "=" in line and not line.strip().startswith("#"):
                k, _, v = line.partition("=")
                merged[k.strip()] = v.strip()
        merged.update(overrides)
        Path(self._env_path).write_text(
            "\n".join(f"{k}={v}" for k, v in merged.items()), encoding="utf-8"
        )

    def wait_ready(self, timeout: float = 60.0) -> bool:
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self.proc.poll() is not None:
                return False
            try:
                r = httpx.get(f"{self.base}/healthz", timeout=2.0)
                if r.status_code == 200:
                    return True
            except Exception:
                pass
            time.sleep(0.3)
        return False

    def stop(self):
        if self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.proc.kill()
        shutil.rmtree(self._tmpdir, ignore_errors=True)


def make_payload():
    return {
        "message": "How do I balance a centrifuge rotor before starting a run?",
        "has_used_before": True,
        "conversation_history": [],
    }


async def run_round(server: Server, concurrency: int, n_per_worker: int):
    latencies: list[float] = []
    statuses: dict[int, int] = {}

    async def worker():
        async with httpx.AsyncClient(timeout=60.0) as client:
            for _ in range(n_per_worker):
                t0 = time.perf_counter()
                try:
                    r = await client.post(f"{server.base}/chat", json=make_payload())
                    latencies.append((time.perf_counter() - t0) * 1000)
                    statuses[r.status_code] = statuses.get(r.status_code, 0) + 1
                except Exception:
                    statuses[-1] = statuses.get(-1, 0) + 1

    await asyncio.gather(*(worker() for _ in range(concurrency)))
    return latencies, statuses


def summarize(label, latencies, statuses, total_time=None):
    ok = statuses.get(200, 0)
    limited = statuses.get(429, 0)
    errors = sum(v for k, v in statuses.items() if k not in (200, 429))
    out = {
        "label": label,
        "requests_200": ok,
        "requests_429": limited,
        "requests_error": errors,
        "p50_ms": percentile(latencies, 50),
        "p95_ms": percentile(latencies, 95),
        "p99_ms": percentile(latencies, 99),
        "mean_ms": round(statistics.fmean(latencies), 2) if latencies else None,
        "n_latencies": len(latencies),
    }
    if total_time and total_time > 0:
        out["throughput_req_s"] = round((ok + limited + errors) / total_time, 2)
    return out


async def throughput_suite(port_offset: int, retrieval_enabled: bool,
                           rate_limit: int, label: str):
    port = BASE_PORT + port_offset
    server = Server(port, {
        "BENCHMARK_BYPASS_LLM": "true",
        "RATE_LIMIT_PER_MINUTE": str(rate_limit),
        "RETRIEVAL_ENABLED": "true" if retrieval_enabled else "false",
        "CHROMA_DIR": str(REPO_ROOT / "chroma_db"),
    })
    results = []
    try:
        if not server.wait_ready():
            print(f"[warn] server on {port} failed to start")
            return results
        # warm up (loads embedder on first call)
        httpx.post(f"{server.base}/chat", json=make_payload(), timeout=120.0)
        for concurrency in CONCURRENCY_LEVELS:
            t0 = time.perf_counter()
            latencies, statuses = await run_round(server, concurrency, REQUESTS_PER_WORKER)
            elapsed = time.perf_counter() - t0
            row = summarize(f"{label} c={concurrency}", latencies, statuses, elapsed)
            results.append(row)
            print(f"  {row['label']}: p50={row['p50_ms']} p95={row['p95_ms']} "
                  f"p99={row['p99_ms']} 200s={row['requests_200']} 429s={row['requests_429']}")
    finally:
        server.stop()
    return results


async def burst_suite(port_offset: int, rate_limit: int):
    port = BASE_PORT + port_offset
    server = Server(port, {
        "BENCHMARK_BYPASS_LLM": "true",
        "RATE_LIMIT_PER_MINUTE": str(rate_limit),
        "RETRIEVAL_ENABLED": "true",
        "CHROMA_DIR": str(REPO_ROOT / "chroma_db"),
    })
    try:
        if not server.wait_ready():
            print("[warn] burst server failed to start")
            return None
        httpx.post(f"{server.base}/chat", json=make_payload(), timeout=120.0)
        # 60 requests at once against a 30/min limit
        t0 = time.perf_counter()
        latencies, statuses = await run_round(server, 30, 2)
        elapsed = time.perf_counter() - t0
        row = summarize(f"burst limit={rate_limit}/min, 60 requests", latencies, statuses, elapsed)
        print(f"  {row['label']}: 200s={row['requests_200']} 429s={row['requests_429']} "
              f"errors={row['requests_error']}")
        return row
    finally:
        server.stop()


async def real_e2e_suite(port_offset: int):
    """Sequential real end-to-end calls including the LLM round trip."""
    port = BASE_PORT + port_offset
    server = Server(port, {
        "BENCHMARK_BYPASS_LLM": "false",
        "RATE_LIMIT_PER_MINUTE": "60",
        "RETRIEVAL_ENABLED": "true",
        "CHROMA_DIR": str(REPO_ROOT / "chroma_db"),
    })
    try:
        if not server.wait_ready():
            print("[warn] e2e server failed to start")
            return None
        latencies = []
        statuses = {}
        async with httpx.AsyncClient(timeout=120.0) as client:
            for _ in range(10):
                t0 = time.perf_counter()
                r = await client.post(f"{server.base}/chat", json=make_payload())
                latencies.append((time.perf_counter() - t0) * 1000)
                statuses[r.status_code] = statuses.get(r.status_code, 0) + 1
                if statuses.get(200, 0) % 3 == 0:
                    await asyncio.sleep(1.0)  # stay under provider RPM
        row = summarize("e2e real LLM (n=10 sequential)", latencies, statuses)
        print(f"  {row['label']}: p50={row['p50_ms']} p95={row['p95_ms']} "
              f"mean={row['mean_ms']} 200s={row['requests_200']}")
        return row
    finally:
        server.stop()


async def main_async(skip_real: bool):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    all_rows = []

    print("== Throughput: retrieval ON (app-layer, LLM bypass) ==")
    all_rows += await throughput_suite(BYTE_OFFSETS["on"], True, 100000, "retrieval=on")

    print("== Throughput: retrieval OFF (app-layer, LLM bypass) ==")
    all_rows += await throughput_suite(BYTE_OFFSETS["off"], False, 100000, "retrieval=off")

    print("== Burst behavior under tight rate limit ==")
    burst_row = await burst_suite(BYTE_OFFSETS["burst"], 30)
    if burst_row:
        all_rows.append(burst_row)

    real_row = None
    if not skip_real:
        print("== Real end-to-end (LLM round trip) ==")
        real_row = await real_e2e_suite(BYTE_OFFSETS["real"])
        if real_row:
            all_rows.append(real_row)

    payload = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "method": (
            "uvicorn subprocess on 127.0.0.1; app-layer rows use BENCHMARK_BYPASS_LLM=true "
            "(deterministic response after rate limit + retrieval + logging); real e2e rows "
            "include the LLM round trip."
        ),
        "concurrency_levels": CONCURRENCY_LEVELS,
        "requests_per_worker": REQUESTS_PER_WORKER,
        "rows": all_rows,
    }
    (RESULTS_DIR / "load_results.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )
    print(f"\nWrote {RESULTS_DIR / 'load_results.json'}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-real", action="store_true")
    args = parser.parse_args()
    asyncio.run(main_async(args.skip_real))


if __name__ == "__main__":
    main()

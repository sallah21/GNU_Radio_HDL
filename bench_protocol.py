#!/usr/bin/env python3
import argparse
import os
import sys
import time
import statistics
from typing import List, Tuple
import builtins

# Ensure we can import OOT_HDL from this repo
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
PY_ROOT = os.path.join(THIS_DIR, 'gr-OOT_HDL', 'python')
if PY_ROOT not in sys.path:
    sys.path.insert(0, PY_ROOT)

from OOT_HDL.model_class import model as HDLModel  # type: ignore
from OOT_HDL.verilog_parser import port_type  # type: ignore


def gen_vectors(ports, steps: int, seed: int = 0) -> List[List[int]]:
    """Generate deterministic input vectors for the given ports.
    Values are small integers mod 2**width to avoid overflow.
    """
    vecs: List[List[int]] = []
    inp = [p for p in ports if p.type != port_type.OUT]
    widths = [max(1, getattr(p, 'size', 32)) for p in inp]
    masks = [(1 << min(31, w)) - 1 for w in widths]  # cap to 31 bits for safety

    for i in range(steps):
        row = []
        for j, m in enumerate(masks):
            val = (seed + i + j * 17) & m
            row.append(int(val))
        vecs.append(row)
    return vecs


def percentiles(samples: List[float]) -> dict:
    if not samples:
        return {}
    s = sorted(samples)
    n = len(s)
    def pct(p):
        if n == 1:
            return s[0]
        k = max(0, min(n - 1, int(round(p * (n - 1)))))
        return s[k]
    return {
        'p50': pct(0.50),
        'p90': pct(0.90),
        'p99': pct(0.99),
    }


def bench_run(m: HDLModel, vectors: List[List[int]], warmup: int) -> Tuple[List[float], dict]:
    """Run warmup then measure per-step time for provided vectors using model.run_model()."""
    # Warm-up
    for v in vectors[:warmup]:
        try:
            _ = m.run_model(v)
        except Exception:
            pass

    # Measure
    times: List[float] = []
    start_overall = time.perf_counter()
    for v in vectors[warmup:]:
        t0 = time.perf_counter()
        _ = m.run_model(v)
        t1 = time.perf_counter()
        times.append(t1 - t0)
    end_overall = time.perf_counter()

    # Return both step times and aggregated stats (bytes/lines)
    stats = m.get_stats() if hasattr(m, 'get_stats') else {}
    stats['elapsed_total'] = end_overall - start_overall
    stats['measured_steps'] = max(0, len(vectors) - warmup)
    return times, stats


def main():
    ap = argparse.ArgumentParser(description='Benchmark protocol overhead per step (legacy vs handle).')
    ap.add_argument('--hdl', required=True, help='Path to HDL file (e.g., multiplier.v)')
    ap.add_argument('--outdir', default=os.path.join(THIS_DIR, 'gr-OOT_HDL', 'python', 'OOT_HDL'), help='Output dir where wrapper/testbench are written')
    ap.add_argument('--steps', type=int, default=1000, help='Total steps (including warmup)')
    ap.add_argument('--warmup', type=int, default=100, help='Warmup steps (excluded from stats)')
    ap.add_argument('--seed', type=int, default=0, help='Seed for deterministic inputs')
    ap.add_argument('--mode_order', choices=['handle_first', 'legacy_first'], default='handle_first')
    ap.add_argument('--quiet', action='store_true', help='Suppress verbose prints from model_class during measurement')
    args = ap.parse_args()

    # Build and compile once
    m = HDLModel(args.hdl, args.outdir)
    m.parse_model()
    # Guard against None params in compile step
    if getattr(m, 'params', None) is None:
        m.params = []
    m.generate_wrapper()
    m.dump_wrapper()
    m.compile_model()

    # Prepare inputs once and reuse across modes
    vectors = gen_vectors(m.ports, args.steps, args.seed)

    def run_mode(use_handles: bool):
        # Reset stats per mode
        if hasattr(m, 'stats') and isinstance(m.stats, dict):
            m.stats.clear()
            m.stats.update({'bytes_in': 0, 'lines_in': 0, 'bytes_out': 0, 'lines_out': 0})
        m.prefer_handles = bool(use_handles)
        # Optionally silence prints while the subprocess + threads run
        restore_print = None
        if args.quiet:
            restore_print = builtins.print
            builtins.print = lambda *a, **k: None
        try:
            m.start_process()
            # If handshake failed, m.use_handles may be False
            if use_handles and not getattr(m, 'use_handles', False):
                if restore_print:
                    builtins.print = restore_print
                    restore_print = None
                print('[warn] Handle handshake failed; falling back to legacy for this run.')
            times, stats = bench_run(m, vectors, args.warmup)
        finally:
            m.stop_process()
            if restore_print:
                builtins.print = restore_print
        return times, stats

    modes = [('handle', True), ('legacy', False)] if args.mode_order == 'handle_first' else [('legacy', False), ('handle', True)]
    results = []

    for name, flag in modes:
        print(f"\n=== Running mode: {name} ===")
        times, stats = run_mode(flag)
        if times:
            n = len(times)
            tot = sum(times)
            mean = tot / n
            pct = percentiles(times)
            thr = n / tot if tot > 0 else 0.0
            print(f"steps: {n}")
            print(f"mean_step_s: {mean:.6e}")
            print(f"median_s: {pct.get('p50', 0):.6e}")
            print(f"p90_s: {pct.get('p90', 0):.6e}")
            print(f"p99_s: {pct.get('p99', 0):.6e}")
            print(f"min_s: {min(times):.6e}")
            print(f"max_s: {max(times):.6e}")
            print(f"throughput_steps_per_s: {thr:.2f}")
        else:
            print("No measurements collected.")
        if stats:
            ms = stats.get('measured_steps', max(1, len(times)))
            print("bytes_out_total:", stats.get('bytes_out', 'n/a'))
            print("bytes_in_total:", stats.get('bytes_in', 'n/a'))
            print("lines_out_total:", stats.get('lines_out', 'n/a'))
            print("lines_in_total:", stats.get('lines_in', 'n/a'))
            try:
                print("bytes_out_per_step:", stats['bytes_out'] / ms)
                print("bytes_in_per_step:", stats['bytes_in'] / ms)
                print("lines_out_per_step:", stats['lines_out'] / ms)
                print("lines_in_per_step:", stats['lines_in'] / ms)
            except Exception:
                pass
        results.append((name, times, stats))

    print("\n=== Summary ===")
    for name, times, stats in results:
        if times:
            tot = sum(times)
            thr = len(times) / tot if tot > 0 else 0.0
        else:
            thr = 0.0
        print(f"{name}: steps={len(times)}, throughput={thr:.2f} steps/s, bytes_out={stats.get('bytes_out','n/a')}, bytes_in={stats.get('bytes_in','n/a')}")


if __name__ == '__main__':
    main()

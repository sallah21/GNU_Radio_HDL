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


def compute_breakdown(tr: dict) -> dict:
    """Compute per-step timing breakdown from a trace dict produced by model_class."""
    out: dict = {}
    g = tr.get
    def dur(a: str, b: str):
        ta, tb = g(a), g(b)
        return (tb - ta) if (ta is not None and tb is not None) else None
    # Queueing and input write
    out['queue_wait_s'] = dur('t_enqueued', 't_input_dequeued')
    # Handle vs legacy write
    if g('t_setb_sent') is not None and g('t_input_write_start') is not None:
        out['input_write_s'] = g('t_setb_sent') - g('t_input_write_start')
    elif g('t_legacy_sent') is not None and g('t_input_write_start') is not None:
        out['input_write_s'] = g('t_legacy_sent') - g('t_input_write_start')
    else:
        out['input_write_s'] = None
    # STEP send (handles path)
    if g('t_step_sent') is not None and g('t_setb_sent') is not None:
        out['step_send_s'] = g('t_step_sent') - g('t_setb_sent')
    else:
        out['step_send_s'] = None
    # Device/model to first output line arrival
    base = g('t_step_sent') if g('t_step_sent') is not None else g('t_legacy_sent')
    out['model_to_output_s'] = (g('t_output_received') - base) if (base is not None and g('t_output_received') is not None) else None
    # Output queueing and delivery to consumer
    out['output_queue_s'] = dur('t_output_received', 't_output_queued')
    out['output_dequeue_wait_s'] = dur('t_output_queued', 't_output_dequeued')
    out['notify_set_s'] = dur('t_output_dequeued', 't_data_ready_set')
    out['wait_unblock_s'] = dur('t_data_ready_set', 't_data_ready_unblocked')
    # End-to-end
    out['run_total_s'] = dur('t_run_start', 't_run_end')
    return out


def aggregate_breakdowns(breakdowns: List[dict]) -> dict:
    keys = ['queue_wait_s','input_write_s','step_send_s','model_to_output_s','output_queue_s','output_dequeue_wait_s','notify_set_s','wait_unblock_s','run_total_s']
    agg = {}
    for k in keys:
        vals = [b[k] for b in breakdowns if b.get(k) is not None]
        if not vals:
            agg[k] = {'count': 0}
            continue
        pct = percentiles(vals)
        agg[k] = {
            'count': len(vals),
            'mean': sum(vals) / len(vals),
            'p50': pct.get('p50', 0.0),
            'p90': pct.get('p90', 0.0),
            'p99': pct.get('p99', 0.0),
            'min': min(vals),
            'max': max(vals),
        }
    return agg


def bench_run(m: HDLModel, vectors: List[List[int]], warmup: int) -> Tuple[List[float], dict, List[dict]]:
    """Run warmup then measure per-step time for provided vectors using model.run_model(), collecting per-step breakdowns."""
    # Enable per-step tracing
    if hasattr(m, 'enable_step_trace'):
        m.enable_step_trace(True)

    # Warm-up
    for v in vectors[:warmup]:
        try:
            _ = m.run_model(v)
        except Exception:
            pass

    # Measure
    times: List[float] = []
    breakdowns: List[dict] = []
    start_overall = time.perf_counter()
    for v in vectors[warmup:]:
        t0 = time.perf_counter()
        _ = m.run_model(v)
        t1 = time.perf_counter()
        times.append(t1 - t0)
        # Capture breakdown
        if hasattr(m, 'get_last_trace'):
            tr = m.get_last_trace()
            if isinstance(tr, dict) and tr:
                breakdowns.append(compute_breakdown(tr))
    end_overall = time.perf_counter()

    # Return both step times and aggregated stats (bytes/lines)
    stats = m.get_stats() if hasattr(m, 'get_stats') else {}
    stats['elapsed_total'] = end_overall - start_overall
    stats['measured_steps'] = max(0, len(vectors) - warmup)
    return times, stats, breakdowns


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
        # Prepare handle vs legacy mode (clear prior handshake state for legacy)
        m.prefer_handles = bool(use_handles)
        if not use_handles:
            try:
                m.use_handles = False
                if hasattr(m, 'name_to_id'):
                    m.name_to_id.clear()
                if hasattr(m, 'id_to_meta'):
                    m.id_to_meta.clear()
                if hasattr(m, 'handshake_done'):
                    m.handshake_done.clear()
                if hasattr(m, '_hello_ok'):
                    m._hello_ok = False
                if hasattr(m, '_bind_expected'):
                    m._bind_expected = None
                if hasattr(m, '_bind_received'):
                    m._bind_received = 0
            except Exception:
                pass
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
            times, stats, breakdowns = bench_run(m, vectors, args.warmup)
        finally:
            m.stop_process()
            if restore_print:
                builtins.print = restore_print
        return times, stats, breakdowns

    modes = [('handle', True), ('legacy', False)] if args.mode_order == 'handle_first' else [('legacy', False), ('handle', True)]
    results = []

    for name, flag in modes:
        print(f"\n=== Running mode: {name} ===")
        times, stats, breakdowns = run_mode(flag)
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
            # Breakdown summary (converted to microseconds for readability)
            agg = aggregate_breakdowns(breakdowns)
            def fmt_us(x):
                return f"{(x*1e6):.1f}" if isinstance(x, (int, float)) else "n/a"
            def p(field, label=None):
                a = agg.get(field, {})
                if not a or a.get('count', 0) == 0:
                    print(f"{label or field}: n/a")
                    return
                print(f"{label or field}: mean_us={fmt_us(a['mean'])}, p50_us={fmt_us(a['p50'])}, p90_us={fmt_us(a['p90'])}, p99_us={fmt_us(a['p99'])}")
            print("breakdown:")
            p('queue_wait_s', 'queue_wait')
            p('input_write_s', 'input_write')
            p('step_send_s', 'step_send')
            p('model_to_output_s', 'model_to_output')
            p('output_queue_s', 'output_queue')
            p('output_dequeue_wait_s', 'output_dequeue_wait')
            p('notify_set_s', 'notify_set')
            p('wait_unblock_s', 'wait_unblock')
            p('run_total_s', 'run_total')
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

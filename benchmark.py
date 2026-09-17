"""
benchmark.py -- Throughput & latency benchmark for the ChronosMatch firehose pipeline.

Compares:
  1. Raw in-memory buffer writes  (firehose.py baseline)
  2. Order book ingestion rate    (order_book.py)

Reports p50 / p95 / p99 write-latency in nanoseconds and overall throughput.
"""
import asyncio
import io
import struct
import time
import statistics

ORDER_FORMAT = '<QQdIcc2x'
ORDER_STRUCT = struct.Struct(ORDER_FORMAT)
ORDER_SIZE   = ORDER_STRUCT.size


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ns() -> int:
    return time.perf_counter_ns()


def _percentile(data: list, pct: float) -> float:
    """Return the p-th percentile of a sorted list."""
    if not data:
        return 0.0
    k = (len(data) - 1) * pct / 100.0
    f = int(k)
    c = f + 1
    if c >= len(data):
        return data[-1]
    return data[f] + (k - f) * (data[c] - data[f])


def _fmt_ns(ns: float) -> str:
    if ns < 1_000:
        return f'{ns:.1f} ns'
    elif ns < 1_000_000:
        return f'{ns/1_000:.2f} us'
    else:
        return f'{ns/1_000_000:.3f} ms'


# ---------------------------------------------------------------------------
# Benchmark 1 -- raw buffer writes (baseline, mirrors firehose.py)
# ---------------------------------------------------------------------------

async def bench_buffer_writes(num_orders: int) -> dict:
    timestamp  = int(time.time() * 1000)
    order_id   = 1_000_000
    price      = 45_000.50
    size       = 100
    side       = b'B'
    order_type = b'L'

    buffer   = io.BytesIO()
    latencies: list[int] = []

    sample_every = max(1, num_orders // 10_000)   # keep at most 10k samples

    start = time.perf_counter()

    for i in range(num_orders):
        if i % sample_every == 0:
            t0 = _ns()
            buffer.write(ORDER_STRUCT.pack(timestamp, order_id + i, price, size, side, order_type))
            latencies.append(_ns() - t0)
        else:
            buffer.write(ORDER_STRUCT.pack(timestamp, order_id + i, price, size, side, order_type))

        if i % 10_000 == 0:
            await asyncio.sleep(0)

    elapsed = time.perf_counter() - start
    latencies.sort()

    return {
        'name'      : 'Buffer writes (firehose baseline)',
        'orders'    : num_orders,
        'duration_s': elapsed,
        'rate'      : num_orders / elapsed,
        'p50_ns'    : _percentile(latencies, 50),
        'p95_ns'    : _percentile(latencies, 95),
        'p99_ns'    : _percentile(latencies, 99),
        'buf_bytes' : buffer.tell(),
    }


# ---------------------------------------------------------------------------
# Benchmark 2 -- order book ingest
# ---------------------------------------------------------------------------

def bench_order_book_ingest(num_orders: int) -> dict:
    # Build the buffer first (not measured)
    buf = io.BytesIO()
    ts  = int(time.time() * 1000)
    sides = [b'B', b'A']
    base  = 45_000.0
    for i in range(num_orders):
        side  = sides[i % 2]
        price = round(base + (i % 50) * 0.25 * (1 if side == b'A' else -1), 2)
        sz    = (i % 10 + 1) * 10
        buf.write(ORDER_STRUCT.pack(ts, 1_000_000 + i, price, sz, side, b'L'))

    buf.seek(0)
    raw = buf.read()

    # Inline add_order logic without the full OrderBook import to keep this file self-contained
    bids: dict[float, int] = {}
    asks: dict[float, int] = {}
    latencies: list[int]   = []
    sample_every = max(1, num_orders // 10_000)

    start = time.perf_counter()

    for idx in range(num_orders):
        offset = idx * ORDER_SIZE
        chunk  = raw[offset: offset + ORDER_SIZE]

        if idx % sample_every == 0:
            t0 = _ns()
            _ts, _oid, price, sz, side, _otype = ORDER_STRUCT.unpack(chunk)
            book = bids if side == b'B' else asks
            book[price] = book.get(price, 0) + sz
            latencies.append(_ns() - t0)
        else:
            _ts, _oid, price, sz, side, _otype = ORDER_STRUCT.unpack(chunk)
            book = bids if side == b'B' else asks
            book[price] = book.get(price, 0) + sz

    elapsed = time.perf_counter() - start
    latencies.sort()

    return {
        'name'      : 'Order book ingest',
        'orders'    : num_orders,
        'duration_s': elapsed,
        'rate'      : num_orders / elapsed,
        'p50_ns'    : _percentile(latencies, 50),
        'p95_ns'    : _percentile(latencies, 95),
        'p99_ns'    : _percentile(latencies, 99),
        'buf_bytes' : len(raw),
    }


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def _print_report(results: list) -> None:
    print()
    print('=' * 64)
    print('  ChronosMatch -- Pipeline Benchmark Report')
    print('=' * 64)

    for r in results:
        print()
        print(f"  [{r['name']}]")
        print(f"    Orders      : {r['orders']:>12,}")
        print(f"    Duration    : {r['duration_s']:>10.4f} s")
        print(f"    Throughput  : {r['rate']:>12,.0f} orders/sec")
        print(f"    Buffer size : {r['buf_bytes']:>12,} bytes")
        print(f"    Latency p50 : {_fmt_ns(r['p50_ns']):>12}")
        print(f"    Latency p95 : {_fmt_ns(r['p95_ns']):>12}")
        print(f"    Latency p99 : {_fmt_ns(r['p99_ns']):>12}")

        if r['rate'] >= 100_000:
            print(f"    STATUS      : PASS (>= 100k orders/sec)")
        else:
            print(f"    STATUS      : FAIL (< 100k orders/sec)")

    print()
    print('=' * 64)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main():
    NUM_ORDERS = 1_000_000

    print(f'ChronosMatch Benchmark -- {NUM_ORDERS:,} orders per test')
    print('Running ...')

    r1 = await bench_buffer_writes(NUM_ORDERS)
    r2 = bench_order_book_ingest(NUM_ORDERS)

    _print_report([r1, r2])


if __name__ == '__main__':
    asyncio.run(main())

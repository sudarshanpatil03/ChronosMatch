# ChronosMatch

High-throughput market-data pipeline spike — async Python, binary-packed order structs, in-memory order book.

## Architecture

```
[firehose.py]         -- Async writer: packs binary order structs into io.BytesIO at 1M+ writes/sec
[ipc_firehose.py]     -- Network layer: blasts the same struct stream over a loopback TCP socket (IPC bus)
[order_book.py]       -- Consumer: ingests the binary buffer into a price-level aggregated order book
[benchmark.py]        -- Harness: measures throughput (orders/sec) and p50/p95/p99 write latency
```

## Order Struct Layout

| Field       | Type   | Size   | Description                    |
|-------------|--------|--------|--------------------------------|
| timestamp   | uint64 | 8 B    | Unix epoch milliseconds        |
| order_id    | uint64 | 8 B    | Unique order identifier        |
| price       | double | 8 B    | Limit price                    |
| size        | uint32 | 4 B    | Order quantity                 |
| side        | char   | 1 B    | 'B' = Bid, 'A' = Ask           |
| order_type  | char   | 1 B    | 'L' = Limit, 'M' = Market      |
| _padding    | 2 B    | 2 B    | Struct alignment               |

**Total: 32 bytes / order** (little-endian, `struct` format `<QQdIcc2x`)

## Quick Start

```bash
# 1. Run the baseline firehose (1M orders -> in-memory buffer)
python firehose.py

# 2. Run the IPC firehose (streams orders over loopback TCP)
python ipc_firehose.py

# 3. Ingest a buffer into the order book
python order_book.py

# 4. Run the full benchmark (throughput + latency percentiles)
python benchmark.py
```

## Performance Targets

| Metric       | Target       |
|--------------|--------------|
| Throughput   | >= 100k orders/sec |
| p99 latency  | < 10 µs      |

## Week 1 Progress

| Day | Commit | What was built |
|-----|--------|----------------|
| Mon | `firehose.py`     | Async binary-write loop; proved 1M+ writes/sec to BytesIO |
| Tue | `ipc_firehose.py` | TCP socket layer; mock IPC bus receiver with per-second throughput reporting |
| Wed | `order_book.py`   | Price-level order book; ingests binary buffer, exposes best bid/ask, spread, depth |
| Thu | `benchmark.py`    | Unified benchmark harness; p50/p95/p99 latency + throughput for each pipeline stage |
| Fri | `README.md`       | Architecture docs, struct layout table, quick-start guide, performance targets |

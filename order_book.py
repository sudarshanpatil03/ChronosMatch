import struct
import io
import time
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

ORDER_FORMAT = '<QQdIcc2x'
ORDER_STRUCT = struct.Struct(ORDER_FORMAT)
ORDER_SIZE   = ORDER_STRUCT.size

SIDE_BID = b'B'
SIDE_ASK = b'A'


@dataclass
class PriceLevel:
    price:      float
    total_size: int = 0
    order_ids:  List[int] = field(default_factory=list)

    def add(self, order_id: int, size: int) -> None:
        self.order_ids.append(order_id)
        self.total_size += size

    def remove(self, order_id: int, size: int) -> None:
        if order_id in self.order_ids:
            self.order_ids.remove(order_id)
            self.total_size -= size


class OrderBook:
    """
    In-memory limit order book backed by sorted price levels.
    Bids  -- sorted descending (best bid = highest price)
    Asks  -- sorted ascending  (best ask = lowest price)
    """

    def __init__(self) -> None:
        self._bids: Dict[float, PriceLevel] = {}
        self._asks: Dict[float, PriceLevel] = {}
        self._orders: Dict[int, Tuple[float, str, int]] = {}
        self.total_orders = 0
        self.rejected     = 0

    def add_order(self, order_id: int, price: float, size: int, side: bytes) -> None:
        if size <= 0 or price <= 0:
            self.rejected += 1
            return
        side_str = 'B' if side == SIDE_BID else 'A'
        book = self._bids if side == SIDE_BID else self._asks
        if price not in book:
            book[price] = PriceLevel(price)
        book[price].add(order_id, size)
        self._orders[order_id] = (price, side_str, size)
        self.total_orders += 1

    def cancel_order(self, order_id: int) -> bool:
        if order_id not in self._orders:
            return False
        price, side_str, size = self._orders.pop(order_id)
        book = self._bids if side_str == 'B' else self._asks
        if price in book:
            book[price].remove(order_id, size)
            if book[price].total_size == 0:
                del book[price]
        return True

    def best_bid(self):
        if not self._bids:
            return None
        price = max(self._bids)
        return (price, self._bids[price].total_size)

    def best_ask(self):
        if not self._asks:
            return None
        price = min(self._asks)
        return (price, self._asks[price].total_size)

    def spread(self):
        bid = self.best_bid()
        ask = self.best_ask()
        if bid is None or ask is None:
            return None
        return ask[0] - bid[0]

    def depth(self, levels: int = 5) -> dict:
        sorted_bids = sorted(self._bids.keys(), reverse=True)[:levels]
        sorted_asks = sorted(self._asks.keys())[:levels]
        return {
            'bids': [(p, self._bids[p].total_size) for p in sorted_bids],
            'asks': [(p, self._asks[p].total_size) for p in sorted_asks],
        }

    def ingest_buffer(self, buffer: io.BytesIO) -> int:
        """Parse every binary-packed order from a firehose buffer."""
        buffer.seek(0)
        raw = buffer.read()
        ingested = 0
        for offset in range(0, len(raw) - ORDER_SIZE + 1, ORDER_SIZE):
            chunk = raw[offset: offset + ORDER_SIZE]
            ts, order_id, price, size, side, order_type = ORDER_STRUCT.unpack(chunk)
            self.add_order(order_id, price, size, side)
            ingested += 1
        return ingested


def _build_demo_buffer(num_orders: int = 500_000) -> io.BytesIO:
    """Generate a mixed bid/ask firehose buffer for demonstration."""
    buf = io.BytesIO()
    ts         = int(time.time() * 1000)
    sides      = [b'B', b'A']
    base_price = 45_000.0
    for i in range(num_orders):
        side  = sides[i % 2]
        price = round(base_price + (i % 50) * 0.25 * (1 if side == b'A' else -1), 2)
        size  = (i % 10 + 1) * 10
        buf.write(ORDER_STRUCT.pack(ts, 1_000_000 + i, price, size, side, b'L'))
    return buf


if __name__ == '__main__':
    print('Building demo buffer ...')
    buf = _build_demo_buffer(500_000)

    book = OrderBook()
    print('Ingesting buffer into order book ...')

    t0      = time.perf_counter()
    count   = book.ingest_buffer(buf)
    elapsed = time.perf_counter() - t0

    rate = count / elapsed
    print()
    print('--- Order Book Stats ---')
    print(f'Orders ingested : {count:,}')
    print(f'Ingest time     : {elapsed:.4f}s  ({rate:,.0f} orders/sec)')
    print(f'Rejected        : {book.rejected}')
    print(f'Best bid        : {book.best_bid()}')
    print(f'Best ask        : {book.best_ask()}')
    print(f'Spread          : {book.spread()}')
    print()
    print('Top-5 Depth:')
    depth = book.depth(5)
    print('  BIDS:')
    for p, s in depth['bids']:
        print(f'    {p:10.2f}  x  {s:8,}')
    print('  ASKS:')
    for p, s in depth['asks']:
        print(f'    {p:10.2f}  x  {s:8,}')

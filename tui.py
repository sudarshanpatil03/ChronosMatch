import curses
import time
import random
from order_book import OrderBook, SIDE_BID, SIDE_ASK

def init_colors():
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_GREEN, -1) # Bids
    curses.init_pair(2, curses.COLOR_RED, -1)   # Asks
    curses.init_pair(3, curses.COLOR_CYAN, -1)  # Headers/Stats

def setup_curses(stdscr):
    curses.curs_set(0) # Hide cursor
    stdscr.nodelay(1)  # Non-blocking getch
    init_colors()

def simulate_market_activity(book: OrderBook, order_id_counter: int) -> int:
    """Generate 100-500 random orders to simulate live market."""
    num_orders = random.randint(100, 500)
    for _ in range(num_orders):
        side = SIDE_BID if random.random() > 0.5 else SIDE_ASK
        price = round(45000.0 + random.uniform(-10, 10), 2)
        size = random.randint(1, 10) * 10
        book.add_order(order_id_counter, price, size, side)
        order_id_counter += 1
    return order_id_counter


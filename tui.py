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

def draw_bbo_and_spread(stdscr, book: OrderBook, y: int, x: int):
    best_bid = book.best_bid()
    best_ask = book.best_ask()
    spread = book.spread()
    
    stdscr.addstr(y, x, "--- Top of Book (BBO) ---", curses.color_pair(3) | curses.A_BOLD)
    y += 1
    
    if best_ask:
        stdscr.addstr(y, x, f"ASK: {best_ask[0]:.2f} x {best_ask[1]}", curses.color_pair(2))
    else:
        stdscr.addstr(y, x, "ASK: NONE", curses.color_pair(2))
    y += 1
    
    if spread is not None:
        stdscr.addstr(y, x, f"SPREAD: {spread:.2f}")
    else:
        stdscr.addstr(y, x, "SPREAD: N/A")
    y += 1
        
    if best_bid:
        stdscr.addstr(y, x, f"BID: {best_bid[0]:.2f} x {best_bid[1]}", curses.color_pair(1))
    else:
        stdscr.addstr(y, x, "BID: NONE", curses.color_pair(1))
    
    return y + 2

def draw_depth(stdscr, book: OrderBook, y: int, x: int, levels: int = 10):
    depth = book.depth(levels)
    stdscr.addstr(y, x, f"--- Order Book Depth ({levels} levels) ---", curses.color_pair(3) | curses.A_BOLD)
    y += 1
    
    stdscr.addstr(y, x, f"{'Price':<12} {'Size':<10}", curses.A_UNDERLINE)
    y += 1
    
    # Asks (descending order on screen looks better)
    asks = sorted(depth['asks'], reverse=True)
    for p, s in asks:
        stdscr.addstr(y, x, f"{p:<12.2f} {s:<10}", curses.color_pair(2))
        y += 1
        
    stdscr.addstr(y, x, "-" * 23)
    y += 1
    
    # Bids
    for p, s in depth['bids']:
        stdscr.addstr(y, x, f"{p:<12.2f} {s:<10}", curses.color_pair(1))
        y += 1
        
    return y


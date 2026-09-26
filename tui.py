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


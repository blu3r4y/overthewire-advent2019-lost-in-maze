import re

# regex that finds ansi color codes
ANSI_ESCAPE = re.compile(r"\x1B[@-_][0-?]*[ -/]*[@-~]")

# regex that removes leading chunk in gps lines
GPS_ESCAPE = re.compile(r"^[^|]*\| ")

# the marker for the gps window
GPS_MARK = b"+----------------+"

# cell states
FREE, START, WALLS = ord(" "), ord("s"), [ord("▀"), ord("▄"), ord("█")]
UP, DOWN, LEFT, RIGHT = ord("^"), ord("v"), ord("<"), ord(">")

# orientation mappings
ORIENTATIONS = [UP, RIGHT, DOWN, LEFT]
COMPLEX_MAPPING = {UP: -1j, DOWN: 1j, LEFT: -1 + 0j, RIGHT: 1 + 0j}

# visualization color codes
MARK_UNKNOWN, MARK_FREE, MARK_WALL, MARK_POS, MARK_BLACKLIST = 19, 11, 1, 5, 3

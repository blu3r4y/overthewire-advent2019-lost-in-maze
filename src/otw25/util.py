import numpy as np
import matplotlib.pyplot as plt

from otw25.const import *


def adjacent(pos):
    return [pos + (1j ** p) for p in range(4)]


def manhattan(a: complex, b: complex):
    return abs(int(a.real - b.real)) + abs(int(a.imag - b.imag))


def tup_to_cmpx(val):
    return val[0] + 1j * val[1]


def cmpx_to_tup(val):
    return int(val.real), int(val.imag)


def dict_to_array(grid):
    # map complex numbers to int tuples
    grid = {cmpx_to_tup(key): val for key, val in grid.items()}

    # retrieve bounds and initialize a new empty grid
    keys = np.array(list(grid.keys()))
    extent = max(np.amax(keys, axis=0)) + 1

    # fill grid cells
    result = np.full((extent, extent), fill_value=MARK_UNKNOWN)
    for (x, y), value in grid.items():
        if x >= 0 and y >= 0:
            result[x, y] = value

    return result


def interactive_plot():
    plt.ion()
    plt.figure(figsize=(10, 10))
    plt.axis("off")

    view = plt.imshow(np.ones((10, 10)), aspect="auto", cmap="tab20c")
    return view

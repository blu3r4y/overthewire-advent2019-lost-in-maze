from collections import defaultdict
from random import choice
from telnetlib import Telnet

from funcy import flatten, some
from parse import parse

from otw25.util import *


class Maze(object):
    """

    the coordinate system

      + --> x-axis / real axis
      |
      V

      y-axis / imag axis

    """

    def __init__(self, ip: str = "3.93.128.89", port: int = 1225):
        self.grid = defaultdict(lambda: MARK_UNKNOWN)
        self.blacklist = set()

        self.frame = None
        self.pos = None
        self.face = None
        self.end = None

        self.view = interactive_plot()
        self.blink = 0

        # initialize game with smallest possible dimensions
        self.tn = Telnet(ip, port)
        self.tn.read_until(b"width: ")
        self.tn.write(b"20\n")
        self.tn.read_until(b"height: ")
        self.tn.write(b"50\n")

        # parse initial scene
        self.parse_frames()

    def close(self):
        self.tn.close()

    def move(self, target):
        print("move", target)

        if self.grid[target] != MARK_FREE:
            raise ValueError(f"target cell {target} is not free")

        ntry = 0
        while self.pos != target:

            path = self.shortest_path(self.pos, target, ignore_blacklist=True)
            if path is None:
                raise ValueError(f"no path from {self.pos} to target {target}")

            # only make the next move, reassess the situation then
            # include random rotations if it seems that we are stuck here
            self._drunk_move(path[1], very_drunk=ntry > 10)
            ntry += 1

        # seems like a good opportunity to check for dead ends
        self._close_up_dead_ends()

    def movable(self, pos, ignore_blacklist=False):
        # get all movable cells adjacent to pos
        return [p for p in adjacent(pos) if self.grid[p] == MARK_FREE or
                (ignore_blacklist and self.grid[p] == MARK_BLACKLIST)]

    def has_known_neighbors(self, pos):
        # are all points around this position explored already?
        return pos in self.grid and all(p in self.grid for p in adjacent(pos))

    def is_dead_end(self, pos):
        # a dead end cell is free and has exactly 3 wall neighbors
        return self.grid[pos] == MARK_FREE and \
               len([p for p in adjacent(pos) if p in self.grid and
                    self.grid[p] in (MARK_WALL, MARK_BLACKLIST)]) == 3

    def show(self, frame=False):
        if frame:
            print("\n".join(self.frame))

        # build grid and mark our location
        view = dict_to_array(self.grid)
        view[cmpx_to_tup(self.pos)] = MARK_POS + self.blink

        # visual effect stuff
        self.blink = 1 - self.blink

        # reset grid content and colorbar range
        self.view.set_data(view.T)
        self.view.set_clim(vmin=np.amin(view), vmax=np.amax(view))

        plt.title(f"pos={self.pos} face={self.face}")

        plt.tight_layout()
        plt.draw()
        plt.pause(.001)

    def parse_frames(self, nframes=0):
        # read and encode gps block (take only the last frame)
        image, gps = None, None
        for _ in range(nframes + 1):
            image = self.tn.read_until(GPS_MARK)
            gps = self.tn.read_until(GPS_MARK)

        self.tn.read_very_eager()

        # remove ascii-codes and store full image
        image = ANSI_ESCAPE.sub("", image.decode("utf8")).split("\n")
        gps = ANSI_ESCAPE.sub("", gps.decode("utf8")).split("\n")

        self.frame = image + gps

        # extract gps part only
        gps = [GPS_ESCAPE.sub("", line)[:-2] for line in gps[:-1]]

        # parse gps block
        raw = [list(map(ord, line)) for line in gps[3:-3]]

        # get facing direction (and grid offset)
        face = some(lambda ch: ch in ORIENTATIONS, flatten(raw))
        offset = [(line.index(face), y) for y, line in enumerate(raw) if face in line][0]

        # get gps view (and transpose for (x, y) coordiante system)
        view = np.array([[ch in WALLS for ch in line] for line in raw], dtype=int)
        view = view.T

        # parse position and end coordinates
        pos = tuple(parse("pos: {:d} {:d}", gps[-2].strip()))
        end = tuple(parse("end: {:d} {:d}", gps[-1].strip()))

        # update internal map
        dx, dy = offset[0] - pos[0], offset[1] - pos[1]
        for (x, y), val in np.ndenumerate(view):
            coords = tup_to_cmpx((x - dx, y - dy))
            if coords not in self.blacklist:
                self.grid[tup_to_cmpx((x - dx, y - dy))] = MARK_WALL if val else MARK_FREE

        # store current state in complex format
        self.pos = tup_to_cmpx(pos)
        self.end = tup_to_cmpx(end)
        self.face = COMPLEX_MAPPING[face]

    def shortest_path(self, start, goal, ignore_blacklist=False):
        # breadth first search shortest path
        queue, distances = [start], {start: 0}
        parents = {}

        def _backtrace_path():
            # resolve all the parents, starting with goal, until we reach start
            path = [goal]
            while path[-1] != start:
                path.append(parents[path[-1]])
            return list(reversed(path))

        while queue:
            node = queue.pop(0)
            if node == goal:
                return _backtrace_path()
            for neighbor in self.movable(node, ignore_blacklist=ignore_blacklist):
                if neighbor not in distances:
                    queue.append(neighbor)
                    parents[neighbor] = node
                    distances[neighbor] = distances[node] + 1  # distance to parent plus one step

        return None  # no path found

    def _drunk_move(self, target, very_drunk=False):
        if self.pos == target:
            return

        if very_drunk:
            print("very drunk moves activated to get back on track")

        # a drunk person should set one foot after another ...
        if manhattan(target, self.pos) > 1:
            return

        vec = target - self.pos

        # determine how often we need to turn such that we face towards the target
        nturns = 0
        while self.face != vec:
            self.face *= 1j
            nturns += 1

        self._control(nsteps=1, nturns=nturns)

        # if we did not make it, correct our turning angles
        if self.pos != target:
            self._turn_correct(very_drunk=very_drunk)

    def _turn_correct(self, very_drunk=False):
        # determine if we are too left or too right by counting pixels on the frame
        left, right = 0, 0
        for line in self.frame[:-14]:
            left += len(line[:len(line) // 2].strip())
            right += len(line[len(line) // 2:].strip())

        # make 1 turn (~ 1/6 of 90-degree rotation) towards the center
        # add randomness if we are very drunk, i.e., if we are stuck ...

        print("turn correct to", "right" if left > right else "left")

        if left > right:
            self._control(nsteps=0, nturns=0.2 if not very_drunk else choice([0.2, 0.4]))  # turn right
        else:
            self._control(nsteps=0, nturns=-0.2 if not very_drunk else choice([-0.2, -0.4]))  # turn left

    def _control(self, nsteps: float = 1, nturns: float = 0):
        cmd = b""

        # avoid going in circle and always choice faster turns
        nturns = np.sign(nturns) * (abs(nturns) % 4)
        if abs(nturns) >= 3:
            nturns = -np.sign(nturns) * (4 - abs(nturns))

        if nturns >= 0:
            cmd += b"d" * int(6 * nturns)  # turn right
        else:
            cmd += b"a" * int(6 * -nturns)  # turn left

        if nsteps > 0:
            cmd += b"w" * int(4 * nsteps)  # move forward
        else:
            cmd += b"s" * int(4 * -nsteps)  # move backward

        print("send", cmd.decode("utf8"))
        self.tn.write(cmd + b"\n")

        self.parse_frames(len(cmd))

    def _close_up_dead_ends(self):
        # close the entry to dead ends to avoid unnecessary traversals

        for point in list(self.grid.keys()):
            if self.is_dead_end(point):

                entry = self._backtrace_dead_end_entry(point, self.end)
                if entry is not None:

                    # avoid closing paths between the dead end and us, our target, or the goal ;)
                    path = self.shortest_path(point, entry)
                    if self.end not in path:
                        if self.pos not in path:
                            print(f"dead end from {point} to {entry}")
                            self.blacklist.add(entry)
                        else:
                            # avoid moving towards a dead end by blacklisting positions in front of us
                            idx = path.index(self.pos) - 1
                            if 0 <= idx < len(path):
                                print(f"dead end from {point} to {entry} - but only closing {path[idx]}")
                                self.blacklist.add(path[idx])

        # close entries to dead ends
        for entry in self.blacklist:
            self.grid[entry] = MARK_BLACKLIST

    def _backtrace_dead_end_entry(self, point, origin=None):
        # we did not explore all neighbors at this point yet, stop!
        if not self.has_known_neighbors(point):
            return None

        options = self.movable(point)
        if origin in options:
            options.remove(origin)

        if len(options) == 0:
            # we are stuck, so there can be no entrance
            return None
        elif len(options) == 1:
            # follow path to entrance
            return self._backtrace_dead_end_entry(options[0], origin=point)
        elif len(options) > 1:
            # intersection point, we found the entrance
            return origin

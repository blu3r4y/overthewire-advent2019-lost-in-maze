from typing import Callable, Iterable

from cmath import polar
from collections import defaultdict

from otw25.maze import Maze


class Tremaux(object):

    def __init__(self, maze: Maze):
        self.maze = maze
        self.marks = defaultdict(int)

    def escape(self, goal_condition: Callable[[Maze], bool]):
        # implementation of tremaux method
        # https://en.wikipedia.org/wiki/Maze_solving_algorithm#Tr%C3%A9maux's_algorithm

        origin = self.maze.pos - self.maze.face

        while not goal_condition(self.maze):

            # possible paths
            options = self.maze.movable(self.maze.pos)
            assert len(options) > 0
            if origin in options:  # going back is not an option
                options.remove(origin)

            # we hit a wall ...
            if len(options) == 0:
                target = origin  # -> go back

            # simply follow the path ...
            elif len(options) == 1:
                target = options[0]

            # we are at a crossing point ...
            else:

                # mark the cell at which we entered the crossing point
                self.marks[origin] += 1

                marks = [self.marks[opt] for opt in options]

                # no marks at all ... ?
                if sum(marks) == 0:
                    target = self.closest(options, self.maze.end)  # -> choose heuristic

                # no marks from origin ... ?
                elif self.marks[origin] == 0:
                    target = origin  # -> go back

                # otherwise, take path with least marks ...
                else:
                    options_marks = sorted(zip(options, marks), key=lambda e: e[1])
                    target = options_marks[0][0]

                # mark the chosen cell
                self.marks[target] += 1

            # make the mave
            origin = target
            self.maze.move(target)

            self.maze.show()

    @staticmethod
    def closest(positions: Iterable[complex], target: complex):
        # choose the position that is closest to the target (line-of-sight distance)
        distances = [polar(target - pos)[0] for pos in positions]
        return sorted(zip(positions, distances), key=lambda e: e[1])[0][0]

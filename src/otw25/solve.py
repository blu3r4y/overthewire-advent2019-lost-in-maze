from otw25.maze import Maze
from otw25.tremaux import Tremaux


def goal_condition(maze):
    # stop if we saw the goal and a path to the goal is possible
    return maze.end in maze.grid and maze.shortest_path(maze.pos, maze.end) is not None


if __name__ == "__main__":
    maze = Maze()
    tremaux = Tremaux(maze)

    # wander around with tremaux until we find a path to the goal
    tremaux.escape(goal_condition)

    print("goal reachable")

    # move to the goal
    maze.move(maze.end)

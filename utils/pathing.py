#!/usr/bin/env python3
import itertools

from queue import PriorityQueue


class Node:
    def __init__(self, id: int):
        self.id: int = id
        self.children: list[Node] = []
        self.previous = None

    def add_child(self, child):
        self.children.append(child)

    def remove_child(self, child):
        self.children.remove(child)

    def get_id(self) -> int:
        return self.id

    def get_children_id(self) -> list[int]:
        return [child.get_id() for child in self.children]


class Graph:
    def __init__(self, length: int, width: int, obstacles: list[int]):
        self.len = length
        self.wid = width
        self.nodes = []

        extended_obstacles = []
        extended_obstacles.extend(obstacles)

        for node in obstacles:
            if node - 1 not in extended_obstacles:
                extended_obstacles.append(node - 1)
            if node + 1 not in extended_obstacles:
                extended_obstacles.append(node + 1)
            if node - width not in extended_obstacles:
                extended_obstacles.append(node - width)
            if node + width not in extended_obstacles:
                extended_obstacles.append(node + width)

        extended_obstacles.sort()

        print(extended_obstacles)

        for i in range(1, length - 1):
            row = []
            for j in range(1, width - 1):
                if i * width + j not in extended_obstacles:
                    node = Node(i * width + j)
                else:
                    node = Node(-1)
                row.append(node)
            self.nodes.append(row)

        graph_nodes_id = list(
            itertools.chain.from_iterable(
                [[node.get_id() for node in row] for row in self.nodes]
            )
        )

        for row in self.nodes:
            for node in row:
                possible_children = [
                    node.id - 1,
                    node.id + 1,
                    node.id - width,
                    node.id + width,
                ]
                for possible_child in possible_children:
                    if possible_child in graph_nodes_id:
                        node.add_child(self.get_node_by_id(possible_child))

    def get_node_by_id(self, id: int) -> Node:
        for row in self.nodes:
            for node in row:
                if node.get_id() == id:
                    return node
        return None

    def mark_as_obstacle(self, target: Node, direction: str):
        obstacles = [target]
        print(direction)
        if direction in ["N", "S"]:
            if self.get_node_by_id(target.id - 1):
                obstacles.append(self.get_node_by_id(target.id - 1))
            if self.get_node_by_id(target.id + 1):
                obstacles.append(self.get_node_by_id(target.id + 1))
        else:
            if self.get_node_by_id(target.id - self.wid):
                obstacles.append(self.get_node_by_id(target.id - self.wid))
            if self.get_node_by_id(target.id + self.wid):
                obstacles.append(self.get_node_by_id(target.id + self.wid))
        for obstacle in obstacles:
            print({obstacle.id: [node.id for node in obstacle.children]})
            for node in obstacle.children:
                node.remove_child(obstacle)
            obstacle.id = -1
        return obstacles

    def build_path(self, start: Node, dest: Node) -> list[Node]:
        frontier = PriorityQueue()
        frontier.put((0, start.id))
        came_from = {}
        cost_so_far = {}
        came_from[start] = Node(-1)
        cost_so_far[start] = 0

        while not frontier.empty():
            current = self.get_node_by_id(frontier.get()[1])

            if current == dest:
                break

            for next in current.children:
                new_cost = cost_so_far[current] + 1
                if next not in cost_so_far or new_cost < cost_so_far[next]:
                    cost_so_far[next] = new_cost
                    priority = new_cost + self.heuristic(dest, next)
                    frontier.put((priority, next.id))
                    came_from[next] = current

        current = dest
        path = [current]
        while came_from[current].id != -1:
            path.append(came_from[current])
            current = came_from[current]

        path.reverse()

        return path

    def heuristic(self, node_1: Node, node_2: Node):
        # Manhattan distance on a square grid
        return abs(node_1.id // self.wid - node_2.id // self.wid) + abs(
            node_1.id % self.wid - node_2.id % self.wid
        )

    def create_command_sequence(
        self, path: list[Node], initial_direction: str
    ) -> list[str]:
        direction = initial_direction
        result = []
        for node, next_node in zip(path[:-1], path[1:]):
            if next_node.id == node.id + 1:
                if direction == "N":
                    result.extend(["rgt", "fwd"])
                elif direction == "S":
                    result.extend(["lft", "fwd"])
                elif direction == "W":
                    result.extend(["rgt", "rgt", "fwd"])
                elif direction == "E":
                    result.append("fwd")
                direction = "E"

            elif next_node.id == node.id - 1:
                if direction == "N":
                    result.extend(["lft", "fwd"])
                elif direction == "S":
                    result.extend(["rgt", "fwd"])
                elif direction == "W":
                    result.append("fwd")
                elif direction == "E":
                    result.extend(["rgt", "rgt", "fwd"])
                direction = "W"

            elif next_node.id == node.id + self.wid:
                if direction == "N":
                    result.extend(["rgt", "rgt", "fwd"])
                elif direction == "S":
                    result.append("fwd")
                elif direction == "W":
                    result.extend(["lft", "fwd"])
                elif direction == "E":
                    result.extend(["rgt", "fwd"])
                direction = "S"

            elif next_node.id == node.id - self.wid:
                if direction == "N":
                    result.append("fwd")
                elif direction == "S":
                    result.extend(["rgt", "rgt", "fwd"])
                elif direction == "W":
                    result.extend(["rgt", "fwd"])
                elif direction == "E":
                    result.extend(["lft", "fwd"])
                direction = "N"

        return result


if __name__ == "__main__":
    graph = Graph(12, 15, [])
    for row in graph.nodes:
        print(["%3.d" % node.get_id() for node in row])

    path = graph.build_path(graph.get_node_by_id(19), graph.get_node_by_id(81))
    cmd_list = graph.create_command_sequence(path, initial_direction="E")

    for node in path:
        print(node.id)

    for cmd in cmd_list:
        print(cmd)

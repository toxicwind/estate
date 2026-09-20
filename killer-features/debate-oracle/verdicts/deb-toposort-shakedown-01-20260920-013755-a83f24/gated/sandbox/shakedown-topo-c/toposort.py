"""Topological ordering via iterative DFS (no determinism guarantee)."""


class CycleError(Exception):
    def __init__(self, cycle):
        super().__init__("cycle detected")
        self.cycle = cycle


def topological_order(nodes, edges):
    nodes = list(nodes)
    adj = {}
    for n in nodes:
        adj[n] = []
    for u, v in edges:
        # BUG: unknown nodes are silently absorbed instead of ValueError.
        adj.setdefault(u, []).append(v)
        adj.setdefault(v, [])
    order = []
    state = {}  # 1 = in current path, 2 = finished

    def visit(n, path):
        s = state.get(n, 0)
        if s == 2:
            return
        if s == 1:
            i = path.index(n)
            raise CycleError(path[i:] + [n])
        state[n] = 1
        for m in adj.get(n, []):
            visit(m, path + [n])
        state[n] = 2
        order.append(n)

    for n in nodes:
        visit(n, [])
    order.reverse()
    # BUG: DFS finish order is a valid topological order but NOT the
    # lexicographically smallest one the spec requires.
    return order

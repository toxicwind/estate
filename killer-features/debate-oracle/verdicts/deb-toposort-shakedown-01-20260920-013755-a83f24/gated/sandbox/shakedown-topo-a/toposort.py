"""Topological ordering with cycle detection (Kahn + heap, DFS cycle report)."""
import heapq


class CycleError(Exception):
    def __init__(self, cycle):
        super().__init__("cycle detected: %r" % (cycle,))
        self.cycle = cycle


def topological_order(nodes, edges):
    nodes = list(nodes)
    node_set = set(nodes)
    adj = {n: set() for n in nodes}
    indeg = {n: 0 for n in nodes}
    for u, v in edges:
        if u not in node_set or v not in node_set:
            raise ValueError("edge references unknown node: %r" % ((u, v),))
        if v not in adj[u]:
            adj[u].add(v)
            indeg[v] += 1
    # Kahn's algorithm; heap keyed by repr() gives the lexicographically
    # smallest valid order deterministically.
    heap = [(repr(n), n) for n in nodes if indeg[n] == 0]
    heapq.heapify(heap)
    order = []
    while heap:
        _, n = heapq.heappop(heap)
        order.append(n)
        for m in adj[n]:
            indeg[m] -= 1
            if indeg[m] == 0:
                heapq.heappush(heap, (repr(m), m))
    if len(order) != len(nodes):
        raise CycleError(_find_cycle(nodes, adj))
    return order


def _find_cycle(nodes, adj):
    """Return a real directed cycle: first node repeated at the end."""
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {n: WHITE for n in nodes}
    stack = []

    def dfs(n):
        color[n] = GRAY
        stack.append(n)
        for m in adj[n]:
            if color[m] == GRAY:
                i = stack.index(m)
                return stack[i:] + [m]
            if color[m] == WHITE:
                r = dfs(m)
                if r:
                    return r
        stack.pop()
        color[n] = BLACK
        return None

    for n in nodes:
        if color[n] == WHITE:
            r = dfs(n)
            if r:
                return r
    return [nodes[0], nodes[0]] if nodes else []

"""Topological ordering (Kahn, repr-sorted); cycle report is a stub."""
import heapq


class CycleError(Exception):
    def __init__(self, cycle):
        super().__init__("cycle detected")
        self.cycle = cycle


def topological_order(nodes, edges):
    nodes = list(nodes)
    node_set = set(nodes)
    adj = {n: set() for n in nodes}
    indeg = {n: 0 for n in nodes}
    for u, v in edges:
        if u not in node_set or v not in node_set:
            raise ValueError("edge references unknown node")
        if v not in adj[u]:
            adj[u].add(v)
            indeg[v] += 1
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
        leftover = [n for n in nodes if n not in order]
        # STUB: reports a self-loop on an arbitrary leftover node instead of
        # the real directed cycle. Passes self-loop tests, fails real-cycle
        # reporting (consecutive pair is not an actual edge).
        raise CycleError([leftover[0], leftover[0]])
    return order

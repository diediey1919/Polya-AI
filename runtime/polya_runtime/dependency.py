"""
Polia AI Runtime - Knowledge Dependency Graph Integration (Phase 9)
In-memory directed graph representing 166 nodes and 693 edges from forensic audit.
"""

import os
import json
from collections import deque, defaultdict
from typing import Dict, List, Set, Optional, Any, Tuple
from polya_runtime.errors import DependencyResolutionError, DependencyCycleError

PRIMARY_GRAPH_PATH = "/home/ubuntu/Polya-AI/.polya/orchestration/dependency-map.json"
FALLBACK_GRAPH_PATH = "/home/ubuntu/.polya/orchestration/dependency-map.json"

class DependencyGraph:
    def __init__(self, graph_path: Optional[str] = None):
        if graph_path:
            self.graph_path = graph_path
        elif os.path.exists(PRIMARY_GRAPH_PATH):
            self.graph_path = PRIMARY_GRAPH_PATH
        elif os.path.exists(FALLBACK_GRAPH_PATH):
            self.graph_path = FALLBACK_GRAPH_PATH
        else:
            self.graph_path = PRIMARY_GRAPH_PATH

        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.out_edges: Dict[str, List[Tuple[str, str]]] = defaultdict(list)  # u -> [(v, relation)]
        self.in_edges: Dict[str, List[Tuple[str, str]]] = defaultdict(list)   # v -> [(u, relation)]
        self._load_graph()

    def _load_graph(self):
        if not os.path.exists(self.graph_path):
            raise DependencyResolutionError(f"Dependency map not found at {self.graph_path}")

        try:
            with open(self.graph_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            raise DependencyResolutionError(f"Failed to parse dependency map: {str(e)}") from e

        for n in data.get("nodes", []):
            self.nodes[n["id"]] = n

        for e in data.get("edges", []):
            src = e["source"]
            tgt = e["target"]
            rel = e.get("relation", "DEPENDS_ON")
            self.out_edges[src].append((tgt, rel))
            self.in_edges[tgt].append((src, rel))

    def node_count(self) -> int:
        return len(self.nodes)

    def edge_count(self) -> int:
        return sum(len(edges) for edges in self.out_edges.values())

    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        return self.nodes.get(node_id)

    def get_prerequisites(self, node_id: str, max_depth: int = 2) -> List[Dict[str, Any]]:
        """
        Return nodes that this node directly or transitively depends upon (out-edges).
        """
        if node_id not in self.nodes:
            return []

        visited: Set[str] = set()
        queue: deque = deque([(node_id, 0)])
        prereqs: List[Dict[str, Any]] = []

        while queue:
            curr, depth = queue.popleft()
            if depth >= max_depth:
                continue

            for target, rel in self.out_edges.get(curr, []):
                if target not in visited and target != node_id:
                    visited.add(target)
                    target_node = self.nodes.get(target, {"id": target, "type": "unknown", "title": target})
                    prereqs.append({
                        "id": target,
                        "node": target_node,
                        "relation": rel,
                        "depth": depth + 1
                    })
                    queue.append((target, depth + 1))

        return prereqs

    def get_dependents(self, node_id: str, max_depth: int = 2) -> List[Dict[str, Any]]:
        """
        Return nodes that depend on or reference this node (in-edges).
        """
        if node_id not in self.nodes:
            return []

        visited: Set[str] = set()
        queue: deque = deque([(node_id, 0)])
        dependents: List[Dict[str, Any]] = []

        while queue:
            curr, depth = queue.popleft()
            if depth >= max_depth:
                continue

            for source, rel in self.in_edges.get(curr, []):
                if source not in visited and source != node_id:
                    visited.add(source)
                    source_node = self.nodes.get(source, {"id": source, "type": "unknown", "title": source})
                    dependents.append({
                        "id": source,
                        "node": source_node,
                        "relation": rel,
                        "depth": depth + 1
                    })
                    queue.append((source, depth + 1))

        return dependents

    def get_critical_path(self, start_id: str, end_id: str) -> Optional[List[str]]:
        """
        Find shortest directed or undirected path between two knowledge nodes.
        """
        if start_id not in self.nodes or end_id not in self.nodes:
            return None

        visited = {start_id}
        queue = deque([(start_id, [start_id])])

        while queue:
            curr, path = queue.popleft()
            if curr == end_id:
                return path

            # Check outbound and inbound
            neighbors = [tgt for tgt, _ in self.out_edges.get(curr, [])] + [src for src, _ in self.in_edges.get(curr, [])]
            for nbr in neighbors:
                if nbr not in visited:
                    visited.add(nbr)
                    queue.append((nbr, path + [nbr]))

        return None

    def resolve_activation_chain(self, seed_node_ids: List[str], max_total: int = 8) -> List[str]:
        """
        Given seed nodes from search, expand prerequisite and dependent chains
        to produce a topologically ordered activation set up to max_total nodes.
        """
        ordered: List[str] = []
        visited: Set[str] = set()

        for seed in seed_node_ids:
            if seed in self.nodes and seed not in visited:
                # Add prerequisites first (foundations)
                prereqs = self.get_prerequisites(seed, max_depth=1)
                for p in prereqs:
                    pid = p["id"]
                    if pid not in visited and len(ordered) < max_total:
                        visited.add(pid)
                        ordered.append(pid)

                # Add seed
                if len(ordered) < max_total:
                    visited.add(seed)
                    ordered.append(seed)

                # Add immediate dependents
                dependents = self.get_dependents(seed, max_depth=1)
                for d in dependents:
                    did = d["id"]
                    if did not in visited and len(ordered) < max_total:
                        visited.add(did)
                        ordered.append(did)

            if len(ordered) >= max_total:
                break

        return ordered[:max_total]

    def detect_cycles(self) -> List[List[str]]:
        """
        Detect any circular dependency loops in the directed graph.
        """
        visited: Dict[str, int] = {}  # 0: unvisited, 1: visiting, 2: visited
        cycles: List[List[str]] = []
        path: List[str] = []

        def dfs(u: str):
            visited[u] = 1
            path.append(u)
            for v, _ in self.out_edges.get(u, []):
                if v in self.nodes:
                    state = visited.get(v, 0)
                    if state == 1:
                        cycle_start = path.index(v)
                        cycles.append(path[cycle_start:] + [v])
                    elif state == 0:
                        dfs(v)
            path.pop()
            visited[u] = 2

        for node_id in self.nodes:
            if visited.get(node_id, 0) == 0:
                dfs(node_id)

        return cycles

    def get_node_degree(self, node_id: str) -> Dict[str, int]:
        """Return in-degree, out-degree, and total degree."""
        out_deg = len(self.out_edges.get(node_id, []))
        in_deg = len(self.in_edges.get(node_id, []))
        return {
            "in_degree": in_deg,
            "out_degree": out_deg,
            "total_degree": in_deg + out_deg
        }

"""
Pure Python SVG Graph Generator for Epic Dependencies Visualization.

Generates dependency graphs as pure SVG with zero JavaScript dependencies.
Implements force-directed layout algorithm and interactive features
server-side.

Related Issue: US-00030 - Visual Filtering Enhancement for Epic
Dependencies Graph
Parent Epic: EP-00005 - Requirements Traceability Matrix Automation
"""

import math
import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from xml.sax.saxutils import escape


@dataclass
class Node:
    """Represents an epic node in the dependency graph."""

    id: str
    epic_id: str
    title: str
    status: str
    capability_id: Optional[str]
    capability_name: Optional[str]
    component: str
    completion_percentage: float
    priority: str
    x: float = 0.0
    y: float = 0.0
    vx: float = 0.0
    vy: float = 0.0


@dataclass
class Link:
    """Represents a dependency link between epics."""

    source: str
    target: str
    type: str
    priority: str
    reason: str


@dataclass
class GraphLayout:
    """Configuration for graph layout and appearance."""

    width: int = 800
    height: int = 600
    node_radius: int = 25
    link_distance: int = 200
    charge_strength: float = -1200
    center_strength: float = 0.05
    collision_radius: int = 80


class ForceDirectedLayout:
    """Pure Python implementation of force-directed graph layout."""

    def __init__(self, layout: GraphLayout):
        self.layout = layout
        self.alpha = 1.0
        self.alpha_min = 0.001
        self.alpha_decay = 0.02
        self.velocity_decay = 0.4

    def apply_forces(self, nodes: Dict[str, Node], links: List[Link]) -> None:
        """Apply force-directed layout algorithm."""
        iterations = 300

        for _ in range(iterations):
            if self.alpha < self.alpha_min:
                break

            # Apply centering force
            self._apply_center_force(nodes)

            # Apply charge force (node repulsion)
            self._apply_charge_force(nodes)

            # Apply link force (spring attraction)
            self._apply_link_force(nodes, links)

            # Apply collision force
            self._apply_collision_force(nodes)

            # Update positions
            self._update_positions(nodes)

            # Cool down
            self.alpha *= 1 - self.alpha_decay

    def _apply_center_force(self, nodes: Dict[str, Node]) -> None:
        """Center nodes around the layout center."""
        center_x = self.layout.width / 2
        center_y = self.layout.height / 2

        for node in nodes.values():
            dx = center_x - node.x
            dy = center_y - node.y
            node.vx += dx * self.layout.center_strength * self.alpha
            node.vy += dy * self.layout.center_strength * self.alpha

    def _apply_charge_force(self, nodes: Dict[str, Node]) -> None:
        """Apply repulsion force between all nodes."""
        node_list = list(nodes.values())

        for i, node_a in enumerate(node_list):
            for node_b in node_list[i + 1 :]:
                dx = node_b.x - node_a.x
                dy = node_b.y - node_a.y
                distance = math.sqrt(dx * dx + dy * dy)

                if distance > 0:
                    force = self.layout.charge_strength * self.alpha / distance
                    fx = (dx / distance) * force
                    fy = (dy / distance) * force

                    node_a.vx -= fx
                    node_a.vy -= fy
                    node_b.vx += fx
                    node_b.vy += fy

    def _apply_link_force(self, nodes: Dict[str, Node], links: List[Link]) -> None:
        """Apply spring force for linked nodes."""
        for link in links:
            source = nodes[link.source]
            target = nodes[link.target]

            dx = target.x - source.x
            dy = target.y - source.y
            distance = math.sqrt(dx * dx + dy * dy)

            if distance > 0:
                force = (distance - self.layout.link_distance) / distance * self.alpha
                fx = dx * force * 0.5
                fy = dy * force * 0.5

                source.vx += fx
                source.vy += fy
                target.vx -= fx
                target.vy -= fy

    def _apply_collision_force(self, nodes: Dict[str, Node]) -> None:
        """Prevent node overlap."""
        node_list = list(nodes.values())

        for i, node_a in enumerate(node_list):
            for node_b in node_list[i + 1 :]:
                dx = node_b.x - node_a.x
                dy = node_b.y - node_a.y
                distance = math.sqrt(dx * dx + dy * dy)
                min_distance = self.layout.collision_radius

                if distance < min_distance and distance > 0:
                    overlap = min_distance - distance
                    force = overlap / distance * 0.5
                    fx = dx * force
                    fy = dy * force

                    node_a.x -= fx
                    node_a.y -= fy
                    node_b.x += fx
                    node_b.y += fy

    def _update_positions(self, nodes: Dict[str, Node]) -> None:
        """Update node positions based on velocity."""
        for node in nodes.values():
            node.vx *= self.velocity_decay
            node.vy *= self.velocity_decay
            node.x += node.vx
            node.y += node.vy

            # Keep nodes within bounds
            margin = self.layout.node_radius
            node.x = max(margin, min(self.layout.width - margin, node.x))
            node.y = max(margin, min(self.layout.height - margin, node.y))


class SVGGraphGenerator:
    """Generates pure SVG dependency graphs with zero JavaScript."""

    def __init__(self):
        self.layout = GraphLayout()
        self.colors = {
            "planned": "#3498db",
            "active": "#f39c12",
            "in-progress": "#f39c12",
            "completed": "#27ae60",
            "on-hold": "#95a5a6",
            "default": "#3498db",
        }
        self.capability_colors = {
            "CAP-00001": "#8e44ad",
            # GitHub Integration - Purple
            "CAP-00002": "#16a085",
            # Requirements Traceability - Teal
            "CAP-00003": "#e67e22",
            # Blog Platform - Orange
            "CAP-00004": "#c0392b",
            # GDPR Compliance - Red
            "unassigned": "#95a5a6",
            # No capability - Gray
        }
        self.dependency_colors = {
            "blocking": "#e74c3c",
            "prerequisite": "#3498db",
            "technical": "#9b59b6",
            "business": "#27ae60",
            "informational": "#95a5a6",
        }

    def generate_svg(
        self,
        epics: List[dict],
        dependencies: List[dict],
        capabilities: List[dict] = None,
        filters: dict = None,
    ) -> str:
        """Generate complete SVG visualization."""
        # Convert data to internal format
        nodes = self._create_nodes(epics, capabilities)
        links = self._create_links(dependencies)

        # Apply filters
        if filters:
            nodes, links = self._apply_filters(nodes, links, filters)

        # Initialize random positions
        self._initialize_positions(nodes)

        # Apply force-directed layout
        layout_engine = ForceDirectedLayout(self.layout)
        layout_engine.apply_forces(nodes, links)

        # Generate SVG
        return self._render_svg(nodes, links, capabilities or [])

    def _create_nodes(
        self, epics: List[dict], capabilities: List[dict] = None
    ) -> Dict[str, Node]:
        """Convert epic data to Node objects."""
        capability_map = {}
        if capabilities:
            capability_map = {cap["capability_id"]: cap["name"] for cap in capabilities}

        nodes = {}
        for epic in epics:
            capability_id = epic.get("capability_capability_id")
            nodes[str(epic["id"])] = Node(
                id=epic["id"],
                epic_id=epic.get("epic_id", f"EP-{epic['id']}"),
                title=epic.get("title", "Untitled Epic"),
                status=epic.get("status", "planned"),
                capability_id=capability_id,
                capability_name=(
                    capability_map.get(capability_id) if capability_id else None
                ),
                component=epic.get("component", "backend"),
                completion_percentage=epic.get("completion_percentage", 0),
                priority=epic.get("priority", "medium"),
            )
        return nodes

    def _create_links(self, dependencies: List[dict]) -> List[Link]:
        """Convert dependency data to Link objects."""
        links = []
        for dep in dependencies:
            links.append(
                Link(
                    source=str(dep["parent_epic_id"]),
                    target=str(dep["dependent_epic_id"]),
                    type=dep.get("dependency_type", "prerequisite"),
                    priority=dep.get("priority", "medium"),
                    reason=dep.get("reason", "Dependency relationship"),
                )
            )
        return links

    def _apply_filters(
        self, nodes: Dict[str, Node], links: List[Link], filters: dict
    ) -> Tuple[Dict[str, Node], List[Link]]:
        """Apply filtering logic."""
        filtered_nodes = {}

        for node_id, node in nodes.items():
            keep_node = True

            # Status filter
            if filters.get("status") and node.status != filters["status"]:
                keep_node = False

            # Component filter
            if filters.get("component") and node.component != filters["component"]:
                keep_node = False

            # Capability filter
            if (
                filters.get("capability")
                and node.capability_id != filters["capability"]
            ):
                keep_node = False

            if keep_node:
                filtered_nodes[node_id] = node

        # Filter links to only include nodes that remain
        filtered_links = []
        node_ids = set(filtered_nodes.keys())

        for link in links:
            if link.source in node_ids and link.target in node_ids:
                filtered_links.append(link)

        return filtered_nodes, filtered_links

    def _initialize_positions(self, nodes: Dict[str, Node]) -> None:
        """Set initial random positions for nodes."""
        center_x = self.layout.width / 2
        center_y = self.layout.height / 2
        radius = min(self.layout.width, self.layout.height) / 4

        for i, node in enumerate(nodes.values()):
            # Circular initial layout
            angle = 2 * math.pi * i / len(nodes)
            node.x = center_x + radius * math.cos(angle)
            node.y = center_y + radius * math.sin(angle)

            # Add some randomness
            node.x += random.uniform(-50, 50)
            node.y += random.uniform(-50, 50)

    def _render_svg(
        self, nodes: Dict[str, Node], links: List[Link], capabilities: List[dict]
    ) -> str:
        """Generate the complete SVG markup."""
        svg_parts = []

        # SVG header with proper namespace and styling
        svg_parts.append(
            f"""<svg width="100%" height="100%" viewBox="0 0 {self.layout.width} {self.layout.height}"
                 xmlns="http://www.w3.org/2000/svg"
                 preserveAspectRatio="xMidYMid meet"
                 style="max-width: 100%; height: auto;">"""
        )

        # Add CSS styling
        svg_parts.append(self._generate_css())

        # Add arrow markers for dependencies
        svg_parts.append(self._generate_markers())

        # Render capability clusters
        svg_parts.append(self._render_capability_clusters(nodes, capabilities))

        # Render links
        svg_parts.append(self._render_links(nodes, links))

        # Render nodes
        svg_parts.append(self._render_nodes(nodes))

        # Close SVG
        svg_parts.append("</svg>")

        return "\n".join(svg_parts)

    def _generate_css(self) -> str:
        """Generate embedded CSS for the SVG."""
        return """
        <style>
            .node { cursor: pointer; }
            .node:hover { filter: brightness(1.2); }
            .node-label {
                font-family: Arial, sans-serif;
                font-size: 10px;
                font-weight: bold;
                text-anchor: middle;
                dominant-baseline: central;
                fill: #333;
                pointer-events: none;
            }
            .link { fill: none; stroke-width: 2; }
            .capability-cluster { fill-opacity: 0.1; stroke-width: 2; stroke-dasharray: 5,5; }
            .capability-label {
     font-family: Arial,
    sans-serif; font-size: 12px; font-weight: bold; text-anchor: middle; fill: #495057; 
}
            .link-blocking { stroke: #e74c3c; stroke-width: 5; }
            .link-prerequisite { stroke: #3498db; stroke-width: 4; }
            .link-technical { stroke: #9b59b6; stroke-width: 4; }
            .link-business { stroke: #27ae60; stroke-width: 4; }
            .link-informational { stroke: #95a5a6; stroke-width: 3; stroke-dasharray: 8,4; }
        </style>
        """

    def _generate_markers(self) -> str:
        """Generate SVG marker definitions for dependency arrows."""
        markers = ["<defs>"]

        for dep_type, color in self.dependency_colors.items():
            size = 12 if dep_type == "blocking" else 10
            markers.append(
                f"""
            <marker id="arrow-{dep_type}" markerWidth="{size}" markerHeight="{size // 2 * 3}"
                    refX="{size - 1}" refY="{size // 2}" orient="auto" markerUnits="strokeWidth">
                <polygon points="0 0,
    {size} {size // 2},
    0 {size}" fill="{color}" />
            </marker>"""
            )

        markers.append("</defs>")
        return "\n".join(markers)

    def _render_capability_clusters(
        self, nodes: Dict[str, Node], capabilities: List[dict]
    ) -> str:
        """Render capability cluster backgrounds."""
        if not capabilities:
            return ""

        # Group nodes by capability
        capability_groups = {}
        for node in nodes.values():
            cap_id = node.capability_id or "unassigned"
            if cap_id not in capability_groups:
                capability_groups[cap_id] = []
            capability_groups[cap_id].append(node)

        cluster_parts = ['<g class="capability-clusters">']

        for cap_id, cap_nodes in capability_groups.items():
            if len(cap_nodes) < 2:  # Skip single-node clusters
                continue

            # Calculate cluster bounds
            xs = [node.x for node in cap_nodes]
            ys = [node.y for node in cap_nodes]
            center_x = sum(xs) / len(xs)
            center_y = sum(ys) / len(ys)

            # Calculate radius to encompass all nodes with padding
            max_distance = 0
            for node in cap_nodes:
                distance = math.sqrt(
                    (node.x - center_x) ** 2 + (node.y - center_y) ** 2
                )
                max_distance = max(max_distance, distance)

            radius = max_distance + 50  # Add padding
            color = self.capability_colors.get(cap_id, "#95a5a6")

            # Find capability name
            cap_name = cap_id
            if cap_id != "unassigned":
                for cap in capabilities:
                    if cap.get("capability_id") == cap_id:
                        cap_name = cap.get("name", cap_id)
                        break

            cluster_parts.append(
                f"""
            <circle cx="{center_x}" cy="{center_y}" r="{radius}"
                    class="capability-cluster" stroke="{color}" fill="{color}" />
            <text x="{center_x}" y="{center_y - radius - 15}" class="capability-label">
                {escape(cap_name)}
            </text>"""
            )

        cluster_parts.append("</g>")
        return "\n".join(cluster_parts)

    def _render_links(self, nodes: Dict[str, Node], links: List[Link]) -> str:
        """Render dependency links between nodes."""
        link_parts = ['<g class="links">']

        for link in links:
            source_node = nodes[link.source]
            target_node = nodes[link.target]

            # Calculate link endpoints at node borders
            dx = target_node.x - source_node.x
            dy = target_node.y - source_node.y
            distance = math.sqrt(dx * dx + dy * dy)

            if distance == 0:
                continue

            # Offset by node radius to start/end at circle edge
            node_radius = self.layout.node_radius + 5
            offset_x = (dx / distance) * node_radius
            offset_y = (dy / distance) * node_radius

            x1 = source_node.x + offset_x
            y1 = source_node.y + offset_y
            x2 = target_node.x - offset_x
            y2 = target_node.y - offset_y

            # Link styling
            css_class = f"link link-{link.type}"
            marker = f"url(#arrow-{link.type})"

            link_parts.append(
                f"""
            <line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"
                  class="{css_class}" marker-end="{marker}">
                <title>{escape(link.reason)}</title>
            </line>"""
            )

        link_parts.append("</g>")
        return "\n".join(link_parts)

    def _render_nodes(self, nodes: Dict[str, Node]) -> str:
        """Render epic nodes with status colors and capability borders."""
        node_parts = ['<g class="nodes">']

        for node in nodes.values():
            # Node colors
            status_color = self.colors.get(node.status, self.colors["default"])
            capability_color = self.capability_colors.get(
                node.capability_id or "unassigned", "#95a5a6"
            )

            # Calculate radius based on completion
            base_radius = self.layout.node_radius
            completion_bonus = (node.completion_percentage / 100) * 5
            inner_radius = base_radius + completion_bonus
            outer_radius = inner_radius + 4

            # Build tooltip content
            tooltip_parts = [
                f"{node.epic_id}: {node.title}",
                f"Status: {node.status}",
                f"Component: {node.component}",
                f"Completion: {node.completion_percentage:.1f}%",
                f"Priority: {node.priority}",
            ]

            if node.capability_name:
                tooltip_parts.append(
                    f"Capability: {node.capability_id} - {node.capability_name}"
                )
            else:
                tooltip_parts.append("⚠️ No capability assigned")

            tooltip_text = escape("\n".join(tooltip_parts))

            # Render node group
            node_parts.append(
                f"""
            <g class="node" transform="translate({node.x},
    {node.y}
)">
                <!-- Capability border (outer circle) -->
                <circle r="{outer_radius}" fill="none" stroke="{capability_color}"
                        stroke-width="3" opacity="0.8" />

                <!-- Epic status circle (inner circle) -->
                <circle r="{inner_radius}" fill="{status_color}" stroke="#fff"
                        stroke-width="2" class="epic-node">
                    <title>{tooltip_text}</title>
                </circle>

                <!-- Epic ID label -->
                <text class="node-label">{escape(node.epic_id)}</text>
            </g>"""
            )

        node_parts.append("</g>")
        return "\n".join(node_parts)

#!/usr/bin/env python3
"""
Simple visualization of the knowledge graph statistics and structure.
This creates a text-based summary of the graph for quick inspection.
"""

import json
import sys
from collections import Counter
from pathlib import Path


def visualize_graph(graph_path: Path):
    """Create a text visualization of the knowledge graph"""

    if not graph_path.exists():
        print(f"❌ Graph file not found: {graph_path}")
        sys.exit(1)

    with open(graph_path, encoding="utf-8") as f:
        graph_data = json.load(f)

    nodes = graph_data.get("nodes", [])
    links = graph_data.get("links", [])

    print("\n" + "=" * 80)
    print("KNOWLEDGE GRAPH VISUALIZATION")
    print("=" * 80 + "\n")

    # Basic stats
    print("📊 GRAPH STATISTICS")
    print(f"{'─' * 80}")
    print(f"Total Nodes:  {len(nodes):3d}")
    print(f"Total Edges:  {len(links):3d}")
    print(f"Avg Degree:   {(len(links) * 2 / len(nodes)) if nodes else 0:.2f}")
    print()

    # Topic distribution
    topic_counts = Counter()
    for node in nodes:
        for tag in node.get("tags", []):
            topic_counts[tag] += 1

    if topic_counts:
        print("🏷️  TOPIC DISTRIBUTION")
        print(f"{'─' * 80}")
        max_count = max(topic_counts.values())
        for topic, count in topic_counts.most_common():
            bar_length = int((count / max_count) * 40)
            bar = "█" * bar_length
            print(f"{topic:20s} │ {bar} {count:2d} nodes")
        print()

    # Node connectivity
    node_connections = Counter()
    for link in links:
        node_connections[link["source"]] += 1
        node_connections[link["target"]] += 1

    if node_connections:
        print("🔗 NODE CONNECTIVITY")
        print(f"{'─' * 80}")
        isolated = sum(
            1 for n in nodes if node_connections.get(n.get("id", nodes.index(n)), 0) == 0
        )
        avg_connections = sum(node_connections.values()) / len(nodes) if nodes else 0
        max_connections = max(node_connections.values()) if node_connections else 0

        print(
            f"Isolated nodes:  {isolated:3d} ({(isolated / len(nodes) * 100) if nodes else 0:.1f}%)"
        )
        print(f"Avg connections: {avg_connections:5.2f}")
        print(f"Max connections: {max_connections:3d}")
        print()

    # Sample nodes by topic
    print("📄 SAMPLE NODES BY TOPIC")
    print(f"{'─' * 80}")

    nodes_by_topic = {}
    for node in nodes:
        for tag in node.get("tags", ["untagged"]):
            if tag not in nodes_by_topic:
                nodes_by_topic[tag] = []
            nodes_by_topic[tag].append(node)

    for topic, topic_nodes in sorted(nodes_by_topic.items()):
        print(f"\n{topic.upper()}:")
        for node in topic_nodes[:3]:  # Show first 3 nodes per topic
            title = node.get("title", "Untitled")[:60]
            keywords = node.get("keywords", [])[:3]
            print(f"  • {title}")
            if keywords:
                print(f"    Keywords: {', '.join(keywords)}")

    print("\n" + "=" * 80)
    print(f"Graph file: {graph_path}")
    print("=" * 80 + "\n")


def main():
    if len(sys.argv) > 1:
        graph_path = Path(sys.argv[1])
    else:
        # Default to showcase output
        graph_path = Path(__file__).parent / "showcase_output" / "knowledge_graph" / "graph.json"

    visualize_graph(graph_path)


if __name__ == "__main__":
    main()

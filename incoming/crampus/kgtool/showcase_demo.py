#!/usr/bin/env python3
"""
Live Demo: Knowledge Graph Tool Showcase
=========================================

This script demonstrates the full power of kgtool with a realistic workflow.
Run this to see the tool in action!

Usage:
    python showcase_demo.py
"""

import json
import subprocess
import sys
from pathlib import Path
import shutil


def print_section(title: str):
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def run_command(cmd: list, description: str):
    """Run a command and show output"""
    print(f"🚀 {description}")
    print(f"💻 Command: {' '.join(cmd)}\n")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.stdout:
        print(result.stdout)
    
    if result.returncode != 0:
        print(f"❌ Error: {result.stderr}")
        return False
    
    print("✅ Success!\n")
    return True


def show_file_preview(filepath: Path, max_lines: int = 20):
    """Show a preview of a file"""
    if not filepath.exists():
        print(f"❌ File not found: {filepath}")
        return
    
    print(f"📄 Preview of {filepath.name}:")
    print("-" * 80)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        for i, line in enumerate(lines[:max_lines], 1):
            print(f"{i:3d} | {line.rstrip()}")
        
        if len(lines) > max_lines:
            print(f"... ({len(lines) - max_lines} more lines)")
    
    print("-" * 80 + "\n")


def analyze_graph(graph_path: Path):
    """Analyze and display graph statistics"""
    with open(graph_path, 'r', encoding='utf-8') as f:
        graph_data = json.load(f)
    
    nodes = graph_data.get('nodes', [])
    links = graph_data.get('links', [])
    
    print("📊 Graph Statistics:")
    print(f"   • Total Nodes: {len(nodes)}")
    print(f"   • Total Edges: {len(links)}")
    
    # Analyze topics
    topics_count = {}
    for node in nodes:
        for tag in node.get('tags', []):
            topics_count[tag] = topics_count.get(tag, 0) + 1
    
    if topics_count:
        print(f"\n   • Topic Distribution:")
        for topic, count in sorted(topics_count.items(), key=lambda x: x[1], reverse=True):
            print(f"     - {topic}: {count} nodes")
    
    # Show sample node
    if nodes:
        print(f"\n   • Sample Node (node 0):")
        node = nodes[0]
        print(f"     - Title: {node.get('title', 'N/A')}")
        print(f"     - Tags: {', '.join(node.get('tags', []))}")
        print(f"     - Keywords: {', '.join(node.get('keywords', [])[:5])}...")
    
    print()


def count_words(filepath: Path) -> int:
    """Count words in a file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return len(f.read().split())


def main():
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║                  KNOWLEDGE GRAPH TOOL - LIVE SHOWCASE                      ║
║                                                                            ║
║         Transform massive documentation into focused context               ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Setup
    base_dir = Path(__file__).parent
    tests_dir = base_dir / "tests"
    data_dir = tests_dir / "data"
    output_dir = base_dir / "showcase_output"
    
    # Clean previous output
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    input_doc = data_dir / "enterprise_architecture_spec.md"
    
    if not input_doc.exists():
        print(f"❌ Demo document not found: {input_doc}")
        print("   Make sure you're running from the knowledge_graph_tool directory")
        sys.exit(1)
    
    # Get document stats
    total_words = count_words(input_doc)
    print(f"📚 Input Document: {input_doc.name}")
    print(f"   Size: {total_words:,} words")
    print(f"   File: {input_doc.stat().st_size / 1024:.1f} KB\n")
    
    # ============================================================================
    # STEP 1: Discover Topics
    # ============================================================================
    print_section("STEP 1: Discover Topics (Unsupervised Learning)")
    
    topics_file = output_dir / "discovered_topics.json"
    
    success = run_command(
        ["kgtool", "discover-topics",
         "--input", str(input_doc),
         "--output", str(topics_file),
         "--num-topics", "5",
         "--terms-per-topic", "15"],
        "Discovering topics using K-Means clustering on TF-IDF vectors"
    )
    
    if not success:
        print("❌ Failed to discover topics")
        sys.exit(1)
    
    # Show discovered topics
    with open(topics_file, 'r', encoding='utf-8') as f:
        topics = json.load(f)
    
    print("🎯 Discovered Topics:\n")
    for topic_id, terms in topics.items():
        print(f"   {topic_id}: {', '.join(terms[:10])}...")
    
    print("\n💡 TIP: Edit discovered_topics.json to rename topics to something meaningful!")
    print("   e.g., topic_0 -> 'frontend', topic_1 -> 'backend', etc.\n")
    
    # Create a human-readable version
    human_topics = {
        "frontend": topics.get("topic_0", []),
        "backend": topics.get("topic_1", []),
        "infrastructure": topics.get("topic_2", []),
        "security": topics.get("topic_3", []),
        "data": topics.get("topic_4", [])
    }
    
    human_topics_file = output_dir / "topics_human_readable.json"
    with open(human_topics_file, 'w', encoding='utf-8') as f:
        json.dump(human_topics, f, indent=2)
    
    print(f"📝 Created human-readable topics: {human_topics_file.name}\n")
    
    # ============================================================================
    # STEP 2: Build Knowledge Graph
    # ============================================================================
    print_section("STEP 2: Build Knowledge Graph with Topic Classification")
    
    graph_dir = output_dir / "knowledge_graph"
    
    success = run_command(
        ["kgtool", "build",
         "--input", str(input_doc),
         "--output", str(graph_dir),
         "--min-sim", "0.25",
         "--top-keywords", "8",
         "--top-keyphrases", "10",
         "--topics", str(human_topics_file)],
        "Building graph with semantic relationships and topic tagging"
    )
    
    if not success:
        print("❌ Failed to build graph")
        sys.exit(1)
    
    # Analyze the graph
    graph_file = graph_dir / "graph.json"
    analyze_graph(graph_file)
    
    # Show a sample node file
    nodes_dir = graph_dir / "nodes"
    node_files = list(nodes_dir.glob("*.md"))
    if node_files:
        print("📄 Sample Node File:")
        show_file_preview(node_files[0], max_lines=15)
    
    # ============================================================================
    # STEP 3: Extract Topic-Specific Context
    # ============================================================================
    print_section("STEP 3: Extract Topic-Specific Context")
    
    topics_to_extract = ["frontend", "backend", "infrastructure"]
    
    context_stats = []
    
    for topic in topics_to_extract:
        output_file = output_dir / f"{topic}_context.md"
        
        print(f"\n🎯 Extracting '{topic}' context...")
        
        success = run_command(
            ["kgtool", "extract",
             "--topic", topic,
             "--graph", str(graph_file),
             "--output", str(output_file),
             "--include-neighbors"],
            f"Extracting {topic}-specific context with neighbor nodes"
        )
        
        if success:
            words = count_words(output_file)
            context_stats.append((topic, words))
            print(f"   📝 {topic}_context.md: {words:,} words\n")
    
    # ============================================================================
    # STEP 4: Show Results & Savings
    # ============================================================================
    print_section("STEP 4: Results & Impact Analysis")
    
    print("📊 CONTEXT EXTRACTION RESULTS:\n")
    print(f"   Original Document: {total_words:,} words (baseline)")
    print()
    
    for topic, words in context_stats:
        reduction = ((total_words - words) / total_words) * 100
        token_estimate = words * 0.75  # rough estimate: 1 word ≈ 0.75 tokens
        
        print(f"   {topic.capitalize()} Context:")
        print(f"      • Words: {words:,}")
        print(f"      • Reduction: {reduction:.1f}%")
        print(f"      • Est. tokens: ~{token_estimate:.0f}")
        print()
    
    print("💰 TOKEN SAVINGS ESTIMATION:")
    print(f"   If you query GPT-4 with full doc: ~{total_words * 0.75:.0f} tokens/request")
    print(f"   If you query with focused context: ~{context_stats[0][1] * 0.75:.0f} tokens/request (avg)")
    print(f"   Cost reduction (at $0.015/1K tokens): ~${(total_words * 0.75 - context_stats[0][1] * 0.75) * 0.015 / 1000:.4f} per request")
    print()
    
    # ============================================================================
    # STEP 5: Preview Extracted Context
    # ============================================================================
    print_section("STEP 5: Preview of Extracted Context")
    
    frontend_file = output_dir / "frontend_context.md"
    if frontend_file.exists():
        print("🎨 Frontend Context Preview (first 25 lines):")
        show_file_preview(frontend_file, max_lines=25)
    
    # ============================================================================
    # Summary
    # ============================================================================
    print_section("✨ SHOWCASE COMPLETE!")
    
    print(f"""
All outputs saved to: {output_dir}

Generated files:
  📊 discovered_topics.json          - Machine-discovered topics
  📝 topics_human_readable.json      - Human-friendly topic names
  🕸️  knowledge_graph/
      ├── graph.json                 - Complete knowledge graph
      └── nodes/                     - Individual node markdown files
  📄 frontend_context.md             - Frontend-only context
  📄 backend_context.md              - Backend-only context
  📄 infrastructure_context.md       - Infrastructure-only context

Next steps:
  1. Explore the generated files
  2. Try extracting different topics
  3. Adjust --min-sim for tighter/looser relationships
  4. Feed extracted contexts to your LLM for focused responses

🚀 Ready to process your own documentation? Just run:
   kgtool build --input your_doc.md --output your_output
    """)


if __name__ == "__main__":
    main()

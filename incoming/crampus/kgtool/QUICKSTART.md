# Quick Start Guide - kgtool

Get started with the Knowledge Graph Tool in 5 minutes!

## Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd kgtool

# Install dependencies
uv sync --extra test

# Verify installation
kgtool --help
```

## Your First Graph in 3 Commands

### 1. Discover Topics (Automatic)

```bash
kgtool discover-topics \
    --input tests/data/sample_spec.md \
    --output topic_terms.json \
    --num-topics 4 \
    --terms-per-topic 10
```

**What it does:** Analyzes your document and automatically identifies 4 major topics using machine learning.

**Output:** `topic_terms.json` with discovered topics like:
```json
{
  "topic_0": ["frontend", "react", "ui", "component", ...],
  "topic_1": ["backend", "api", "service", "database", ...],
  ...
}
```

### 2. Build the Knowledge Graph

```bash
kgtool build \
    --input tests/data/sample_spec.md \
    --output my_graph \
    --min-sim 0.3 \
    --topics topic_terms.json
```

**What it does:** 
- Creates a graph with nodes (document sections) and edges (relationships)
- Tags each node with relevant topics
- Extracts keywords and keyphrases
- Generates individual markdown files for each concept

**Output:** 
- `my_graph/graph.json` - Complete graph data
- `my_graph/nodes/node_*.md` - Individual concept files

### 3. Extract Topic-Specific Context

```bash
kgtool extract \
    --topic frontend \
    --graph my_graph/graph.json \
    --output frontend_only.md \
    --include-neighbors
```

**What it does:** Extracts ONLY frontend-related content plus connected concepts.

**Output:** `frontend_only.md` - Focused documentation (typically 60-80% smaller)

## Live Demo

Run the interactive showcase:

```bash
python showcase_demo.py
```

This will:
1. ✨ Process a real enterprise architecture document
2. 📊 Show before/after statistics
3. 💰 Calculate token/cost savings
4. 📄 Generate example outputs

## Common Use Cases

### For AI Development

```bash
# Build once
kgtool build --input docs/architecture.md --output knowledge_base

# Query many times with focused context
kgtool extract --topic backend --graph knowledge_base/graph.json --output backend_ctx.md
# Feed backend_ctx.md to your LLM instead of full docs
```

### For Documentation Analysis

```bash
# Discover what topics exist in your massive docs
kgtool discover-topics --input huge_spec.md --output discovered.json --num-topics 8

# Visualize by examining the graph
cat output/graph.json | jq '.nodes[] | {title, tags}'
```

### For Team Onboarding

```bash
# Generate role-specific documentation
kgtool extract --topic frontend --graph kb/graph.json --output for_frontend_devs.md
kgtool extract --topic devops --graph kb/graph.json --output for_sre_team.md
kgtool extract --topic security --graph kb/graph.json --output for_security_review.md
```

## Understanding the Parameters

### `--min-sim` (similarity threshold)

Controls how concepts are linked:

- `0.4` - Very strict, only highly related concepts linked (fewer edges)
- `0.3` - Balanced (default, recommended)
- `0.15` - Loose, more connections (more context, some noise)

### `--top-keywords` and `--top-keyphrases`

Controls information extraction per node:

- Higher numbers = more detail per concept
- Lower numbers = more focused, essential terms only
- Default: 5 keywords, 5 keyphrases

### `--include-neighbors`

When extracting context:

- **With flag**: Includes connected concepts (recommended for LLMs)
- **Without flag**: Only exact topic matches (ultra-focused)

## Troubleshooting

### "No headings found"

Your document needs markdown headings (# or ##). Add them to structure your content.

### "n_samples should be >= n_clusters"

You asked for more topics than sections exist. Reduce `--num-topics`.

### Graph has 0 edges

Your `--min-sim` is too high. Try 0.2 or 0.15 to create more connections.

## What's Next?

1. **Process your own docs**: Replace test files with your documentation
2. **Integrate with LLMs**: Feed extracted contexts to GPT-4, Claude, etc.
3. **Automate**: Add to CI/CD to auto-update knowledge graphs
4. **Explore**: Check out `showcase_output/` folder to see real results

## Examples with Real Data

All examples use included test data:

```bash
# Small document (3,500 words)
kgtool build --input tests/data/sample_spec.md --output output_small

# Large document (10,000+ words)  
kgtool build --input tests/data/enterprise_architecture_spec.md --output output_large

# Chaotic/messy document (stress test)
kgtool build --input tests/data/chaotic_mess.md --output output_chaos
```

## Need Help?

- Run `kgtool --help` for command options
- Check `README.md` for detailed documentation
- Run `python showcase_demo.py` for a live walkthrough
- Look at test files in `tests/` for code examples

---

**Ready?** Run your first command now! 🚀

```bash
python showcase_demo.py
```

# Add LLM-assisted UX + better retrieval (natural language) without making the core heavy

## 1) Principle: LLM is an optional “orchestrator”, not a dependency
- Core still works with FTS + (optional) embeddings.
- LLM is used to:
  - translate natural language → structured retrieval plan,
  - re-rank + compress results into LLM-ready context,
  - generate queries, expansions, and “follow-up fetch” suggestions.
- Provide multiple backends (OpenAI/OpenRouter/Ollama) via HTTP.

## 2) New capabilities

### A) Natural language query → retrieval plan
Add a command:
- `kg ask --q "<natural language>" [--doc <id>] [--budget 12000] [--policy direct+ancestors] [--window 1] [--model ...]`

LLM output (JSON) describes:
- which retrieval method(s) to use:
  - FTS query
  - semantic query (embedding)
  - heading path constraints
  - node kinds (heading/paragraph/codeblock)
  - time/section constraints (if metadata exists)
- how much to expand and what to collapse:
  - expansion policy + context window size
  - maximum bytes/tokens per node
- whether to ask follow-up questions (if ambiguous)

### B) LLM re-ranking and “answer-focused” context packing
Pipeline:
1) gather candidates via FTS + semsearch (top N each)
2) dedupe by `full_id` / overlaps
3) LLM re-ranks candidates by relevance to the user query
4) render skeleton with selective expansion
5) optionally: “summary nodes” (derived artifacts) that cite node IDs

This improves relevance without losing traceability.

### C) LLM-assisted “structured output mode”
Add:
- `kg pack --q "<natural language>" --format md|json --budget ...`

Outputs:
- a Markdown pack with:
  - short outline of sections chosen,
  - expanded node spans,
  - references for collapsed nodes (`[@ABCD]`),
  - a provenance block listing included node IDs.
- or a JSON object suitable for downstream agents:
  - `{query, included_ids, collapsed_ids, render_policy, snippets}`

### D) LLM-driven expansion refinement (interactive)
Add optional prompt loop:
- `kg chat --doc <id>` (REPL)
User: “Focus on the part about projections and eventual consistency, ignore deployment.”
Tool:
- runs `ask` plan,
- shows skeleton+expanded,
- offers “expand these refs” suggestions as buttons/commands:
  - `kg expand --id ABCD`
  - `kg render --filter ... --window 2`

### E) LLM-aided parsing upgrades (optional)
LLM can help:
- infer section titles for paragraphs without headings,
- classify block types more accurately (esp. messy text),
- extract entities/tags for better graph edges.

But keep it “post-processing”:
- don’t let the LLM rewrite raw text nodes unless explicitly requested.
- derived nodes get kind `derived` and store provenance edges (`derived_from`).

## 3) Safety + determinism rules (so results don’t drift)

### Hard rules
- Reconstruction always uses raw spans (never LLM).
- LLM output must be *validated* against a JSON schema before execution.
- Any derived content must cite node IDs.
- Any plan that would exceed `--budget` is automatically reduced deterministically (e.g., shrink k, reduce window, prefer headings).

### Validation schema (example fields)
- `mode`: `fts|semantic|hybrid`
- `fts_query`: string
- `semantic_query`: string
- `k_fts`, `k_sem`: ints
- `kinds`: list
- `doc_scope`: list of doc_ids or empty
- `policy`: `direct|direct+ancestors|direct+ancestors+siblings`
- `window`: int
- `budget_bytes`: int
- `output_format`: `md|json`
- `followups`: list of questions (optional)

## 4) Minimal implementation approach

### LLM interface module
- `kgshred/llm/client.py`:
  - HTTP adapters: `openai`, `openrouter`, `ollama`
  - standard method: `complete_json(prompt, schema) -> dict`

No heavy deps required; use stdlib `urllib.request` or optional `httpx` under extras.

### Prompting strategy (short, reliable)
System prompt:
- “You are a query planner. Output ONLY JSON matching schema.”
User prompt:
- include:
  - the user query,
  - available docs (optional),
  - allowed node kinds,
  - max budget,
  - examples of valid outputs.

### Execution engine
- `planner.py` validates JSON, then:
  - runs FTS/semantic retrieval,
  - re-ranks (optional),
  - calls renderer with selective expansion.

## 5) New CLI commands (minimal set)

### Primary
- `kg ask --q "<nl>" [--doc ...] [--model ...] [--budget ...]`
  - outputs packed Markdown (structure + expanded matches + refs)

### Advanced
- `kg plan --q "<nl>" --json` (debug: prints the retrieval plan JSON)
- `kg pack --q "<nl>" --format md|json`
- `kg rerank --q "<nl>" --ids <ABCD,...>` (optional utility)

## 6) Suggested UX defaults (works well in practice)
- Hybrid retrieval by default:
  - `k_fts=40`, `k_sem=40`, then rerank to `k_final=20`
- Expansion policy:
  - `direct+ancestors`, `window=1`
- Budget:
  - default bytes cap, e.g. `--budget-bytes 80_000` (stable, deterministic)
- Always include:
  - headings for structure,
  - provenance list of expanded node IDs.

## 7) Note about the attached reference file
The previously attached repo snapshot is no longer accessible in this session (expired). If you want specific mapping from that repo’s current design to this new architecture (module-by-module diffs), re-upload it.

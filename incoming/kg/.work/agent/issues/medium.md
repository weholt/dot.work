# Medium Priority Issues (P2)

Enhancements, technical debt, valuable improvements.

---

## FEAT-013@a3f6c9 — LLM Query Planner Interface

```yaml
id: "FEAT-013@a3f6c9"
title: "LLM Query Planner Interface"
description: "Implement LLM client for translating natural language to retrieval plans."
created: 2024-12-19
section: "llm"
tags: [llm, query-planner, natural-language, json-schema]
type: enhancement
priority: medium
status: proposed
references:
  - src/kgshred/llm/client.py
  - src/kgshred/llm/planner.py
  - chat-2.md#4-minimal-implementation
```

### Problem
Natural language queries need translation to structured retrieval plans (FTS query, semantic query, filters).

### Affected Files
- `src/kgshred/llm/__init__.py` (to create)
- `src/kgshred/llm/client.py` (to create)
- `src/kgshred/llm/planner.py` (to create)
- `tests/unit/test_llm_planner.py` (to create)
- `tests/integration/test_llm_planner_integration.py` (to create)

### Importance
Enables `kg ask` command for natural language queries. High-value UX improvement.

### Proposed Solution
From chat-2.md section 4:

**LLM client:**
- `complete_json(prompt, schema) -> dict`
- Backends: openai, openrouter, ollama

**Planner:**
- System prompt: "You are a query planner. Output ONLY JSON matching schema."
- User prompt: query + available docs + allowed kinds + budget + examples
- Validate output against JSON schema

**Plan schema fields:**
- `mode`: fts | semantic | hybrid
- `fts_query`, `semantic_query`: strings
- `k_fts`, `k_sem`: ints
- `kinds`: list
- `policy`: direct | direct+ancestors | direct+ancestors+siblings
- `window`: int
- `budget_bytes`: int

### Acceptance Criteria
- [ ] LLM client with multiple backends
- [ ] JSON schema validation on output
- [ ] Plan includes retrieval method, queries, filters
- [ ] Falls back gracefully if LLM unavailable
- [ ] Budget constraints respected

### Unit Tests — `tests/unit/test_llm_planner.py`

```python
# LLM client
def test_llm_client_sends_prompt():
    """Client should send prompt to LLM."""

def test_llm_client_includes_system_prompt():
    """Client should include system prompt."""

def test_llm_client_parses_json_response():
    """Client should parse JSON from response."""

def test_llm_client_validates_json_schema():
    """Client should validate response against schema."""

def test_llm_client_handles_invalid_json():
    """Should raise error on invalid JSON."""

def test_llm_client_handles_schema_violation():
    """Should raise error on schema mismatch."""

def test_llm_client_retries_on_failure():
    """Should retry on transient failures."""

def test_llm_client_timeout():
    """Should timeout after configured duration."""

# Query planner
def test_planner_returns_plan():
    """Planner should return valid plan object."""

def test_planner_plan_has_mode():
    """Plan should specify mode (fts/semantic/hybrid)."""

def test_planner_plan_has_queries():
    """Plan should include fts_query and/or semantic_query."""

def test_planner_plan_has_k_values():
    """Plan should include k_fts and k_sem."""

def test_planner_plan_has_policy():
    """Plan should include expansion policy."""

def test_planner_plan_has_budget():
    """Plan should include budget_bytes."""

def test_planner_respects_max_budget():
    """Plan budget should not exceed max allowed."""

# Plan generation
def test_planner_includes_context():
    """Planner prompt should include available docs."""

def test_planner_includes_examples():
    """Planner prompt should include few-shot examples."""

def test_planner_handles_simple_query():
    """Simple query should produce simple plan."""

def test_planner_handles_complex_query():
    """Complex query should produce appropriate plan."""

# Fallback
def test_planner_fallback_on_llm_unavailable():
    """Should return default plan if LLM unavailable."""

def test_planner_fallback_plan_is_valid():
    """Fallback plan should be valid and usable."""

# Backend selection
def test_llm_client_openai_backend():
    """Should use OpenAI backend when configured."""

def test_llm_client_ollama_backend():
    """Should use Ollama backend when configured."""

def test_llm_client_openrouter_backend():
    """Should use OpenRouter backend when configured."""
```

### Integration Tests — `tests/integration/test_llm_planner_integration.py`

```python
@pytest.mark.integration
def test_planner_with_real_llm(llm_available):
    """Should generate plan using real LLM."""

@pytest.mark.integration
def test_planner_plan_executable():
    """Generated plan should execute successfully."""

@pytest.mark.integration
def test_planner_with_large_context():
    """Planner should handle large context gracefully."""
```

---

## FEAT-014@b4a7d1 — `kg ask` Command (Natural Language Query)

```yaml
id: "FEAT-014@b4a7d1"
title: "`kg ask` Command (Natural Language Query)"
description: "Implement natural language query command using LLM planner and hybrid retrieval."
created: 2024-12-19
section: "cli"
tags: [cli, ask, natural-language, hybrid-retrieval]
type: enhancement
priority: medium
status: proposed
references:
  - src/kgshred/cli.py
  - chat-2.md#2-new-capabilities
  - chat-2.md#5-new-cli-commands
```

### Problem
Users want to ask questions in natural language rather than crafting FTS queries.

### Affected Files
- `src/kgshred/cli.py` (to extend)
- `src/kgshred/commands/ask.py` (to create)
- `tests/integration/test_ask.py` (to create)

### Importance
Primary UX improvement. Makes tool accessible to non-technical users.

### Proposed Solution
From chat-2.md sections 2 and 5:

**Command:**
```
kg ask --q "<natural language>" [--doc <id>] [--budget 12000] [--policy direct+ancestors] [--window 1] [--model ...]
```

**Pipeline:**
1. LLM translates query to plan
2. Execute FTS + semantic search (hybrid)
3. Dedupe by full_id
4. Optionally re-rank via LLM
5. Render skeleton with selective expansion
6. Include provenance (node IDs)

**Defaults:**
- `k_fts=40`, `k_sem=40`, rerank to `k_final=20`
- `policy=direct+ancestors`, `window=1`
- `budget_bytes=80000`

### Acceptance Criteria
- [ ] Natural language query accepted
- [ ] Hybrid retrieval executed
- [ ] Results rendered as skeleton + expanded
- [ ] Provenance block with node IDs
- [ ] Budget constraints enforced

### Unit Tests — `tests/unit/test_ask.py`

```python
# Query handling
def test_ask_accepts_natural_language():
    """Should accept natural language query string."""

def test_ask_calls_planner():
    """Should call LLM planner with query."""

def test_ask_executes_plan():
    """Should execute the generated plan."""

# Hybrid retrieval
def test_ask_hybrid_fts_and_semantic():
    """Should run both FTS and semantic search."""

def test_ask_dedupes_results():
    """Should dedupe by full_id."""

def test_ask_reranks_results():
    """Should optionally rerank via LLM."""

# Rendering
def test_ask_renders_skeleton():
    """Should render document skeleton."""

def test_ask_expands_matches():
    """Should expand matching nodes."""

def test_ask_includes_provenance():
    """Output should include provenance block."""

# Budget enforcement
def test_ask_respects_budget():
    """Should not exceed budget_bytes."""

def test_ask_truncates_for_budget():
    """Should truncate output to meet budget."""

# Options
def test_ask_doc_filter():
    """--doc should limit to specific document."""

def test_ask_policy_option():
    """--policy should control expansion."""

def test_ask_window_option():
    """--window should control sibling inclusion."""

def test_ask_model_option():
    """--model should select LLM/embedding model."""
```

### Integration Tests — `tests/integration/test_ask.py`

```python
@pytest.mark.integration
def test_ask_end_to_end(ingested_corpus, llm_available):
    """Full ask pipeline should work."""

@pytest.mark.integration
def test_ask_with_real_llm():
    """Should work with real LLM backend."""

@pytest.mark.integration
def test_ask_fallback_without_llm():
    """Should fallback gracefully without LLM."""

@pytest.mark.integration
def test_ask_cli_invocation():
    """kg ask --q 'question' should work from CLI."""

@pytest.mark.integration
def test_ask_output_format():
    """Output should be readable markdown."""

@pytest.mark.integration
def test_ask_provenance_parseable():
    """Provenance block should be machine-parseable."""
```

---

## FEAT-015@c5b8e2 — `kg pack` Command (Structured Output)

```yaml
id: "FEAT-015@c5b8e2"
title: "`kg pack` Command (Structured Output)"
description: "Implement structured output command for LLM-ready context packs."
created: 2024-12-19
section: "cli"
tags: [cli, pack, output, json, markdown]
type: enhancement
priority: medium
status: proposed
references:
  - src/kgshred/cli.py
  - chat-2.md#2-new-capabilities
```

### Problem
Downstream agents need structured output format with clear provenance.

### Affected Files
- `src/kgshred/cli.py` (to extend)
- `src/kgshred/commands/pack.py` (to create)
- `tests/unit/test_pack.py` (to create)
- `tests/integration/test_pack.py` (to create)

### Importance
Enables tool integration with LLM agents and automation pipelines.

### Proposed Solution
From chat-2.md section 2C:

**Command:**
```
kg pack --q "<natural language>" --format md|json --budget ...
```

**Outputs:**
- **Markdown**: outline + expanded nodes + references + provenance
- **JSON**: `{query, included_ids, collapsed_ids, render_policy, snippets}`

### Acceptance Criteria
- [ ] Markdown format with outline and refs
- [ ] JSON format with full metadata
- [ ] Provenance block listing included IDs
- [ ] Budget constraints enforced
- [ ] Machine-parseable output

### Unit Tests — `tests/unit/test_pack.py`

```python
# Markdown format
def test_pack_markdown_includes_outline():
    """Markdown output should include document outline."""

def test_pack_markdown_includes_expanded():
    """Markdown should include expanded node content."""

def test_pack_markdown_includes_references():
    """Markdown should include reference links."""

def test_pack_markdown_includes_provenance():
    """Markdown should include provenance section."""

def test_pack_markdown_is_valid():
    """Markdown should be valid, parseable markdown."""

# JSON format
def test_pack_json_includes_query():
    """JSON should include original query."""

def test_pack_json_includes_included_ids():
    """JSON should list included node IDs."""

def test_pack_json_includes_collapsed_ids():
    """JSON should list collapsed node IDs."""

def test_pack_json_includes_policy():
    """JSON should include render policy."""

def test_pack_json_includes_snippets():
    """JSON should include content snippets."""

def test_pack_json_is_valid():
    """JSON should be valid, parseable JSON."""

# Budget
def test_pack_respects_budget():
    """Pack should not exceed budget_bytes."""

def test_pack_budget_applies_to_output():
    """Budget should limit final output size."""

# Options
def test_pack_format_md():
    """--format md should produce markdown."""

def test_pack_format_json():
    """--format json should produce JSON."""

def test_pack_default_format():
    """Default format should be markdown."""
```

### Integration Tests — `tests/integration/test_pack.py`

```python
@pytest.mark.integration
def test_pack_markdown_end_to_end():
    """Full pack → markdown pipeline."""

@pytest.mark.integration
def test_pack_json_end_to_end():
    """Full pack → JSON pipeline."""

@pytest.mark.integration
def test_pack_cli_invocation():
    """kg pack --q 'query' --format json should work."""

@pytest.mark.integration
def test_pack_json_parseable():
    """JSON output should be parseable by json.loads."""

@pytest.mark.integration
def test_pack_integration_with_ask():
    """Pack should work after ask pipeline."""
```

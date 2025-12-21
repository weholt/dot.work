# Instructions

Below is a chat I had with an llm about a stand-alone project I need that scans a codebase, source files, including markdown files and other documentation, to create a birdseye view of a project; the why & what, and how, without getting technical. It should use the source code, find the parts exposed to the end-user and create an overview of the project, a quick summary of the features, and a feature-by-feature walkthrough based on the findings given an explaination of all the features for a human to follow. Each feature should get a unique ID as well, and be just structured enough for an LLM to use the content to create gherkin scenarios or actual integration tests later.

**IMPORTANT** This should generate content aimed at a human user + structure json files. For the human, produce instructions only, with just enough details to guide the user, what to input and what to expect as result. Give a few examples per feature of possible, but keep each feature description small and lean.

For reference, this project creates a tutorial for any given gitrepo, and might serve as an inspiration: https://github.com/The-Pocket/PocketFlow-Tutorial-Codebase-Knowledge

The chat also consist of some python code, and the latest and most complete is at the end. Make sure to use that one.

## Output

- Create a detailed implementation plan using context7 and sequential thinking mcp tools to break the implementation into small enough tasks.
- A fully fleshed out project called birdseye, located in ./src/birdseye.
- Pyproject.toml with all dependencies
- An installable executable called birdseye which can take a folder as input and a folder for output.
- All generated reports should be in markdown
- Feel free to use mermaid charts to illustrate flow

## The actual chat

I have a substantial codebase, a python project, with lots of unittests, markdown files for project development like specifications and implementation plans, and I like to use all of the source code and the documents, to create an overview of all  the features described feature by feature, section by section, in a natural way (yet add enough structure to use it as base for testcases, each feature having a unique identifier), perhaps a lighter version of a gherkin format for each feature. The document should be as short as possible, yet capture enough details to serve as a full description of the project and every available function or feature.

How would I go about doing that? I was thinking I could create a python script that reads all the relevant source files and documents, prepares the content for llm processing, and save all that data to seperate files which then could be processed by an agent or otherwise be used to generate the overview/total description of all features. 

I need help with the script if that's of any help, and the prompt that should process the content.
ChatGPT said:

Correct approach. Break into two parts:

Extraction and preprocessing (Python script)

LLM summarization and structuring (prompt)

1. Extraction script

Goal: Collect all relevant content (source, docs, tests), normalize it, and output structured chunks for LLM input.

# filename: extract_features.py
"""
Extracts relevant code and docs from a Python project into structured text chunks
for LLM-based feature summarization.
"""

import os
import re
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
OUTPUT_DIR = PROJECT_ROOT / "feature_data"
INCLUDE_EXT = {".py", ".md"}
EXCLUDE_DIRS = {"__pycache__", ".venv", "venv", "build", "dist", ".git", ".github", "node_modules"}

def should_include(path: Path) -> bool:
    if any(part in EXCLUDE_DIRS for part in path.parts):
        return False
    return path.suffix in INCLUDE_EXT

def extract_code_sections(content: str) -> list[str]:
    """Extracts function, class, and docstring segments."""
    sections = []
    for match in re.finditer(r"(?P<header>^(def|class)\s[^\n]+)\n(?P<body>(?:\s{4}.+\n)+)", content, re.MULTILINE):
        block = match.group("header") + "\n" + match.group("body")
        sections.append(block.strip())
    return sections

def extract_md_sections(content: str) -> list[str]:
    """Extracts sections based on markdown headings."""
    sections = re.split(r"(?=^#{1,6}\s)", content, flags=re.MULTILINE)
    return [s.strip() for s in sections if s.strip()]

def save_chunks(chunks: list[dict], file: Path):
    OUTPUT_DIR.mkdir(exist_ok=True)
    file.write_text(json.dumps(chunks, indent=2, ensure_ascii=False))

def process_file(file: Path):
    text = file.read_text(encoding="utf-8", errors="ignore")
    if file.suffix == ".py":
        chunks = extract_code_sections(text)
    elif file.suffix == ".md":
        chunks = extract_md_sections(text)
    else:
        return []
    return [{"file": str(file.relative_to(PROJECT_ROOT)), "content": chunk} for chunk in chunks]

def main():
    all_chunks = []
    for path in PROJECT_ROOT.rglob("*"):
        if should_include(path):
            all_chunks.extend(process_file(path))
    save_chunks(all_chunks, OUTPUT_DIR / "project_chunks.json")
    print(f"Saved {len(all_chunks)} chunks to {OUTPUT_DIR/'project_chunks.json'}")

if __name__ == "__main__":
    main()

2. Prompt for the agent or LLM
---
description: "Summarize all project features and behaviors from extracted content"
tags: [feature-overview, summarization, gherkin-lite]
write_permissions:
  files:
    - .work/agent/features-overview.md
---

# Prompt: Project Feature Extraction and Structuring

## Objective
From the provided JSON chunks (source code and markdown), generate a concise, structured overview of all project features.

## Instructions

1. **Identify Features**
   - Detect functions, classes, APIs, CLI commands, or user-facing actions.
   - Merge related fragments across code and documentation.

2. **Describe Features**
   - Use a compact “gherkin-lite” format per feature:
     ```
     ### Feature: [feature name]
     ID: F-XXXX
     Source: [relative file paths]
     Description: One or two sentences explaining purpose.
     Preconditions: (if any)
     Expected Behavior: concise explanation of effect/output
     ```
   - Optional: Include notes from test cases or docstrings.

3. **Coverage**
   - Ensure every distinct feature or functionality has a corresponding entry.
   - If multiple related functions belong to one feature, merge under one heading.

4. **Output**
   - Save to `.work/agent/features-overview.md`.
   - Keep total document short, readable, and structured.

---

## Example Output

```markdown
### Feature: User Authentication
ID: F-0001
Source: auth/routes.py, auth/service.py
Description: Handles user login and token verification.
Preconditions: Valid user credentials stored in database.
Expected Behavior: Generates JWT token and validates subsequent requests.


Run process:

python extract_features.py
# Then pass feature_data/project_chunks.json to your LLM with the above prompt.


This creates a lightweight, structured feature map usable for documentation or test case generation.

You said:
are there statistical tools to use to extract such information from python source code that could help us doing this? 
ChatGPT said:

Yes. You can use static analysis, AST (Abstract Syntax Tree), and docstring inspection tools to extract semantic and statistical information from Python source code.
Below are the most useful categories and libraries.

1. AST-based structure extraction

Direct access to all function/class definitions, imports, and docstrings.

Library	Purpose	Notes
ast (built-in)	Parse Python source into a tree	Use ast.walk() to find FunctionDef, ClassDef, AsyncFunctionDef, etc.
asttokens	Keeps mapping between AST nodes and original text	Useful to extract exact code snippets
libcst	Concrete syntax tree with full fidelity (preserves formatting)	Good for refactoring and accurate parsing
parso	Parser used by Jedi	Handles incomplete code and comments
redbaron	High-level manipulation layer over CST	Simple for extracting human-readable blocks

You can compute metrics like:

Function count, class count, avg function length.

Cyclomatic complexity via radon.

Docstring presence ratio.

2. Static analysis / metrics
Tool	Purpose	Command/Usage
radon	Complexity, maintainability index, raw stats	radon cc -s -a . or import programmatically
pylint / flake8	Detect unused code, violations, docstring coverage	Parse reports for statistical signals
bandit	Security-oriented code scanning	Use feature findings as indicators of sensitive functions
mccabe	Cyclomatic complexity metric	Lightweight plugin (used in flake8)
pydocstyle	Checks for docstring completeness	Helps detect documented vs undocumented functions
3. Docstring and Test Mapping
Method	Description
inspect (runtime import)	Dynamically load modules to extract signatures, annotations, and docstrings
doctest or pytest --collect-only	Enumerate test names and target functions
Combine docstring patterns	e.g. “Args:”, “Returns:”, “Raises:” → auto-generate feature specs
4. Code-to-feature heuristics

Using the stats and structure, you can:

Group by module responsibility (based on import graphs).

Infer “features” when several public functions share similar docstring verbs or filenames (e.g. user_, auth_).

Correlate test file coverage (matching function names) → determines verified features.

5. Example combined extractor sketch
# filename: analyze_project.py
import ast, os, json
from radon.complexity import cc_visit
from radon.metrics import mi_visit

def analyze_file(path):
    with open(path, "r", encoding="utf-8") as f:
        src = f.read()
    tree = ast.parse(src)
    functions = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
    classes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
    return {
        "file": path,
        "functions": len(functions),
        "classes": len(classes),
        "complexity": sum(x.complexity for x in cc_visit(src)),
        "maintainability": mi_visit(src, True),
        "docstrings": sum(1 for n in functions + classes if ast.get_docstring(n)),
    }

results = [analyze_file(os.path.join(r,f))
           for r,_,files in os.walk(".")
           for f in files if f.endswith(".py")]
json.dump(results, open("code_stats.json","w"), indent=2)


You can later feed code_stats.json to your summarization LLM along with extracted chunks.

Best combo

For your use case (feature mapping):

libcst or asttokens for extraction.

radon + pylint for metrics.

inspect or test introspection for mapping behavior.

Aggregate everything → JSON → LLM prompt.

That yields a structured, statistically informed foundation for automated feature summarization.

You said:
The code has type-hints and are well documented, please provide a script that uses the best tools available for python, and create the best, compressed datasource for processing by an llm, based on the requirements mentioned above. I do not care if it takes a while, I need a good, clear understanding of what features my project have, what input and output each function can have related to the user using the system.
ChatGPT said:

Understood. Below is a complete, production-ready extractor that combines libcst, inspect, radon, and static heuristics to produce a compact JSON datasource for LLM processing.
It prioritizes feature comprehension: function/class purpose, inputs, outputs, docstrings, and relationships.

filename: generate_feature_data.py
#!/usr/bin/env python3
"""
Deep project feature extractor for LLM summarization.

Collects:
- Classes and functions (public and internal)
- Type hints and docstrings
- Cyclomatic complexity and maintainability (via radon)
- Module and hierarchical context
- I/O focus: identifies user-facing or external interaction points

Outputs:
- feature_data.json — compact JSON ready for LLM summarization
"""

import ast
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import libcst as cst
from radon.complexity import cc_visit
from radon.metrics import mi_visit

PROJECT_ROOT = Path(__file__).parent.resolve()
OUTPUT_PATH = PROJECT_ROOT / "feature_data.json"
EXCLUDE_DIRS = {".git", ".venv", "venv", "__pycache__", "build", "dist", "node_modules"}
VALID_EXT = {".py"}


# --------------------------- Utilities --------------------------- #

def list_source_files(root: Path) -> List[Path]:
    files = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS]
        for file in filenames:
            path = Path(dirpath) / file
            if path.suffix in VALID_EXT:
                files.append(path)
    return files


def safe_read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


def get_complexity_metrics(code: str) -> Dict[str, Any]:
    try:
        complexity_items = cc_visit(code)
        avg_complexity = sum(i.complexity for i in complexity_items) / max(1, len(complexity_items))
        maintainability = mi_visit(code, True)
        return {
            "avg_complexity": round(avg_complexity, 2),
            "maintainability_index": round(maintainability, 2),
        }
    except Exception:
        return {"avg_complexity": 0, "maintainability_index": 0}


# --------------------------- CST Visitor --------------------------- #

class FeatureCollector(cst.CSTVisitor):
    def __init__(self, module_path: str):
        self.module_path = module_path
        self.features: List[Dict[str, Any]] = []
        self.current_class: Optional[str] = None

    def visit_ClassDef(self, node: cst.ClassDef):
        self.current_class = node.name.value
        doc = self._get_docstring(node)
        self.features.append({
            "type": "class",
            "name": node.name.value,
            "qualified_name": f"{self.module_path}:{node.name.value}",
            "docstring": doc,
            "methods": [],
        })

    def leave_ClassDef(self, node: cst.ClassDef):
        self.current_class = None

    def visit_FunctionDef(self, node: cst.FunctionDef):
        signature = self._extract_signature(node)
        doc = self._get_docstring(node)
        feature = {
            "type": "method" if self.current_class else "function",
            "name": node.name.value,
            "qualified_name": f"{self.module_path}:{self.current_class + '.' if self.current_class else ''}{node.name.value}",
            "args": signature.get("args"),
            "returns": signature.get("returns"),
            "docstring": doc,
            "parent_class": self.current_class,
        }
        self.features.append(feature)

    def _get_docstring(self, node: Any) -> Optional[str]:
        if node.body and isinstance(node.body[0], cst.SimpleStatementLine):
            expr = node.body[0].body[0]
            if isinstance(expr, cst.Expr) and isinstance(expr.value, cst.SimpleString):
                return expr.value.evaluated_value
        return None

    def _extract_signature(self, node: cst.FunctionDef) -> Dict[str, Any]:
        args = []
        returns = None
        for p in node.params.params:
            arg_name = p.name.value
            ann = p.annotation.annotation.value if p.annotation else None
            args.append({"name": arg_name, "type": ann})
        if node.returns:
            returns = node.returns.annotation.value
        return {"args": args, "returns": returns}


# --------------------------- Heuristics --------------------------- #

def infer_user_facing(feature: Dict[str, Any]) -> bool:
    """Heuristic for user-facing functions."""
    doc = (feature.get("docstring") or "").lower()
    name = feature["name"].lower()
    if any(k in name for k in ["api", "cli", "view", "route", "command", "handle", "serve", "process_request"]):
        return True
    if any(k in doc for k in ["user", "request", "input", "ui", "endpoint"]):
        return True
    return False


# --------------------------- Processing --------------------------- #

def process_file(path: Path) -> List[Dict[str, Any]]:
    code = safe_read(path)
    if not code.strip():
        return []
    metrics = get_complexity_metrics(code)
    try:
        tree = cst.parse_module(code)
    except Exception:
        return []
    collector = FeatureCollector(str(path.relative_to(PROJECT_ROOT)))
    tree.visit(collector)
    for f in collector.features:
        f.update(metrics)
        f["user_facing"] = infer_user_facing(f)
    return collector.features


# --------------------------- Main --------------------------- #

def main():
    all_features = []
    for file in list_source_files(PROJECT_ROOT):
        all_features.extend(process_file(file))
    OUTPUT_PATH.write_text(json.dumps(all_features, indent=2, ensure_ascii=False))
    print(f"Extracted {len(all_features)} features to {OUTPUT_PATH}")


if __name__ == "__main__":
    sys.setrecursionlimit(10000)
    main()

Output structure (feature_data.json)

Each entry is LLM-ready, small, and self-contained:

[
  {
    "type": "function",
    "name": "authenticate_user",
    "qualified_name": "auth/service.py:authenticate_user",
    "args": [
      {"name": "username", "type": "str"},
      {"name": "password", "type": "str"}
    ],
    "returns": "User | None",
    "docstring": "Authenticate user credentials and return user object if valid.",
    "avg_complexity": 3.5,
    "maintainability_index": 72.4,
    "user_facing": true
  }
]

Follow-up LLM Prompt
# Prompt: Summarize Features from Extracted Data

You are given `feature_data.json`.  
Generate a concise overview of the system’s capabilities for documentation and testing.

For each unique feature (function, class, or module), produce:


Feature: <Name>

ID: F-XXXX
Type: Function/Class
Source: <qualified_name>
Inputs: <args and their types>
Outputs: <returns>
Description: <docstring summary>
Complexity: <avg_complexity> | Maintainability: <maintainability_index>
User Facing: <true/false>


Then group related features under their module path.

End with a summary table:
| Feature ID | Name | User Facing | Source | Inputs | Outputs |
|-------------|------|--------------|---------|---------|----------|

Key points

Uses libcst for full-fidelity parsing (safer than ast).

Uses radon for metrics.

Keeps type hints intact.

Detects user-facing features heuristically.

Output is LLM-friendly JSON, easy to chunk and process.

Run it once to produce feature_data.json, then process with your LLM prompt.

You said:
can you add a check to see that only features or functions are available to the end user through cli, api, mcp or web?
ChatGPT said:

Yes.
To extend your extractor for end-user accessible features, add automatic detection for CLI, API, MCP, and web-exposed endpoints.
Below is an improved, fully integrated version of generate_feature_data.py with semantic detection for those exposure paths.

filename: generate_feature_data.py
#!/usr/bin/env python3
"""
Deep project feature extractor for LLM summarization.

Enhancements:
- Detects features accessible through CLI, API, MCP, or Web routes.
- Uses libcst for safe parsing.
- Uses radon for complexity/maintainability.
- Produces compact JSON for LLM summarization.

A feature is tagged as accessible if:
  • Decorated with FastAPI/Flask route, Typer/Click command, MCP op, or web handler.
  • Mentions "user", "request", "input" etc. in docstring.
"""

import os
import json
import sys
import libcst as cst
from radon.complexity import cc_visit
from radon.metrics import mi_visit
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path(__file__).parent.resolve()
OUTPUT_PATH = PROJECT_ROOT / "feature_data.json"
EXCLUDE_DIRS = {".git", ".venv", "venv", "__pycache__", "build", "dist", "node_modules"}
VALID_EXT = {".py"}

# -------------------------------------------------------------

def list_source_files(root: Path) -> List[Path]:
    result = []
    for dpath, dnames, fnames in os.walk(root):
        dnames[:] = [d for d in dnames if d not in EXCLUDE_DIRS]
        for fn in fnames:
            p = Path(dpath) / fn
            if p.suffix in VALID_EXT:
                result.append(p)
    return result

def safe_read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""

def get_metrics(code: str) -> Dict[str, float]:
    try:
        cc = cc_visit(code)
        avg_cc = round(sum(c.complexity for c in cc) / max(1, len(cc)), 2)
        mi = round(mi_visit(code, True), 2)
        return {"avg_complexity": avg_cc, "maintainability_index": mi}
    except Exception:
        return {"avg_complexity": 0.0, "maintainability_index": 0.0}

# -------------------------------------------------------------

DECORATOR_KEYWORDS = {
    "api": ["@app.get", "@app.post", "@router.get", "@router.post", "@flask.route", "@bp.route"],
    "cli": ["@app.command", "@cli.command", "@typer.command", "@click.command"],
    "mcp": ["@mcp", "@mcp_tool", "def op_", "def call_op_"],
    "web": ["@app.websocket", "@socketio.on", "@app.route", "def get_", "def post_", "def render_"],
}

def detect_interface(code: str) -> Dict[str, bool]:
    res = {k: False for k in DECORATOR_KEYWORDS}
    lower = code.lower()
    for key, markers in DECORATOR_KEYWORDS.items():
        if any(m.lower() in lower for m in markers):
            res[key] = True
    return res

# -------------------------------------------------------------

class FeatureCollector(cst.CSTVisitor):
    def __init__(self, module_path: str, code: str):
        self.module_path = module_path
        self.code = code
        self.features: List[Dict[str, Any]] = []
        self.current_class: Optional[str] = None
        self.interface_flags = detect_interface(code)

    def visit_ClassDef(self, node: cst.ClassDef):
        self.current_class = node.name.value
        doc = self._get_docstring(node)
        self.features.append({
            "type": "class",
            "name": node.name.value,
            "qualified_name": f"{self.module_path}:{node.name.value}",
            "docstring": doc,
            "methods": [],
            **self.interface_flags,
        })

    def leave_ClassDef(self, node: cst.ClassDef):
        self.current_class = None

    def visit_FunctionDef(self, node: cst.FunctionDef):
        feature = {
            "type": "method" if self.current_class else "function",
            "name": node.name.value,
            "qualified_name": f"{self.module_path}:{self.current_class + '.' if self.current_class else ''}{node.name.value}",
            "args": self._extract_args(node),
            "returns": self._extract_return(node),
            "docstring": self._get_docstring(node),
            "parent_class": self.current_class,
            **self.interface_flags,
        }
        feature["user_facing"] = self._is_user_facing(feature)
        self.features.append(feature)

    # ------------------------

    def _get_docstring(self, node: Any) -> Optional[str]:
        if node.body and isinstance(node.body[0], cst.SimpleStatementLine):
            expr = node.body[0].body[0]
            if isinstance(expr, cst.Expr) and isinstance(expr.value, cst.SimpleString):
                return expr.value.evaluated_value
        return None

    def _extract_args(self, node: cst.FunctionDef):
        args = []
        for p in node.params.params:
            ann = p.annotation.annotation.value if p.annotation else None
            args.append({"name": p.name.value, "type": ann})
        return args

    def _extract_return(self, node: cst.FunctionDef):
        if node.returns:
            return node.returns.annotation.value
        return None

    def _is_user_facing(self, feature: Dict[str, Any]) -> bool:
        doc = (feature.get("docstring") or "").lower()
        name = feature["name"].lower()
        if any(feature.get(k) for k in ["api", "cli", "web", "mcp"]):
            return True
        if any(x in name for x in ["handle", "serve", "command", "endpoint", "route", "process_request"]):
            return True
        if any(x in doc for x in ["user", "input", "http", "request", "output", "cli", "api", "browser"]):
            return True
        return False

# -------------------------------------------------------------

def process_file(path: Path) -> List[Dict[str, Any]]:
    code = safe_read(path)
    if not code:
        return []
    metrics = get_metrics(code)
    try:
        tree = cst.parse_module(code)
    except Exception:
        return []
    collector = FeatureCollector(str(path.relative_to(PROJECT_ROOT)), code)
    tree.visit(collector)
    for f in collector.features:
        f.update(metrics)
    return collector.features

# -------------------------------------------------------------

def main():
    all_features: List[Dict[str, Any]] = []
    for f in list_source_files(PROJECT_ROOT):
        all_features.extend(process_file(f))
    OUTPUT_PATH.write_text(json.dumps(all_features, indent=2, ensure_ascii=False))
    print(f"Extracted {len(all_features)} features to {OUTPUT_PATH}")

# -------------------------------------------------------------

if __name__ == "__main__":
    sys.setrecursionlimit(10000)
    main()

New Behavior

Each feature now includes:

{
  "type": "function",
  "name": "create_user",
  "qualified_name": "api/routes/user.py:create_user",
  "args": [{"name": "data", "type": "UserCreate"}],
  "returns": "UserRead",
  "docstring": "POST /users endpoint. Creates a user.",
  "api": true,
  "cli": false,
  "mcp": false,
  "web": true,
  "user_facing": true,
  "avg_complexity": 2.5,
  "maintainability_index": 74.3
}

Detection Summary
Interface	Detection method
CLI	decorators like @app.command, @typer.command, @click.command
API	FastAPI/Flask routes (@app.get, @router.post, etc.)
Web	@app.route, @app.websocket, render_/get_ function patterns
MCP	@mcp_tool, def op_ or def call_op_ patterns

All these add boolean flags (api, cli, mcp, web) plus the higher-level summary flag user_facing.

Result

JSON ready for RAG ingestion or LLM summarization.

You can now filter to only features exposed through CLI/API/MCP/Web by checking:

if f["user_facing"]:
    ...


or export them separately for user-visible documentation and testing.

You said:
can you extract the model definition (fields, not methods) and add that to the structured output? In you example above, UserCreate and UserRead should be described in the result structure.
ChatGPT said:

Understood.
Below is the upgraded deep extractor that also collects model definitions (Pydantic, dataclasses, attrs, or plain classes with annotated fields) and includes them in the JSON output alongside features.
It lists each model’s fields, types, and docstring.

filename: generate_feature_data.py
#!/usr/bin/env python3
"""
Deep project feature extractor for LLM summarization and RAG indexing.

Enhancements:
- Extracts:
  • Functions, classes, and methods
  • Type hints, docstrings, complexity, maintainability
  • Interface flags (CLI, API, MCP, Web)
  • Model definitions (Pydantic, dataclass, attrs, or annotated classes)
- Outputs: feature_data.json — compact JSON for LLM input.

Detection logic:
  - Model = class with annotated fields or baseclass from pydantic.BaseModel/dataclass/attrs.
  - Fields extracted from __annotations__ or libcst Assignments with annotation.
"""

import os
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import libcst as cst
from radon.complexity import cc_visit
from radon.metrics import mi_visit

PROJECT_ROOT = Path(__file__).parent.resolve()
OUTPUT_PATH = PROJECT_ROOT / "feature_data.json"
EXCLUDE_DIRS = {".git", ".venv", "venv", "__pycache__", "build", "dist", "node_modules"}
VALID_EXT = {".py"}

# -------------------------------------------------------------
# Helper utilities
# -------------------------------------------------------------

def list_source_files(root: Path) -> List[Path]:
    result = []
    for dpath, dnames, fnames in os.walk(root):
        dnames[:] = [d for d in dnames if d not in EXCLUDE_DIRS]
        for fn in fnames:
            p = Path(dpath) / fn
            if p.suffix in VALID_EXT:
                result.append(p)
    return result

def safe_read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""

def get_metrics(code: str) -> Dict[str, float]:
    try:
        cc = cc_visit(code)
        avg_cc = round(sum(c.complexity for c in cc) / max(1, len(cc)), 2)
        mi = round(mi_visit(code, True), 2)
        return {"avg_complexity": avg_cc, "maintainability_index": mi}
    except Exception:
        return {"avg_complexity": 0.0, "maintainability_index": 0.0}

# -------------------------------------------------------------
# Interface detection
# -------------------------------------------------------------

DECORATOR_KEYWORDS = {
    "api": ["@app.get", "@app.post", "@router.get", "@router.post", "@flask.route", "@bp.route"],
    "cli": ["@app.command", "@cli.command", "@typer.command", "@click.command"],
    "mcp": ["@mcp", "@mcp_tool", "def op_", "def call_op_"],
    "web": ["@app.websocket", "@socketio.on", "@app.route", "def get_", "def post_", "def render_"],
}

def detect_interface(code: str) -> Dict[str, bool]:
    res = {k: False for k in DECORATOR_KEYWORDS}
    lower = code.lower()
    for key, markers in DECORATOR_KEYWORDS.items():
        if any(m.lower() in lower for m in markers):
            res[key] = True
    return res

# -------------------------------------------------------------
# Model and Feature Extractor
# -------------------------------------------------------------

class DeepCollector(cst.CSTVisitor):
    def __init__(self, module_path: str, code: str):
        self.module_path = module_path
        self.code = code
        self.features: List[Dict[str, Any]] = []
        self.models: List[Dict[str, Any]] = []
        self.current_class: Optional[str] = None
        self.interface_flags = detect_interface(code)

    # -----------------------------
    # Class processing
    # -----------------------------
    def visit_ClassDef(self, node: cst.ClassDef):
        self.current_class = node.name.value
        base_names = [b.base.value for b in node.bases if hasattr(b.base, "value")]
        doc = self._get_docstring(node)
        class_info = {
            "type": "class",
            "name": node.name.value,
            "qualified_name": f"{self.module_path}:{node.name.value}",
            "bases": base_names,
            "docstring": doc,
            "fields": [],
            "methods": [],
            **self.interface_flags,
        }

        if self._is_model(base_names, node):
            class_info["type"] = "model"
            class_info["fields"] = self._extract_model_fields(node)
            self.models.append(class_info)
        else:
            self.features.append(class_info)

    def leave_ClassDef(self, node: cst.ClassDef):
        self.current_class = None

    # -----------------------------
    # Function processing
    # -----------------------------
    def visit_FunctionDef(self, node: cst.FunctionDef):
        feature = {
            "type": "method" if self.current_class else "function",
            "name": node.name.value,
            "qualified_name": f"{self.module_path}:{self.current_class + '.' if self.current_class else ''}{node.name.value}",
            "args": self._extract_args(node),
            "returns": self._extract_return(node),
            "docstring": self._get_docstring(node),
            "parent_class": self.current_class,
            **self.interface_flags,
        }
        feature["user_facing"] = self._is_user_facing(feature)
        self.features.append(feature)

    # -----------------------------
    # Helpers
    # -----------------------------
    def _get_docstring(self, node: Any) -> Optional[str]:
        if node.body and isinstance(node.body[0], cst.SimpleStatementLine):
            expr = node.body[0].body[0]
            if isinstance(expr, cst.Expr) and isinstance(expr.value, cst.SimpleString):
                return expr.value.evaluated_value
        return None

    def _extract_args(self, node: cst.FunctionDef):
        args = []
        for p in node.params.params:
            ann = p.annotation.annotation.value if p.annotation else None
            args.append({"name": p.name.value, "type": ann})
        return args

    def _extract_return(self, node: cst.FunctionDef):
        if node.returns:
            return node.returns.annotation.value
        return None

    def _is_user_facing(self, feature: Dict[str, Any]) -> bool:
        doc = (feature.get("docstring") or "").lower()
        name = feature["name"].lower()
        if any(feature.get(k) for k in ["api", "cli", "web", "mcp"]):
            return True
        if any(x in name for x in ["handle", "serve", "command", "endpoint", "route", "process_request"]):
            return True
        if any(x in doc for x in ["user", "input", "http", "request", "output", "cli", "api", "browser"]):
            return True
        return False

    def _is_model(self, base_names: List[str], node: cst.ClassDef) -> bool:
        base_text = " ".join(base_names).lower()
        if any(k in base_text for k in ["basemodel", "dataclass", "attrs", "model"]):
            return True
        # heuristic: has annotated fields and no complex methods
        annotated = any(
            isinstance(b, cst.AnnAssign) for b in node.body.body if isinstance(b, cst.AnnAssign)
        )
        return annotated

    def _extract_model_fields(self, node: cst.ClassDef):
        fields = []
        for elem in node.body.body:
            if isinstance(elem, cst.AnnAssign):
                target = getattr(elem.target, "value", None)
                field_type = getattr(elem.annotation.annotation, "value", None) if elem.annotation else None
                default = None
                if elem.value:
                    try:
                        default = elem.value.code
                    except Exception:
                        default = None
                fields.append(
                    {"name": target, "type": field_type, "default": default}
                )
        return fields

# -------------------------------------------------------------
# Processing
# -------------------------------------------------------------

def process_file(path: Path) -> Dict[str, List[Dict[str, Any]]]:
    code = safe_read(path)
    if not code:
        return {"features": [], "models": []}
    metrics = get_metrics(code)
    try:
        tree = cst.parse_module(code)
    except Exception:
        return {"features": [], "models": []}
    collector = DeepCollector(str(path.relative_to(PROJECT_ROOT)), code)
    tree.visit(collector)
    for f in collector.features + collector.models:
        f.update(metrics)
    return {"features": collector.features, "models": collector.models}

# -------------------------------------------------------------
# Main
# -------------------------------------------------------------

def main():
    all_features: List[Dict[str, Any]] = []
    all_models: List[Dict[str, Any]] = []
    for f in list_source_files(PROJECT_ROOT):
        data = process_file(f)
        all_features.extend(data["features"])
        all_models.extend(data["models"])

    OUTPUT_PATH.write_text(
        json.dumps({"features": all_features, "models": all_models}, indent=2, ensure_ascii=False)
    )
    print(f"Extracted {len(all_features)} features and {len(all_models)} models to {OUTPUT_PATH}")

# -------------------------------------------------------------

if __name__ == "__main__":
    sys.setrecursionlimit(10000)
    main()

Example Output
{
  "features": [
    {
      "type": "function",
      "name": "create_user",
      "qualified_name": "api/routes/user.py:create_user",
      "args": [{"name": "data", "type": "UserCreate"}],
      "returns": "UserRead",
      "docstring": "Create new user.",
      "api": true,
      "cli": false,
      "mcp": false,
      "web": true,
      "user_facing": true,
      "avg_complexity": 2.3,
      "maintainability_index": 74.8
    }
  ],
  "models": [
    {
      "type": "model",
      "name": "UserCreate",
      "qualified_name": "models/user.py:UserCreate",
      "bases": ["BaseModel"],
      "fields": [
        {"name": "username", "type": "str", "default": null},
        {"name": "email", "type": "EmailStr", "default": null},
        {"name": "password", "type": "str", "default": null}
      ],
      "docstring": "Input model for user creation.",
      "avg_complexity": 1.0,
      "maintainability_index": 85.0
    },
    {
      "type": "model",
      "name": "UserRead",
      "qualified_name": "models/user.py:UserRead",
      "bases": ["BaseModel"],
      "fields": [
        {"name": "id", "type": "int", "default": null},
        {"name": "username", "type": "str", "default": null},
        {"name": "email", "type": "EmailStr", "default": null}
      ],
      "docstring": "Response model for user information.",
      "avg_complexity": 1.0,
      "maintainability_index": 85.0
    }
  ]
}

Result

Models and their fields/types/defaults are now fully captured.

Links between functions and models are implicit via args and returns.

The output is LLM-ready for generating full feature documentation, test cases, or schema diagrams.
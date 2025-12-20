# Low Priority Issues (P3)

Cosmetic, incremental improvements.

---

---
id: "CR-001@e9f2a3"
title: "Remove unused mock_console fixture from conftest.py"
description: "Dead code: fixture defined but never used in any test"
created: 2024-12-20
section: "tests"
tags: [review, dead-code, deletion-test]
type: refactor
priority: low
status: proposed
references:
  - tests/conftest.py
---

### Problem
The `mock_console` fixture in [conftest.py#L33-37](tests/conftest.py#L33-37) is defined but never used in any test file.

```python
@pytest.fixture
def mock_console() -> Generator:
    """Create a mock Rich console for testing output."""
    from unittest.mock import MagicMock

    console = MagicMock()
    yield console
```

### Affected Files
- `tests/conftest.py`

### Importance
Dead code adds confusion and maintenance burden. Deletion test: removing this fixture changes nothing.

### Proposed Solution
Delete the unused fixture.

### Acceptance Criteria
- [ ] `mock_console` fixture removed from conftest.py
- [ ] All tests still pass

---

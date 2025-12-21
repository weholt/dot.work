# Birdseye Project Guide

This guide explains what to run, what to expect, and how to follow up on the automatically discovered project features.

## Quick Orientation

Follow the steps below to repeat this analysis on any repository:
1. Run `birdseye analyze <input-path> <output-path>`.
2. Wait for the scan to finish; it looks at source code and supporting markdown docs.
3. Open the generated `birdseye_overview.md` for human guidance and the JSON files for handoff to tooling.

**What we found:** 8 features, 1 data models, and 20 documentation sections ready for cross-reference.

```mermaid
flowchart TD
    A[Choose project folder] --> B[Run birdseye scan]
    B --> C[Feature JSON for LLM tooling]
    B --> D[Human guide (this file)]
    C --> E[Test generation or planning]
    D --> E
```

## Feature Walkthrough

Each feature includes a short purpose, what to provide, and what should happen. Use the ID to trace it in JSON data.

### Module: demo_project\api.py

#### F-0001 · APIRouter
- **Kind:** class in `demo_project\api.py:APIRouter`
- **Purpose:** Minimal stub to mimic a router decorator for static analysis.
- **Inputs:** None
- **Outputs:** None
- **Exposure:** User facing
- **Quality:** complexity 0.0, maintainability 0.0
- **References:** Docs: none linked
- **Try this:** Call `APIRouter` with typical inputs and describe the observable change or return value.; Summarize the before/after state in one or two sentences.

#### F-0002 · read_greeting
- **Kind:** function in `demo_project\api.py:read_greeting`
- **Purpose:** Return a greeting payload for web clients.
- **Inputs:** name: str
- **Outputs:** dict[str, str]
- **Exposure:** API, CLI, Web, User facing
- **Quality:** complexity 0.0, maintainability 0.0
- **References:** Docs: none linked
- **Try this:** Run the CLI command that triggers `read_greeting` and capture the console output.; List the required flags and what they influence.; Issue a sample request exercising `read_greeting` and note the expected response fields.; Record one happy-path payload and the expected status/result.

#### F-0003 · decorator
- **Kind:** method in `demo_project\api.py:APIRouter.decorator`
- **Purpose:** No description provided.
- **Inputs:** func: F
- **Outputs:** F
- **Exposure:** Internal
- **Quality:** complexity 0.0, maintainability 0.0
- **References:** Docs: none linked
- **Try this:** Call `decorator` with typical inputs and describe the observable change or return value.; Summarize the before/after state in one or two sentences.

#### F-0004 · get
- **Kind:** method in `demo_project\api.py:APIRouter.get`
- **Purpose:** No description provided.
- **Inputs:** self: unknown, _path: str
- **Outputs:** Callable[[F], F]
- **Exposure:** Internal
- **Quality:** complexity 0.0, maintainability 0.0
- **References:** Docs: none linked
- **Try this:** Call `get` with typical inputs and describe the observable change or return value.; Summarize the before/after state in one or two sentences.


### Module: demo_project\cli.py

#### F-0005 · greet
- **Kind:** function in `demo_project\cli.py:greet`
- **Purpose:** Print a greeting for command line users.
- **Inputs:** name: str
- **Outputs:** None
- **Exposure:** CLI, User facing
- **Quality:** complexity 1.0, maintainability 100.0
- **References:** Docs: demo_project/docs/feature-guide.md#feature-guide-greet
- **Try this:** Run the CLI command that triggers `greet` and capture the console output.; List the required flags and what they influence.


### Module: demo_project\models.py

#### F-0006 · BaseModel
- **Kind:** class in `demo_project\models.py:BaseModel`
- **Purpose:** Minimal stand-in for Pydantic's BaseModel.
- **Inputs:** None
- **Outputs:** None
- **Exposure:** Internal
- **Quality:** complexity 0.0, maintainability 0.0
- **References:** Docs: none linked
- **Try this:** Call `BaseModel` with typical inputs and describe the observable change or return value.; Summarize the before/after state in one or two sentences.


### Module: demo_project\services.py

#### F-0007 · GreetingService
- **Kind:** class in `demo_project\services.py:GreetingService`
- **Purpose:** Coordinates greeting flows for user-facing surfaces.
- **Inputs:** None
- **Outputs:** None
- **Exposure:** User facing
- **Quality:** complexity 0.0, maintainability 0.0
- **References:** Docs: none linked
- **Try this:** Call `GreetingService` with typical inputs and describe the observable change or return value.; Summarize the before/after state in one or two sentences.

#### F-0008 · greet
- **Kind:** method in `demo_project\services.py:GreetingService.greet`
- **Purpose:** Return a greeting string that UIs or bots can render.
- **Inputs:** self: unknown, name: str
- **Outputs:** str
- **Exposure:** Internal
- **Quality:** complexity 0.0, maintainability 0.0
- **References:** Docs: demo_project/docs/feature-guide.md#feature-guide-greet, demo_project/README.md#greetingservice-greet
- **Try this:** Call `greet` with typical inputs and describe the observable change or return value.; Summarize the before/after state in one or two sentences.


## Data Models

### Profile (demo_project\models.py:Profile)
Profile details shared with end users.
| Field | Type | Default |
|-------|------|---------|
| username | str | — |
| bio | str | None | None |


---

Generated by birdseye. Use this document to brief stakeholders or to seed scenario generation workflows.
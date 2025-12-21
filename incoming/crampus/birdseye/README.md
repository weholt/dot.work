# Birdseye

Birdseye scans a project directory to produce a concise, human-friendly overview and structured JSON datasets for follow-up automation.

## Installation

```powershell
pip install .
```

## Usage

```powershell
birdseye <path-to-project> <path-to-output>
```

The output directory receives:

- `birdseye_overview.md` – instructions and feature walkthrough for people.
- `features.json` – structured features and model metadata.
- `documents.json` – extracted markdown section summaries.

### Sample walkthrough

Try the bundled sample to see the outputs without wiring a full project:

```powershell
birdseye samples/demo_project samples/demo_output
```

Then open `samples/demo_output/birdseye_overview.md` for the human report and inspect the JSON files for tooling handoff examples.

## Development

Run tests with:

```powershell
pytest
```

# Changelog

All notable changes to Python Project Builder will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release of Python Project Builder
- Comprehensive build pipeline with 9 quality check steps
- Code formatting with ruff
- Linting with ruff
- Type checking with mypy
- Testing with pytest and coverage
- Security scanning
- Optional static analysis tools (radon, vulture, jscpd, import-linter, bandit)
- Documentation building with MkDocs
- CLI interface with `pybuilder` command
- Auto-detection of project source directories
- Configurable coverage thresholds
- Support for uv package manager
- Verbose and fix modes
- Artifact cleaning functionality

### Features
- Multi-step build pipeline with detailed reporting
- Configurable source and test directories
- Coverage threshold enforcement
- Build duration tracking
- Failed step reporting
- Optional tools with graceful degradation

## [0.1.0] - 2025-11-25

### Added
- First alpha release
- Core build functionality
- Documentation and usage guides

[Unreleased]: https://github.com/your-username/python-project-builder/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/your-username/python-project-builder/releases/tag/v0.1.0

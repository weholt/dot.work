"""
Regression Guard - Multi-agent validation system to prevent code regressions.
"""

__version__ = "0.1.0"

from regression_guard.orchestrator import RegressionOrchestrator

__all__ = ["RegressionOrchestrator", "__version__"]

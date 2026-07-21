"""Read-only repository discovery primitives.

This package establishes the safe boundary for examining a target project. Mutation and command
execution are intentionally deferred to dedicated tool-layer milestones.
"""

from ai_change_agent.repository.discovery import DiscoveryOptions, RepositoryScanner

__all__ = ["DiscoveryOptions", "RepositoryScanner"]

"""Fact collectors. No collector reads source code or contacts non-GitHub hosts."""

from changepassport.collectors.github import GitHubCollector, load_snapshot

__all__ = ["GitHubCollector", "load_snapshot"]

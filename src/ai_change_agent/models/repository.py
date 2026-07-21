"""Data contracts produced by repository discovery."""

from __future__ import annotations

from pydantic import Field, field_validator, model_validator

from ai_change_agent.models.enums import SkipReason
from ai_change_agent.models.schemas import ContractModel, RepositoryPath, _validate_repository_path


class RepositoryFile(ContractModel):
    """Metadata for one readable, non-binary file in a discovered repository."""

    path: RepositoryPath
    size_bytes: int = Field(ge=0)
    extension: str = ""

    @field_validator("path")
    @classmethod
    def validate_path(cls, value: str) -> str:
        """Keep file paths relative to the scanned repository root."""
        return _validate_repository_path(value)


class SkippedEntry(ContractModel):
    """An omitted filesystem entry, retained for transparent scan diagnostics."""

    path: RepositoryPath
    reason: SkipReason

    @field_validator("path")
    @classmethod
    def validate_path(cls, value: str) -> str:
        """Keep diagnostic paths relative to the scanned repository root."""
        return _validate_repository_path(value)


class RepositoryMap(ContractModel):
    """Deterministic, read-only view of the files available to the agent.

    The map carries metadata only. File contents are deliberately retrieved later through the
    dedicated read-file tool, which keeps discovery inexpensive and access auditable.
    """

    root: str
    directories: tuple[RepositoryPath, ...] = (".",)
    files: tuple[RepositoryFile, ...] = ()
    skipped_entries: tuple[SkippedEntry, ...] = ()

    @model_validator(mode="after")
    def validate_unique_paths(self) -> RepositoryMap:
        """Reject ambiguous maps before they reach planning or tool-selection code."""
        file_paths = tuple(file.path for file in self.files)
        skipped_paths = tuple(entry.path for entry in self.skipped_entries)
        if len(set(self.directories)) != len(self.directories):
            raise ValueError("Repository-map directories must be unique.")
        if len(set(file_paths)) != len(file_paths):
            raise ValueError("Repository-map files must be unique.")
        if len(set(skipped_paths)) != len(skipped_paths):
            raise ValueError("Repository-map skipped entries must be unique.")
        if set(file_paths) & set(skipped_paths):
            raise ValueError("A repository entry cannot be both included and skipped.")
        return self

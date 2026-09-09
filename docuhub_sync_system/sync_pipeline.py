"""Shared orchestration primitives for every DocuHub synchronization mode."""
from __future__ import annotations

import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable


ROOT = Path(__file__).resolve().parent
FORMATTED_DIR = ROOT / "dashboard" / "formated_files"
Action = Callable[[], Any]
CommandFactory = Callable[[], list[str]]


@dataclass(frozen=True)
class SyncStep:
    number: int
    key: str
    label: str
    action: Action


@dataclass(frozen=True)
class StepResult:
    number: int
    key: str
    label: str
    elapsed_seconds: float
    data: Any = None


class CommandFailed(RuntimeError):
    def __init__(self, command: list[str], returncode: int):
        self.command = command
        self.returncode = returncode
        super().__init__(
            f"Command failed with exit code {returncode}: {' '.join(command)}"
        )


class SyncStepError(RuntimeError):
    def __init__(self, step: SyncStep, cause: BaseException):
        self.step = step
        self.cause = cause
        self.returncode = getattr(cause, "returncode", None)
        detail = (
            f" (exit code {self.returncode})" if self.returncode is not None else ""
        )
        super().__init__(f"Step {step.number} failed{detail}: {step.label}: {cause}")


def _as_command_factory(command: list[str] | CommandFactory) -> CommandFactory:
    if callable(command):
        return command
    frozen = [str(part) for part in command]
    return lambda: list(frozen)


def command_step(
    number: int,
    key: str,
    label: str,
    command: list[str] | CommandFactory,
    *,
    cwd: Path | str = ROOT,
) -> SyncStep:
    command_factory = _as_command_factory(command)

    def action() -> dict:
        resolved = [str(part) for part in command_factory()]
        print(f"[run] {' '.join(resolved)}")
        result = subprocess.run(resolved, cwd=str(cwd))
        if result.returncode != 0:
            raise CommandFailed(resolved, result.returncode)
        return {"command": resolved, "returncode": result.returncode}

    return SyncStep(number, key, label, action)


def callback_step(number: int, key: str, label: str, action: Action) -> SyncStep:
    return SyncStep(number, key, label, action)


def repository_sync_steps(
    *,
    root: Path | str = ROOT,
    python_executable: str = sys.executable,
    repository_directory: str = "ciroh_hub",
) -> list[SyncStep]:
    """The canonical source-refresh phase shared by every entry point."""
    return [
        command_step(
            1,
            "pull_repository",
            "Pulling latest repo...",
            [python_executable, "download_repo.py"],
            cwd=root,
        ),
        command_step(
            2,
            "detect_changes",
            "Detecting changes...",
            [python_executable, "local_change_dashboard/check_changes.py"],
            cwd=root,
        ),
        command_step(
            3,
            "check_external_repositories",
            "Checking external repos...",
            [
                python_executable,
                "local_change_dashboard/external_repo_checker.py",
                "--root",
                repository_directory,
                "--download",
                "--download-changed",
                "--download-local",
            ],
            cwd=root,
        ),
    ]


def generation_step(
    number: int = 5,
    *,
    mixed_docs: Path | str | Callable[[], Path | str] | None = None,
    output_dir: Path | str | None = None,
    summarize: bool = True,
    root: Path | str = ROOT,
    python_executable: str = sys.executable,
) -> SyncStep:
    def build_command() -> list[str]:
        command = [python_executable, "dashboard/generate_formatted_files.py"]
        resolved_mixed_docs = mixed_docs() if callable(mixed_docs) else mixed_docs
        if resolved_mixed_docs is not None:
            command.extend(["--mixed-docs", str(resolved_mixed_docs)])
        if output_dir is not None:
            command.extend(["--output", str(output_dir)])
        if summarize:
            command.append("--summarize")
        return command

    return command_step(
        number,
        "generate_artifacts",
        "Generating artifacts & summaries...",
        build_command,
        cwd=root,
    )


def github_repository_generation_step(
    number: int = 4,
    *,
    summarize: bool = True,
    force: bool = False,
    root: Path | str = ROOT,
    python_executable: str = sys.executable,
) -> SyncStep:
    """Build type-4 repository artifacts/chunks without updating the database."""
    command = [python_executable, "run_github_repository_sync.py", "--execute"]
    if not summarize:
        command.append("--skip-summaries")
    if force:
        command.append("--force")
    return command_step(
        number,
        "generate_github_repository_artifacts",
        "Generating GitHub repository artifacts, descriptions & chunks...",
        command,
        cwd=root,
    )


def database_step(
    number: int = 6,
    *,
    artifacts: Path | str | None = None,
    chunks: Path | str | None = None,
    deactivate_active_artifact_type: int | None = None,
    expected_artifact_type: int | None = None,
    reconcile_snapshot_artifact_type: int | None = None,
    ensure_repository_chunk_types: bool = False,
    require_summaries: bool = False,
    result_file: Path | str = "db_update_result.json",
    key: str = "update_database",
    label: str = "Updating database (embeddings)...",
    skip_embeddings: bool = False,
    root: Path | str = ROOT,
    python_executable: str = sys.executable,
) -> SyncStep:
    command = [python_executable, "Andres_implementation/process_delta.py"]
    if artifacts is not None or chunks is not None:
        if artifacts is None or chunks is None:
            raise ValueError("artifacts and chunks must be supplied together")
        command.extend(["--artifacts", str(artifacts), "--chunks", str(chunks)])
    if deactivate_active_artifact_type is not None:
        command.extend(
            ["--deactivate-active-artifact-type", str(deactivate_active_artifact_type)]
        )
    if expected_artifact_type is not None:
        command.extend(["--expected-artifact-type", str(expected_artifact_type)])
    if reconcile_snapshot_artifact_type is not None:
        command.extend(
            [
                "--reconcile-snapshot-artifact-type",
                str(reconcile_snapshot_artifact_type),
            ]
        )
    if ensure_repository_chunk_types:
        command.append("--ensure-repository-chunk-types")
    if require_summaries:
        command.append("--require-summaries")
    command.extend(["--result-file", str(result_file)])
    if skip_embeddings:
        command.append("--skip-embeddings")
    return command_step(
        number,
        key,
        label,
        command,
        cwd=root,
    )


def github_repository_database_step(
    number: int,
    *,
    root: Path | str = ROOT,
    python_executable: str = sys.executable,
    skip_embeddings: bool = False,
    require_summaries: bool = True,
) -> SyncStep:
    """Incrementally reconcile the generated type-4 snapshot with PostgreSQL."""
    root_path = Path(root)
    formatted = root_path / "dashboard" / "formated_files"
    return database_step(
        number,
        artifacts=formatted / "coderepo_artifacts.json",
        chunks=formatted / "coderepo_chunks.json",
        expected_artifact_type=4,
        reconcile_snapshot_artifact_type=4,
        ensure_repository_chunk_types=True,
        require_summaries=require_summaries,
        result_file="github_repository_db_update_result.json",
        key="update_github_repository_database",
        label="Updating GitHub repository database rows & embeddings...",
        skip_embeddings=skip_embeddings,
        root=root_path,
        python_executable=python_executable,
    )


def run_sync_steps(
    steps: Iterable[SyncStep],
    *,
    on_step_start: Callable[[SyncStep], None] | None = None,
    on_step_complete: Callable[[StepResult], None] | None = None,
) -> list[StepResult]:
    """Run steps in order and stop before any dependent step after a failure."""
    results: list[StepResult] = []
    for step in steps:
        if on_step_start:
            on_step_start(step)
        started = time.perf_counter()
        try:
            data = step.action()
        except BaseException as exc:
            if isinstance(exc, SyncStepError):
                raise
            raise SyncStepError(step, exc) from exc
        result = StepResult(
            number=step.number,
            key=step.key,
            label=step.label,
            elapsed_seconds=round(time.perf_counter() - started, 3),
            data=data,
        )
        results.append(result)
        if on_step_complete:
            on_step_complete(result)
    return results

"""Persistent, org-scoped Job store.

A Job is the operator-facing unit of work: one uploaded survey (document_id)
plus intake metadata and a status that drives the UI. Storage mirrors
``organisation_store`` — a JSON file per organisation at
``STORAGE_ROOT/{org_id}/jobs.json``.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from .repository import get_repository
from .schemas import CreateJobRequest, Job, JobStatus


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _read_jobs(org_id: str) -> list[Job]:
    return get_repository().list_jobs(org_id)


def _write_jobs(org_id: str, jobs: list[Job]) -> None:
    get_repository().put_jobs(org_id, jobs)


def create_job(
    org_id: str,
    *,
    document_id: str,
    file_name: str,
    request: CreateJobRequest | None = None,
    survey_type: str | None = None,
    quotable: bool = True,
    created_by: str | None = None,
) -> Job:
    request = request or CreateJobRequest()
    now = _now()
    job = Job(
        id=f"job-{uuid4().hex[:12]}",
        organisation_id=org_id,
        document_id=document_id,
        file_name=file_name,
        client_name=request.client_name,
        site_address=request.site_address,
        job_reference=request.job_reference,
        survey_type=survey_type,
        quotable=quotable,
        status="uploaded",
        created_by=created_by,
        created_at=now,
        updated_at=now,
    )
    jobs = _read_jobs(org_id)
    jobs.append(job)
    _write_jobs(org_id, jobs)
    return job


def list_jobs(org_id: str) -> list[Job]:
    # Newest first — the Jobs list shows recent work at the top.
    return sorted(_read_jobs(org_id), key=lambda job: job.created_at, reverse=True)


def get_job(org_id: str, job_id: str) -> Job | None:
    for job in _read_jobs(org_id):
        if job.id == job_id:
            return job
    return None


def update_job(org_id: str, job_id: str, **fields: object) -> Job | None:
    """Patch arbitrary Job fields and bump ``updated_at``. Returns the saved Job."""
    jobs = _read_jobs(org_id)
    updated: Job | None = None
    for index, job in enumerate(jobs):
        if job.id != job_id:
            continue
        data = job.model_dump()
        data.update(fields)
        data["updated_at"] = _now()
        updated = Job.model_validate(data)
        jobs[index] = updated
        break
    if updated is not None:
        _write_jobs(org_id, jobs)
    return updated


def set_status(org_id: str, job_id: str, status: JobStatus, **fields: object) -> Job | None:
    return update_job(org_id, job_id, status=status, **fields)

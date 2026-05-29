from dataclasses import dataclass


@dataclass(frozen=True)
class ExtractionJob:
    workup_id: str
    document_id: str
    file_path: str


def run_demo_extraction(job: ExtractionJob) -> dict[str, str]:
    """Phase 1 placeholder; real PDF parsing starts in Phase 2."""
    return {
        "workup_id": job.workup_id,
        "document_id": job.document_id,
        "status": "placeholder_only",
    }


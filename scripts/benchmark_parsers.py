#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path
from uuid import uuid4

import fitz


REPO_ROOT = Path(__file__).resolve().parents[1]
API_ROOT = REPO_ROOT / "services" / "api"
SAMPLE_PDF = REPO_ROOT / "samples" / "surveys" / "38-Asbestos-Survey-_Rev_0.pdf"

sys.path.insert(0, str(API_ROOT))

from app.parser_adapters import ParserUnavailable, get_parser_adapters  # noqa: E402
from app.schemas import ParsedDocument  # noqa: E402


def _image_count(file_path: Path) -> int:
    try:
        with fitz.open(file_path) as document:
            return sum(len(page.get_images(full=True)) for page in document)
    except Exception:
        return 0


def _normalized_text(parsed: ParsedDocument) -> str:
    text = "\n".join(page.text for page in parsed.pages)
    return re.sub(r"\s+", " ", text).strip()


def _metrics(parsed: ParsedDocument, runtime_seconds: float, file_path: Path) -> dict[str, object]:
    full_text = _normalized_text(parsed)
    lowered = full_text.lower()
    pages_with_text = sum(1 for page in parsed.pages if page.text.strip())
    page_count = parsed.page_count or len(parsed.pages)
    warnings = sorted(
        {
            warning
            for page in parsed.pages
            for warning in page.warnings
            if warning
        }
    )

    return {
        "status": "ok",
        "parser_version": parsed.parser_version,
        "page_count": page_count,
        "text_coverage": {
            "pages_with_text": pages_with_text,
            "page_count": page_count,
            "ratio": round(pages_with_text / page_count, 4) if page_count else 0,
            "character_count": len(full_text),
        },
        "table_count": len(parsed.tables),
        "ocr_required": parsed.ocr_status != "not_required",
        "ocr_status": parsed.ocr_status,
        "register_section_detected": "register" in lowered,
        "no_access_section_detected": (
            "summary of areas or items of limited access or no access" in lowered
            or "limited access or no access" in lowered
            or "no access" in lowered
        ),
        "class_a_class_b_section_detected": (
            "class a and class b asbestos meaning" in lowered
            or ("class a" in lowered and "class b" in lowered)
        ),
        "image_count": _image_count(file_path),
        "runtime_seconds": round(runtime_seconds, 3),
        "extraction_warnings": warnings,
    }


def _run_adapter(file_path: Path, adapter_name: str, parser_index: int) -> dict[str, object]:
    adapter = get_parser_adapters()[parser_index]
    document_id = f"bench-{adapter_name}-{uuid4().hex[:8]}"
    started_at = time.perf_counter()
    try:
        parsed = adapter.parse(file_path=file_path, document_id=document_id)
    except ParserUnavailable as exc:
        return {
            "status": "skipped",
            "skip_reason": str(exc),
            "runtime_seconds": round(time.perf_counter() - started_at, 3),
        }
    except Exception as exc:
        return {
            "status": "failed",
            "error": str(exc),
            "runtime_seconds": round(time.perf_counter() - started_at, 3),
        }

    return _metrics(parsed, time.perf_counter() - started_at, file_path)


def run_benchmark(file_path: Path) -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    adapters = get_parser_adapters()
    for index, adapter in enumerate(adapters):
        result = _run_adapter(file_path, adapter.name, index)
        results.append({"parser": adapter.name, **result})
    return results


def _print_table(results: list[dict[str, object]]) -> None:
    print("\nParser benchmark summary")
    print("| Parser | Status | Pages | Text chars | Tables | OCR | Register | No Access | Class A/B | Runtime |")
    print("| --- | --- | ---: | ---: | ---: | --- | --- | --- | --- | ---: |")
    for result in results:
        coverage = result.get("text_coverage")
        text_chars = coverage.get("character_count") if isinstance(coverage, dict) else ""
        print(
            "| {parser} | {status} | {pages} | {chars} | {tables} | {ocr} | {register} | {no_access} | {classes} | {runtime} |".format(
                parser=result["parser"],
                status=result["status"],
                pages=result.get("page_count", ""),
                chars=text_chars,
                tables=result.get("table_count", ""),
                ocr=result.get("ocr_status", ""),
                register=result.get("register_section_detected", ""),
                no_access=result.get("no_access_section_detected", ""),
                classes=result.get("class_a_class_b_section_detected", ""),
                runtime=result.get("runtime_seconds", ""),
            )
        )


def main() -> int:
    if not SAMPLE_PDF.exists():
        print(
            "Missing sample PDF: add samples/surveys/38-Asbestos-Survey-_Rev_0.pdf before running the parser benchmark.",
            file=sys.stderr,
        )
        return 2

    results = run_benchmark(SAMPLE_PDF)
    _print_table(results)
    print("\nRaw results")
    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

import json
import re
from collections.abc import Mapping, Sequence
from typing import Any, Iterable, List


INLINE_PREFIX = "引用来源："
CITATION_TITLE = "参考资料："
LEGACY_CITATION_TITLES = ("依据：",)


def append_inline_citations(text: str, raw_result: Any) -> str:
    citations = extract_citations(raw_result)
    if not citations:
        return text
    existing = text or ""
    additions = [f"{INLINE_PREFIX}{item}" for item in citations if f"{INLINE_PREFIX}{item}" not in existing]
    if not additions:
        return existing
    return "\n".join([part for part in [existing.strip(), *additions] if part])


def append_citation_section(answer: str, tool_results: Iterable[Mapping[str, Any]]) -> str:
    section = build_citation_section(tool_results)
    if not section:
        return answer
    cleaned = (answer or "").rstrip()
    if CITATION_TITLE in cleaned or any(title in cleaned for title in LEGACY_CITATION_TITLES):
        return cleaned
    return f"{cleaned}\n\n{section}"


def build_citation_section(tool_results: Iterable[Mapping[str, Any]]) -> str:
    citations = extract_citations_from_tool_results(tool_results)
    if not citations:
        return ""
    lines = [CITATION_TITLE]
    lines.extend(f"{idx}. {item}" for idx, item in enumerate(citations, start=1))
    return "\n".join(lines)


def extract_citations_from_tool_results(tool_results: Iterable[Mapping[str, Any]]) -> List[str]:
    citations: List[str] = []
    for item in tool_results or []:
        if not isinstance(item, Mapping) or not item.get("success"):
            continue
        output = str(item.get("output") or "")
        for match in re.finditer(rf"{re.escape(INLINE_PREFIX)}([^\n\r]+)", output):
            citations.append(match.group(1).strip())
    return _dedupe(citations)


def extract_citations(value: Any) -> List[str]:
    return _dedupe(_walk_for_citations(value))


def _walk_for_citations(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return _extract_from_text(value)
    if isinstance(value, Mapping):
        return _extract_from_mapping(value)
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        citations: List[str] = []
        for item in value:
            citations.extend(_walk_for_citations(item))
        return citations
    if hasattr(value, "text"):
        return _walk_for_citations(getattr(value, "text", ""))
    if hasattr(value, "__dict__"):
        return _walk_for_citations(vars(value))
    return []


def _extract_from_text(text: str) -> List[str]:
    stripped = text.strip()
    if not stripped:
        return []
    if stripped.startswith("{") or stripped.startswith("["):
        try:
            return _walk_for_citations(json.loads(stripped))
        except (json.JSONDecodeError, TypeError):
            return []
    return [m.group(1).strip() for m in re.finditer(rf"{re.escape(INLINE_PREFIX)}([^\n\r]+)", stripped)]


def _extract_from_mapping(value: Mapping[str, Any]) -> List[str]:
    citations: List[str] = []
    metadata = value.get("metadata")
    if isinstance(metadata, Mapping):
        citation = _format_metadata_citation(metadata)
        if citation:
            citations.append(citation)
    course_citation = _format_course_citation(value)
    if course_citation:
        citations.append(course_citation)
    nested_course_citation = _format_nested_course_citation(value)
    if nested_course_citation:
        citations.append(nested_course_citation)
    for key in ("results", "content", "text", "data"):
        if key in value:
            citations.extend(_walk_for_citations(value[key]))
    return citations


def _format_metadata_citation(metadata: Mapping[str, Any]) -> str:
    source = str(metadata.get("source") or "").strip()
    return source


def _format_course_citation(value: Mapping[str, Any]) -> str:
    source = _first_text(value, ("source_title", "source_name"))
    if not source and ("source_id" in value or "source_type" in value):
        source = _first_text(value, ("title", "name"))
    return source


def _format_nested_course_citation(value: Mapping[str, Any]) -> str:
    source = value.get("source")
    if not isinstance(source, Mapping):
        return ""
    source_title = _first_text(source, ("title", "source_title", "source_name", "name"))
    if not source_title:
        return ""
    return source_title


def _first_text(value: Mapping[str, Any], keys: Iterable[str]) -> str:
    for key in keys:
        text = str(value.get(key) or "").strip()
        if text:
            return text
    return ""


def _dedupe(items: Iterable[str]) -> List[str]:
    result: List[str] = []
    seen = set()
    for item in items:
        cleaned = str(item or "").strip()
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        result.append(cleaned)
    return result

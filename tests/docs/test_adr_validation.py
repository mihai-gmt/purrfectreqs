"""Validator for Architecture Decision Records in docs/adr/.

Enforces the ADR contract defined in _TEMP/20260708_adr_backfill_plan.md §1:
frontmatter schema, id/filename agreement, relation resolution, supersedes
consistency, required body sections, and README index synchronisation.

The MANIFEST below is the RED→GREEN driver for the 2026-07 backfill: every
planned ADR id fails its completeness test until the file exists and conforms.
Do not weaken these tests to make them pass — fix the ADR files instead.
"""

import datetime
import re
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).parents[2]
ADR_DIR = REPO_ROOT / "docs" / "adr"

# Planned ADR ids — copied from _TEMP/20260708_adr_backfill_plan.md §3.
# The plan is the source; this list is the enforcement.
MANIFEST = [f"ADR-{n:04d}" for n in range(1, 40)]

VALID_STATUSES = {"proposed", "accepted", "deprecated", "superseded"}
ID_PATTERN = re.compile(r"^ADR-\d{4}$")
FILENAME_PATTERN = re.compile(r"^(ADR-\d{4})-[a-z0-9]+(-[a-z0-9]+)*\.md$")

REQUIRED_FRONTMATTER_KEYS = {
    "id",
    "title",
    "status",
    "date",
    "backfilled",
    "deciders",
    "tags",
    "supersedes",
    "superseded_by",
    "depends_on",
    "related_to",
    "affects_modules",
    "governed_by",
    "rejected_alternatives",
}

REQUIRED_BODY_SECTIONS = ["## Context", "## Decision", "## Rationale", "## Consequences"]


def _adr_paths() -> list[Path]:
    """Return all ADR files (excludes TEMPLATE.md and README.md by pattern)."""
    if not ADR_DIR.is_dir():
        return []
    return sorted(p for p in ADR_DIR.glob("ADR-*.md"))


def _parse_adr(path: Path) -> tuple[dict, str]:
    """Split an ADR file into (frontmatter dict, body text).

    The file must open with a `---` line and close the frontmatter with a
    second `---` line; everything after is the Markdown body.
    """
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        pytest.fail(f"{path.name}: file does not start with YAML frontmatter delimiter '---'")
    try:
        _, fm_text, body = text.split("---\n", 2)
    except ValueError:
        pytest.fail(f"{path.name}: frontmatter is not closed with a second '---' line")
    frontmatter = yaml.safe_load(fm_text)
    if not isinstance(frontmatter, dict):
        pytest.fail(f"{path.name}: frontmatter did not parse to a mapping")
    return frontmatter, body


def _all_adrs() -> dict[str, tuple[Path, dict, str]]:
    """Parse every ADR file, keyed by its frontmatter id."""
    result: dict[str, tuple[Path, dict, str]] = {}
    for path in _adr_paths():
        frontmatter, body = _parse_adr(path)
        result[str(frontmatter.get("id"))] = (path, frontmatter, body)
    return result


# --- Rule 9: manifest completeness (the RED→GREEN driver) -------------------


@pytest.mark.parametrize("adr_id", MANIFEST)
def test_manifest_adr_exists(adr_id: str) -> None:
    """Every ADR planned in the backfill manifest exists as a file."""
    matches = list(ADR_DIR.glob(f"{adr_id}-*.md")) if ADR_DIR.is_dir() else []
    assert matches, f"{adr_id} is in the backfill manifest but no docs/adr/{adr_id}-*.md file exists"


# --- Rules 1-3: per-file schema ---------------------------------------------


@pytest.mark.parametrize("path", _adr_paths(), ids=lambda p: p.name)
def test_frontmatter_schema(path: Path) -> None:
    """Frontmatter parses and carries all required keys with valid values."""
    frontmatter, _ = _parse_adr(path)

    missing = REQUIRED_FRONTMATTER_KEYS - frontmatter.keys()
    assert not missing, f"{path.name}: missing frontmatter keys: {sorted(missing)}"

    adr_id = frontmatter["id"]
    assert ID_PATTERN.match(str(adr_id)), f"{path.name}: id {adr_id!r} does not match ADR-NNNN"

    fn_match = FILENAME_PATTERN.match(path.name)
    assert fn_match, f"{path.name}: filename does not match ADR-NNNN-<kebab-slug>.md"
    assert fn_match.group(1) == adr_id, f"{path.name}: filename id prefix does not match frontmatter id {adr_id}"

    assert frontmatter["status"] in VALID_STATUSES, f"{path.name}: invalid status {frontmatter['status']!r}"
    assert isinstance(frontmatter["date"], datetime.date), f"{path.name}: date must be an ISO date"
    assert isinstance(frontmatter["backfilled"], bool), f"{path.name}: backfilled must be a boolean"
    assert isinstance(frontmatter["title"], str) and frontmatter["title"].strip(), f"{path.name}: empty title"

    for key in (
        "deciders",
        "tags",
        "supersedes",
        "depends_on",
        "related_to",
        "affects_modules",
        "governed_by",
        "rejected_alternatives",
    ):
        assert isinstance(frontmatter[key], list), f"{path.name}: {key} must be a list"

    superseded_by = frontmatter["superseded_by"]
    assert superseded_by is None or ID_PATTERN.match(str(superseded_by)), (
        f"{path.name}: superseded_by must be null or an ADR id"
    )


def test_ids_unique() -> None:
    """No two ADR files declare the same id."""
    seen: dict[str, str] = {}
    for path in _adr_paths():
        frontmatter, _ = _parse_adr(path)
        adr_id = str(frontmatter.get("id"))
        assert adr_id not in seen, f"duplicate id {adr_id} in {path.name} and {seen[adr_id]}"
        seen[adr_id] = path.name


# --- Rules 4-5: relation graph ----------------------------------------------


def test_relations_resolve() -> None:
    """Every relation target points at an ADR id that exists."""
    adrs = _all_adrs()
    for adr_id, (path, frontmatter, _) in adrs.items():
        targets = list(frontmatter["supersedes"]) + list(frontmatter["depends_on"]) + list(frontmatter["related_to"])
        if frontmatter["superseded_by"] is not None:
            targets.append(frontmatter["superseded_by"])
        for target in targets:
            assert str(target) in adrs, f"{path.name}: relation target {target} does not exist"
            assert str(target) != adr_id, f"{path.name}: ADR relates to itself"


def test_supersedes_consistency() -> None:
    """superseded status and supersedes/superseded_by edges are mutually consistent."""
    adrs = _all_adrs()
    for _, (path, frontmatter, _) in adrs.items():
        is_superseded = frontmatter["status"] == "superseded"
        has_successor = frontmatter["superseded_by"] is not None
        assert is_superseded == has_successor, (
            f"{path.name}: status 'superseded' and a non-null superseded_by must appear together"
        )
        if has_successor:
            successor = adrs.get(str(frontmatter["superseded_by"]))
            assert successor is not None, f"{path.name}: superseded_by target missing"
            assert frontmatter["id"] in successor[1]["supersedes"], (
                f"{path.name}: {frontmatter['superseded_by']} does not list {frontmatter['id']} in supersedes"
            )
    for _, (path, frontmatter, _) in adrs.items():
        for old_id in frontmatter["supersedes"]:
            old = adrs.get(str(old_id))
            assert old is not None, f"{path.name}: supersedes target {old_id} missing"
            assert old[1]["superseded_by"] == frontmatter["id"], (
                f"{path.name}: supersedes {old_id}, but {old_id}.superseded_by is {old[1]['superseded_by']!r}"
            )


# --- Rules 6-7: body structure ----------------------------------------------


@pytest.mark.parametrize("path", _adr_paths(), ids=lambda p: p.name)
def test_body_sections(path: Path) -> None:
    """Required body sections exist; rejected alternatives each get an H3."""
    frontmatter, body = _parse_adr(path)

    for section in REQUIRED_BODY_SECTIONS:
        assert re.search(rf"^{re.escape(section)}\s*$", body, re.MULTILINE), (
            f"{path.name}: missing body section '{section}'"
        )

    rejected = frontmatter["rejected_alternatives"]
    if rejected:
        assert re.search(r"^## Alternatives considered\s*$", body, re.MULTILINE), (
            f"{path.name}: rejected_alternatives set but no '## Alternatives considered' section"
        )
        for slug in rejected:
            assert re.search(rf"^### {re.escape(str(slug))}\s*$", body, re.MULTILINE), (
                f"{path.name}: no '### {slug}' heading for rejected alternative"
            )


# --- Rule 8: README index sync ----------------------------------------------


def test_readme_index_in_sync() -> None:
    """docs/adr/README.md lists exactly the ADR ids present, with their status."""
    readme = ADR_DIR / "README.md"
    adrs = _all_adrs()
    if not adrs and not readme.exists():
        pytest.skip("no ADRs and no index yet")
    assert readme.exists(), "docs/adr/README.md index is missing"

    text = readme.read_text(encoding="utf-8")
    listed = set(re.findall(r"ADR-\d{4}", text))
    present = set(adrs)
    assert listed == present, (
        f"README index out of sync — listed but missing as files: {sorted(listed - present)}; "
        f"files not listed: {sorted(present - listed)}"
    )
    for adr_id, (path, frontmatter, _) in adrs.items():
        row = next((line for line in text.splitlines() if adr_id in line), "")
        assert frontmatter["status"] in row, (
            f"README row for {adr_id} does not show its status {frontmatter['status']!r} ({path.name})"
        )

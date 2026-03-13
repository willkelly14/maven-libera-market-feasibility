#!/usr/bin/env python3
"""
Research API — CLI interface for the research pipeline.

Abstracts YAML I/O for facts, documents, and staging files.
All output is JSON to stdout. Complex input comes as JSON on stdin.

Usage:
    python3 research_api.py <command> [options]
    echo '{"claim":"..."}' | python3 research_api.py add-fact --section 01
"""

import argparse
import fnmatch
import glob
import json
import os
import re
import subprocess
import sys

try:
    import yaml
except ImportError:
    print(json.dumps({"error": "PyYAML not found. Run: pip install pyyaml"}), file=sys.stderr)
    sys.exit(3)

# ── Constants ────────────────────────────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FACT_DB_DIR = os.path.join(BASE_DIR, "Fact Database")
DOCS_DIR = os.path.join(BASE_DIR, "Documents")
FACT_STAGING_DIR = os.path.join(FACT_DB_DIR, "staging")
DOC_STAGING_DIR = os.path.join(DOCS_DIR, "staging")
ARCHIVE_FILE = os.path.join(FACT_DB_DIR, "archive.yaml")
DOC_INDEX_FILE = os.path.join(DOCS_DIR, "documents_index.yaml")

SECTION_LABELS = {
    "01_Macro_Context": "01 — Macro Context",
    "02_Regional_Endowment": "02 — Regional Endowment",
    "03_Market_Definition": "03 — Market Definition",
    "04_Demand_Assessment": "04 — Demand Assessment",
    "05_Supply_Side": "05 — Supply Side",
    "06_Gap_Analysis": "06 — Gap Analysis",
    "07_Growth_Outlook": "07 — Growth Outlook",
    "08_Pricing": "08 — Pricing",
    "09_Risk_Factors": "09 — Risk Factors",
    "10_Conclusions": "10 — Conclusions",
}

VALID_SOURCE_TYPES = {
    "government_publication", "government_data", "international_organisation",
    "academic_paper", "industry_report", "company_filing", "company_website",
    "media", "consultation", "internal_data", "local_file",
}

VALID_SECTION_IDS = set(SECTION_LABELS.keys())

VALID_DOC_TYPES = {
    "section_draft", "data_sources", "research_plan",
    "research_report", "source_reference",
}

VALID_DOC_STATUSES = {"draft", "stub", "complete", "in_review"}

VALID_CONFIDENCE = {"high", "medium", "low"}

# ── Exceptions ───────────────────────────────────────────────────────────────


class ValidationError(Exception):
    pass


class NotFoundError(Exception):
    pass


class ConflictError(Exception):
    pass


# ── Helpers ──────────────────────────────────────────────────────────────────


def read_yaml(path):
    """Read and parse a YAML file. Returns [] if file doesn't exist or is empty."""
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f.read())
    if data is None:
        return []
    if not isinstance(data, list):
        return [data]
    return data


def write_yaml(path, data):
    """Write data to a YAML file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


def read_stdin_json():
    """Read JSON from stdin."""
    raw = sys.stdin.read().strip()
    if not raw:
        raise ValidationError("No input on stdin")
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValidationError(f"Invalid JSON on stdin: {e}")


def read_stdin_raw():
    """Read raw text from stdin."""
    return sys.stdin.read()


def output_json(data):
    """Write JSON to stdout."""
    print(json.dumps(data, indent=2, default=str))


def output_error(msg, code=1):
    """Write error JSON to stdout and exit."""
    print(json.dumps({"error": msg}))
    sys.exit(code)


def resolve_section_file(section_prefix):
    """Find the YAML file for a section prefix (e.g. '01' -> '01_macro_context.yaml').
    Returns the full path, or raises NotFoundError."""
    if section_prefix.upper() == "XX":
        path = os.path.join(FACT_DB_DIR, "_cross_section.yaml")
        if os.path.exists(path):
            return path
        # Create it if it doesn't exist
        write_yaml(path, [])
        return path

    pattern = os.path.join(FACT_DB_DIR, f"{section_prefix}_*.yaml")
    matches = glob.glob(pattern)
    if not matches:
        raise NotFoundError(f"No YAML file found for section prefix '{section_prefix}'")
    if len(matches) > 1:
        # Multiple files for same prefix — pick the first alphabetically
        matches.sort()
    return matches[0]


def get_all_fact_files():
    """Return all YAML fact files (not staging, not archive)."""
    all_files = sorted(glob.glob(os.path.join(FACT_DB_DIR, "*.yaml")))
    return [f for f in all_files if os.path.basename(f) != "archive.yaml"]


def load_all_facts():
    """Load all facts from all section files."""
    facts = []
    for fpath in get_all_fact_files():
        for fact in read_yaml(fpath):
            if isinstance(fact, dict) and "id" in fact:
                fact["_file"] = os.path.basename(fpath)
                facts.append(fact)
    return facts


def load_archive():
    """Load archived facts."""
    return [f for f in read_yaml(ARCHIVE_FILE) if isinstance(f, dict) and "id" in f]


def prefix_from_id(fact_id):
    """Extract section prefix from a fact ID (e.g. '01-003' -> '01')."""
    parts = fact_id.split("-")
    if len(parts) != 2:
        raise ValidationError(f"Invalid fact ID format: {fact_id}")
    return parts[0]


def find_fact_in_files(fact_id):
    """Find a fact by ID across all files. Returns (filepath, index, fact) or raises NotFoundError."""
    prefix = prefix_from_id(fact_id)
    # Try the expected section file first
    try:
        section_file = resolve_section_file(prefix)
        facts = read_yaml(section_file)
        for i, fact in enumerate(facts):
            if isinstance(fact, dict) and fact.get("id") == fact_id:
                return section_file, i, fact
    except NotFoundError:
        pass

    # Fallback: scan all files
    for fpath in get_all_fact_files():
        facts = read_yaml(fpath)
        for i, fact in enumerate(facts):
            if isinstance(fact, dict) and fact.get("id") == fact_id:
                return fpath, i, fact

    raise NotFoundError(f"Fact '{fact_id}' not found")


# ── Validators ───────────────────────────────────────────────────────────────


def validate_fact(data):
    """Validate a fact dict. Returns list of error strings."""
    errors = []

    # Required fields
    required = ["claim", "source_quotes", "source_name", "source_url",
                "source_type", "source_date", "sections_used", "verified", "date_added"]
    for field in required:
        if field not in data:
            errors.append(f"Missing required field: {field}")

    # Type checks on present fields
    if "claim" in data and not isinstance(data["claim"], str):
        errors.append("'claim' must be a string")

    if "source_quotes" in data:
        if not isinstance(data["source_quotes"], list):
            errors.append("'source_quotes' must be a list")
        elif len(data["source_quotes"]) == 0:
            errors.append("'source_quotes' must not be empty")
        else:
            for i, q in enumerate(data["source_quotes"]):
                if not isinstance(q, str):
                    errors.append(f"source_quotes[{i}] must be a string")

    if "source_type" in data and data["source_type"] not in VALID_SOURCE_TYPES:
        errors.append(f"Invalid source_type: '{data['source_type']}'. Must be one of: {sorted(VALID_SOURCE_TYPES)}")

    if "sections_used" in data:
        if not isinstance(data["sections_used"], list):
            errors.append("'sections_used' must be a list")
        elif len(data["sections_used"]) == 0:
            errors.append("'sections_used' must not be empty")
        else:
            for s in data["sections_used"]:
                if s not in VALID_SECTION_IDS:
                    errors.append(f"Invalid section identifier: '{s}'. Must be one of: {sorted(VALID_SECTION_IDS)}")

    if "verified" in data and not isinstance(data["verified"], bool):
        errors.append("'verified' must be a boolean")

    if "date_added" in data:
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", str(data["date_added"])):
            errors.append("'date_added' must be YYYY-MM-DD format")

    if "source_date" in data:
        if not re.match(r"^\d{4}-\d{2}(-\d{2})?$", str(data["source_date"])):
            errors.append("'source_date' must be YYYY-MM or YYYY-MM-DD format")

    # Optional field type checks
    if "document" in data and data["document"]:
        if not re.match(r"^DOC-\d{3}$", str(data["document"])):
            errors.append("'document' must be in DOC-NNN format")

    if "confidence" in data and data["confidence"]:
        if data["confidence"] not in VALID_CONFIDENCE:
            errors.append(f"Invalid confidence: '{data['confidence']}'. Must be one of: {sorted(VALID_CONFIDENCE)}")

    for field in ["source_name", "source_url", "source_author", "source_page",
                  "source_accessed", "source_excerpt", "added_by", "notes",
                  "verification_notes"]:
        if field in data and data[field] is not None and not isinstance(data[field], str):
            errors.append(f"'{field}' must be a string")

    return errors


def validate_doc(data):
    """Validate a document dict. Returns list of error strings."""
    errors = []

    required = ["title", "type", "section"]
    for field in required:
        if field not in data:
            errors.append(f"Missing required field: {field}")

    if "type" in data and data["type"] not in VALID_DOC_TYPES:
        errors.append(f"Invalid doc type: '{data['type']}'. Must be one of: {sorted(VALID_DOC_TYPES)}")

    if "section" in data and data["section"] not in VALID_SECTION_IDS:
        errors.append(f"Invalid section: '{data['section']}'. Must be one of: {sorted(VALID_SECTION_IDS)}")

    if "status" in data and data["status"] and data["status"] not in VALID_DOC_STATUSES:
        errors.append(f"Invalid status: '{data['status']}'. Must be one of: {sorted(VALID_DOC_STATUSES)}")

    return errors


# ── Fact Commands ─────────────────────────────────────────────────────────────


def cmd_list_facts(args):
    facts = load_all_facts()

    # Apply filters
    if args.section:
        prefix = args.section
        facts = [f for f in facts if f["id"].startswith(prefix + "-")]

    if args.verified is not None:
        v = args.verified.lower() == "true"
        facts = [f for f in facts if f.get("verified") == v]

    if args.document:
        facts = [f for f in facts if f.get("document") == args.document]

    # Remove internal _file field from output
    for f in facts:
        f.pop("_file", None)

    output_json(facts)


def cmd_get_fact(args):
    _, _, fact = find_fact_in_files(args.id)
    output_json(fact)


def cmd_add_fact(args):
    data = read_stdin_json()
    section_prefix = args.section

    # Auto-assign ID
    next_id = _compute_next_id(section_prefix)
    data["id"] = next_id

    # Validate
    errors = validate_fact(data)
    if errors:
        output_json({"errors": errors})
        sys.exit(1)

    # Find the section file and append
    section_file = resolve_section_file(section_prefix)
    facts = read_yaml(section_file)
    facts.append(data)
    write_yaml(section_file, facts)

    output_json(data)


def cmd_update_fact(args):
    filepath, idx, fact = find_fact_in_files(args.id)
    updates = read_stdin_json()

    # Don't allow changing the ID
    updates.pop("id", None)

    fact.update(updates)

    # Write back
    facts = read_yaml(filepath)
    facts[idx] = fact
    write_yaml(filepath, facts)

    output_json(fact)


def cmd_archive_fact(args):
    filepath, idx, fact = find_fact_in_files(args.id)

    # Add archive metadata
    fact["archive_reason"] = args.reason
    fact["archive_date"] = _today()

    # Append to archive
    archive = read_yaml(ARCHIVE_FILE) if os.path.exists(ARCHIVE_FILE) else []
    archive.append(fact)
    write_yaml(ARCHIVE_FILE, archive)

    # Remove from section file
    facts = read_yaml(filepath)
    facts.pop(idx)
    write_yaml(filepath, facts)

    output_json({"archived": args.id, "reason": args.reason})


def cmd_next_id(args):
    next_id = _compute_next_id(args.section_prefix)
    output_json({"next_id": next_id})


def _compute_next_id(section_prefix):
    """Compute the next available ID for a section, checking both active facts and archive."""
    max_seq = 0

    # Check section file
    try:
        section_file = resolve_section_file(section_prefix)
        for fact in read_yaml(section_file):
            if isinstance(fact, dict) and "id" in fact:
                fid = fact["id"]
                parts = fid.split("-")
                if len(parts) == 2 and parts[0] == section_prefix:
                    try:
                        seq = int(parts[1])
                        max_seq = max(max_seq, seq)
                    except ValueError:
                        pass
    except NotFoundError:
        pass

    # Check archive too (IDs are never reused)
    for fact in load_archive():
        fid = fact.get("id", "")
        parts = fid.split("-")
        if len(parts) == 2 and parts[0] == section_prefix:
            try:
                seq = int(parts[1])
                max_seq = max(max_seq, seq)
            except ValueError:
                pass

    return f"{section_prefix}-{max_seq + 1:03d}"


def _today():
    from datetime import date
    return date.today().isoformat()


# ── Document Commands ─────────────────────────────────────────────────────────


def cmd_list_docs(args):
    docs = read_yaml(DOC_INDEX_FILE)
    output_json(docs)


def cmd_get_doc(args):
    docs = read_yaml(DOC_INDEX_FILE)
    for doc in docs:
        if isinstance(doc, dict) and doc.get("id") == args.id:
            # Load content if available
            content_file = doc.get("content_file", "")
            if content_file:
                content_path = os.path.join(DOCS_DIR, content_file)
                if os.path.exists(content_path):
                    with open(content_path, "r", encoding="utf-8") as f:
                        doc["content"] = f.read()
                else:
                    doc["content"] = ""
            output_json(doc)
            return
    raise NotFoundError(f"Document '{args.id}' not found")


def cmd_add_doc(args):
    data = read_stdin_json()

    errors = validate_doc(data)
    if errors:
        output_json({"errors": errors})
        sys.exit(1)

    # Auto-assign DOC-NNN ID
    docs = read_yaml(DOC_INDEX_FILE)
    max_num = 0
    for doc in docs:
        if isinstance(doc, dict) and "id" in doc:
            m = re.match(r"^DOC-(\d{3})$", doc["id"])
            if m:
                max_num = max(max_num, int(m.group(1)))
    new_id = f"DOC-{max_num + 1:03d}"
    data["id"] = new_id

    # Set defaults
    data.setdefault("status", "draft")
    data.setdefault("date_created", _today())
    data.setdefault("description", "")
    data.setdefault("content_file", "")

    docs.append(data)
    write_yaml(DOC_INDEX_FILE, docs)

    output_json(data)


def cmd_update_doc(args):
    docs = read_yaml(DOC_INDEX_FILE)
    updates = read_stdin_json()
    updates.pop("id", None)

    for i, doc in enumerate(docs):
        if isinstance(doc, dict) and doc.get("id") == args.id:
            doc.update(updates)
            docs[i] = doc
            write_yaml(DOC_INDEX_FILE, docs)
            output_json(doc)
            return

    raise NotFoundError(f"Document '{args.id}' not found")


def cmd_write_doc_content(args):
    docs = read_yaml(DOC_INDEX_FILE)
    for doc in docs:
        if isinstance(doc, dict) and doc.get("id") == args.id:
            content_file = doc.get("content_file", "")
            if not content_file:
                raise ValidationError(f"Document '{args.id}' has no content_file set")
            content_path = os.path.join(DOCS_DIR, content_file)
            content = read_stdin_raw()
            os.makedirs(os.path.dirname(content_path), exist_ok=True)
            with open(content_path, "w", encoding="utf-8") as f:
                f.write(content)
            output_json({"ok": True, "file": content_file, "bytes": len(content)})
            return

    raise NotFoundError(f"Document '{args.id}' not found")


# ── Staging Commands ──────────────────────────────────────────────────────────


def cmd_write_staging_facts(args):
    data = read_stdin_json()
    if not isinstance(data, list):
        data = [data]
    path = os.path.join(FACT_STAGING_DIR, args.filename)
    write_yaml(path, data)
    output_json({"ok": True, "file": args.filename, "count": len(data)})


def cmd_read_staging_facts(args):
    pattern = args.pattern or "*"
    results = {}
    if os.path.exists(FACT_STAGING_DIR):
        for fname in sorted(os.listdir(FACT_STAGING_DIR)):
            if fnmatch.fnmatch(fname, pattern) and fname.endswith((".yaml", ".yml")):
                fpath = os.path.join(FACT_STAGING_DIR, fname)
                results[fname] = read_yaml(fpath)
    output_json(results)


def cmd_write_staging_doc(args):
    content = read_stdin_raw()
    path = os.path.join(DOC_STAGING_DIR, args.filename)
    os.makedirs(DOC_STAGING_DIR, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    output_json({"ok": True, "file": args.filename, "bytes": len(content)})


def cmd_read_staging_docs(args):
    pattern = args.pattern or "*"
    results = {}
    if os.path.exists(DOC_STAGING_DIR):
        for fname in sorted(os.listdir(DOC_STAGING_DIR)):
            if fnmatch.fnmatch(fname, pattern):
                fpath = os.path.join(DOC_STAGING_DIR, fname)
                with open(fpath, "r", encoding="utf-8") as f:
                    results[fname] = f.read()
    output_json(results)


def cmd_write_corrections(args):
    data = read_stdin_json()
    if not isinstance(data, list):
        data = [data]
    path = os.path.join(FACT_STAGING_DIR, args.filename)
    write_yaml(path, data)
    output_json({"ok": True, "file": args.filename, "count": len(data)})


def cmd_read_corrections(args):
    pattern = args.pattern or "corrections_*"
    results = {}
    if os.path.exists(FACT_STAGING_DIR):
        for fname in sorted(os.listdir(FACT_STAGING_DIR)):
            if fnmatch.fnmatch(fname, pattern) and fname.endswith((".yaml", ".yml")):
                fpath = os.path.join(FACT_STAGING_DIR, fname)
                results[fname] = read_yaml(fpath)
    output_json(results)


def cmd_clean_staging(args):
    removed = []
    for staging_dir in [FACT_STAGING_DIR, DOC_STAGING_DIR]:
        if os.path.exists(staging_dir):
            for fname in os.listdir(staging_dir):
                fpath = os.path.join(staging_dir, fname)
                if os.path.isfile(fpath):
                    os.remove(fpath)
                    removed.append(os.path.join(os.path.basename(staging_dir), fname))
    output_json({"ok": True, "removed": removed, "count": len(removed)})


# ── Utility Commands ──────────────────────────────────────────────────────────


def cmd_build(args):
    result = subprocess.run(
        [sys.executable, os.path.join(BASE_DIR, "build_dashboard.py")],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        output_json({"ok": True, "output": result.stdout.strip()})
    else:
        output_json({"ok": False, "error": result.stderr.strip(), "output": result.stdout.strip()})
        sys.exit(3)


def cmd_validate_fact(args):
    data = read_stdin_json()
    errors = validate_fact(data)
    if errors:
        output_json({"valid": False, "errors": errors})
        sys.exit(1)
    else:
        output_json({"valid": True, "errors": []})


def cmd_count_facts(args):
    facts = load_all_facts()
    total = len(facts)
    verified = sum(1 for f in facts if f.get("verified"))
    unverified = total - verified

    by_section = {}
    for f in facts:
        prefix = f["id"].split("-")[0]
        by_section.setdefault(prefix, {"total": 0, "verified": 0})
        by_section[prefix]["total"] += 1
        if f.get("verified"):
            by_section[prefix]["verified"] += 1

    result = {
        "total": total,
        "verified": verified,
        "unverified": unverified,
        "by_section": by_section,
    }

    if args.section:
        prefix = args.section
        section_data = by_section.get(prefix, {"total": 0, "verified": 0})
        result = {
            "section": prefix,
            "total": section_data["total"],
            "verified": section_data["verified"],
            "unverified": section_data["total"] - section_data["verified"],
        }

    output_json(result)


# ── CLI Wiring ────────────────────────────────────────────────────────────────


def build_parser():
    parser = argparse.ArgumentParser(
        prog="research_api",
        description="CLI API for the research pipeline — JSON-in/JSON-out interface for facts, documents, and staging."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # Facts
    p = sub.add_parser("list-facts", help="List facts with optional filters")
    p.add_argument("--section", help="Filter by section prefix (e.g. 01)")
    p.add_argument("--verified", help="Filter by verified status (true/false)")
    p.add_argument("--document", help="Filter by document ID (e.g. DOC-001)")

    p = sub.add_parser("get-fact", help="Get a single fact by ID")
    p.add_argument("id", help="Fact ID (e.g. 01-003)")

    p = sub.add_parser("add-fact", help="Add a fact (JSON on stdin), auto-assigns ID")
    p.add_argument("--section", required=True, help="Section prefix (e.g. 01, XX)")

    p = sub.add_parser("update-fact", help="Partial update of a fact (JSON on stdin)")
    p.add_argument("id", help="Fact ID to update")

    p = sub.add_parser("archive-fact", help="Move a fact to archive.yaml")
    p.add_argument("id", help="Fact ID to archive")
    p.add_argument("--reason", required=True, help="Reason for archiving")

    p = sub.add_parser("next-id", help="Return next available ID for a section")
    p.add_argument("section_prefix", help="Section prefix (e.g. 01, XX)")

    # Documents
    sub.add_parser("list-docs", help="List all documents from index")

    p = sub.add_parser("get-doc", help="Get document metadata and content")
    p.add_argument("id", help="Document ID (e.g. DOC-001)")

    sub.add_parser("add-doc", help="Add a document (JSON on stdin), auto-assigns ID")

    p = sub.add_parser("update-doc", help="Partial update of document metadata (JSON on stdin)")
    p.add_argument("id", help="Document ID to update")

    p = sub.add_parser("write-doc-content", help="Write document content from stdin (raw text)")
    p.add_argument("id", help="Document ID")

    # Staging
    p = sub.add_parser("write-staging-facts", help="Write facts to staging (JSON stdin -> YAML)")
    p.add_argument("filename", help="Staging filename (e.g. batch_01.yaml)")

    p = sub.add_parser("read-staging-facts", help="Read matching staging fact files as JSON")
    p.add_argument("pattern", nargs="?", default="*", help="Glob pattern (default: *)")

    p = sub.add_parser("write-staging-doc", help="Write doc section to staging (raw stdin)")
    p.add_argument("filename", help="Staging filename")

    p = sub.add_parser("read-staging-docs", help="Read matching staging doc files as JSON")
    p.add_argument("pattern", nargs="?", default="*", help="Glob pattern (default: *)")

    p = sub.add_parser("write-corrections", help="Write corrections to staging (JSON stdin)")
    p.add_argument("filename", help="Corrections filename (e.g. corrections_01.yaml)")

    p = sub.add_parser("read-corrections", help="Read correction files as JSON")
    p.add_argument("pattern", nargs="?", default="corrections_*", help="Glob pattern (default: corrections_*)")

    sub.add_parser("clean-staging", help="Remove all staging files from both dirs")

    # Utility
    sub.add_parser("build", help="Rebuild dashboard.html")

    sub.add_parser("validate-fact", help="Validate fact JSON from stdin")

    p = sub.add_parser("count-facts", help="Count facts with breakdown")
    p.add_argument("--section", help="Filter by section prefix")

    return parser


COMMAND_MAP = {
    "list-facts": cmd_list_facts,
    "get-fact": cmd_get_fact,
    "add-fact": cmd_add_fact,
    "update-fact": cmd_update_fact,
    "archive-fact": cmd_archive_fact,
    "next-id": cmd_next_id,
    "list-docs": cmd_list_docs,
    "get-doc": cmd_get_doc,
    "add-doc": cmd_add_doc,
    "update-doc": cmd_update_doc,
    "write-doc-content": cmd_write_doc_content,
    "write-staging-facts": cmd_write_staging_facts,
    "read-staging-facts": cmd_read_staging_facts,
    "write-staging-doc": cmd_write_staging_doc,
    "read-staging-docs": cmd_read_staging_docs,
    "write-corrections": cmd_write_corrections,
    "read-corrections": cmd_read_corrections,
    "clean-staging": cmd_clean_staging,
    "build": cmd_build,
    "validate-fact": cmd_validate_fact,
    "count-facts": cmd_count_facts,
}


def main():
    parser = build_parser()
    args = parser.parse_args()

    handler = COMMAND_MAP.get(args.command)
    if not handler:
        output_error(f"Unknown command: {args.command}")

    try:
        handler(args)
    except ValidationError as e:
        output_error(str(e), code=1)
    except NotFoundError as e:
        output_error(str(e), code=2)
    except IOError as e:
        output_error(str(e), code=3)
    except ConflictError as e:
        output_error(str(e), code=4)


if __name__ == "__main__":
    main()

"""Stream the three large CMHG CSVs and check exact annotated-data overlap."""

import csv
import hashlib
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit


REVISION = "71e854248c3af4f12ad04abfb85848a0d648ae9e"
SOURCES = {"bo": "bo-all.csv", "mn": "mn-all.csv", "ug": "ug-3.csv"}
EXPECTED_BYTES = {"bo": 570812548, "mn": 330051948, "ug": 468395008}


def file_sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def pair_hash(row):
    title = row["title"].strip()
    content = row["content"].strip()
    return hashlib.sha256((title + "\0" + content).encode("utf-8")).hexdigest()


def normalized_content_hash(content):
    normalized = re.sub(r"\s+", " ", unicodedata.normalize("NFC", content)).strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def annotated_sets(root, language):
    ids, pairs, contents = set(), set(), set()
    for filename in ("average_score_4_or_higher.csv", "average_score_below_4.csv"):
        with (root / language / filename).open(encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                if row["id"].strip():
                    ids.add(row["id"].strip())
                if row["title"].strip() and row["content"].strip():
                    pairs.add(pair_hash(row))
                if row["content"].strip():
                    contents.add(normalized_content_hash(row["content"]))
    return ids, pairs, contents


def main():
    csv.field_size_limit(2**31 - 1)
    workspace = Path(__file__).resolve().parents[1]
    root = workspace / "data/raw/cmhg" / REVISION
    report = {
        "dataset_id": "KEVVVV/CMHG",
        "revision": REVISION,
        "scope": "Exact ID and title-content overlap between full and annotated CSVs; near duplicates not checked",
        "languages": {},
    }
    for language, filename in SOURCES.items():
        source = root / language / filename
        size = source.stat().st_size
        if size != EXPECTED_BYTES[language]:
            raise ValueError(f"Incomplete or changed download: {source} is {size} bytes")
        annotated_ids, annotated_pairs, annotated_contents = annotated_sets(root, language)
        summary = {
            "file": f"{language}/{filename}",
            "bytes": size,
            "sha256": file_sha256(source),
            "columns": [],
            "rows": 0,
            "row_width_errors": 0,
            "missing_id": 0,
            "missing_title": 0,
            "missing_content": 0,
            "duplicate_ids_within_full": 0,
            "duplicate_title_content_pairs_within_full": 0,
            "annotated_unique_ids": len(annotated_ids),
            "annotated_unique_title_content_pairs": len(annotated_pairs),
            "annotated_unique_normalized_contents": len(annotated_contents),
            "full_rows_matching_annotated_id": 0,
            "full_rows_matching_annotated_pair": 0,
            "full_rows_matching_both": 0,
            "full_rows_matching_annotated_normalized_content": 0,
            "full_rows_matching_content_but_not_pair": 0,
            "unique_annotated_pairs_found_in_full": 0,
            "matched_pair_url_hosts_top_10": [],
            "candidate_training_rows_after_exact_exclusion": 0,
            "candidate_training_rows_after_content_exclusion": 0,
        }
        seen_ids, seen_pairs, matched_pairs = set(), set(), set()
        matched_hosts = Counter()
        with source.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            summary["columns"] = reader.fieldnames
            for column in ("id", "title", "content"):
                if column not in reader.fieldnames:
                    raise ValueError(f"{source}: missing {column}; found {reader.fieldnames}")
            for row in reader:
                summary["rows"] += 1
                if None in row or any(value is None for value in row.values()):
                    summary["row_width_errors"] += 1
                    continue
                article_id = row["id"].strip()
                title = row["title"].strip()
                content = row["content"].strip()
                if not article_id:
                    summary["missing_id"] += 1
                if not title:
                    summary["missing_title"] += 1
                if not content:
                    summary["missing_content"] += 1
                if article_id:
                    if article_id in seen_ids:
                        summary["duplicate_ids_within_full"] += 1
                    seen_ids.add(article_id)
                pair = pair_hash(row) if title and content else None
                if pair:
                    if pair in seen_pairs:
                        summary["duplicate_title_content_pairs_within_full"] += 1
                    seen_pairs.add(pair)
                match_id = article_id in annotated_ids if article_id else False
                match_pair = pair in annotated_pairs if pair else False
                match_content = (normalized_content_hash(content) in annotated_contents
                                 if content else False)
                summary["full_rows_matching_annotated_id"] += int(match_id)
                summary["full_rows_matching_annotated_pair"] += int(match_pair)
                summary["full_rows_matching_both"] += int(match_id and match_pair)
                summary["full_rows_matching_annotated_normalized_content"] += int(match_content)
                summary["full_rows_matching_content_but_not_pair"] += int(match_content and not match_pair)
                if match_pair:
                    matched_pairs.add(pair)
                    matched_hosts[urlsplit(row.get("url", "")).hostname or "(missing)"] += 1
                if not match_id and not match_pair and article_id and title and content:
                    summary["candidate_training_rows_after_exact_exclusion"] += 1
                    if not match_content:
                        summary["candidate_training_rows_after_content_exclusion"] += 1
        summary["unique_annotated_pairs_found_in_full"] = len(matched_pairs)
        summary["matched_pair_url_hosts_top_10"] = matched_hosts.most_common(10)
        report["languages"][language] = summary
        print(json.dumps({"language": language, **summary}, ensure_ascii=False), flush=True)
    output = workspace / "results/cmhg_full_audit.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()

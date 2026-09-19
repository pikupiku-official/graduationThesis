"""Choose reproducible CMHG evaluation candidates, without running a model.

The output is provisional until near-duplicate and source-domain review is done.
"""

import csv
import hashlib
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path


REVISION = "71e854248c3af4f12ad04abfb85848a0d648ae9e"
LANGUAGES = ("bo", "mn", "ug")
N_PER_LANGUAGE = 200


def normalized_hash(value):
    normalized = re.sub(r"\s+", " ", unicodedata.normalize("NFC", value)).strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def read_rows(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def main():
    workspace = Path(__file__).resolve().parents[1]
    dev = json.loads((workspace / "experiments/cmhg_dev_ids.json").read_text(encoding="utf-8"))
    if dev["revision"] != REVISION:
        raise ValueError("Dataset revision mismatch")
    report = {
        "status": "candidate only; do not use before near-duplicate and domain review",
        "dataset_id": "KEVVVV/CMHG",
        "dataset_revision": REVISION,
        "selection_rule": "200 lowest SHA-256 of cmhg-eval-v1|language|normalized-content-hash, after exclusions",
        "score_rule": "average_score > 4; score exactly 4 is excluded to follow the paper's stated boundary",
        "languages": {},
    }
    for language in LANGUAGES:
        root = workspace / "data/raw/cmhg" / REVISION / language
        high = read_rows(root / "average_score_4_or_higher.csv")
        low = read_rows(root / "average_score_below_4.csv")
        all_id_counts = Counter(row["id"].strip() for row in high + low if row["id"].strip())
        low_contents = {normalized_hash(row["content"]) for row in low if row["content"].strip()}
        dev_ids = set(dev["languages"][language])
        dev_contents = {normalized_hash(row["content"]) for row in high
                        if row["id"] in dev_ids and row["content"].strip()}
        excluded = Counter()
        eligible = {}
        for row in high:
            article_id = row["id"].strip()
            title = row["title"].strip()
            content = row["content"].strip()
            if not article_id or not title or not content:
                excluded["missing_field"] += 1
                continue
            try:
                score = float(row["average_score"])
            except ValueError:
                excluded["invalid_score"] += 1
                continue
            if score <= 4:
                excluded["score_at_or_below_4"] += 1
                continue
            if all_id_counts[article_id] != 1:
                excluded["repeated_id"] += 1
                continue
            content_hash = normalized_hash(content)
            if content_hash in low_contents:
                excluded["content_also_in_low_score_file"] += 1
                continue
            if article_id in dev_ids or content_hash in dev_contents:
                excluded["development_id_or_content"] += 1
                continue
            rank = hashlib.sha256(
                f"cmhg-eval-v1|{language}|{content_hash}".encode("ascii")
            ).hexdigest()
            candidate = {"id": article_id, "normalized_content_sha256": content_hash,
                         "average_score": score, "rank": rank}
            if content_hash in eligible:
                excluded["duplicate_content_within_high_score"] += 1
                if (rank, article_id) < (eligible[content_hash]["rank"], eligible[content_hash]["id"]):
                    eligible[content_hash] = candidate
            else:
                eligible[content_hash] = candidate
        ordered = sorted(eligible.values(), key=lambda row: (row["rank"], row["id"]))
        if len(ordered) < N_PER_LANGUAGE:
            raise ValueError(f"Only {len(ordered)} eligible records for {language}")
        selected = ordered[:N_PER_LANGUAGE]
        if any(row["id"] in dev_ids or row["normalized_content_sha256"] in dev_contents
               for row in selected):
            raise AssertionError("Development leakage")
        report["languages"][language] = {
            "high_score_source_rows": len(high),
            "low_score_source_rows": len(low),
            "exclusions_in_filter_order": dict(excluded),
            "eligible_unique_contents": len(ordered),
            "selected_count": len(selected),
            "selected": selected,
        }
        print(f"{language}: {len(selected)} selected from {len(ordered)} eligible unique contents; exclusions={dict(excluded)}")
    output = workspace / "experiments/cmhg_eval_candidates.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()

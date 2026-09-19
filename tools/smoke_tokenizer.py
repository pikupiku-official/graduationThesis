"""Tokenization-only smoke test for the fixed CMHG development IDs."""

import argparse
import csv
import json
import statistics
from pathlib import Path

from transformers import AutoTokenizer


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="Qwen/Qwen3-8B")
    parser.add_argument("--model-revision", default="b968826d9c46dd6066d109eabc6255188de91218")
    parser.add_argument("--context-budget", type=int, default=2048)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    dev = json.loads((root / "experiments/cmhg_dev_ids.json").read_text(encoding="utf-8"))
    tokenizer = AutoTokenizer.from_pretrained(args.model, revision=args.model_revision)
    report = {
        "purpose": "Pipeline feasibility only; do not use as performance estimate",
        "dataset_revision": dev["revision"],
        "model_id": args.model,
        "model_revision": args.model_revision,
        "transformers_version": __import__("transformers").__version__,
        "context_budget_tokens": args.context_budget,
        "languages": {},
    }
    for language, ids in dev["languages"].items():
        source = root / "data/raw/cmhg" / dev["revision"] / language / "average_score_4_or_higher.csv"
        wanted = set(ids)
        rows = {}
        with source.open(encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                if row["id"] in wanted:
                    if row["id"] in rows:
                        raise ValueError(f"Duplicate development ID: {language}/{row['id']}")
                    rows[row["id"]] = row
        if set(rows) != wanted:
            raise ValueError(f"Missing development IDs: {language}/{sorted(wanted - set(rows))}")
        records = []
        for article_id in ids:
            row = rows[article_id]
            content = row["content"].strip()
            title = row["title"].strip()
            if not content or not title:
                raise ValueError(f"Blank development article: {language}/{article_id}")
            content_tokens = len(tokenizer.encode(content, add_special_tokens=False))
            title_tokens = len(tokenizer.encode(title, add_special_tokens=False))
            records.append({
                "id": article_id,
                "content_characters": len(content),
                "content_tokens": content_tokens,
                "title_characters": len(title),
                "title_tokens": title_tokens,
                "exceeds_context_budget": content_tokens > args.context_budget,
            })
        lengths = [record["content_tokens"] for record in records]
        report["languages"][language] = {
            "n": len(records),
            "content_tokens_median": statistics.median(lengths),
            "content_tokens_max": max(lengths),
            "exceeds_context_budget_count": sum(record["exceeds_context_budget"] for record in records),
            "records": records,
        }
    output = root / "results/cmhg_tokenizer_smoke.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: {name: value for name, value in summary.items() if name != "records"}
                      for key, summary in report["languages"].items()}, indent=2))
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()

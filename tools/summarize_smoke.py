"""Summarize the dev-20 run without publishing generated article text."""

import json
import statistics
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[1]
    dev = json.loads((root / "experiments/cmhg_dev_ids.json").read_text(encoding="utf-8"))
    source = root / "outputs/cmhg_dev20_generate.jsonl"
    rows = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines() if line]
    report = {
        "purpose": "Pipeline smoke test; not a model-performance estimate",
        "dataset_revision": dev["revision"],
        "model_id": "Qwen/Qwen3-8B",
        "model_revision": "b968826d9c46dd6066d109eabc6255188de91218",
        "languages": {},
    }
    for language, ids in dev["languages"].items():
        subset = [row for row in rows if row["language"] == language]
        if len(subset) != len(ids) or set(row["article_id"] for row in subset) != set(ids):
            raise ValueError(f"Incomplete or duplicate run: {language}, got {len(subset)} rows")
        if any(row["dataset_revision"] != dev["revision"] or
               row["model_id"] != report["model_id"] or
               row["model_revision"] != report["model_revision"] for row in subset):
            raise ValueError(f"Mixed dataset/model revision: {language}")
        report["languages"][language] = {
            "n": len(subset),
            "inference_seconds_median": round(statistics.median(row["seconds"] for row in subset), 3),
            "inference_seconds_max": max(row["seconds"] for row in subset),
            "input_clipped_count": sum(bool(row["clipped"]) for row in subset),
            "blank_output_count": sum(not row["prediction"].strip() for row in subset),
            "hit_generation_token_cap_count": sum(row["generated_tokens"] >= row["max_new_tokens"] for row in subset),
            "generation_token_cap": subset[0]["max_new_tokens"],
            "article_token_budget": subset[0]["article_token_budget"],
        }
    output = root / "results/cmhg_generation_smoke.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

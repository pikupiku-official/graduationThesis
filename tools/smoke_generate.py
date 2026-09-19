"""One or 20 articles per language: output-saving smoke test only."""

import argparse
import csv
import json
import time
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig


MODEL_ID = "Qwen/Qwen3-8B"
MODEL_REVISION = "b968826d9c46dd6066d109eabc6255188de91218"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--article-token-budget", type=int, default=1800)
    parser.add_argument("--max-new-tokens", type=int, default=96)
    parser.add_argument("--all-dev", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    dev = json.loads((root / "experiments/cmhg_dev_ids.json").read_text(encoding="utf-8"))
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is unavailable; this test requires GPU quantization")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, revision=MODEL_REVISION)
    quantization = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
    )
    print("Loading model", flush=True)
    load_start = time.perf_counter()
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_ID,
        revision=MODEL_REVISION,
        device_map="auto",
        dtype=torch.bfloat16,
        quantization_config=quantization,
        low_cpu_mem_usage=True,
    )
    print(f"Model loaded in {time.perf_counter() - load_start:.1f}s", flush=True)
    output_path = root / ("outputs/cmhg_dev20_generate.jsonl" if args.all_dev
                          else "outputs/cmhg_smoke_generate.jsonl")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    completed = set()
    if args.all_dev and output_path.exists():
        with output_path.open(encoding="utf-8") as prior:
            for line in prior:
                record = json.loads(line)
                completed.add((record["language"], record["article_id"]))
    with output_path.open("a" if args.all_dev else "w", encoding="utf-8") as output:
        for language, ids in dev["languages"].items():
            source = root / "data/raw/cmhg" / dev["revision"] / language / "average_score_4_or_higher.csv"
            with source.open(encoding="utf-8-sig", newline="") as handle:
                rows = [row for row in csv.DictReader(handle) if row["id"] in ids]
            by_id = {}
            for row in rows:
                if row["id"] in by_id:
                    raise ValueError(f"Duplicate development ID: {language}/{row['id']}")
                by_id[row["id"]] = row
            for article_id in (ids if args.all_dev else ids[:1]):
                if (language, article_id) in completed:
                    continue
                if article_id not in by_id:
                    raise ValueError(f"Missing development article: {language}/{article_id}")
                article = by_id[article_id]["content"].strip()
                raw_ids = tokenizer.encode(article, add_special_tokens=False)
                clipped_article = tokenizer.decode(raw_ids[:args.article_token_budget], skip_special_tokens=True)
                messages = [
                    {"role": "system", "content": "Write one news headline in the same language as the article. Output only the headline."},
                    {"role": "user", "content": clipped_article},
                ]
                model_inputs = tokenizer.apply_chat_template(
                    messages, tokenize=True, add_generation_prompt=True,
                    enable_thinking=False, return_tensors="pt", return_dict=True,
                ).to(model.device)
                torch.cuda.synchronize()
                start = time.perf_counter()
                with torch.inference_mode():
                    generated = model.generate(
                        **model_inputs,
                        max_new_tokens=args.max_new_tokens,
                        do_sample=False,
                        pad_token_id=tokenizer.eos_token_id,
                    )
                torch.cuda.synchronize()
                seconds = time.perf_counter() - start
                new_ids = generated[0, model_inputs["input_ids"].shape[1]:]
                prediction = tokenizer.decode(new_ids, skip_special_tokens=True).strip()
                record = {
                    "purpose": "pipeline smoke test only; not a performance measurement",
                    "dataset_revision": dev["revision"],
                    "model_id": MODEL_ID,
                    "model_revision": MODEL_REVISION,
                    "language": language,
                    "article_id": article_id,
                    "raw_article_tokens": len(raw_ids),
                    "article_token_budget": args.article_token_budget,
                    "clipped": len(raw_ids) > args.article_token_budget,
                    "actual_prompt_tokens": model_inputs["input_ids"].shape[1],
                    "generated_tokens": len(new_ids),
                    "max_new_tokens": args.max_new_tokens,
                    "seconds": round(seconds, 3),
                    "prediction": prediction,
                }
                output.write(json.dumps(record, ensure_ascii=False) + "\n")
                output.flush()
                print(json.dumps({k: v for k, v in record.items() if k != "prediction"}), flush=True)
    print(f"Saved predictions to {output_path}", flush=True)


if __name__ == "__main__":
    main()

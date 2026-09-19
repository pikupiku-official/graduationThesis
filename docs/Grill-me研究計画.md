# 卒業論文研究計画: Discovery Notes
Date: 2026-09-20
Goal: 卒業論文として成立する研究目的、実験範囲、判断基準、提出までの進め方を明確にする。

## Summary

現時点のテーマは、CMHGを用いて中国少数民族言語のニュース見出し生成を調べ、7Bから14B級の軽量LLMの性能上の制約を、内容理解・見出し生成・表記処理・tokenizer・翻訳媒介・追加学習の観点から切り分けること。

計画の核は、同じ本文について見出し生成と見出し選択を比較し、さらに可能なら翻訳媒介処理とQLoRAを追加すること。ただし、対象言語、主モデル、翻訳器、選択課題の負例設計、QLoRAの実施可否は未確定。

暫定的には、研究を成立させる最小構成を先に確保し、追加実験が失敗しても生成・選択比較で卒論を完成できる設計にする。

## Q&A log

### Session 2026-09-20

- User requested a Grill-me style process that asks the questions and advances the research plan, rather than requiring the user to invent the questions.
- User explicitly prefers receiving the necessary questions all at once as a list, rather than one question per turn.
- The project folder already contains a research plan DOCX and structured Markdown planning documents.
- The interview mode is treated as ongoing context because the research plan must remain usable across future sessions.

## Decisions

- Use this file as the durable discovery record for the research-plan interview.
- Present the initial discovery questions together as a numbered list.
- After the user answers, update this file, reconcile contradictions, and continue with a revised question list if needed.
- Record confirmed facts separately from assumptions and unresolved decisions.
- Keep the minimal viable thesis separate from optional experiments.

## Initial question list

Answer in one message using the same numbers. `未定` is acceptable. If the decision can be delegated, answer `任せる` and the plan will record a provisional choice with its reason.

1. 最終提出日はいつか。
2. 次に指導教員へ見せる期限、発表、中間提出などの予定はあるか。
3. 卒論として最低限成立すればよい成果は何か。実験結果、論文本文、発表資料などを含める。
4. 研究の主軸は、生成と選択の差、翻訳媒介、文字体系・tokenizer分析、QLoRAのどれに置きたいか。
5. 対象言語はどの2言語にしたいか。未定なら、こちらの推奨案に任せるか。
6. 対象モデルは既に使えるものがあるか。モデル名、サイズ、量子化、取得制限が分かれば書く。
7. 実行環境は何か。GPU名・VRAM、ローカルかクラウドか、使用可能時間を分かる範囲で書く。
8. CMHGの全データを扱う必要があるか。それとも小規模サンプルから始めてよいか。
9. 見出し選択課題は、4択程度の正解1件＋負例3件でよいか。別案があれば書く。
10. 負例はランダム負例と同言語・同ジャンルの難負例を分ける方針でよいか。
11. 翻訳媒介処理は必須か、余力があれば行う補助実験でよいか。翻訳先は中国語・英語のどちらを優先するか。
12. QLoRAは必須か、実行できた場合だけ追加する補助実験でよいか。
13. 対象言語を読める評価者や協力者はいるか。いなければ、どこまで人手評価を諦めてよいか。
14. 評価指標はROUGE-L、chrF、選択正解率、invalid出力率、token統計、エラー分類を基本セットとしてよいか。
15. 外部APIや有料GPUの利用は可能か。不可なら完全ローカル前提にする。
16. 研究上、絶対に避けたいことは何か。例：大規模学習、外国語の人手評価、外部API、複雑な実装。
17. 論文の文体・提出形式・引用形式について、大学や指導教員から指定はあるか。
18. 未回答の項目は、こちらが研究成立性を優先して仮決定してよいか。

## Open questions

- What is the official submission deadline and what intermediate deadlines exist?
- What result would count as a successful graduation thesis if QLoRA or translation-mediated processing cannot be completed?
- Which hardware and software environment is actually available?
- Which two languages and which primary model should be fixed?
- How will the selection task and hard negatives be constructed without leaking the answer?

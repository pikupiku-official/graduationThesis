# 卒業論文研究計画: Discovery Notes
Date: 2026-09-20
Goal: 卒業論文として成立する研究目的、実験範囲、判断基準、提出までの進め方を明確にする。

## Summary

現時点のテーマは、CMHGを用いて中国少数民族言語のニュース見出し生成を調べ、7Bから14B級の軽量LLMの性能上の制約を、内容理解・見出し生成・表記処理・tokenizer・翻訳媒介・追加学習の観点から切り分けること。

計画の核は、同じ本文について見出し生成と見出し選択を比較し、さらに可能なら翻訳媒介処理とQLoRAを追加すること。ただし、対象言語、主モデル、翻訳器、選択課題の負例設計、QLoRAの実施可否は未確定。

暫定的には、研究を成立させる最小構成を先に確保し、追加実験が失敗しても生成・選択比較で卒論を完成できる設計にする。

2026年9月20日の回答により、最終提出日は2026年12月31日、中間期限は現時点でなし、最優先条件は卒業可能な論文を完成させることと確認された。研究の中心成果は、比較結果を入力すると失敗要因の候補と残る不確実性を示す診断フローとする。モデル・言語・サンプル数・負例作成の詳細は研究成立性を優先してこちらで仮決定できる。外部APIと有料GPUはできるだけ使わず、ローカルのRTX 5060 Ti 16GBを起点にする。

## Q&A log

### Session 2026-09-20

- User requested a Grill-me style process that asks the questions and advances the research plan, rather than requiring the user to invent the questions.
- User explicitly prefers receiving the necessary questions all at once as a list, rather than one question per turn.
- The project folder already contains a research plan DOCX and structured Markdown planning documents.
- The interview mode is treated as ongoing context because the research plan must remain usable across future sessions.

### 回答 2026-09-20

| 番号 | 回答の記録 | 状態 |
| --- | --- | --- |
| 1 | 最終提出日：2026年12月31日 | 確認済み。大学の正式要項との照合は未実施 |
| 2 | 中間期限：なし | 本人回答 |
| 3 | 新規性のある学士論文で卒業したい。必要成果の具体的な評価基準は不明 | 目標は確認済み、基準は未確認 |
| 4 | 失敗原因を診断するフローチャートの形を想定 | 方向性は確認済み |
| 5 | 対象言語は未定、検証して決める | 未決定 |
| 6 | モデルは未定、変化が速いため現時点で固定したくない | 未決定 |
| 7 | PC環境は助手がdxdiagで確認する | 委任 |
| 8–10 | データ規模、4択、負例設計は助手に委任 | 委任 |
| 11–13 | 翻訳媒介とQLoRAは診断上重要そうだが、必須かどうかは助手に委任 | 研究上の依存関係を要確認 |
| 14 | 評価者はLLMを想定 | 本人回答。信頼性の検証は必要 |
| 15 | 提案した評価指標でよい | 暫定承認 |
| 16 | 外部API・有料GPUはあまり使いたくない | 制約 |
| 17 | 卒業できないことを避けたい | 最優先制約 |
| 18 | 厳密なAPA形式を希望 | 希望。大学指定の確認は未実施 |
| 19 | 未回答項目は助手が研究成立性を優先して仮決定してよい | 委任 |

環境確認：`dxdiag` でWindows 11 Home、Ryzen 7 5700X、RAM 32GB、RTX 5060 Ti、専用VRAM約16GBを確認。`nvidia-smi` ではGPU総量16,311MiB、確認時の空き10,772MiB。数値は実験時に再確認する。Windowsの`python`コマンドは現時点で利用できず、Python環境の準備が必要。

外部資料確認：CMHGの公式Hugging Faceデータセットビューアは、CSV間で列が一致しないため `DatasetGenerationCastError` を表示する。個別CSVの取得と列監査が必要。参照：https://huggingface.co/datasets/KEVVVV/CMHG

### 点検の目的に関する確認

ユーザーから「点検の目的は？」との確認があった。ここでの点検は研究結果を出すためではなく、CMHGの公開ファイルとローカル推論経路が比較可能な状態にあるかを確かめる準備作業である。全件に対する機械的なデータ監査と、各言語20件程度の動作確認を区別する。20件は性能評価にも対象言語の優劣判定にも使わない。この疑問は計画の説明不足として受け止め、プロトコルの記述を修正した。追加のユーザー判断は現時点で不要。

## Decisions

- Use this file as the durable discovery record for the research-plan interview.
- Present the initial discovery questions together as a numbered list.
- After the user answers, update this file, reconcile contradictions, and continue with a revised question list if needed.
- Record confirmed facts separately from assumptions and unresolved decisions.
- Keep the minimal viable thesis separate from optional experiments.
- 最終提出日を2026年12月31日として逆算する。正式な提出要項を入手したら照合する。
- 中核成果は「失敗要因候補を示す診断フローと、その各分岐を支える実験結果」とする。
- 外部APIと有料GPUを前提にしない。
- 人手による対象言語の内容評価は確保できていない。LLM判定は補助証拠として扱い、無検証の正解ラベルにしない。
- 形式はAPA第7版を仮採用し、大学指定があればそちらを優先する。

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

- 大学の正式な提出要項、字数、提出形式、指導教員の最低基準は未入手。
- 対象言語とモデルは、データ・tokenizer・推論の小規模監査後に固定する。
- 生成と選択の課題難度が異なるため、両者の差から「理解不足」と「生成不足」をどこまで言えるか、解釈規則を事前登録する。
- 翻訳媒介は言語処理の切り分けに有用だが、翻訳器の誤りが交絡する。実施範囲と対照条件を確定する。
- QLoRAは適応可能性を検証する介入であり、失敗原因の診断に必須かどうかを研究上の問いに合わせて決める。
- LLMによるエラー分類の妥当性をどう監査するか。

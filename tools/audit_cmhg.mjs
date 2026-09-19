import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';

const revision = process.argv[2];
if (!revision || !/^[0-9a-f]{40}$/.test(revision)) {
  console.error('Usage: node tools/audit_cmhg.mjs <40-character-dataset-revision>');
  process.exit(2);
}

const root = path.resolve('data', 'raw', 'cmhg', revision);
const expectedColumns = [
  'id', 'title', 'content', 'title_match_1', 'title_match_2',
  'tendency', 'average_score', 'score_difference',
];
const languages = ['bo', 'mn', 'ug'];
const categories = ['average_score_4_or_higher.csv', 'average_score_below_4.csv'];
const report = {
  dataset_id: 'KEVVVV/CMHG',
  revision,
  generated_at_utc: new Date().toISOString(),
  scope: 'Six annotated CSV files only; unannotated full CSV files not audited',
  files: [],
  language_summary: {},
  caveats: [],
};
const devIds = {
  dataset_id: 'KEVVVV/CMHG',
  revision,
  purpose: 'Pipeline smoke test only; exclude these IDs from final evaluation',
  selection_rule: '20 lowest SHA-256 hashes of cmhg-dev-v1|language|id from annotated high-score file',
  languages: {},
  exclude_title_content_sha256: {},
};

function parseCsv(input, callback) {
  let text = input.charCodeAt(0) === 0xfeff ? input.slice(1) : input;
  let field = '';
  let row = [];
  let quoted = false;
  let rowNumber = 0;
  for (let i = 0; i < text.length; i++) {
    const char = text[i];
    if (quoted) {
      if (char === '"') {
        if (text[i + 1] === '"') {
          field += '"';
          i++;
        } else {
          quoted = false;
        }
      } else {
        field += char;
      }
    } else if (char === '"' && field.length === 0) {
      quoted = true;
    } else if (char === ',') {
      row.push(field);
      field = '';
    } else if (char === '\n' || char === '\r') {
      if (char === '\r' && text[i + 1] === '\n') i++;
      row.push(field);
      field = '';
      rowNumber++;
      callback(row, rowNumber);
      row = [];
    } else {
      field += char;
    }
  }
  if (quoted) throw new Error('Unclosed CSV quote');
  if (field.length || row.length) {
    row.push(field);
    rowNumber++;
    callback(row, rowNumber);
  }
}

const hash = (value) => crypto.createHash('sha256').update(value).digest('hex');
for (const language of languages) {
  const seenIds = new Set();
  const seenPairs = new Set();
  const candidates = [];
  const summary = {
    annotated_rows: 0,
    high_score_rows: 0,
    low_score_rows: 0,
    duplicate_ids_within_language: 0,
    duplicate_title_content_pairs_within_language: 0,
    dev_ids_count: 0,
  };
  for (const category of categories) {
    const relative = `${language}/${category}`;
    const filePath = path.join(root, language, category);
    if (!fs.existsSync(filePath)) throw new Error(`Missing file: ${filePath}`);
    const bytes = fs.readFileSync(filePath);
    const file = {
      path: relative,
      bytes: bytes.length,
      sha256: hash(bytes),
      columns: [],
      rows: 0,
      row_width_errors: 0,
      missing_id: 0,
      missing_title: 0,
      missing_content: 0,
      average_score_outside_1_to_7: 0,
      average_score_minus_one: 0,
      wrong_score_category: 0,
      duplicate_ids_within_language: 0,
      duplicate_title_content_pairs_within_language: 0,
    };
    let columnIndex = null;
    parseCsv(bytes.toString('utf8'), (row) => {
      if (!columnIndex) {
        file.columns = row;
        columnIndex = Object.fromEntries(row.map((name, i) => [name, i]));
        const missing = expectedColumns.filter((name) => !(name in columnIndex));
        if (missing.length) throw new Error(`${relative}: missing columns ${missing.join(', ')}`);
        return;
      }
      file.rows++;
      if (row.length !== file.columns.length) {
        file.row_width_errors++;
        return;
      }
      const id = row[columnIndex.id].trim();
      const title = row[columnIndex.title].trim();
      const content = row[columnIndex.content].trim();
      const score = Number(row[columnIndex.average_score]);
      if (!id) file.missing_id++;
      if (!title) file.missing_title++;
      if (!content) file.missing_content++;
      if (!Number.isFinite(score) || score < 1 || score > 7) {
        file.average_score_outside_1_to_7++;
        if (score === -1) file.average_score_minus_one++;
      } else if ((category.includes('4_or_higher') && score < 4) ||
                 (category.includes('below_4') && score >= 4)) {
        file.wrong_score_category++;
      }
      if (id) {
        if (seenIds.has(id)) file.duplicate_ids_within_language++;
        seenIds.add(id);
      }
      if (title && content) {
        const pair = hash(`${title}\0${content}`);
        if (seenPairs.has(pair)) file.duplicate_title_content_pairs_within_language++;
        seenPairs.add(pair);
      }
      if (category.includes('4_or_higher') && id && title && content) {
        candidates.push({
          id,
          pair_hash: hash(`${title}\0${content}`),
          rank: hash(`cmhg-dev-v1|${language}|${id}`),
        });
      }
    });
    summary.annotated_rows += file.rows;
    if (category.includes('4_or_higher')) summary.high_score_rows = file.rows;
    else summary.low_score_rows = file.rows;
    summary.duplicate_ids_within_language += file.duplicate_ids_within_language;
    summary.duplicate_title_content_pairs_within_language +=
      file.duplicate_title_content_pairs_within_language;
    report.files.push(file);
  }
  candidates.sort((a, b) => a.rank.localeCompare(b.rank) || a.id.localeCompare(b.id));
  const selected = [];
  const selectedIds = new Set();
  const selectedPairs = new Set();
  for (const candidate of candidates) {
    if (selectedIds.has(candidate.id) || selectedPairs.has(candidate.pair_hash)) continue;
    selected.push(candidate);
    selectedIds.add(candidate.id);
    selectedPairs.add(candidate.pair_hash);
    if (selected.length === 20) break;
  }
  if (selected.length !== 20) throw new Error(`${language}: fewer than 20 unique development records`);
  devIds.languages[language] = selected.map(({id}) => id);
  devIds.exclude_title_content_sha256[language] = selected.map(({pair_hash}) => pair_hash);
  summary.dev_ids_count = devIds.languages[language].length;
  report.language_summary[language] = summary;
}

report.caveats.push('The 20 development IDs per language are for pipeline checks, not performance estimates.');
report.caveats.push('A future full-data audit must check evaluation/training overlap and near duplicates.');
fs.mkdirSync(path.resolve('results'), {recursive: true});
fs.mkdirSync(path.resolve('experiments'), {recursive: true});
fs.writeFileSync(path.resolve('results', 'cmhg_annotated_audit.json'), JSON.stringify(report, null, 2) + '\n');
fs.writeFileSync(path.resolve('experiments', 'cmhg_dev_ids.json'), JSON.stringify(devIds, null, 2) + '\n');
console.log(JSON.stringify(report.language_summary, null, 2));
console.log(`Wrote results/cmhg_annotated_audit.json and experiments/cmhg_dev_ids.json`);

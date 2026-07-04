# -*- coding: utf-8 -*-
"""Build a single-page HTML viewer for all PM exam question files.

Each Markdown file is split into:
  - header (H1 title + H2 subtitle)
  - 問題文 + 設問 (shown immediately)
  - 解答と解説 + 参考：主要キーワード (hidden behind a toggle button)

Output: index.html at repo root, referencing images/ as-is.
"""
import json
import re
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
MD_EXCLUDE_DIRS = {"images", "pdfs", "scripts"}

YEAR_ORDER = []
for year in range(2015, 2026):
    for season in ("春", "秋"):
        name = f"{year}{season}"
        if (ROOT / name).is_dir():
            YEAR_ORDER.append(name)

QNUM_RE = re.compile(r"_問(\d+)_")

def parse_file(path: Path):
    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")

    idx = {}
    for i, line in enumerate(lines):
        if line.strip() == "## 問題文":
            idx["mondai"] = i
        elif line.strip() == "## 設問":
            idx["setumon"] = i
        elif line.strip() == "## 解答と解説":
            idx["kaitou"] = i
        elif line.strip() == "## 参考：主要キーワード":
            idx["sanko"] = i

    h1 = lines[0].lstrip("# ").strip()
    h2 = lines[1].lstrip("# ").strip() if lines[1].startswith("##") else ""

    front_end = idx.get("kaitou", len(lines))
    front_lines = lines[idx["mondai"]:front_end]
    back_lines = lines[idx["kaitou"]:]

    # rewrite image paths: MD files live in year subfolders and reference ../images/
    def fix_images(block_lines):
        return [ln.replace("(../images/", "(images/") for ln in block_lines]

    front_md = "\n".join(fix_images(front_lines))
    back_md = "\n".join(fix_images(back_lines))

    front_html = markdown.markdown(front_md, extensions=["tables", "fenced_code", "sane_lists"])
    back_html = markdown.markdown(back_md, extensions=["tables", "fenced_code", "sane_lists"])

    m = QNUM_RE.search(path.name)
    qnum = int(m.group(1)) if m else 0

    return {
        "h1": h1,
        "h2": h2,
        "qnum": qnum,
        "front": front_html,
        "back": back_html,
    }


def main():
    data = {}
    for year_dir in YEAR_ORDER:
        d = ROOT / year_dir
        entries = []
        for f in sorted(d.glob("*.md")):
            entries.append(parse_file(f))
        entries.sort(key=lambda e: e["qnum"])
        data[year_dir] = entries

    data_json = json.dumps(data, ensure_ascii=False)

    html = HTML_TEMPLATE.replace("__DATA_JSON__", data_json)
    out_path = ROOT / "index.html"
    out_path.write_text(html, encoding="utf-8")
    print(f"Wrote {out_path} ({out_path.stat().st_size/1024:.1f} KB)")


HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>応用情報技術者試験 午後問題集</title>
<style>
  :root {
    --bg: #f5f6f8;
    --panel: #ffffff;
    --accent: #2563eb;
    --accent-dark: #1d4ed8;
    --text: #1f2430;
    --muted: #6b7280;
    --border: #e2e5ea;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    font-family: "Hiragino Kaku Gothic ProN", "Yu Gothic", "Segoe UI", sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.75;
  }
  header {
    background: var(--panel);
    border-bottom: 1px solid var(--border);
    padding: 14px 20px;
    position: sticky;
    top: 0;
    z-index: 10;
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    align-items: center;
  }
  header h1 {
    font-size: 18px;
    margin: 0 16px 0 0;
    white-space: nowrap;
  }
  select, button.nav-btn {
    font-size: 14px;
    padding: 6px 10px;
    border-radius: 6px;
    border: 1px solid var(--border);
    background: #fff;
  }
  button.nav-btn {
    cursor: pointer;
    background: var(--accent);
    color: #fff;
    border: none;
  }
  button.nav-btn:hover { background: var(--accent-dark); }
  button.nav-btn:disabled { background: #cbd2db; cursor: not-allowed; }
  button.nav-btn.secondary { background: #fff; color: var(--accent-dark); border: 1px solid var(--accent); }
  button.nav-btn.secondary:hover { background: #eef2ff; }

  main {
    max-width: 900px;
    margin: 24px auto;
    padding: 0 16px 80px;
  }

  #listView { display: none; }
  #listView.show { display: block; }
  #detailView.hide { display: none; }

  .year-block {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 18px 22px;
    margin-bottom: 16px;
  }
  .year-block h2 {
    font-size: 16px;
    margin: 0 0 12px;
    color: var(--accent-dark);
  }
  .q-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(230px, 1fr));
    gap: 8px;
  }
  .q-item {
    display: block;
    text-align: left;
    padding: 8px 12px;
    border: 1px solid var(--border);
    border-radius: 6px;
    background: #fafbfc;
    cursor: pointer;
    font-size: 13px;
    color: var(--text);
  }
  .q-item:hover { background: #eef2ff; border-color: var(--accent); }
  .q-item .qn { font-weight: bold; color: var(--accent-dark); margin-right: 4px; }
  .card {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 24px 28px;
  }
  .card h1 { font-size: 20px; margin-top: 0; }
  .card h2 { font-size: 17px; color: var(--accent-dark); }
  .card h3 { font-size: 15px; margin-top: 28px; }
  .card table {
    border-collapse: collapse;
    width: 100%;
    margin: 12px 0;
    font-size: 14px;
  }
  .card th, .card td {
    border: 1px solid var(--border);
    padding: 6px 10px;
    text-align: left;
    vertical-align: top;
  }
  .card th { background: #f0f2f5; }
  .card img { max-width: 100%; border: 1px solid var(--border); border-radius: 4px; margin: 8px 0; }
  .card blockquote {
    margin: 8px 0;
    padding: 8px 14px;
    background: #f7f8fa;
    border-left: 4px solid var(--accent);
    color: var(--muted);
    font-size: 13.5px;
  }
  .card code { background: #f0f2f5; padding: 1px 5px; border-radius: 4px; }
  .card pre { background: #1f2430; color: #e2e5ea; padding: 14px; border-radius: 8px; overflow-x: auto; }
  .card pre code { background: none; color: inherit; padding: 0; }

  #answerToggleWrap {
    text-align: center;
    margin: 32px 0 24px;
  }
  #answerToggle {
    font-size: 15px;
    padding: 12px 28px;
    border-radius: 999px;
    border: none;
    background: linear-gradient(135deg, #2563eb, #7c3aed);
    color: #fff;
    cursor: pointer;
    box-shadow: 0 4px 14px rgba(37, 99, 235, 0.35);
  }
  #answerToggle:hover { filter: brightness(1.05); }
  #answerBlock {
    display: none;
    border-top: 2px dashed var(--border);
    padding-top: 20px;
    margin-top: 8px;
  }
  #answerBlock.show { display: block; }
  #answerBlock h3 { color: var(--accent-dark); }
  #answerBlock strong { color: #b91c1c; }

  footer {
    text-align: center;
    color: var(--muted);
    font-size: 12px;
    padding: 20px;
  }

  @media (max-width: 600px) {
    header h1 { width: 100%; }
    .card { padding: 18px 16px; }
  }
</style>
</head>
<body>

<header>
  <h1>応用情報 午後問題集</h1>
  <select id="yearSelect"></select>
  <select id="qSelect"></select>
  <button class="nav-btn" id="prevBtn">← 前の問題</button>
  <button class="nav-btn" id="nextBtn">次の問題 →</button>
  <button class="nav-btn secondary" id="listBtn">一覧</button>
</header>

<main>
  <div id="listView">
    <div id="listContainer"></div>
  </div>

  <div id="detailView">
    <div class="card" id="card">
      <div id="front"></div>
      <div id="answerToggleWrap">
        <button id="answerToggle">解答・解説を表示する</button>
      </div>
      <div id="answerBlock"></div>
    </div>
  </div>
</main>

<footer>応用情報技術者試験 午後問題 学習用ビューア（自作解説）</footer>

<script>
const DATA = __DATA_JSON__;
const years = Object.keys(DATA);

const yearSelect = document.getElementById('yearSelect');
const qSelect = document.getElementById('qSelect');
const frontEl = document.getElementById('front');
const answerToggle = document.getElementById('answerToggle');
const answerBlock = document.getElementById('answerBlock');
const prevBtn = document.getElementById('prevBtn');
const nextBtn = document.getElementById('nextBtn');
const listBtn = document.getElementById('listBtn');
const listView = document.getElementById('listView');
const detailView = document.getElementById('detailView');
const listContainer = document.getElementById('listContainer');

let curYearIdx = 0;
let curQIdx = 0;
let inListView = false;

function buildListView() {
  listContainer.innerHTML = '';
  years.forEach((y, yi) => {
    const block = document.createElement('div');
    block.className = 'year-block';
    const h2 = document.createElement('h2');
    h2.textContent = y + '期';
    block.appendChild(h2);

    const grid = document.createElement('div');
    grid.className = 'q-grid';
    DATA[y].forEach((e, qi) => {
      const item = document.createElement('div');
      item.className = 'q-item';
      item.innerHTML = '<span class="qn">問' + e.qnum + '</span>' + e.h2.split('：')[0];
      item.addEventListener('click', () => {
        curYearIdx = yi;
        curQIdx = qi;
        populateQSelect();
        showDetail();
        render();
      });
      grid.appendChild(item);
    });
    block.appendChild(grid);
    listContainer.appendChild(block);
  });
}

function showList() {
  inListView = true;
  listView.classList.add('show');
  detailView.classList.add('hide');
  listBtn.textContent = '問題に戻る';
  window.scrollTo({top: 0, behavior: 'instant'});
}

function showDetail() {
  inListView = false;
  listView.classList.remove('show');
  detailView.classList.remove('hide');
  listBtn.textContent = '一覧';
}

listBtn.addEventListener('click', () => {
  if (inListView) {
    showDetail();
  } else {
    showList();
  }
});

function populateYearSelect() {
  years.forEach((y, i) => {
    const opt = document.createElement('option');
    opt.value = i;
    opt.textContent = y + '期';
    yearSelect.appendChild(opt);
  });
}

function populateQSelect() {
  qSelect.innerHTML = '';
  const entries = DATA[years[curYearIdx]];
  entries.forEach((e, i) => {
    const opt = document.createElement('option');
    opt.value = i;
    opt.textContent = '問' + e.qnum + '　' + e.h2.split('：')[0];
    qSelect.appendChild(opt);
  });
}

function render() {
  const entries = DATA[years[curYearIdx]];
  const e = entries[curQIdx];
  frontEl.innerHTML = e.front;
  answerBlock.innerHTML = e.back;
  answerBlock.classList.remove('show');
  answerToggle.textContent = '解答・解説を表示する';
  yearSelect.value = curYearIdx;
  qSelect.value = curQIdx;
  window.scrollTo({top: 0, behavior: 'instant'});
  updateNavButtons();
}

function updateNavButtons() {
  prevBtn.disabled = (curYearIdx === 0 && curQIdx === 0);
  const lastY = years.length - 1;
  const lastQ = DATA[years[lastY]].length - 1;
  nextBtn.disabled = (curYearIdx === lastY && curQIdx === lastQ);
}

yearSelect.addEventListener('change', () => {
  curYearIdx = parseInt(yearSelect.value, 10);
  curQIdx = 0;
  populateQSelect();
  render();
});

qSelect.addEventListener('change', () => {
  curQIdx = parseInt(qSelect.value, 10);
  render();
});

answerToggle.addEventListener('click', () => {
  const showing = answerBlock.classList.toggle('show');
  answerToggle.textContent = showing ? '解答・解説を隠す' : '解答・解説を表示する';
});

prevBtn.addEventListener('click', () => {
  const entries = DATA[years[curYearIdx]];
  if (curQIdx > 0) {
    curQIdx -= 1;
  } else if (curYearIdx > 0) {
    curYearIdx -= 1;
    populateQSelect();
    curQIdx = DATA[years[curYearIdx]].length - 1;
  }
  render();
});

nextBtn.addEventListener('click', () => {
  const entries = DATA[years[curYearIdx]];
  if (curQIdx < entries.length - 1) {
    curQIdx += 1;
  } else if (curYearIdx < years.length - 1) {
    curYearIdx += 1;
    populateQSelect();
    curQIdx = 0;
  }
  render();
});

populateYearSelect();
populateQSelect();
buildListView();
render();
</script>

</body>
</html>
"""

if __name__ == "__main__":
    main()

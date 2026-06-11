import html


REPORT_CSS = """
:root {
  color-scheme: light;
  --bg: #f8fafc;
  --paper: #ffffff;
  --ink: #1e293b;
  --muted: #64748b;
  --line: #dbe3ef;
  --brand: #2563eb;
  --brand-soft: #eff6ff;
  --accent: #f97316;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  background: var(--bg);
  color: var(--ink);
  font-family: "Segoe UI", "Microsoft YaHei", Arial, sans-serif;
  line-height: 1.7;
}
.report-page {
  width: min(1040px, calc(100% - 40px));
  margin: 32px auto;
}
.report-hero {
  padding: 32px;
  border-radius: 16px;
  background: linear-gradient(135deg, #173b77, #2563eb);
  color: #fff;
  box-shadow: 0 18px 40px rgba(37, 99, 235, 0.18);
}
.eyebrow {
  margin: 0 0 8px;
  color: #bfdbfe;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0;
  text-transform: uppercase;
}
h1 {
  margin: 0;
  font-size: 34px;
  line-height: 1.25;
}
.hero-subtitle {
  max-width: 680px;
  margin: 12px 0 0;
  color: #dbeafe;
}
.report-section {
  margin-top: 18px;
  padding: 24px;
  border: 1px solid var(--line);
  border-radius: 14px;
  background: var(--paper);
  box-shadow: 0 10px 28px rgba(15, 23, 42, 0.06);
}
.report-section h2 {
  margin: 0 0 14px;
  padding-left: 12px;
  border-left: 4px solid var(--brand);
  color: #0f172a;
  font-size: 20px;
  line-height: 1.35;
}
.report-section p {
  margin: 8px 0;
  color: #334155;
}
.report-list {
  display: grid;
  gap: 10px;
  margin: 0;
  padding: 0;
  list-style: none;
}
.report-list li {
  padding: 12px 14px;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  background: #f8fafc;
}
.report-list li::before {
  content: "";
  display: inline-block;
  width: 7px;
  height: 7px;
  margin-right: 8px;
  border-radius: 50%;
  background: var(--accent);
  vertical-align: 2px;
}
.list-note {
  margin: -4px 0 10px 16px;
  padding: 10px 12px;
  border-left: 3px solid #93c5fd;
  background: var(--brand-soft);
  color: #334155;
}
@media print {
  body { background: #fff; }
  .report-page { width: 100%; margin: 0; }
  .report-hero, .report-section { box-shadow: none; border-radius: 0; }
  .report-section { break-inside: avoid; }
}
""".strip()


def render_report_html(markdown):
    title, sections = _parse_markdown(markdown)
    html_sections = ''.join(_render_section(section) for section in sections)
    return (
        '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f'<title>{html.escape(title)}</title><style>{REPORT_CSS}</style></head>'
        f'<body><main class="report-page">{_render_hero(title)}{html_sections}</main></body></html>'
    )


def _parse_markdown(markdown):
    title = '游客感受度报告'
    sections = []
    current = None
    for raw_line in markdown.splitlines():
        line = raw_line.rstrip()
        if not line:
            continue
        if line.startswith('# '):
            title = line[2:].strip()
        elif line.startswith('## '):
            current = {'heading': line[3:].strip(), 'items': []}
            sections.append(current)
        elif current is not None:
            current['items'].append(line)
    return title, sections


def _render_hero(title):
    return (
        '<header class="report-hero">'
        '<p class="eyebrow">Visitor Experience Report</p>'
        f'<h1>{html.escape(title)}</h1>'
        '<p class="hero-subtitle">基于游客交互记录生成，便于管理方快速查看关注点、情感风险、原始依据与服务改进建议。</p>'
        '</header>'
    )


def _render_section(section):
    content = _render_items(section['items'])
    return (
        '<section class="report-section">'
        f'<h2>{html.escape(section["heading"])}</h2>'
        f'{content}</section>'
    )


def _render_items(items):
    blocks = []
    list_open = False
    for item in items:
        stripped = item.strip()
        if stripped.startswith('- '):
            list_open = _open_list(blocks, list_open)
            blocks.append(f'<li>{html.escape(stripped[2:])}</li>')
        else:
            list_open = _close_list(blocks, list_open)
            class_name = ' class="list-note"' if item.startswith('  ') else ''
            blocks.append(f'<p{class_name}>{html.escape(stripped)}</p>')
    _close_list(blocks, list_open)
    return ''.join(blocks)


def _open_list(blocks, list_open):
    if not list_open:
        blocks.append('<ul class="report-list">')
    return True


def _close_list(blocks, list_open):
    if list_open:
        blocks.append('</ul>')
    return False

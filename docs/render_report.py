"""Build a dependency-free printable HTML version of the CCA report."""

import html
from pathlib import Path
import re


def inline(text: str) -> str:
    """Escape source text before applying the small supported Markdown subset."""
    text = html.escape(text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    return re.sub(r'`([^`]+)`', r'<code>\1</code>', text)


def render(source: str) -> str:
    """Render paragraphs, headings, fenced code and tables without dependencies."""
    lines = source.strip().splitlines()
    output: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        if not line.strip():
            index += 1
            continue
        if line.startswith('```'):
            block = []
            index += 1
            while index < len(lines) and not lines[index].startswith('```'):
                block.append(lines[index])
                index += 1
            output.append('<pre>' + html.escape('\n'.join(block)) + '</pre>')
        elif line.startswith('|'):
            rows = []
            while index < len(lines) and lines[index].startswith('|'):
                cells = [cell.strip() for cell in lines[index].strip('|').split('|')]
                if not all(re.fullmatch(r'[-: ]+', cell) for cell in cells):
                    rows.append(cells)
                index += 1
            output.append('<table><thead><tr>' + ''.join('<th>' + inline(c) + '</th>' for c in rows[0]) + '</tr></thead><tbody>')
            output.extend('<tr>' + ''.join('<td>' + inline(c) + '</td>' for c in row) + '</tr>' for row in rows[1:])
            output.append('</tbody></table>')
            continue
        elif line.startswith('#'):
            level = len(line) - len(line.lstrip('#'))
            output.append(f'<h{level}>' + inline(line[level:].strip()) + f'</h{level}>')
        else:
            paragraph = [line]
            while index + 1 < len(lines) and lines[index + 1].strip() and not lines[index + 1].startswith(('#', '|', '```')):
                index += 1
                paragraph.append(lines[index])
            output.append('<p>' + inline(' '.join(paragraph)) + '</p>')
        index += 1
    return '\n'.join(output)


def main() -> None:
    root = Path(__file__).resolve().parent
    pages = (root / 'CCA-REPORT-ROMAN-URDU.md').read_text(encoding='utf-8').split('<!-- pagebreak -->')
    style = '''
    *{box-sizing:border-box}body{margin:0;background:#e8ecf0;color:#18232f;font-family:Arial,sans-serif;font-size:14.67px;line-height:1.28}
    .toolbar{max-width:816px;margin:18px auto;padding:10px;background:white}button{padding:8px 16px;font:inherit;cursor:pointer}
    .page{width:816px;min-height:1056px;padding:34px 44px 42px;margin:20px auto;background:white;position:relative}
    header{font-size:10px;letter-spacing:1px;color:#526171;margin-bottom:12px}h1{font-size:25px;line-height:1.12;margin:0 0 12px;color:#000}
    h2{font-size:19px;line-height:1.2;margin:0 0 12px;color:#000}h3{font-size:14.67px;margin:12px 0 5px;color:#000}
    p{margin:0 0 8px}table{border-collapse:collapse;width:100%;font-size:12px;margin:8px 0 10px;break-inside:avoid}
    td,th{border:1px solid #d9d9d9;padding:6px 9px;vertical-align:middle;text-align:left}th{background:#173957;color:white}
    tbody tr:nth-child(even){background:#f3f6f8}pre{font:11px/1.35 Consolas,monospace;white-space:pre-wrap;overflow-wrap:anywhere;margin:10px 0 13px}
    code{font-family:Consolas,monospace;font-size:.94em}footer{position:absolute;bottom:22px;left:48px;right:48px;font-size:10px;color:#526171;display:flex;justify-content:space-between}
    @page{size:Letter;margin:0}@media print{body{background:white}.toolbar{display:none}.page{margin:0;break-after:page}.page:last-child{break-after:auto}}
    '''
    body = ''.join(f'<section class="page" id="page-{i}"><header>PARKPILOT · MACHINE LEARNING LAB · CCA</header>{render(page)}<footer><span>Roman Urdu project report · 18 November 2026</span><span>{i} / {len(pages)}</span></footer></section>' for i, page in enumerate(pages, 1))
    script = '''
    const selected=new URLSearchParams(location.search).get('page');
    if(selected){document.querySelector('.toolbar').style.display='none';document.querySelectorAll('.page').forEach((p,i)=>{if(String(i+1)!==selected)p.style.display='none';else p.style.margin='0';});}
    document.body.dataset.pageHeights=Array.from(document.querySelectorAll('.page')).map(p=>p.offsetHeight).join(',');
    '''
    target = root / 'CCA-REPORT-ROMAN-URDU.html'
    target.write_text('<!doctype html><html lang="ur-Latn"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>ParkPilot CCA Report</title><style>' + style + '</style><body><div class="toolbar"><button onclick="window.print()">Print or save as PDF</button> Team details source Markdown mein fill karke render_report.py dobara run karein.</div>' + body + '<script>' + script + '</script></body></html>', encoding='utf-8')
    print(target)


if __name__ == '__main__':
    main()

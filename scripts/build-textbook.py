#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把一本教材 Markdown 清洗成可检索的知识库。

用法：
    python scripts/build-textbook.py <教材.md> <书名> [--out 目录]

例：
    python scripts/build-textbook.py 必修第一册.md 必修第一册
    python scripts/build-textbook.py 教材.md 选择性必修1-化学反应原理

生成（默认写到 references/知识库/教材原文/）：
    <书名>.md        清洗后的全文，去掉图片外链，行号与原文一致
    <书名>-索引.md    章 / 节 / 小节 → 行号

说明：
  - 只做行内替换，不增删行，因此索引里的行号与清洗后的文件严格对齐。
  - 教材全文受版权保护，请勿提交到公开仓库（.gitignore 已排除该目录）。
"""

import argparse
import io
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_OUT = os.path.join(HERE, '..', 'references', '知识库', '教材原文')


def clean(raw: str) -> str:
    """把超长的图片外链换成短标记，行数不变。"""
    url_re = re.compile(r'!\[([^\]]*)\]\(([^)]*)\)')
    out = []
    for line in raw.split('\n'):
        m = url_re.search(line)
        if m:
            alt = m.group(1)
            short = alt if len(alt) <= 40 else alt[:40] + '…'
            line = f'![{short}]（图，外链已移除）'
        out.append(line)
    return '\n'.join(out)


def headings(lines):
    hs = []
    for i, line in enumerate(lines, 1):
        m = re.match(r'^(#{1,3})\s*(.+?)\s*$', line)
        if m:
            hs.append([i, len(m.group(1)), m.group(2), ''])
    # 章节标题常被排版断成两行：标题行只有「第X章」，名字在下一行
    for idx, h in enumerate(hs):
        if re.fullmatch(r'第[一二三四五六七八九十]+[章节]', h[2]) and idx + 1 < len(hs):
            h[3] = hs[idx + 1][2]
    return hs


def name(h):
    base = h[2]
    if h[3] and re.fullmatch(r'第[一二三四五六七八九十]+[章节]', base):
        join = '' if base.endswith(('的', '与', '和', '及')) else ' '
        return base + join + h[3]
    return base


def build(src, book, outdir):
    raw = open(src, encoding='utf-8-sig').read()
    lines = raw.split('\n')
    text = clean(raw)
    os.makedirs(outdir, exist_ok=True)
    open(os.path.join(outdir, book + '.md'), 'w', encoding='utf-8', newline='\n').write(text)

    hs = headings(lines)
    marks = []
    for h in hs:
        t = h[2]
        if re.match(r'第[一二三四五六七八九十]+章', t):
            marks.append(['chapter', h[0], name(h)])
        elif re.match(r'第[一二三四五六七八九十]+节', t):
            marks.append(['section', h[0], name(h)])
        elif t in ('整理与提升', '复习与提高', '目录'):
            marks.append(['section', h[0], t])
    for i, m in enumerate(marks):
        m.append(marks[i + 1][1] - 1 if i + 1 < len(marks) else len(lines))

    o = io.StringIO()
    o.write(f'# 教材索引（{book}）\n\n')
    o.write('用法：先在表中定位行号，再用 read 工具带 `offset`/`limit` 读对应区间，不要整本读入。\n')
    o.write(f'原文：`教材原文/{book}.md`（行号与本表一致）。\n\n')
    o.write('| 章 | 节 | 起始行 | 结束行 | 行数 |\n|---|---|---|---|---|\n')
    cur = ''
    for kind, ln, nm, end in marks:
        if kind == 'chapter':
            cur = nm
            o.write(f'| **{nm}** | — | {ln} | {end} | {end - ln + 1} |\n')
        else:
            o.write(f'| {cur} | {nm} | {ln} | {end} | {end - ln + 1} |\n')

    o.write('\n## 细目（章 → 节 → 小节）\n')
    for h in hs:
        ln, lvl, t, extra = h
        if re.match(r'第[一二三四五六七八九十]+章', t):
            o.write(f'\n### 行 {ln}　{name(h)}\n\n')
            continue
        if re.match(r'第[一二三四五六七八九十]+节', t):
            o.write(f'\n- **行 {ln}　{name(h)}**\n')
            continue
        if lvl == 2 and t != '目录':
            o.write(f'  - 行 {ln}　{t}\n')

    idx_path = os.path.join(outdir, book + '-索引.md')
    open(idx_path, 'w', encoding='utf-8', newline='\n').write(o.getvalue())

    print(f'原文：{os.path.join(outdir, book + ".md")}（{len(lines)} 行）')
    print(f'索引：{idx_path}（章 {sum(1 for m in marks if m[0] == "chapter")}，节 {sum(1 for m in marks if m[0] == "section")}）')
    print('提示：教材原文受版权保护，不要提交到公开仓库。')


def main():
    ap = argparse.ArgumentParser(description='把教材 Markdown 转成可检索的知识库')
    ap.add_argument('src', help='教材 Markdown 路径')
    ap.add_argument('book', help='书名，用作文件名，如 必修第一册')
    ap.add_argument('--out', default=DEFAULT_OUT, help='输出目录')
    args = ap.parse_args()
    if not os.path.isfile(args.src):
        raise SystemExit(f'找不到文件：{args.src}')
    build(args.src, args.book, args.out)


if __name__ == '__main__':
    main()

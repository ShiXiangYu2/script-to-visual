#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 rewrite_map.json 的改写结果落盘为新 docx（纯标准库）

原理：复制原 docx 的 zip 条目，仅替换 word/document.xml 中目标 <w:p> 段落内
      <w:t> 的文字，其余 XML 字节完全不动 -> 样式/页码/字体/图片/对白 100% 保留。
      输出必须是新文件路径，绝不覆盖原件。

用法:
    python3 apply_rewrite.py "剧本.docx" "rewrite_map.json" "输出_画面化稿.docx"
"""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parse_docx import PARA_RE, TEXT_RE, read_document_xml, iter_paragraph_blocks, classify  # noqa: E402

T_OPEN_RE = re.compile(r"<w:t(?:\s[^>]*)?>")
XML_DECL = b'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'


def _escape(text: str) -> str:
    # 只转义 XML 必需的三个字符，避免二次转义
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def rewrite_paragraph_block(block: str, new_text: str) -> str:
    """把段落内第一个 <w:t> 换成 new_text，其余 <w:t> 置空（保留 run/格式）"""
    matches = list(TEXT_RE.finditer(block))
    if not matches:
        return block
    out, last = [], 0
    escaped = _escape(new_text)
    for i, m in enumerate(matches):
        out.append(block[last:m.start(1)])
        out.append(escaped if i == 0 else "")
        last = m.end(1)
    out.append(block[last:])
    result = "".join(out)
    # 若新文本首尾有空格，确保第一个 w:t 带 xml:space="preserve"
    if new_text != new_text.strip():
        def fix(m):
            tag = m.group(0)
            return tag if "xml:space" in tag else tag[:-1] + ' xml:space="preserve">'
        result = T_OPEN_RE.sub(fix, result, count=1)
    return result


def apply(src: str, map_path: str, dst: str) -> dict:
    if os.path.abspath(src) == os.path.abspath(dst):
        raise RuntimeError("输出路径与原件相同，拒绝覆盖原件。请换一个新文件名。")
    with open(map_path, "r", encoding="utf-8") as f:
        rewrite_map = json.load(f)
    rewrite_map = {int(k): str(v) for k, v in rewrite_map.items()
                   if not str(k).startswith("_")}   # 跳过说明性元数据字段

    xml_text = read_document_xml(src)
    blocks = list(iter_paragraph_blocks(xml_text))

    # 安全校验：映射的 key 必须都是 action 类型段落
    bad = []
    for idx in rewrite_map:
        if idx >= len(blocks) or classify(blocks[idx][4]) != "action":
            bad.append(idx)
    if bad:
        raise RuntimeError(f"rewrite_map 含非 △ 行段落 index，拒绝写入: {bad}")

    # 从后往前替换，避免偏移影响
    parts, last = [], 0
    replaced = 0
    edits = sorted(rewrite_map.items(), key=lambda kv: kv[0])
    cursor = 0
    for idx, new_text in edits:
        _i, start, end, block, old_text = blocks[idx]
        parts.append(xml_text[cursor:start])
        parts.append(rewrite_paragraph_block(block, new_text))
        cursor = end
        replaced += 1
    parts.append(xml_text[cursor:])
    new_xml = "".join(parts)

    os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
    with zipfile.ZipFile(src) as zin, zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "word/document.xml":
                data = new_xml.encode("utf-8")
            zout.writestr(item, data)

    return {"output": os.path.abspath(dst), "replaced": replaced}


def main() -> int:
    ap = argparse.ArgumentParser(description="落盘改写结果为新 docx（不覆盖原件）")
    ap.add_argument("docx", help="原始剧本 docx")
    ap.add_argument("map", help="rewrite_map.json")
    ap.add_argument("output", help="输出的新 docx 路径")
    args = ap.parse_args()

    for p in (args.docx, args.map):
        if not os.path.isfile(p):
            print(f"[ERROR] 文件不存在: {p}", file=sys.stderr)
            return 2
    try:
        r = apply(args.docx, args.map, args.output)
    except Exception as e:
        print(f"[FAIL] {e}", file=sys.stderr)
        return 1
    print(f"[OK] 已生成 {r['output']}")
    print(f"  改写 △ 行: {r['replaced']} 条 | 其余内容字节级保持不变")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

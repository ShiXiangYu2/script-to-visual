#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""解析中文剧本 docx -> 结构化 JSON（纯标准库，无第三方依赖）

用法:
    python3 parse_docx.py "剧本.docx" -o "parsed.json"
    python3 parse_docx.py "剧本.docx" --scene 21        # 只看第 21 场

输出 JSON:
{
  "source": "绝对路径",
  "stats": {"total_paragraphs":N, "scenes":N, "actions":N, "dialogues":N, "os":N},
  "paragraphs": [
    {"index":0, "type":"scene|action|dialogue|os|other", "scene_id":"第二十一场", "text":"..."}
  ]
}

说明: index 是 <w:p> 段落在 word/document.xml 中的 0-based 顺序号，
      apply_rewrite.py 用同一套提取逻辑，保证 index 严格对齐。
"""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import zipfile

PARA_RE = re.compile(r"<w:p(?:\s[^>]*)?>.*?</w:p>", re.S)
TEXT_RE = re.compile(r"<w:t(?:\s[^>]*)?>(.*?)</w:t>", re.S)
SCENE_RE = re.compile(r"第\s*[一二三四五六七八九十百千零〇两\d]+\s*场")
OS_RE = re.compile(r"(?i)\b(os|vo|画外音|旁白)\b|(?:os|OS)\s*[:：]")


def read_document_xml(docx_path: str) -> str:
    with zipfile.ZipFile(docx_path) as zf:
        name = "word/document.xml"
        if name not in zf.namelist():
            raise RuntimeError(f"不是有效的 docx（缺少 {name}）: {docx_path}")
        return zf.read(name).decode("utf-8")


def plain_text(block: str) -> str:
    """拼出段落纯文本（含 xml 反转义）"""
    parts = TEXT_RE.findall(block)
    return html.unescape("".join(parts)).strip()


def iter_paragraph_blocks(xml_text: str):
    """产出 (index, start, end, block, text)"""
    for i, m in enumerate(PARA_RE.finditer(xml_text)):
        block = m.group(0)
        yield i, m.start(), m.end(), block, plain_text(block)


def classify(text: str) -> str:
    if not text:
        return "other"
    s = text.strip()
    # 场次标题：以「第X场」开头（脚本里通常是 Heading，但也可能只是普通段落）
    if SCENE_RE.search(s[:20]) and (s.startswith("第") or "场" in s[:12]):
        return "scene"
    # △ 动作/舞台指示行
    if s.startswith("△") or s.startswith("▲") or s.startswith("△ "):
        return "action"
    # os / 内心独白
    if OS_RE.search(s[:20]):
        return "os"
    # 对白：角色名 + 冒号
    m = re.match(r"^([^\s：:]{1,12})\s*[:：]", s)
    if m:
        return "dialogue"
    return "other"


def build(docx_path: str) -> dict:
    xml_text = read_document_xml(docx_path)
    paragraphs = []
    current_scene = ""
    for idx, _start, _end, _block, text in iter_paragraph_blocks(xml_text):
        typ = classify(text)
        if typ == "scene":
            m = SCENE_RE.search(text)
            current_scene = m.group(0) if m else text[:20]
        paragraphs.append({
            "index": idx,
            "type": typ,
            "scene_id": current_scene if typ != "scene" else current_scene,
            "text": text,
        })
    stats = {
        "total_paragraphs": len(paragraphs),
        "scenes": sum(1 for p in paragraphs if p["type"] == "scene"),
        "actions": sum(1 for p in paragraphs if p["type"] == "action"),
        "dialogues": sum(1 for p in paragraphs if p["type"] == "dialogue"),
        "os": sum(1 for p in paragraphs if p["type"] == "os"),
        "other": sum(1 for p in paragraphs if p["type"] == "other"),
    }
    return {
        "source": os.path.abspath(docx_path),
        "stats": stats,
        "paragraphs": paragraphs,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="解析中文剧本 docx 为结构化 JSON")
    ap.add_argument("docx", help="剧本 docx 路径")
    ap.add_argument("-o", "--output", help="输出 JSON 路径（默认打印到 stdout）")
    ap.add_argument("--scene", help="只显示指定场次（如 21 或 第二十一场）")
    args = ap.parse_args()

    if not os.path.isfile(args.docx):
        print(f"[ERROR] 文件不存在: {args.docx}", file=sys.stderr)
        return 2

    data = build(args.docx)
    if args.scene:
        key = args.scene.replace("第", "").replace("场", "")
        wanted = args.scene if "场" in args.scene else None
        sel = [p for p in data["paragraphs"]
               if p["scene_id"] == wanted or key in p["scene_id"] or p["scene_id"].endswith(key)]
        # 场次标题自身的 scene_id 是上一场，补上标题行
        data["paragraphs"] = sel
        print(f"# 场次筛选: {args.scene} -> {len(sel)} 段", file=sys.stderr)

    payload = json.dumps(data, ensure_ascii=False, indent=2)
    if args.output:
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(payload)
        print(f"[OK] 已写出 {args.output}")
        s = data["stats"]
        print(f"  场次 {s['scenes']} | △动作行 {s['actions']} | 对白 {s['dialogues']} | os {s['os']} | 其他 {s['other']} | 总段落 {s['total_paragraphs']}")
    else:
        print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按场次切分为可并行改写的分片（纯标准库）

用法:
    python3 split_scenes.py "parsed.json" -o "分片目录" --per-shard 8

产出:
    shards/shard_01.md ...      带完整场次上下文 + △行 index 标注 + A/B 级初筛
    shards/shard_01.index.json  该片 △ 行 index 清单
    shards/manifest.json        分片总览
"""
from __future__ import annotations

import argparse
import json
import os
import re

# 感官/物理细节词：命中即倾向已有画面感
DETAIL_WORDS = [
    "光", "水", "汗", "灰", "尘", "风", "雨", "雪", "烟", "声", "响", "滴", "溅", "淌",
    "红", "白", "黑", "青", "亮", "暗", "凉", "热", "湿", "干", "皱", "颤", "抖", "印",
    "痕", "缝", "沿", "角", "尖", "边", "纹", "影", "气", "雾", "霜", "泥", "土", "屑",
]
# 具体动作动词：≥2 个通常说明已有动作链
ACTION_VERBS = [
    "抬", "低", "转", "侧", "伸", "收", "攥", "抠", "扒", "摁", "推", "拉", "拎", "提",
    "放", "搁", "递", "接", "端", "捧", "掀", "揭", "翻", "抹", "擦", "刷", "洗", "扫",
    "蹲", "站", "坐", "靠", "倚", "走", "停", "退", "挪", "凑", "探", "弯", "直", "仰",
    "看", "盯", "望", "瞥", "扫", "盯", "咽", "抿", "咬", "喘", "哼", "笑", "皱", "点",
    "摇", "摆", "顿", "僵", "撑", "扶", "掖", "裹", "拢", "拨", "捻", "捏", "抠",
]
# 抽象静场 / 纯结果信号：倾向需改写
ABSTRACT_SIGNALS = [
    "静了一会儿", "安静", "沉默", "没说话", "没接话", "没动", "点了点头", "点点头",
    "摇了摇头", "摇摇头", "愣了一下", "怔", "看了他一眼", "看了一眼", "抬头", "抬起头",
    "回过神", "松了口气", "气氛", "心里", "意识到", "觉得", "感到",
]


def grade(text: str) -> tuple[str, str]:
    """返回 (级别 A/B, 理由)"""
    body = text.lstrip("△▲ ").strip()
    n = len(body)
    detail_hits = sum(1 for w in DETAIL_WORDS if w in body)
    verb_hits = sum(1 for w in ACTION_VERBS if w in body)
    if any(s in body for s in ABSTRACT_SIGNALS) and detail_hits <= 1:
        return "B", "抽象静场/单动作"
    if n >= 30 and (detail_hits >= 2 or verb_hits >= 3):
        return "A", "已含细节/动作链"
    if detail_hits >= 2 and verb_hits >= 2:
        return "A", "已含细节/动作链"
    if n < 20 and detail_hits == 0:
        return "B", "纯功能性短句"
    if verb_hits <= 1 and detail_hits <= 1:
        return "B", "单动作无细节"
    return "A", "已有画面基础"


def build_shards(parsed: dict, scenes_per_shard: int, out_dir: str) -> dict:
    paragraphs = parsed["paragraphs"]
    # 按 scene 标题切场
    scenes, cur = [], None
    for p in paragraphs:
        if p["type"] == "scene":
            cur = {"title": p["text"], "start": p["index"], "items": [p]}
            scenes.append(cur)
        elif cur is not None:
            cur["items"].append(p)
        else:
            # 场次标题前的段落，单独归入「前置」
            cur = {"title": "（前置）", "start": p["index"], "items": [p]}
            scenes.append(cur)

    shards = []
    for i in range(0, len(scenes), scenes_per_shard):
        group = scenes[i:i + scenes_per_shard]
        sid = len(shards) + 1
        lines = [
            f"# 改写分片 {sid:02d}",
            "",
            f"本片含 **{len(group)} 场**。请逐条改写下面标 `[B]` 的 △ 行；标 `[A]` 的 △ 行"
            "**保持原文不改**（除非明显有不可演词，才轻修）。",
            "",
            "> 对白行、`os` 行、场次标题**一律不改**，它们只是给你理解剧情的上下文。",
            "> 每条改写必须保留 `△ ` 前缀，30–70 字，只写镜头拍得到的物理事实。",
            "",
            "---",
            "",
        ]
        idx_list, grade_count = [], {"A": 0, "B": 0}
        for sc in group:
            lines.append(f"## {sc['title']}")
            lines.append("")
            for p in sc["items"]:
                t = p["text"]
                if not t:
                    continue
                if p["type"] == "action":
                    g, why = grade(t)
                    grade_count[g] += 1
                    idx_list.append({"index": p["index"], "grade": g, "original": t})
                    lines.append(f"- `{p['index']}` `[{g}]` {t}   <!-- {why} -->")
                elif p["type"] == "scene":
                    continue
                else:
                    tag = "os" if p["type"] == "os" else "对白"
                    lines.append(f"- [{tag}] {t}")
            lines.append("")
            lines.append("---")
            lines.append("")

        md = "\n".join(lines)
        name = f"shard_{sid:02d}"
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, name + ".md"), "w", encoding="utf-8") as f:
            f.write(md)
        with open(os.path.join(out_dir, name + ".index.json"), "w", encoding="utf-8") as f:
            json.dump({"shard": sid, "scenes": [s["title"] for s in group],
                       "grade_count": grade_count, "actions": idx_list},
                      f, ensure_ascii=False, indent=2)
        shards.append({"shard": sid, "file": name + ".md", "scenes": len(group),
                       "actions": len(idx_list), "A": grade_count["A"], "B": grade_count["B"]})
    return {"total_scenes": len(scenes), "total_actions": sum(s["actions"] for s in shards),
            "shards": shards}


def main() -> int:
    ap = argparse.ArgumentParser(description="按场次切分剧本为并行改写分片")
    ap.add_argument("parsed", help="parse_docx.py 产出的 parsed.json")
    ap.add_argument("-o", "--output", required=True, help="分片输出目录")
    ap.add_argument("--per-shard", type=int, default=8, help="每片场次数（默认 8）")
    args = ap.parse_args()

    with open(args.parsed, "r", encoding="utf-8") as f:
        parsed = json.load(f)
    manifest = build_shards(parsed, args.per_shard, args.output)
    with open(os.path.join(args.output, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(f"[OK] {manifest['total_scenes']} 场 -> {len(manifest['shards'])} 片 | △行 {manifest['total_actions']} 条")
    print(f"  分级: A(保留) {sum(s['A'] for s in manifest['shards'])} | B(需改写) {sum(s['B'] for s in manifest['shards'])}")
    for s in manifest["shards"]:
        print(f"  shard_{s['shard']:02d}: {s['scenes']:2d}场 / {s['actions']:3d}条 (A{s['A']} B{s['B']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""改写结果校验 + 生成前后对照表（纯标准库）

用法:
    python3 check_rewrite.py "parsed.json" "rewrite_map.json" -o "改写对照.md"

检查项（见 references/03-校验规则.md）:
    🔴 FAIL  1 对白零改动 / 2 △前缀保留 / 3 无不可演词 / 4 可拍摄性
    🟡 WARN  5 事实锚点（时间/数量/角色名是否在改写后仍可追踪）/ 6 长度
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

FORBIDDEN = [
    "感到", "觉得", "心想", "意识到", "心里一紧", "松了口气", "暗自", "暗暗",
    "不禁", "下意识地", "气氛凝固", "意味深长", "说不出的", "复杂情绪",
    "心如刀绞", "仿佛", "似乎", "好像", "镜头拉近", "特写", "配乐", "转场", "画面定格",
]
ACTION_WORDS = [
    "站", "蹲", "坐", "走", "停", "抬", "放", "伸", "收", "攥", "抠", "扒", "摁",
    "掀", "拎", "提", "推", "拉", "看", "盯", "望", "扫", "瞥", "别开", "移", "转",
    "侧", "低下", "仰", "点", "摇", "顿", "僵", "哼", "咽", "喘", "咬", "抿", "扯",
    "抖", "颤", "蹭", "挪", "蹬", "撑", "拱", "舔", "溅", "滴", "洒", "刷", "洗",
    "凑", "落", "摞", "拨", "摁灭", "抠住", "攥紧",
]
FACT_RE = re.compile(r"[一二三四五六七八九十百千两\d]+\s*(?:天|日|年|月|岁|秒|分钟|小时|块钱|元|斤|里|集|步|遍|只|个|下|口|分|块|次)")
# 虚化量词：只是语气/节奏，不构成剧情事实，锚点比对时忽略
VAGUE_QUANTIFIERS = {
    "一个", "一下", "一口", "一块", "一次", "一声", "一眼", "一愣", "一僵",
    "一顿", "一抖", "一颤", "一回", "一分", "两步", "半步", "两下", "一下下",
}


def check(parsed: dict, rewrite_map: dict) -> dict:
    global ROLE_NAMES
    by_index = {p["index"]: p for p in parsed["paragraphs"]}
    ROLE_NAMES = sorted({re.match(r"^([^\s：:]{1,12})", p["text"]).group(1)
                         for p in parsed["paragraphs"]
                         if p["type"] in ("dialogue", "os") and re.match(r"^([^\s：:]{1,12})", p["text"])},
                        key=len, reverse=True)

    fails, warns, rows = [], [], []

    for k, v in rewrite_map.items():
        if str(k).startswith("_"):   # 跳过说明性元数据字段
            continue
        idx, new = int(k), str(v)
        src = by_index.get(idx)
        tag = f"#{idx}"
        if src is None:
            fails.append(f"{tag} index 不存在于 parsed.json")
            continue
        if src["type"] != "action":
            fails.append(f"{tag} 🔴 非 △ 行被改写（type={src['type']}）：{src['text'][:30]}")
            continue
        old = src["text"]

        # 2 △ 前缀
        if not new.lstrip().startswith(("△", "▲")):
            fails.append(f"{tag} 🔴 丢了 △ 前缀：{new[:30]}")
        # 3 禁词
        hit = [w for w in FORBIDDEN if w in new]
        if hit:
            fails.append(f"{tag} 🔴 含不可演词 {hit}：{new[:40]}")
        # 4 可拍摄性
        if not any(w in new for w in ACTION_WORDS):
            fails.append(f"{tag} 🔴 没有可拍摄动作词：{new[:40]}")
        # 5 事实锚点
        facts = (set(FACT_RE.findall(old)) | {r for r in ROLE_NAMES if r in old}) - VAGUE_QUANTIFIERS
        missing = [f for f in facts if f not in new]
        if missing:
            warns.append(f"{tag} 🟡 事实锚点疑似丢失 {missing}（请人工确认是否换了说法）")
        # 6 长度
        n = len(new)
        if n > 90:
            warns.append(f"{tag} 🟡 偏长 {n} 字，建议删到 70 字内")
        elif n < 12:
            warns.append(f"{tag} 🟡 偏短 {n} 字，可能没补画面")

        rows.append({"index": idx, "scene": src["scene_id"], "old": old, "new": new})

    return {"fails": fails, "warns": warns, "rows": rows,
            "count": len(rows),
            "total_actions": sum(1 for p in parsed["paragraphs"] if p["type"] == "action")}


def render_compare(result: dict) -> str:
    lines = [
        "# 剧本 △ 行改写前后对照",
        "",
        f"- 本次改写 **{result['count']}** 条 / 全文 △ 行共 **{result['total_actions']}** 条",
        f"- 机检：🔴 失败 **{len(result['fails'])}** 项，🟡 提醒 **{len(result['warns'])}** 项",
        "",
    ]
    if result["fails"]:
        lines += ["## 🔴 必须回修", ""] + [f"- {f}" for f in result["fails"]] + [""]
    if result["warns"]:
        lines += ["## 🟡 人工复核", ""] + [f"- {w}" for w in result["warns"]] + [""]
    lines += ["## 逐条对照", "", "| # | 场次 | 原文 | 改后 |", "|---|---|---|---|"]
    for r in result["rows"]:
        old = r["old"].replace("|", "\\|").replace("\n", " ")
        new = r["new"].replace("|", "\\|").replace("\n", " ")
        lines.append(f"| {r['index']} | {r['scene']} | {old} | {new} |")
    lines += ["", "---", "",
              "> 对白行、os 行、场次标题、剧情事实均未改动。输出为另存新文件，原件保留。"]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="校验改写并生成前后对照表")
    ap.add_argument("parsed", help="parse_docx.py 产出的 parsed.json")
    ap.add_argument("map", help="rewrite_map.json")
    ap.add_argument("-o", "--output", help="对照表 md 输出路径")
    args = ap.parse_args()

    with open(args.parsed, "r", encoding="utf-8") as f:
        parsed = json.load(f)
    with open(args.map, "r", encoding="utf-8") as f:
        rewrite_map = json.load(f)

    result = check(parsed, rewrite_map)
    print(f"改写 {result['count']} 条 | 🔴 FAIL {len(result['fails'])} | 🟡 WARN {len(result['warns'])}")
    for f in result["fails"]:
        print("  " + f)
    for w in result["warns"]:
        print("  " + w)

    if args.output:
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(render_compare(result))
        print(f"[OK] 对照表已写出 {args.output}")

    return 1 if result["fails"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

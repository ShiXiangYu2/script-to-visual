#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全本镜头体检：景别暗含是否成立、整场节奏是否平（纯标准库）

用法:
    python3 lint_shot_scale.py parsed.json -o 镜头体检.md
    python3 lint_shot_scale.py parsed.json --shotlist 分镜草表.md

与 check_rewrite.py 的分工:
    check_rewrite.py   逐条改写质量（前缀/禁词/可拍摄性/事实锚点）
    lint_shot_scale.py 全本整体（越界景别名/跨档/收束模板/缺定场/整场单档）

检查项（见 references/03-校验规则.md）:
    🔴 FAIL  S1 出现元叙事景别词（特写/近景/镜头/机位…）
    🟡 WARN  S2 一条 △ 行跨到画面装不下的两档
    🟡 WARN  S3 单场同款收束 > 2 次
    🟡 WARN  S4 场次首条 △ 行缺空间参照（没定场）
    🟡 WARN  S5 一个机位停太久（最长连续同档 >= 5）或整场只有一个档
    统计     S6 档位未判定率（这条没把框写死的比例）

模型说明: 一条 △ 行默认沿用上一条的景别——镜头不会因为换了一行就自己切。
所以「连续同档」本身不是缺陷，只有一个机位停满全场才是。
"""
from __future__ import annotations

import argparse
import collections
import json
import os

# 元叙事：属于分镜层，写进剧本 △ 行就越界（S1）
META = [
    "特写", "近景", "中景", "全景", "远景", "大远景", "景别", "镜头", "机位",
    "画外", "入画", "出画", "构图", "景深", "焦段", "俯拍", "仰拍", "跟拍",
    "推近", "拉远", "摇镜", "甩镜", "切至", "淡出", "叠化",
]
# 已知误报：实物位置，不是摄影机位（「缝纫机的机位」）
META_FALSE_POSITIVE = {"缝纫机": ("机位", "镜头")}
# 收束模板（S3）
TAILS = ["停住", "没动", "没再", "顿住", "不动", "停了一下", "定住", "僵住",
         "没挪", "没松开", "没抬眼", "没吭声"]
# 空间参照（S4 定场）：地点、建筑、容器、陈设——凡是能把人放进一个「哪儿」的词
SPACE = ["门", "窗", "墙", "院", "屋", "房", "桌", "床", "炕", "路", "街", "站台",
         "圈", "槽", "灶", "柜", "梁", "坡", "田", "河", "门槛", "门框", "地", "场",
         "井", "摊", "架", "盆", "锅", "筐", "篮", "箱", "桥", "店", "铺", "车", "树",
         "坎", "渠", "坝", "台", "缸", "桶", "席", "板", "铺", "栏", "坡", "埂",
         "坊", "馆", "社", "部", "厂", "屯", "村", "队", "校", "棚", "窖", "窑", "堂"]

TIERS = {
    0: ["整条街", "半个村", "远处的", "天边", "山头", "旷野", "一整排", "满院子",
        "全村", "村口", "整片", "一直排到", "满地", "小得", "辨不出", "挨着人"],
    1: ["整个人", "全身", "背影", "门口", "屋", "院", "堂", "站台", "街上", "炕",
        "路面", "圈墙", "屋外", "床边", "炕上", "桌边", "灶前", "墙根", "门槛", "门框"],
    2: ["半身", "肩膀", "胳膊", "后背", "两个人", "对面", "隔着", "身边", "一步",
        "半步", "并肩", "侧过身", "背对", "蹲在", "手里", "挡住", "坐下", "站起来",
        "半个身子", "半个人"],
    3: ["眼里", "眼底", "眼神", "目光", "脸上", "脸色", "嘴角", "嘴唇", "下巴",
        "额头", "眉头", "腮", "鼻梁", "侧脸", "半边脸", "眼皮", "喉咙", "眼眶"],
    4: ["指节", "指尖", "指甲", "指腹", "睫毛", "瞳孔", "眼白", "掌纹", "喉结",
        "牙关", "咬肌", "针脚", "汗毛", "耳廓", "手背", "虎口", "手腕", "疤"],
}
TIER_NAME = {0: "T0 大远景", 1: "T1 全景", 2: "T2 中景", 3: "T3 近景", 4: "T4 特写",
             None: "未定"}


def meta_hits(text: str) -> list:
    hits = [w for w in META if w in text]
    for ctx, words in META_FALSE_POSITIVE.items():
        if ctx in text:
            hits = [w for w in hits if w not in words]
    return hits


def classify(text: str):
    """按可见尺度词表推定档位。返回 (tier|None, 命中的词)

    取「最紧」的一档：一行里同时写了嘴唇和屋子时，镜头在脸上——因为要看见嘴唇，
    机位就必须近。空间词只是坐标，细节词才是机位。T0 例外，它是刻意的比例陈述。
    """
    hit = {t: [w for w in ws if w in text] for t, ws in TIERS.items()}
    if hit[0]:
        return 0, hit[0]
    for t in (4, 3, 2, 1):
        if hit[t]:
            return t, hit[t]
    return None, []


def lint(parsed: dict) -> dict:
    acts = [p for p in parsed["paragraphs"] if p["type"] == "action"]
    scenes = collections.OrderedDict()
    for p in acts:
        scenes.setdefault(p["scene_id"], []).append(p)

    fails, warns = [], []
    seq, tail_by_scene = collections.OrderedDict(), collections.defaultdict(list)
    tier_counter = collections.Counter()
    no_space, flat_scenes = 0, 0

    for sid, rows in scenes.items():
        raw = [classify(p["text"])[0] for p in rows]
        seq[sid] = raw

        for p, t in zip(rows, raw):
            if t is not None:
                tier_counter[t] += 1
            m = meta_hits(p["text"])
            if m:
                fails.append(f"#{p['index']} [{sid}] 🔴 出现元叙事景别词 {m}：{p['text'][:40]}")
            if t == 4 and any(w in p["text"] for w in TIERS[0]):
                warns.append(f"#{p['index']} [{sid}] 🟡 一行跨到 T4 与 T0，一个画面装不下：{p['text'][:40]}")
            hs = [w for w in TAILS if w in p["text"]]
            if hs:
                tail_by_scene[sid].append((p["index"], hs))

        first = rows[0]
        if not any(w in first["text"] for w in SPACE) and classify(first["text"])[0] not in (0, 1):
            no_space += 1
            warns.append(f"#{first['index']} [{sid}] 🟡 场首 △ 行缺空间参照（没定场）：{first['text'][:40]}")

        # S5：只抓两种真问题——一个机位停太久 / 整场只有一个档
        # 覆盖率不足 60% 时档位序列不可靠，不下结论（避免把词表没命中当成稿子有问题）
        known = [t for t in raw if t is not None]
        if len(known) < max(4, int(len(raw) * 0.6)):
            pass
        elif len(set(known)) == 1:
            flat_scenes += 1
            warns.append(f"[{sid}] 🟡 整场 {len(known)} 条只有 {TIER_NAME[known[0]]}，没有换档")
        else:
            run, best = 1, 1
            for i in range(1, len(raw)):
                if raw[i] is not None and raw[i] == raw[i - 1]:
                    run += 1
                    best = max(best, run)
                else:
                    run = 1
            if best >= 5:
                warns.append(f"[{sid}] 🟡 一个机位连停 {best} 条，考虑中途换档")

    for sid, items in tail_by_scene.items():
        if len(items) > 2:
            warns.append(f"[{sid}] 🟡 同款收束 {len(items)} 次（{items[0][1][0]} 类）：不超 2 次")

    total = len(acts)
    undecided = sum(1 for t in (t for v in seq.values() for t in v) if t is None)
    return {
        "scenes": len(scenes), "actions": total,
        "fails": fails, "warns": warns,
        "tier_counter": tier_counter,
        "tail_total": sum(len(v) for v in tail_by_scene.values()),
        "no_space": no_space, "flat_scenes": flat_scenes,
        "undecided": undecided,
        "seq": seq,
    }


def resolve(raw: list) -> list:
    """把「未定」按镜头不自动切的原则，沿用上一档；场首未定默认 T1。"""
    out, prev = [], 1
    for t in raw:
        if t is None:
            out.append(prev)
        else:
            out.append(t)
            prev = t
    return out


def render(result: dict) -> str:
    total = result["actions"]
    c = result["tier_counter"]
    lines = [
        "# 镜头体检报告（暗含景别）",
        "",
        f"- 场次 **{result['scenes']}** / △ 行 **{total}**",
        f"- 🔴 失败 **{len(result['fails'])}** 项，🟡 提醒 **{len(result['warns'])}** 项",
        "",
        "## 一、推定景别分布",
        "",
        "| 档 | 条数 | 占比 |",
        "|---|---|---|",
    ]
    for t in (0, 1, 2, 3, 4, None):
        n = c.get(t, 0)
        if n:
            lines.append(f"| {TIER_NAME[t]} | {n} | {n / total * 100:.1f}% |")
    lines += [
        "",
        "| 指标 | 数值 | 读法 |",
        "|---|---|---|",
        f"| 档位未判定 | {result['undecided']}（{result['undecided'] / total * 100:.1f}%） | 词表没命中，需人工看图；**不是缺陷**，只用于同稿前后对比 |",
        f"| 同款收束 | {result['tail_total']}（{result['tail_total'] / total * 100:.1f}%） | 停住/没动 一类的模板尾巴 |",
        f"| 缺定场场次 | {result['no_space']} / {result['scenes']} | 场首没有空间交代 |",
        f"| 整场单档 | {result['flat_scenes']} 场 | 全场没换过档，最平 |",
        "",
    ]
    if result["fails"]:
        lines += ["## 二、🔴 必须回修", ""] + [f"- {x}" for x in result["fails"]] + [""]
    if result["warns"]:
        lines += ["## 三、🟡 建议复核", ""] + [f"- {x}" for x in result["warns"]] + [""]
    lines += ["---", "",
              "> 档位按可见尺度词表**推定**，用于看分布与节奏，不用于判单条好坏。",
              "> 剧本里不出现任何景别名（S1 硬拦截），景别由「画面装得下什么」暗含。"]
    return "\n".join(lines)


def render_shotlist(result: dict) -> str:
    mark = {0: "T0", 1: "T1", 2: "T2", 3: "T3", 4: "T4"}
    lines = ["# 分镜草表（从剧本反向推定）", "",
             "> 剧本原稿不含景别名。本表按可见尺度反推，同档视为镜头不切（延续上一机位），",
             "> 可直接作 AI 视频提示词的 framing 字段，或交分镜师作起点。", "",
             "| 场次 | 条数 | 换档次数 | 景别序列 |", "|---|---|---|---|"]
    for sid, raw in result["seq"].items():
        full = resolve(raw)
        cuts = sum(1 for i in range(1, len(full)) if full[i] != full[i - 1])
        s = " → ".join(mark[t] for t in full)
        lines.append(f"| {sid} | {len(full)} | {cuts} | {s} |")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description="全本镜头体检：暗含景别是否成立、整场节奏是否平")
    ap.add_argument("parsed", help="parse_docx.py 产出的 parsed.json")
    ap.add_argument("-o", "--output", help="体检报告 md 输出路径")
    ap.add_argument("--shotlist", help="另出分镜草表（推定景别序列）")
    args = ap.parse_args()

    with open(args.parsed, "r", encoding="utf-8") as f:
        parsed = json.load(f)

    r = lint(parsed)
    print(f"场次 {r['scenes']} | △行 {r['actions']} | 🔴 FAIL {len(r['fails'])} | 🟡 WARN {len(r['warns'])}"
          f" | 未定 {r['undecided']} | 单档场 {r['flat_scenes']}")
    for x in r["fails"]:
        print("  " + x)
    for x in r["warns"][:15]:
        print("  " + x)
    if len(r["warns"]) > 15:
        print(f"  …… 其余 {len(r['warns']) - 15} 条见报告")

    if args.output:
        os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(render(r))
        print(f"[OK] 体检报告 {args.output}")
    if args.shotlist:
        os.makedirs(os.path.dirname(os.path.abspath(args.shotlist)), exist_ok=True)
        with open(args.shotlist, "w", encoding="utf-8") as f:
            f.write(render_shotlist(r))
        print(f"[OK] 分镜草表 {args.shotlist}")
    return 1 if r["fails"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

# 示例

一个 3 场 / 17 段 / 10 条 `△` 行的迷你剧本，用来跑通完整五步工作流。剧情为虚构，仅作演示。

## 文件

| 文件 | 说明 |
|---|---|
| `demo_scene.docx` | 输入剧本（3 场：修车铺・夜・内 / 街边・夜・外 / 出租屋・夜・内） |
| `rewrite_map.demo.json` | 手工按规则改好的结果（8 条 B 级行） |
| `demo_scene_rewritten.docx` | 跑完 ④ 落盘后的成品，可直接用 Word 打开对比 |
| `demo_compare.md` | 跑完 ③ 机检后自动生成的前后对照表 |
| `demo_shot_scale.md` | **暗含景别五档改法对照**（T1 定场 / T2 关系 / T3 反应 / T4 落点 / T0 尺度） |
| `demo_shotcheck.md` | 跑完 ④ 全本体检后自动生成的镜头体检报告 |
| `demo_shotlist.md` | 跑完 ④ 后反推的分镜草表（每场景别序列） |
| `build_demo_docx.py` | 上面那个 docx 的生成器（纯标准库手搓 OOXML） |

## 复现

```bash
cd script-to-visual

python3 scripts/parse_docx.py examples/demo_scene.docx -o /tmp/parsed.json
#   场次 3 | △动作行 10 | 对白 2 | os 2 | 总段落 17

python3 scripts/check_rewrite.py /tmp/parsed.json examples/rewrite_map.demo.json
#   改写 8 条 | 🔴 FAIL 0 | 🟡 WARN 0

python3 scripts/lint_shot_scale.py /tmp/parsed.json --shotlist /tmp/shotlist.md
#   场次 3 | △行 10 | 🔴 FAIL 0 | 🟡 WARN 0

python3 scripts/apply_rewrite.py examples/demo_scene.docx \
        examples/rewrite_map.demo.json /tmp/out.docx
#   改写 △ 行: 8 条 | 其余内容字节级保持不变
```

## 分级示意

`split_scenes.py` 把这 10 条 △ 行分成 **A 级 2 条 / B 级 8 条**：

- A 级（已有画面感，保留原文）：`△ 老陈蹲在车边，手电咬在嘴里，光柱贴着地面扫过去，照亮了半只轮胎。`
- B 级（需改写）：`△ 老陈没接话。` → `△ 老陈的喉结动了一下，把手里的扳手翻了个面，抬眼扫了下小王，又低下去看那只轮胎。`

> `demo_shotcheck.md` 里「档位未判定」偏高（10 条里 6 条）是正常的：示例剧本本身就是改写前那种干瘪句式，
> 词表抓不到尺度线索。这个数说明的是「得人看图」，不是稿子有缺陷。

试跑时你可以故意把某条改歪（比如写成"他感到一阵心酸"，或写成"特写他的手"），跑 ③ 就会看到机检直接判 🔴 FAIL 打回 —— 这正是它该做的事。

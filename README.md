# script-to-visual · 剧本画面化工作流

> 把短剧剧本里"人能读懂、但 AI 演不出来"的动作舞台指示（`△` 行），改写成**有文学画面感、且视频模型拍得出来**的画面描述。
> 只改 `△` 行；对白、内心独白、场次标题、剧情事实**一字不动**；输出另存新文件，排版零损伤。

![Python](https://img.shields.io/badge/Python-3.9%2B%2C%20标准库零依赖-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)
![Format](https://img.shields.io/badge/输入格式-.docx-2b579a)
![Skill](https://img.shields.io/badge/Agent%20Skill-Claude%20%2F%20WorkBuddy-8b5cf6)

---

## 它解决什么问题

短剧剧本的舞台提示往往只交代"发生了什么"，不交代"镜头里看得见什么"。这类句子编剧能懂、导演能拍，但**丢给 AI 视频模型就废了**——模型不知道该让人物做什么动作、手放哪儿、脸朝哪儿。

| | 原文（功能性动作） | 改写后（可拍画面） |
|---|---|---|
| 静场 | `△ 老陈没接话。` | `△ 老陈的喉结动了一下，把手里的扳手翻了个面，抬眼扫了下小王，又低下去看那只轮胎。` |
| 纯结果 | `△ 屋里静了一会儿。` | `△ 铺子里的挂钟走了三格，风从卷帘门底下钻进来，把地上的一张报纸掀了个角又落下。` |
| 单动作 | `△ 老陈点了点头。` | `△ 老陈下巴往下压了压，眼睛还看着那辆车，指节在裤缝上蹭了一下。` |
| 无细节 | `△ 路灯下停着一辆黑色轿车，车门开着。` | `△ 路灯的光斜切下来，一辆黑色轿车停在光里，驾驶室的门开着，车里的顶灯亮着。` |

核心只有一句话：**把"告知"改成"可见"**——只写镜头拍得到的物理事实，让读者和模型自己得出情绪。

---

## 快速开始

只依赖 **Python 3.9+ 标准库**，不需要 `python-docx`、不需要 `lxml`、不需要联网。

```bash
git clone https://github.com/ShiXiangYu2/script-to-visual.git
cd script-to-visual

# ① 解析（自带示例剧本，先跑通再换成你自己的）
python3 scripts/parse_docx.py examples/demo_scene.docx -o parsed.json

# ② 改写（这一步由模型/人来做，产出 rewrite_map.json；示例结果已给好）
#     参照 references/01-改写规则.md 与 02-情绪外显对照表.md 逐条改写 △ 行

# ③ 机检（对白零改动 / 无不可演词 / 保留△前缀 / 含可拍摄动作）
python3 scripts/check_rewrite.py parsed.json examples/rewrite_map.demo.json -o 对照表.md

# ④ 落盘（复制 zip 只替换 △ 段落文字，排版 100% 保留，另存新文件）
python3 scripts/apply_rewrite.py examples/demo_scene.docx examples/rewrite_map.demo.json 输出_画面化稿.docx
```

跑完你会得到 `输出_画面化稿.docx`：**8 条 △ 行被改写，对白与 os 逐字未动，样式/字体/页码全保留**。

---

## 四阶段工作流

| 阶段 | 谁做 | 产出 |
|---|---|---|
| **① 解析** | `parse_docx.py` | 结构化 JSON：每段的 `index / type(scene｜action｜dialogue｜os｜other) / text / scene_id`；先报统计（几场、多少 △ 行、多少对白）确认识别无误 |
| **② 改写** | 模型 / 人（按 `references/` 规则库） | `rewrite_map.json`：`{"<段落index>": "改写后的 △ 文本"}`，只放 △ 行 |
| **③ 校验** | `check_rewrite.py` | 机检报告 + 逐条对照表；有 FAIL 必须打回重写 |
| **④ 落盘** | `apply_rewrite.py` | 新 docx（原件不动）+ 对照 md |

### 大剧本怎么办（80 集那种）

一次性把上千条 △ 行丢给模型改写，后半段质量必然塌方。正确做法是先分级、再并行：

```bash
# 按场次切片，同时做 A/B 级初筛
python3 scripts/split_scenes.py parsed.json -o shards --per-shard 8
```

- **A 级**：本身已有具体物理细节/动作链 → **保留原文**（强行拉长只会加戏变油腻）
- **B 级**：功能性短句、纯结果、抽象静场 → 重点改写

每片产出一个 `rewrite_map` 分片 JSON，最后合并、一次性机检、一次性落盘。

---

## 机检机制

| 级别 | 检查项 |
|---|---|
| 🔴 **FAIL**（必须回修） | 改到了非 `△` 行 ｜ 丢了 `△` 前缀 ｜ 含不可演词（感到/觉得/心想/意识到/仿佛/似乎/镜头拉近…）｜ 整句没有一个可拍摄动作词 |
| 🟡 **WARN**（人工复核） | 事实锚点疑似丢失（时间/数量/人名）｜ 过短 <12 字 ｜ 过长 >90 字 |

`apply_rewrite.py` 落盘前还会再拦一次：**若 `rewrite_map` 里混进了非 `△` 行的 index，直接拒绝写入**。

---

## 六条硬约束

1. **只改 `△` 行** —— 对白、`os`、场次标题一律原样
2. **剧情事实不增不减** —— "三天后/车身擦干/油污清走"这类信息必须全保留，不许新增原文没有的情节、道具、人物
3. **只写镜头拍得到的** —— 禁止心理描写，禁止"仿佛/似乎/某种说不清的"这类不可渲染的模糊修辞
4. **克制** —— 每条 1–2 个准细节，不堆五个动作、不堆排比、不撒装饰符号
5. **保留 `△ ` 前缀与标点习惯**
6. **另存新文件** —— 绝不覆盖原件

---

## 实测效果

在一部 **80 集 / 152 场 / 3449 段** 的中文短剧上跑完全量：

| 项 | 数量 |
|---|---|
| △ 行总数 | 1171 条 |
| A 级保留原文 | 208 条 |
| **B 级改写** | **964 条** |
| 机检结果 | **FAIL 0 / WARN 0** |
| 回读验证 | 段落数不变 · 非 △ 行改动 **0** · 对白/os/标题逐字一致 · zip 完整 |

> 为什么不是 1171 条全改：那份稿子此前已做过一轮画面优化，像"他把伞朝她那边偏了些，水从低下去的伞沿往下滴"本来就有画面感，再拉长只会加戏。分级是为了**只动真正干瘪的句子**。

---

## 作为 Agent Skill 安装

仓库根目录就是 Skill 本体（`SKILL.md` + `references/` + `scripts/`），整个目录丢进技能目录即可。

**WorkBuddy / Claude Code（用户级，全项目可用）**

```bash
git clone https://github.com/ShiXiangYu2/script-to-visual.git ~/.workbuddy/skills/script-to-visual
# Claude Code: ~/.claude/skills/script-to-visual
```

之后直接说：

> 用 script-to-visual 处理这份剧本 `xxx.docx`，先试跑前 2 场给我看

Skill 会自动按四阶段执行，并在全量前先给你试跑样张确认风格。

---

## 目录结构

```
script-to-visual/
├── SKILL.md                      # 工作流定义（Agent Skill 入口）
├── README.md
├── references/
│   ├── 01-改写规则.md             # 核心改写规则
│   ├── 02-情绪外显对照表.md        # 情绪→可见行为速查表
│   └── 03-校验规则.md             # 质检清单与常见翻车案例
├── examples/
│   ├── demo_scene.docx           # 3 场 / 10 条 △ 行的迷你剧本
│   ├── rewrite_map.demo.json     # 示例改写结果
│   ├── demo_scene_rewritten.docx # 走完四步的成品
│   ├── demo_compare.md           # 机检产出的对照表
│   └── build_demo_docx.py        # 示例 docx 生成器
├── scripts/
│   ├── parse_docx.py             # ① 解析
│   ├── split_scenes.py           # 大剧本切分 + A/B 初筛
│   ├── check_rewrite.py          # ③ 机检 + 对照表
│   └── apply_rewrite.py          # ④ OOXML 原位替换落盘
├── templates/
│   └── rewrite_map.example.json
└── vendor/                       # 第三方素材（各自许可，见下）
```

### 为什么不直接用 python-docx

`apply_rewrite.py` 的做法是**复制原 docx 的 zip，只替换目标段落内 `<w:t>` 的文字**，其余 XML 字节完全不动。因此：

- 场次标题样式、对白、页码、字体、图片、页眉页脚 **100% 保留**
- 不依赖任何第三方库，任何环境 `python3` 直接跑
- 天然满足"另存新文件"，物理上不可能改坏原件

---

## 素材来源与许可

`references/` 的规则提炼自两个开源项目，`vendor/` 内为其原样下载的部分素材（版权归原作者）：

| 项目 | 贡献 | 许可 |
|---|---|---|
| [tance-mang/chinese-webnovel-skills](https://github.com/tance-mang/chinese-webnovel-skills) | 情绪外显（show don't tell）六通道、描写克制、句法节奏 | MIT |
| [smixs/visual-skills](https://github.com/smixs/visual-skills) | AI 视频可渲染性规则（具体物理细节 > 抽象概念、三细节检查、镜头光影词汇） | **CC-BY-4.0，需署名 Serge Shima** |

详细取用清单见 [`vendor/SOURCES.md`](vendor/SOURCES.md)，原许可证见 `vendor/LICENSE_*`、`vendor/NOTICE_*`。

本仓库**原创部分**（`SKILL.md`、`references/`、`scripts/`、`templates/`、`examples/`）以 **MIT** 许可发布，见 [LICENSE](LICENSE)。
`vendor/` 目录不属于 MIT 覆盖范围，按各自许可证使用；二次分发请保留其 LICENSE / NOTICE。

---

## 边界（它不做什么）

- ❌ 不改对白、不改内心独白、不改剧情（这工作流是"翻译镜头"，不是"重写剧本"）
- ❌ 不做分镜表、不生成视频提示词（那是下游工序，可接 Seedance / 可灵 / 即梦）
- ❌ 不支持 `.doc`（老格式）、PDF、纯文本（先转 `.docx`）
- ❌ 不做文生视频本身——它只保证"文字层面已经可拍"

---

## 一句话

**编剧写"发生了什么"，这个工作流补上"镜头里看得见什么"。**

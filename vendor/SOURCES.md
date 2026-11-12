# 素材来源与许可证

本工作流 `script-to-visual` 打包了以下两个 GitHub 开源技能的**部分素材**（原样下载，未修改），
并在 `references/` 中基于其规则做了面向「中文剧本 △ 行画面化」的再编排与中文改写。

---

## 1. tance-mang/chinese-webnovel-skills

- **仓库**：https://github.com/tance-mang/chinese-webnovel-skills
- **用途**：提供中文网文写作的「情绪外显（show don't tell）」规则与文风约束
- **本包取用文件**：
  | 文件 | 原路径 |
  |---|---|
  | `emotion_SKILL.md` | `skills/emotion/SKILL.md` |
  | `expand_SKILL.md` | `skills/expand/SKILL.md` |
  | `show-emotion.md` | `references/show-emotion.md` |
  | `writing-craft.md` | `references/writing-craft.md` |
  | `sentence-rhythm.md` | `references/sentence-rhythm.md` |
  | `script-format.md` | `references/script-format.md` |
  | `human-texture.md` | `references/human-texture.md` |
- **许可证**：见 `LICENSE_chinese-webnovel-skills`（原仓库 LICENSE 原文）

---

## 2. smixs/visual-skills

- **仓库**：https://github.com/smixs/visual-skills
- **用途**：提供 AI 视频模型的「可渲染性」规则 —— 具体物理细节优于抽象、show don't tell、三细节检查、镜头/光影词汇
- **本包取用文件**：
  | 文件 | 原路径 |
  |---|---|
  | `visual_video_SKILL.md` | `video/SKILL.md` |
  | `visual_universal-rules.md` | `video/references/universal-rules.md` |
  | `visual_dramaturgy.md` | `video/references/dramaturgy.md` |
  | `visual_camera-lighting-vocabulary.md` | `video/references/camera-lighting-vocabulary.md` |
- **许可证**：**CC-BY-4.0**，见 `LICENSE_visual-skills` / `NOTICE_visual-skills`
- **署名要求**：
  > **Attribution required — Serge Shima, github.com/smixs/visual-skills**

  本工作流在此明确署名；`references/01-改写规则.md` 中的「AI 可演硬约束 / 三细节检查」即改编自其
  `universal-rules.md` 的 U3 (Show don't tell)、U9 (Concrete physical detail over abstract concept)、
  U12 (The three-detail check)。

---

## 引用与再编排说明

- `vendor/` 内文件为**原样下载**的第三方素材，版权归原作者所有，仅作工作流内部参考。
- `references/01`、`02`、`03` 为 WorkBuddy 在上述素材基础上的**中文改写、裁剪与再编排**，
  已保留原作者署名与许可证链接。
- 若将本工作流对外分发，请一并保留本文件及两份 LICENSE / NOTICE。

---

_下载日期：2026-11-12　｜　下载方式：`gh api repos/<owner>/<repo>/contents/<path>`_

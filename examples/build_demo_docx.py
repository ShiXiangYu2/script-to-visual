#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成示例剧本 examples/demo_scene.docx（纯标准库，无需 python-docx）

用法:
    python3 examples/build_demo_docx.py

产出:
    examples/demo_scene.docx   一个 3 场的迷你剧本，可直接跑完整四步工作流

说明: 这是一个「最小合法 docx」的构造器，只用于造 demo，不是工作流的一部分。
"""
from __future__ import annotations

import os
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "demo_scene.docx")

CT = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>"""

RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>"""

DOC_RELS = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>"""

STYLES = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:docDefaults>
  <w:rPrDefault><w:rPr>
    <w:rFonts w:ascii="Microsoft YaHei" w:eastAsia="Microsoft YaHei" w:hAnsi="Microsoft YaHei"/>
    <w:sz w:val="22"/><w:szCs w:val="22"/>
  </w:rPr></w:rPrDefault>
  <w:pPrDefault><w:pPr><w:spacing w:line="320" w:lineRule="auto"/></w:pPr></w:pPrDefault>
</w:docDefaults>
<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/></w:style>
<w:style w:type="paragraph" w:styleId="Heading1">
  <w:name w:val="heading 1"/><w:basedOn w:val="Normal"/>
  <w:pPr><w:spacing w:before="240" w:after="120"/><w:outlineLvl w:val="0"/></w:pPr>
  <w:rPr><w:b/><w:sz w:val="28"/><w:szCs w:val="28"/></w:rPr>
</w:style>
</w:styles>"""

CORE = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
 xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/"
 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
<dc:title>示例剧本 demo_scene</dc:title>
<dc:creator>script-to-visual</dc:creator>
<cp:lastModifiedBy>script-to-visual</cp:lastModifiedBy>
</cp:coreProperties>"""

APP = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"
 xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
<Application>script-to-visual</Application>
</Properties>"""

# 虚构剧本：3 场，覆盖「已有画面感(A)」与「功能性短句(B)」两类 △ 行
SCRIPT = [
    ("scene", "第七场：修车铺・夜・内"),
    ("action", "△ 老陈蹲在车边，手电咬在嘴里，光柱贴着地面扫过去，照亮了半只轮胎。"),
    ("dialogue", "小王：这车还能跑？"),
    ("action", "△ 老陈没接话。"),
    ("os", "老陈os：跑是能跑，看谁开。"),
    ("action", "△ 他站起来，踢了踢轮胎。"),
    ("action", "△ 屋里静了一会儿。"),
    ("scene", "第八场：街边・夜・外"),
    ("action", "△ 小王把车推到路边，熄了火。"),
    ("dialogue", "小王：我明天来取。"),
    ("action", "△ 老陈点了点头。"),
    ("action", "△ 路灯下停着一辆黑色轿车，车门开着。"),
    ("scene", "第九场：出租屋・夜・内"),
    ("action", "△ 老陈把外套挂在门后，倒在床上。"),
    ("os", "老陈os：轮胎该换了。"),
    ("action", "△ 手机响了两声。"),
    ("action", "△ 窗外的雨下到半夜。"),
]


def esc(t: str) -> str:
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def para(kind: str, text: str) -> str:
    ppr = '<w:pPr><w:pStyle w:val="Heading1"/></w:pPr>' if kind == "scene" else ""
    return (
        "<w:p>" + ppr +
        '<w:r><w:rPr><w:rFonts w:hint="eastAsia"/></w:rPr>'
        f'<w:t xml:space="preserve">{esc(text)}</w:t></w:r></w:p>'
    )


def build() -> str:
    body = "".join(para(k, t) for k, t in SCRIPT)
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body>{body}"
        '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/>'
        '<w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"/></w:sectPr>'
        "</w:body></w:document>"
    )


def main() -> int:
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", CT)
        z.writestr("_rels/.rels", RELS)
        z.writestr("docProps/core.xml", CORE)
        z.writestr("docProps/app.xml", APP)
        z.writestr("word/_rels/document.xml.rels", DOC_RELS)
        z.writestr("word/styles.xml", STYLES)
        z.writestr("word/document.xml", build())
    print(f"[OK] 已生成 {OUT}")
    print(f"  {len(SCRIPT)} 段 / {sum(1 for k, _ in SCRIPT if k == 'scene')} 场")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import html
import shutil
import zipfile
from pathlib import Path

try:
    from PIL import Image
except Exception:
    Image = None


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "跌倒检测与事件留证系统-答辩PPT-第一版.pptx"
ASSETS = ROOT / "thesis_assets"
SHOTS = ASSETS / "screenshots"

W, H = 13_333_500, 7_500_000
BG = "F7F7F5"
NAVY = "2F4858"
TEAL = "3A7D7C"
ACCENT = "E07A5F"
GOLD = "F2CC8F"
TEXT = "1F2933"
MUTED = "52606D"
LINE = "D9E2EC"
WHITE = "FFFFFF"
SOFT = "EEF4F3"


def emu(v: float) -> int:
    return int(v)


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def xywh(x, y, w, h):
    return f'<a:xfrm><a:off x="{emu(x)}" y="{emu(y)}"/><a:ext cx="{emu(w)}" cy="{emu(h)}"/></a:xfrm>'


def fill(color: str, alpha: int | None = None) -> str:
    a = f'<a:alpha val="{alpha}"/>' if alpha is not None else ""
    return f'<a:solidFill><a:srgbClr val="{color}">{a}</a:srgbClr></a:solidFill>'


def rect(idx, x, y, w, h, color, line=None, round_rect=False, alpha=None):
    line_xml = '<a:ln><a:noFill/></a:ln>' if line is None else f'<a:ln w="9525">{fill(line)}</a:ln>'
    geom = "roundRect" if round_rect else "rect"
    return f"""
    <p:sp>
      <p:nvSpPr><p:cNvPr id="{idx}" name="Shape {idx}"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>
      <p:spPr>{xywh(x,y,w,h)}<a:prstGeom prst="{geom}"><a:avLst/></a:prstGeom>{fill(color, alpha)}{line_xml}</p:spPr>
      <p:txBody><a:bodyPr/><a:lstStyle/><a:p/></p:txBody>
    </p:sp>"""


def text_box(idx, text, x, y, w, h, size=20, color=TEXT, bold=False, align="l", font="Microsoft YaHei"):
    paras = text.split("\n")
    p_xml = []
    for para in paras:
        p_xml.append(
            f'<a:p><a:pPr algn="{align}"/>'
            f'<a:r><a:rPr lang="zh-CN" sz="{size * 100}" b="{1 if bold else 0}"><a:solidFill><a:srgbClr val="{color}"/></a:solidFill><a:latin typeface="{font}"/><a:ea typeface="{font}"/></a:rPr><a:t>{esc(para)}</a:t></a:r>'
            f'</a:p>'
        )
    return f"""
    <p:sp>
      <p:nvSpPr><p:cNvPr id="{idx}" name="Text {idx}"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>
      <p:spPr>{xywh(x,y,w,h)}<a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr>
      <p:txBody><a:bodyPr wrap="square" lIns="76200" rIns="76200" tIns="38100" bIns="38100"/><a:lstStyle/>{''.join(p_xml)}</p:txBody>
    </p:sp>"""


def bullets(idx, items, x, y, w, h, size=18, color=TEXT):
    p_xml = []
    for item in items:
        p_xml.append(
            f'<a:p><a:pPr marL="228600" indent="-228600"><a:buChar char="•"/></a:pPr>'
            f'<a:r><a:rPr lang="zh-CN" sz="{size * 100}"><a:solidFill><a:srgbClr val="{color}"/></a:solidFill><a:latin typeface="Microsoft YaHei"/><a:ea typeface="Microsoft YaHei"/></a:rPr><a:t>{esc(item)}</a:t></a:r>'
            f'</a:p>'
        )
    return f"""
    <p:sp>
      <p:nvSpPr><p:cNvPr id="{idx}" name="Bullets {idx}"/><p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>
      <p:spPr>{xywh(x,y,w,h)}<a:prstGeom prst="rect"><a:avLst/></a:prstGeom><a:noFill/><a:ln><a:noFill/></a:ln></p:spPr>
      <p:txBody><a:bodyPr wrap="square" lIns="76200" rIns="76200" tIns="38100" bIns="38100"/><a:lstStyle/>{''.join(p_xml)}</p:txBody>
    </p:sp>"""


def image_size(path: Path, max_w, max_h):
    if Image is None:
        return max_w, max_h
    with Image.open(path) as im:
        iw, ih = im.size
    scale = min(max_w / iw, max_h / ih)
    return int(iw * scale), int(ih * scale)


def pic(idx, rid, x, y, max_w, max_h, path: Path):
    w, h = image_size(path, max_w, max_h)
    return f"""
    <p:pic>
      <p:nvPicPr><p:cNvPr id="{idx}" name="{esc(path.name)}"/><p:cNvPicPr/><p:nvPr/></p:nvPicPr>
      <p:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></p:blipFill>
      <p:spPr>{xywh(x,y,w,h)}<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr>
    </p:pic>"""


def title_bar(title, sub, n):
    return (
        rect(10, 0, 0, W, 565000, NAVY)
        + text_box(11, title, 430000, 70000, 7_800_000, 360000, 25, WHITE, True)
        + text_box(12, sub, 8_750_000, 105000, 3_200_000, 300000, 11, GOLD, False, "r")
        + text_box(13, f"{n:02d}", 12_350_000, 70000, 450000, 330000, 20, GOLD, True, "ctr")
    )


def slide_xml(shapes: str) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main">
  <p:cSld>
    <p:bg><p:bgPr>{fill(BG)}<a:effectLst/></p:bgPr></p:bg>
    <p:spTree>
      <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
      <p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{W}" cy="{H}"/><a:chOff x="0" y="0"/><a:chExt cx="{W}" cy="{H}"/></a:xfrm></p:grpSpPr>
      {shapes}
    </p:spTree>
  </p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sld>"""


def rels_xml(images):
    rels = [
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>'
    ]
    for rid, target in images:
        rels.append(f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="../media/{target}"/>')
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">{''.join(rels)}</Relationships>"""


slides = [
    {
        "shapes": lambda: rect(2, 700000, 1_050_000, 5_300_000, 4_450_000, NAVY)
        + rect(3, 1_000_000, 1_350_000, 5_300_000, 4_450_000, TEAL, alpha=80000)
        + text_box(4, "跌倒检测与事件留证系统的设计与实现", 900000, 1_650_000, 4_850_000, 1_700_000, 28, WHITE, True)
        + text_box(5, "本科毕业设计答辩汇报", 920000, 3_450_000, 3_700_000, 400000, 18, GOLD)
        + text_box(6, "基于项目实现与论文定稿内容整理", 920000, 3_860_000, 4_100_000, 340000, 13, WHITE)
        + rect(7, 920000, 4_500_000, 1_800_000, 45000, ACCENT)
        + text_box(8, "研究方向：智能养老 / 计算机视觉 / Web系统设计", 900000, 6_350_000, 5_300_000, 320000, 14, MUTED)
        + pic(9, "rId2", 6_700_000, 1_180_000, 5_300_000, 4_100_000, SHOTS / "detect-5173.png")
        + text_box(14, "系统实时检测界面", 6_700_000, 5_460_000, 5_300_000, 260000, 10, MUTED, False, "ctr"),
        "images": [SHOTS / "detect-5173.png"],
    },
    {
        "shapes": lambda: title_bar("1. 研究背景及意义", "老龄化监护需求推动非接触式跌倒检测研究", 2)
        + rect(20, 420000, 850000, 5_600_000, 5_850_000, WHITE, LINE, True)
        + text_box(21, "课题背景", 650000, 1_080_000, 1_900_000, 340000, 22, TEAL, True)
        + bullets(22, ["人口老龄化加深，养老场景对安全监护提出更高要求。", "跌倒事件突发性强、危害高，对救援时效要求高。", "穿戴式方案依赖主动佩戴，长期监护中容易漏戴和误报。"], 650000, 1_520_000, 5_000_000, 1_850_000)
        + text_box(23, "研究意义", 650000, 3_750_000, 1_900_000, 340000, 22, TEAL, True)
        + bullets(24, ["基于视觉的非接触式识别更适合连续看护场景。", "将跌倒识别、报警、留证、回放和人工处理串成闭环。", "为智慧养老系统工程化落地提供参考。"], 650000, 4_170_000, 5_000_000, 1_650_000)
        + pic(25, "rId2", 6_750_000, 1_350_000, 5_000_000, 3_800_000, ASSETS / "use_case_diagram.png")
        + text_box(26, "系统参与者与核心业务关系图", 6_750_000, 5_300_000, 5_000_000, 260000, 10, MUTED, False, "ctr")
        + rect(27, 7_100_000, 5_800_000, 4_400_000, 700000, SOFT, LINE, True)
        + text_box(28, "目标：构建面向养老监护场景的跌倒检测与事件留证系统", 7_250_000, 5_960_000, 4_100_000, 360000, 17, NAVY, True, "ctr"),
        "images": [ASSETS / "use_case_diagram.png"],
    },
    {
        "shapes": lambda: title_bar("2. 研究方法及过程", "技术路线与总体架构", 3)
        + rect(30, 420000, 900000, 11_900_000, 5_650_000, WHITE, LINE, True)
        + text_box(31, "总体技术路线", 650000, 1_120_000, 2_500_000, 340000, 23, TEAL, True)
        + bullets(32, ["核心识别：YOLO 目标检测模型 + OpenCV 视频流处理。", "系统架构：Vue 3 前端 + Flask 后端 + MongoDB / GridFS 存储。", "运行方式：支持摄像头与本地视频输入，覆盖检测、报警、留证、回放、统计与训练。"], 650000, 1_600_000, 5_600_000, 1_900_000)
        + text_box(33, "关键研究过程", 650000, 3_850_000, 2_500_000, 340000, 23, TEAL, True)
        + bullets(34, ["需求分析：明确实时性、可用性、安全性与可维护性目标。", "总体设计：划分检测、报警、回放、用户中心、日志与训练模块。", "详细实现：完成接口、权限、数据库结构和留证链路。"], 650000, 4_320_000, 5_600_000, 1_700_000)
        + pic(35, "rId2", 6_850_000, 1_350_000, 5_100_000, 4_100_000, ASSETS / "er_diagram.png")
        + text_box(36, "数据库与业务对象关系示意", 6_850_000, 5_620_000, 5_100_000, 260000, 10, MUTED, False, "ctr"),
        "images": [ASSETS / "er_diagram.png"],
    },
    {
        "shapes": lambda: title_bar("2. 研究方法及过程", "功能模块设计", 4)
        + rect(40, 430000, 980000, 3_800_000, 5_450_000, WHITE, LINE, True)
        + text_box(41, "系统功能模块", 650000, 1_200_000, 2_500_000, 340000, 23, TEAL, True)
        + bullets(42, ["实时检测：视频输入、参数调整、识别结果展示、报警触发。", "报警管理：报警记录、联系人配置、通知时段、工单处理。", "历史回放：视频片段留存、关键帧截图、记录删除与回放。", "管理模块：用户资料、日志中心、统计分析、模型训练、系统配置。"], 650000, 1_700_000, 3_250_000, 3_000_000, 17)
        + rect(43, 650000, 5_050_000, 3_200_000, 1_050_000, SOFT, LINE, True)
        + text_box(44, "模块设计强调形成完整的事件处理与业务管理闭环。", 820000, 5_310_000, 2_850_000, 460000, 17, NAVY, True, "ctr")
        + pic(45, "rId2", 4_650_000, 1_200_000, 3_300_000, 2_200_000, SHOTS / "detect-5173.png")
        + pic(46, "rId3", 8_600_000, 1_200_000, 3_300_000, 2_200_000, SHOTS / "alarm-5173.png")
        + pic(47, "rId4", 4_650_000, 4_000_000, 3_300_000, 2_050_000, SHOTS / "replay-5173.png")
        + pic(48, "rId5", 8_600_000, 4_000_000, 3_300_000, 2_050_000, SHOTS / "statistics-5173.png"),
        "images": [SHOTS / "detect-5173.png", SHOTS / "alarm-5173.png", SHOTS / "replay-5173.png", SHOTS / "statistics-5173.png"],
    },
    {
        "shapes": lambda: title_bar("2. 研究方法及过程", "关键业务流程", 5)
        + pic(50, "rId2", 700000, 1_250_000, 5_800_000, 4_550_000, ASSETS / "sequence_diagram_alarm_flow.png")
        + text_box(51, "报警处理时序图", 700000, 5_950_000, 5_800_000, 260000, 10, MUTED, False, "ctr")
        + rect(52, 7_000_000, 1_250_000, 5_050_000, 4_600_000, WHITE, LINE, True)
        + text_box(53, "核心闭环", 7_250_000, 1_500_000, 1_900_000, 340000, 23, TEAL, True)
        + bullets(54, ["视频输入：支持摄像头或本地视频文件。", "模型推理：输出边界框、类别和置信度。", "触发报警：前端提示，后端保存报警记录。", "事件留证：保存事件前后视频片段与关键帧。", "人工处置：工单反馈、通知日志、状态更新。"], 7_250_000, 1_950_000, 4_450_000, 2_700_000, 17)
        + rect(55, 7_250_000, 4_900_000, 4_450_000, 750000, SOFT, LINE, True)
        + text_box(56, "系统把“检测识别”拓展为“识别 + 留证 + 反馈”的工程化流程。", 7_450_000, 5_080_000, 4_050_000, 380000, 17, NAVY, True, "ctr"),
        "images": [ASSETS / "sequence_diagram_alarm_flow.png"],
    },
    {
        "shapes": lambda: title_bar("2. 研究方法及过程", "详细实现亮点", 6)
        + rect(60, 430000, 950000, 5_700_000, 5_500_000, WHITE, LINE, True)
        + text_box(61, "工程实现要点", 670000, 1_180_000, 2_500_000, 340000, 23, TEAL, True)
        + bullets(62, ["角色权限控制：区分管理员端与普通用户端，前后端双重校验。", "数据留证机制：GridFS 保存报警视频，history 集合记录索引信息。", "日志与通知：记录审计日志、通知日志，支持消息反馈追踪。", "训练与配置：管理员可发起训练、轮询指标并保存系统参数。"], 670000, 1_700_000, 5_100_000, 2_900_000, 17)
        + rect(63, 670000, 5_050_000, 5_100_000, 1_050_000, SOFT, LINE, True)
        + text_box(64, "技术栈落到项目中后，覆盖数据库、接口、权限、训练日志和通知链路。", 900000, 5_300_000, 4_650_000, 420000, 17, NAVY, True, "ctr")
        + pic(65, "rId2", 6_800_000, 1_250_000, 2_600_000, 2_050_000, SHOTS / "train-5173.png")
        + pic(66, "rId3", 9_650_000, 1_250_000, 2_600_000, 2_050_000, SHOTS / "logs-5173.png")
        + pic(67, "rId4", 6_800_000, 4_000_000, 2_600_000, 2_050_000, SHOTS / "settings-5173.png")
        + pic(68, "rId5", 9_650_000, 4_000_000, 2_600_000, 2_050_000, SHOTS / "contacts-5173.png"),
        "images": [SHOTS / "train-5173.png", SHOTS / "logs-5173.png", SHOTS / "settings-5173.png", SHOTS / "contacts-5173.png"],
    },
    {
        "shapes": lambda: title_bar("3. 研究结论", "系统完成情况", 7)
        + rect(70, 520000, 1_050_000, 11_800_000, 5_300_000, WHITE, LINE, True)
        + text_box(71, "研究结论概括", 800000, 1_350_000, 2_500_000, 340000, 23, TEAL, True)
        + bullets(72, ["系统已完成实时检测、报警管理、历史回放、模型训练、系统配置等基础模块。", "扩展了角色权限、用户资料、报警工单、通知日志、健康报告、设备心跳等功能。", "实现报警记录、视频片段、关键帧截图、用户消息和日志审计的全流程闭环。", "项目验证表明，该设计能够满足毕业设计场景下的核心功能目标，并具备扩展基础。"], 800000, 1_850_000, 6_200_000, 2_550_000, 18)
        + rect(73, 800000, 4_850_000, 6_200_000, 1_050_000, NAVY, None, True)
        + text_box(74, "结论定位：本课题不只停留在算法验证，而是完成了一个可运行、可管理、可留证的原型系统。", 1_050_000, 5_120_000, 5_700_000, 440000, 17, WHITE, True, "ctr")
        + pic(75, "rId2", 7_700_000, 1_550_000, 3_900_000, 2_200_000, SHOTS / "login-5173.png")
        + pic(76, "rId3", 7_700_000, 4_150_000, 3_900_000, 1_850_000, SHOTS / "statistics-5173.png"),
        "images": [SHOTS / "login-5173.png", SHOTS / "statistics-5173.png"],
    },
    {
        "shapes": lambda: title_bar("3. 研究结论", "测试结果与效果分析", 8)
        + rect(80, 500000, 1_000_000, 5_700_000, 5_450_000, WHITE, LINE, True)
        + text_box(81, "测试结果", 750000, 1_250_000, 2_000_000, 340000, 23, TEAL, True)
        + bullets(82, ["登录与权限测试：管理员与普通用户菜单、接口权限控制均符合预期。", "实时检测测试：可切换视频源，支持阈值调整并能触发报警。", "报警与回放测试：报警记录、留证视频、关键帧截图与删除操作均可用。", "管理功能测试：统计分析、日志中心、模型训练与系统配置协同正常。"], 750000, 1_750_000, 5_050_000, 2_900_000, 17)
        + rect(83, 750000, 5_100_000, 5_050_000, 900000, SOFT, LINE, True)
        + text_box(84, "测试结论：系统已具备较完整的“输入-识别-显示-报警-留证-处置”能力。", 1_000_000, 5_330_000, 4_550_000, 380000, 17, NAVY, True, "ctr")
        + pic(85, "rId2", 6_850_000, 1_350_000, 5_000_000, 2_650_000, SHOTS / "statistics-5173.png")
        + pic(86, "rId3", 6_850_000, 4_300_000, 5_000_000, 1_850_000, SHOTS / "logs-5173.png"),
        "images": [SHOTS / "statistics-5173.png", SHOTS / "logs-5173.png"],
    },
    {
        "shapes": lambda: title_bar("4. 创新及不足", "项目价值与后续改进方向", 9)
        + rect(90, 600000, 1_100_000, 5_450_000, 5_000_000, WHITE, LINE, True)
        + rect(91, 6_850_000, 1_100_000, 5_450_000, 5_000_000, WHITE, LINE, True)
        + text_box(92, "创新点", 900000, 1_400_000, 1_800_000, 340000, 23, TEAL, True)
        + bullets(93, ["将跌倒检测与报警管理、历史留证、工单反馈整合为统一平台。", "采用前后端分离架构，便于界面扩展、接口维护和业务迭代。", "补充角色权限、通知日志、训练管理等工程化设计。", "围绕养老监护需求，突出“识别 + 留证 + 反馈”的业务闭环。"], 900000, 1_900_000, 4_800_000, 2_900_000, 17)
        + text_box(94, "不足与展望", 7_150_000, 1_400_000, 2_200_000, 340000, 23, ACCENT, True)
        + bullets(95, ["当前密码仍为明文存储，后续需引入哈希加密和更规范的认证机制。", "多设备并发接入、长时间稳定运行与高并发访问能力仍待增强。", "统计分析以基础数量统计为主，风险预测能力有待扩展。", "通知链路依赖第三方服务配置，跨环境部署时需要进一步标准化。"], 7_150_000, 1_900_000, 4_800_000, 2_900_000, 17)
        + rect(96, 900000, 5_250_000, 10_900_000, 760000, NAVY, None, True)
        + text_box(97, "后续可沿模型优化、安全加固、多设备协同和行为趋势预测四个方向继续深化。", 1_200_000, 5_470_000, 10_300_000, 320000, 18, WHITE, True, "ctr"),
        "images": [],
    },
    {
        "shapes": lambda: rect(100, 0, 0, W, H, NAVY)
        + rect(101, 1_500_000, 1_250_000, 10_300_000, 4_400_000, TEAL, None, True, alpha=80000)
        + text_box(102, "感谢各位老师聆听", 2_500_000, 2_300_000, 8_300_000, 700000, 34, WHITE, True, "ctr")
        + text_box(103, "恳请批评指正", 2_500_000, 3_250_000, 8_300_000, 550000, 24, GOLD, False, "ctr")
        + rect(104, 4_900_000, 4_250_000, 3_500_000, 45000, ACCENT)
        + text_box(105, "Q & A", 2_500_000, 4_650_000, 8_300_000, 700000, 30, WHITE, True, "ctr"),
        "images": [],
    },
]


def write_static(z: zipfile.ZipFile):
    z.writestr("[Content_Types].xml", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Default Extension="png" ContentType="image/png"/>
<Default Extension="jpg" ContentType="image/jpeg"/>
<Default Extension="jpeg" ContentType="image/jpeg"/>
<Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>
<Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>
<Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>
<Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>
""" + "\n".join(f'<Override PartName="/ppt/slides/slide{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>' for i in range(1, len(slides) + 1)) + """
<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>""")
    z.writestr("_rels/.rels", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>""")
    z.writestr("docProps/core.xml", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/"><dc:title>跌倒检测与事件留证系统答辩PPT</dc:title><dc:creator>Codex</dc:creator></cp:coreProperties>""")
    z.writestr("docProps/app.xml", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"><Application>Microsoft PowerPoint</Application><Slides>10</Slides></Properties>""")
    z.writestr("ppt/theme/theme1.xml", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?><a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Defense"><a:themeElements><a:clrScheme name="Defense"><a:dk1><a:srgbClr val="000000"/></a:dk1><a:lt1><a:srgbClr val="FFFFFF"/></a:lt1><a:dk2><a:srgbClr val="2F4858"/></a:dk2><a:lt2><a:srgbClr val="F7F7F5"/></a:lt2><a:accent1><a:srgbClr val="3A7D7C"/></a:accent1><a:accent2><a:srgbClr val="E07A5F"/></a:accent2><a:accent3><a:srgbClr val="F2CC8F"/></a:accent3><a:accent4><a:srgbClr val="52606D"/></a:accent4><a:accent5><a:srgbClr val="D9E2EC"/></a:accent5><a:accent6><a:srgbClr val="EEF4F3"/></a:accent6><a:hlink><a:srgbClr val="0563C1"/></a:hlink><a:folHlink><a:srgbClr val="954F72"/></a:folHlink></a:clrScheme><a:fontScheme name="Defense"><a:majorFont><a:latin typeface="Microsoft YaHei"/><a:ea typeface="Microsoft YaHei"/></a:majorFont><a:minorFont><a:latin typeface="Microsoft YaHei"/><a:ea typeface="Microsoft YaHei"/></a:minorFont></a:fontScheme><a:fmtScheme name="Defense"><a:fillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:fillStyleLst><a:lnStyleLst><a:ln w="9525"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln></a:lnStyleLst><a:effectStyleLst><a:effectStyle><a:effectLst/></a:effectStyle></a:effectStyleLst><a:bgFillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:bgFillStyleLst></a:fmtScheme></a:themeElements><a:objectDefaults/><a:extraClrSchemeLst/></a:theme>""")
    z.writestr("ppt/slideLayouts/slideLayout1.xml", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:sldLayout xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" type="blank" preserve="1"><p:cSld name="Blank"><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr/></p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sldLayout>""")
    z.writestr("ppt/slideLayouts/_rels/slideLayout1.xml.rels", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="../slideMasters/slideMaster1.xml"/></Relationships>""")
    z.writestr("ppt/slideMasters/slideMaster1.xml", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?><p:sldMaster xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"><p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr/></p:spTree></p:cSld><p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/><p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst><p:txStyles><p:titleStyle/><p:bodyStyle/><p:otherStyle/></p:txStyles></p:sldMaster>""")
    z.writestr("ppt/slideMasters/_rels/slideMaster1.xml.rels", """<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="../theme/theme1.xml"/></Relationships>""")


def build():
    media_map: dict[Path, str] = {}
    rel_targets: list[list[tuple[str, str]]] = []
    for s in slides:
        current = []
        for i, img in enumerate(s["images"], start=2):
            img = Path(img)
            if img not in media_map:
                ext = img.suffix.lower().lstrip(".") or "png"
                media_map[img] = f"image{len(media_map) + 1}.{ext}"
            current.append((f"rId{i}", media_map[img]))
        rel_targets.append(current)

    if OUT.exists():
        OUT.unlink()
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        write_static(z)
        for i, s in enumerate(slides, start=1):
            z.writestr(f"ppt/slides/slide{i}.xml", slide_xml(s["shapes"]()))
            z.writestr(f"ppt/slides/_rels/slide{i}.xml.rels", rels_xml(rel_targets[i - 1]))
        for src, target in media_map.items():
            z.write(src, f"ppt/media/{target}")
        slide_ids = "\n".join(f'<p:sldId id="{256 + i}" r:id="rId{i + 1}"/>' for i in range(1, len(slides) + 1))
        z.writestr("ppt/presentation.xml", f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"><p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1"/></p:sldMasterIdLst><p:sldIdLst>{slide_ids}</p:sldIdLst><p:sldSz cx="{W}" cy="{H}" type="wide"/><p:notesSz cx="6858000" cy="9144000"/><p:defaultTextStyle/></p:presentation>""")
        pres_rels = ['<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>']
        pres_rels.extend(f'<Relationship Id="rId{i + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide{i}.xml"/>' for i in range(1, len(slides) + 1))
        z.writestr("ppt/_rels/presentation.xml.rels", f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">{''.join(pres_rels)}</Relationships>""")
    print(OUT)


if __name__ == "__main__":
    build()

from browser_launch import launch_persistent, launch
# -*- coding: utf-8 -*-
"""
小红书 3:4 图文生产流水线 v3
- 6 套封面风格（A 黑底大字报 / B 米白宋体 / C 克莱因蓝 / D 实拍压图 / E 黑金宋体 / F 正红大字报）
- 共用同一骨架：内页统一白/米底 + 同款字体家族 + 同款强调色
- 每天一套，10 天轮换
"""
import os, asyncio, urllib.parse, json
from playwright.async_api import async_playwright

BASE = os.environ.get("XHS_HOME", os.path.expanduser("~/xhs-workspace"))
OUT = os.path.join(BASE, "output")
PHOTOS = os.path.join(BASE, "photos")
FX = os.environ.get("XHS_FONTS", os.path.join(BASE, "fonts"))

MAC_FONT_DIRS = [
    "/System/Library/Fonts",
    "/System/Library/Fonts/Supplemental",
    "/Library/Fonts",
    os.path.expanduser("~/Library/Fonts"),
]


def _mac(name):
    """在 macOS 字体目录里找同名文件（找不到返回 None）"""
    for d in MAC_FONT_DIRS:
        f = os.path.join(d, name)
        if os.path.exists(f):
            return f
    return None


def _font(name, *cands):
    for c in cands:
        if c and os.path.exists(c):
            return c
    return cands[-1]


FONT = {
    "Smiley": _font("SmileySans", os.path.join(FX, "SmileySans-Oblique.ttf")),
    "SongH": _font("SongH", os.path.join(FX, "SourceHanSerifSC-Heavy.otf"),
                   os.path.join(FX, "SourceHanSerifSC-Heavy.otf"), _mac("Songti.ttc"),
                   r"C:\Windows\Fonts\Source Han Serif SC Heavy (TrueType).ttf"),
    "SongV": _font("SongV", os.path.join(FX, "NotoSerifSC-VF.ttf"),
                   _mac("Songti.ttc"), r"C:\Windows\Fonts\NotoSerifSC-VF.ttf"),
    "HOSB": _font("HOSB", os.path.join(FX, "HarmonyOS_Sans_SC_Bold.ttf"),
                  _mac("PingFang.ttc"), r"C:\Windows\Fonts\HarmonyOS_Sans_SC_Bold.ttf"),
    "HOSM": _font("HOSM", os.path.join(FX, "HarmonyOS_Sans_SC_Medium.ttf"),
                  _mac("PingFang.ttc"), r"C:\Windows\Fonts\HarmonyOS_Sans_SC_Medium.ttf"),
    "HOSR": _font("HOSR", os.path.join(FX, "HarmonyOS_Sans_SC_Regular.ttf"),
                  _mac("PingFang.ttc"), r"C:\Windows\Fonts\HarmonyOS_Sans_SC_Regular.ttf"),
}

def _facelist():
    out = []
    for k, v in FONT.items():
        out.append("@font-face{font-family:'%s';src:url('file:///%s');}" % (k, v.replace(chr(92), "/")))
    return "".join(out)


FACES = _facelist()
def P(name):
    return "file:///" + urllib.parse.quote(os.path.join(BASE, name).replace("\\", "/"))

PHOTO = {
    1: "DSC08716-opq5036715503.jpg", 2: "DSC_5673.JPG.jpg", 3: "DSC08707-opq5036658545.jpg",
    4: "DSC_5708.JPG.jpg", 5: "DSC_5775.JPG.jpg", 6: "DSC08816-opq5036910356.jpg",
    7: "DSC_5807.JPG.jpg", 8: "DSC_5838.JPG.jpg", 9: "DSC_5677.JPG.jpg", 10: "DSC_5926.JPG.jpg",
}

# ============ 皮肤 ============

import re as _re, unicodedata as _ud
def _w(s):
    s = _re.sub(r"<[^>]+>", "", s)
    w = 0.0
    for ch in s:
        if _ud.east_asian_width(ch) in ("W", "F"):
            w += 1.0
        elif ch in " \u00b7.,:;!?/|()-\u2014":
            w += 0.34
        else:
            w += 0.56
    return w

def fit2(line, maxw, base, minv=90, ls=0):
    txt = _re.sub(r"<[^>]+>", "", line)
    n = max(len(txt), 1)
    sz = base
    while sz > minv:
        if _w(line) * sz + (n - 1) * ls <= maxw:
            break
        sz -= 2
    return sz

SKIN = {
    "A": dict(key="A", name="黑底大字报", bg="#0A0A0B", ink="#FFFFFF", dim="#6F6F6F", sub="#ABABAB",
              accent="#D9FF3E", head="Smiley", inner_bg="#FAFAF7", inner_ink="#0B0B0C",
              inner_muted="#6E6E6E", inner_accent="#D99A00", inner_mark="#FFE45C", inner_head="Smiley", inner_bar_col="#0B0B0C"),
    "B": dict(key="B", name="米白宋体", bg="#F1EADB", ink="#171310", dim="#5C5348", sub="#443C32",
              accent="#8A2B1D", head="SongH", inner_bg="#F1EADB", inner_ink="#171310",
              inner_muted="#6B6053", inner_accent="#8A2B1D", inner_mark="#E9C8C0", inner_head="SongV", inner_bar_col="#171310"),
    "C": dict(key="C", name="克莱因蓝", bg="#0B23C4", ink="#FFFFFF", dim="#AAB8F7", sub="#D3DBFF",
              accent="#E9FF3D", head="Smiley", inner_bg="#FAFAF7", inner_ink="#0B23C4",
              inner_muted="#5A6B9A", inner_accent="#0B23C4", inner_mark="#BAC8FF", inner_head="Smiley", inner_bar_col="#0B23C4"),
    "D": dict(key="D", name="实拍压图", bg="#0E0E10", ink="#FFFFFF", dim="#D8D8D8", sub="#E8E8E8",
              accent="#FFD84D", head="Smiley", inner_bg="#FAFAF7", inner_ink="#141414",
              inner_muted="#6E6E6E", inner_accent="#D97D00", inner_mark="#FFD84D", inner_head="Smiley", inner_bar_col="#141414"),
    "E": dict(key="E", name="黑金宋体", bg="#0B0B0C", ink="#F4F1EA", dim="#8C8577", sub="#B8B1A3",
              accent="#C9A96A", head="SongH", inner_bg="#F7F3EA", inner_ink="#14110D",
              inner_muted="#7A6E5F", inner_accent="#9A7B3F", inner_mark="#E6D2A6", inner_head="SongV", inner_bar_col="#14110D"),
    "F": dict(key="F", name="正红大字报", bg="#E01B12", ink="#FFFFFF", dim="#FFD9D5", sub="#FFD9D5",
              accent="#FFE14D", head="Smiley", inner_bg="#FAFAF7", inner_ink="#141414",
              inner_muted="#6E6E6E", inner_accent="#C8150D", inner_mark="#FFC9C4", inner_head="Smiley", inner_bar_col="#141414"),
}

COMMON = "*{margin:0;padding:0;box-sizing:border-box}body{width:1080px;height:1440px;overflow:hidden}" \
         ".s{position:relative;width:1080px;height:1440px;overflow:hidden;font-family:HOSM,'PingFang SC','Hiragino Sans GB','Microsoft YaHei',sans-serif}"


# ============ 封面 ============
def cover_A(sk, d):
    z1 = fit2(d["h1"], 950, 318); z2 = fit2(d["h2"], 950, 190)
    f = "".join("<span><b>%s</b>%s</span>" % (n, t) for n, t in d["facts"])
    return f"""<!doctype html><html><head><meta charset='utf-8'><style>{FACES}{COMMON}
.s{{background:{sk['bg']};color:{sk['ink']}}}
.grain{{position:absolute;inset:0;opacity:.05;background-image:radial-gradient(#fff 1px,transparent 1px);background-size:5px 5px}}
.top{{position:absolute;top:62px;left:72px;right:72px;display:flex;justify-content:space-between;font-size:21px;letter-spacing:5px;color:{sk['dim']}}}
.head{{position:absolute;top:214px;left:64px;right:64px}}
.h1{{font-family:Smiley;font-size:{z1}px;line-height:.92;letter-spacing:-6px}}
.h2{{font-family:Smiley;font-size:{z2}px;line-height:1.02;letter-spacing:-2px;margin-top:4px}}
.hl{{color:{sk['accent']}}}
.void{{position:absolute;left:72px;top:1000px;display:flex;align-items:center;gap:26px}}
.vline{{width:56px;height:2px;background:#3A3A3A}}
.vtxt{{font-size:23px;letter-spacing:4px;color:{sk['dim']};display:flex;gap:30px}}
.sub{{position:absolute;left:72px;bottom:236px;font-size:35px;line-height:1.62;color:{sk['sub']}}}
.rule{{position:absolute;left:72px;right:72px;bottom:178px;height:2px;background:#262626}}
.bottom{{position:absolute;left:72px;right:72px;bottom:92px;display:flex;justify-content:space-between;font-size:23px;letter-spacing:3px}}
.bottom .dim{{color:{sk['dim']}}}
</style></head><body><div class='s'>
<div class='grain'></div>
<div class='top'><span>{d['brandtop']}</span><span>NO.{d['no']:02d} / 10</span></div>
<div class='head'><div class='h1'>{d['h1']}</div><div class='h2'>{d['h2']}</div></div>
<div class='void'><div class='vline'></div><div class='vtxt'>{f}</div></div>
<div class='sub'>{d['sub']}</div><div class='rule'></div>
<div class='bottom'><span>{d['handle']}</span><span class='dim'>左滑看方法 →</span></div>
</div></body></html>"""


def cover_B(sk, d):
    z1 = fit2(d["h1"], 840, 238, ls=8); z2 = fit2(d["h2"], 840, 152, ls=4)
    f = "".join("<span><b>%s</b>%s</span>" % (n, t) for n, t in d["facts"])
    return f"""<!doctype html><html><head><meta charset='utf-8'><style>{FACES}{COMMON}
.s{{background:{sk['bg']};color:{sk['ink']}}}
.paper{{position:absolute;inset:0;opacity:.45;background-image:radial-gradient(#00000016 1px,transparent 1px);background-size:4px 4px}}
.frame{{position:absolute;left:46px;right:46px;top:46px;bottom:46px;border:2px solid {sk['ink']}}}
.top{{position:absolute;top:94px;left:94px;right:94px;display:flex;justify-content:space-between;font-size:19px;letter-spacing:4px;color:{sk['dim']}}}
.head{{position:absolute;top:238px;left:90px;right:90px}}
.line1{{font-family:SongV;font-weight:600;font-size:46px;letter-spacing:3px;color:{sk['accent']}}}
.h1{{font-family:SongH;font-size:{z1}px;line-height:1.02;letter-spacing:8px;margin-top:14px}}
.h2{{font-family:SongH;font-size:{z2}px;line-height:1.14;letter-spacing:4px}}
.eng{{font-family:SongV;font-weight:400;font-size:29px;letter-spacing:9px;color:{sk['dim']};margin-top:26px}}
.hl{{color:{sk['accent']}}}
.stamp{{position:absolute;right:88px;top:150px;width:104px;height:104px;border:3px solid {sk['accent']};
  display:flex;align-items:center;justify-content:center;transform:rotate(-7deg);color:{sk['accent']};
  font-family:SongV;font-weight:600;font-size:30px;line-height:1.1;text-align:center;letter-spacing:2px}}
.chain{{position:absolute;left:94px;right:94px;top:900px;font-size:25px;letter-spacing:1px;color:{sk['dim']};
  border-top:1.5px solid #B9AE9A;border-bottom:1.5px solid #B9AE9A;padding:22px 0;display:flex;justify-content:space-between}}
.chain b{{font-family:SongV;font-weight:600;color:{sk['accent']};font-weight:normal}}
.sub{{position:absolute;left:94px;right:200px;bottom:215px;font-size:34px;line-height:1.72;color:{sk['sub']};
  border-left:5px solid {sk['accent']};padding-left:26px}}
.pull{{position:absolute;right:94px;bottom:262px;font-family:HOSB;font-size:22px;letter-spacing:3px;color:{sk['accent']};
  border:1.5px solid {sk['accent']};border-radius:40px;padding:12px 24px}}
.bottom{{position:absolute;left:94px;right:94px;bottom:94px;display:flex;justify-content:space-between;
  font-size:22px;letter-spacing:3px;border-top:1.5px solid {sk['ink']};padding-top:22px}}
</style></head><body><div class='s'>
<div class='paper'></div><div class='frame'></div>
<div class='top'><span>{d['brandtop']}</span><span>VOL. {d['no']:02d} / 10</span></div>
<div class='head'><div class='line1'>{d['kicker']}</div><div class='h1'>{d['h1']}</div><div class='h2'>{d['h2']}</div>
  <div class='eng'>{d['eng']}</div></div>
<div class='stamp'>验货<br/>笔记</div>
<div class='chain'>{f}</div>
<div class='sub'>{d['sub']}</div>
<div class='pull'>左滑 →</div>
<div class='bottom'><span>{d['handle']}</span><span>{d['no']:02d} / 10</span></div>
</div></body></html>"""


def cover_C(sk, d):
    z1 = fit2(d["h1"], 950, 300); z2 = fit2(d["h2"], 950, 170)
    f = "".join("<span><b>%s</b>%s</span>" % (n, t) for n, t in d["facts"])
    return f"""<!doctype html><html><head><meta charset='utf-8'><style>{FACES}{COMMON}
.s{{background:{sk['bg']};color:{sk['ink']}}}
.ghost{{position:absolute;right:-60px;top:-120px;font-family:Smiley;font-size:640px;color:#fff;opacity:.08}}
.bar{{position:absolute;left:0;top:0;width:24px;height:100%;background:{sk['accent']}}}
.top{{position:absolute;top:70px;left:82px;right:72px;display:flex;justify-content:space-between;font-size:21px;letter-spacing:5px;color:{sk['dim']}}}
.head{{position:absolute;top:246px;left:76px;right:76px}}
.h1{{font-family:Smiley;font-size:{z1}px;line-height:.95;letter-spacing:-4px}}
.h2{{font-family:Smiley;font-size:{z2}px;line-height:1.06;margin-top:12px}}
.hl{{color:{sk['accent']}}}
.sub{{position:absolute;left:82px;bottom:240px;font-size:35px;line-height:1.62;color:{sk['sub']}}}
.stats{{position:absolute;left:82px;bottom:430px;display:flex;gap:48px}}
.stats div{{font-size:22px;letter-spacing:2px;color:{sk['dim']}}}
.stats b{{display:block;font-family:Smiley;font-size:58px;color:#fff;letter-spacing:0;margin-bottom:6px}}
.bottom{{position:absolute;left:82px;right:72px;bottom:92px;display:flex;justify-content:space-between;font-size:23px;letter-spacing:3px}}
</style></head><body><div class='s'>
<div class='ghost'>{d['no']:02d}</div><div class='bar'></div>
<div class='top'><span>{d['brandtop']}</span><span>{d['no']:02d} / 10</span></div>
<div class='head'><div class='h1'>{d['h1']}</div><div class='h2'>{d['h2']}</div></div>
<div class='stats'>{f}</div>
<div class='sub'>{d['sub']}</div>
<div class='bottom'><span>{d['handle']}</span><span>左滑 →</span></div>
</div></body></html>"""


def cover_D(sk, d):
    z1 = fit2(d["h1"], 920, 176); z2 = fit2(d["h2"], 920, 150)
    return f"""<!doctype html><html><head><meta charset='utf-8'><style>{FACES}{COMMON}
.s{{background:{sk['bg']}}}
.s img{{position:absolute;left:-6%;top:-11%;width:112%;height:118%;object-fit:cover;filter:saturate(.92) contrast(1.04)}}
.shade{{position:absolute;inset:0;background:linear-gradient(180deg,rgba(8,12,20,.62) 0%,rgba(8,12,20,.05) 30%,rgba(8,12,20,.72) 62%,rgba(8,12,20,.97) 100%)}}
.top{{position:absolute;top:60px;left:64px;right:64px;display:flex;justify-content:space-between;font-size:20px;letter-spacing:4px;color:rgba(255,255,255,.72)}}
.head{{position:absolute;left:64px;right:64px;bottom:266px}}
.h1{{font-family:Smiley;font-size:{z1}px;line-height:1;color:#fff;letter-spacing:-2px;text-shadow:0 8px 34px rgba(0,0,0,.4)}}
.h2{{font-family:Smiley;font-size:{z2}px;line-height:1.08;color:#fff;letter-spacing:-2px}}
.hl{{color:{sk['accent']}}}
.sub{{font-size:32px;line-height:1.6;color:rgba(255,255,255,.9);margin-top:26px}}
.bottom{{position:absolute;left:64px;right:64px;bottom:88px;display:flex;justify-content:space-between;align-items:center;font-size:22px;letter-spacing:3px;color:rgba(255,255,255,.95)}}
.pill{{border:1.5px solid rgba(255,255,255,.5);border-radius:40px;padding:11px 26px;font-size:21px}}
.badge{{position:absolute;left:64px;top:150px;background:{sk['accent']};color:#111;font-size:26px;letter-spacing:2px;padding:10px 22px;font-weight:600}}
</style></head><body><div class='s'>
<img src='{P(d['photo'])}'/><div class='shade'></div>
<div class='top'><span>{d['brandtop']}</span><span>NO.{d['no']:02d} / 10</span></div>
<div class='badge'>{d['kicker']}</div>
<div class='head'><div class='h1'>{d['h1']}</div><div class='h2'>{d['h2']}</div><div class='sub'>{d['sub']}</div></div>
<div class='bottom'><span>{d['handle']}</span><span class='pill'>左滑看方法 →</span></div>
</div></body></html>"""


def cover_E(sk, d):
    z1 = fit2(d["h1"], 880, 222, ls=10); z2 = fit2(d["h2"], 880, 158, ls=6)
    f = "".join("<span><b>%s</b>%s</span>" % (n, t) for n, t in d["facts"])
    return f"""<!doctype html><html><head><meta charset='utf-8'><style>{FACES}{COMMON}
.s{{background:{sk['bg']};color:{sk['ink']}}}
.top{{position:absolute;top:66px;left:74px;right:74px;display:flex;justify-content:space-between;font-size:20px;letter-spacing:6px;color:{sk['dim']}}}
.hair{{position:absolute;left:74px;right:74px;top:120px;height:1.5px;background:#4A4236}}
.head{{position:absolute;top:252px;left:74px;right:74px}}
.h1{{font-family:SongH;font-size:{z1}px;line-height:1;letter-spacing:10px}}
.h2{{font-family:SongH;font-size:{z2}px;line-height:1.16;letter-spacing:6px}}
.hl{{color:{sk['accent']}}}
.eng{{font-family:SongV;font-weight:400;font-size:30px;letter-spacing:11px;color:{sk['dim']};margin-top:30px}}
.facts{{position:absolute;left:74px;right:74px;top:1000px;font-size:24px;letter-spacing:6px;color:{sk['dim']};
  border-top:1.5px solid #2A2520;padding-top:26px;display:flex;justify-content:space-between}}
.facts b{{font-family:SongH;color:{sk['accent']};font-weight:normal;font-size:30px;margin-right:10px}}
.sub{{position:absolute;left:74px;bottom:250px;font-size:34px;line-height:1.72;color:{sk['sub']};
  border-left:4px solid {sk['accent']};padding-left:26px}}
.bottom{{position:absolute;left:74px;right:74px;bottom:92px;display:flex;justify-content:space-between;
  font-size:22px;letter-spacing:4px;color:{sk['dim']};border-top:1.5px solid #3A342B;padding-top:22px}}
</style></head><body><div class='s'>
<div class='top'><span>SIMA YUE FDE · METHOD NOTE</span><span>NO.{d['no']:02d}</span></div>
<div class='hair'></div>
<div class='head'><div class='h1'>{d['h1']}</div><div class='h2'>{d['h2']}</div><div class='eng'>{d['eng']}</div></div>
<div class='facts'>{f}</div>
<div class='sub'>{d['sub']}</div>
<div class='bottom'><span>{d['handle']}</span><span>左滑看方法 →</span></div>
</div></body></html>"""


def cover_F(sk, d):
    z1 = fit2(d["h1"], 940, 316); z2 = fit2(d["h2"], 940, 186)
    f = "".join("<span><b>%s</b>%s</span>" % (n, t) for n, t in d["facts"])
    return f"""<!doctype html><html><head><meta charset='utf-8'><style>{FACES}{COMMON}
.s{{background:{sk['bg']};color:{sk['ink']}}}
.dots{{position:absolute;inset:0;opacity:.16;background-image:radial-gradient(#fff 1.6px,transparent 1.6px);background-size:26px 26px}}
.top{{position:absolute;top:64px;left:74px;right:74px;display:flex;justify-content:space-between;font-size:21px;letter-spacing:5px;color:{sk['dim']}}}
.kicker{{position:absolute;left:74px;top:150px;font-size:24px;letter-spacing:5px;color:{sk['accent']}}}
.head{{position:absolute;top:236px;left:68px;right:68px}}
.h1{{font-family:Smiley;font-size:{z1}px;line-height:.92;letter-spacing:-4px}}
.h2{{font-family:Smiley;font-size:{z2}px;line-height:1.04;color:{sk['accent']}}}
.facts{{position:absolute;left:74px;right:74px;top:930px;display:flex;gap:56px;font-size:23px;letter-spacing:3px;color:{sk['dim']}}}
.facts b{{font-family:Smiley;font-size:60px;display:block;color:#fff;letter-spacing:0;margin-bottom:4px}}
.rule{{position:absolute;left:74px;right:74px;top:1064px;height:3px;background:rgba(255,255,255,.5)}}
.sub{{position:absolute;left:74px;right:74px;top:1110px;font-size:35px;line-height:1.6;color:{sk['sub']}}}
.bottom{{position:absolute;left:74px;right:74px;bottom:92px;display:flex;justify-content:space-between;font-size:23px;letter-spacing:3px}}
</style></head><body><div class='s'>
<div class='dots'></div>
<div class='top'><span>{d['brandtop']}</span><span>NO.{d['no']:02d} / 10</span></div>
<div class='kicker'>{d['kicker']}</div>
<div class='head'><div class='h1'>{d['h1']}</div><div class='h2'>{d['h2']}</div></div>
<div class='facts'>{f}</div><div class='rule'></div>
<div class='sub'>{d['sub']}</div>
<div class='bottom'><span>{d['handle']}</span><span>左滑看方法 →</span></div>
</div></body></html>"""

COVERS = {"A": cover_A, "B": cover_B, "C": cover_C, "D": cover_D, "E": cover_E, "F": cover_F}


# ============ 内页（统一骨架 + 皮肤） ============
def inner_css(sk):
    return f"""
.s{{background:{sk['inner_bg']};color:{sk['inner_ink']}}}
.grid{{position:absolute;inset:0;z-index:0;background-image:linear-gradient(#00000008 1.5px,transparent 1.5px),linear-gradient(90deg,#00000008 1.5px,transparent 1.5px);background-size:72px 72px}}
.top{{position:absolute;top:0;left:0;right:0;height:104px;display:flex;align-items:center;justify-content:space-between;padding:0 76px;z-index:20}}
.brand{{display:flex;align-items:center;gap:15px;font-size:26px;letter-spacing:.5px;color:{sk['inner_ink']}}}
.dot{{width:13px;height:13px;border-radius:3px;background:{sk['inner_accent']};transform:rotate(45deg)}}
.ep{{font-size:22px;color:{sk['inner_muted']};letter-spacing:4px}}
.ctext{{position:absolute;top:150px;left:76px;right:76px;z-index:5}}
.kicker{{font-size:26px;color:{sk['inner_accent']};letter-spacing:7px;margin-bottom:30px}}
h1{{font-family:{sk['inner_head']};line-height:1.2;color:{sk['inner_ink']}}}
.hl{{position:relative;display:inline-block;z-index:1}}
.hl::before{{content:'';position:absolute;left:-8px;right:-8px;bottom:12px;height:28px;background:{sk['inner_mark']};opacity:.55;z-index:-1}}
.foot{{position:absolute;left:76px;right:76px;bottom:0;height:92px;display:flex;align-items:center;justify-content:space-between;font-size:21px;color:{sk['inner_muted']};letter-spacing:1.5px;z-index:20}}
.pageno{{font-family:{sk['inner_head']};font-size:24px;color:{sk['inner_accent']};letter-spacing:2px}}
"""


def wrap(sk, inner_html, page, extra_css=""):
    return f"""<!doctype html><html><head><meta charset='utf-8'><style>{FACES}{COMMON}{inner_css(sk)}{extra_css}</style></head>
<body><div class='s'><div class='grid'></div>
<div class='top'><div class='brand'><span class='dot'></span>{sk['_handle']}</div><div class='ep'>DAY {sk['_day']:02d} &nbsp;·&nbsp; {page:02d}</div></div>
{inner_html}
<div class='foot'><span>{sk['_handle']}</span><span class='pageno'>{page:02d}</span></div>
</div></body></html>"""


def slide_quote(sk, d, page):
    css = f""".quote{{font-family:{sk['inner_head']};font-size:48px;line-height:1.5;color:{sk['inner_ink']};
  background:#fff;border:1.5px solid #E2E2E2;border-left:12px solid {sk['inner_accent']};border-radius:8px;padding:54px 56px;margin-top:56px}}
.note{{font-size:33px;line-height:1.8;color:{sk['inner_muted']};margin-top:46px}}
.lay{{position:absolute;left:76px;right:76px;top:0;bottom:0;z-index:5}}"""
    html = f"""<div class='lay'><div class='ctext'>
{top_head(sk, d['q']['kicker'], d['q']['title'])}
<div class='quote'>{d['q']['quote']}</div>
<div class='note'>{d['q']['note']}</div></div></div>"""
    return wrap(sk, html, page, css)


def slide_chain(sk, d, page):
    n = len(d["ch"]["steps"])
    if n <= 3:
        top, gap, pad, minh, fs_q, fs_a = 660, 14, 24, 118, 27, 37
    elif n == 4:
        top, gap, pad, minh, fs_q, fs_a = 566, 13, 20, 96, 26, 35
    else:
        top, gap, pad, minh, fs_q, fs_a = 522, 9, 14, 76, 23, 30
    rows = "".join(
        f"<div class='cdn'><div class='cn'>{i+1:02d}</div><div class='ck'>{s.get('q','')}</div><div class='cv'>{s['a']}</div></div>"
        for i, s in enumerate(d["ch"]["steps"]))
    css = f""".chain{{position:absolute;left:76px;right:76px;top:{top}px;z-index:4}}
.cdn{{position:relative;background:#fff;border:1.5px solid #E4E4E4;border-radius:8px;padding:{pad}px 34px {pad}px 118px;
  min-height:{minh}px;display:flex;flex-direction:column;justify-content:center}}
.cdn + .cdn{{margin-top:{gap}px}}
.cn{{position:absolute;left:34px;top:50%;transform:translateY(-50%);font-family:{sk['inner_head']};font-size:32px;color:#C3C3C3}}
.ck{{font-size:{fs_q}px;color:{sk['inner_muted']};line-height:1.25}}
.cv{{font-family:{sk['inner_head']};font-size:{fs_a}px;color:{sk['inner_ink']};line-height:1.3;margin-top:6px}}
.closing{{position:absolute;left:76px;right:76px;bottom:136px;font-size:31px;line-height:1.65;color:{sk['inner_ink']};
  background:{sk['inner_accent']}22;border-radius:8px;padding:28px 36px;z-index:4}}
.lead{{font-size:34px;line-height:1.65;color:{sk['inner_muted']};margin-top:36px}}"""
    html = f"""<div class='ctext'>{top_head(sk, d['ch']['kicker'], d['ch']['title'])}<div class='lead'>{d['ch']['lead']}</div></div>
<div class='chain'>{rows}</div><div class='closing'>{d['ch']['closing']}</div>"""
    return wrap(sk, html, page, css)


def slide_quad(sk, d, page):
    cards = "".join(f"<div class='qcard'><div class='qi'>{it['k']}</div><div class='qt'>{it['t']}</div><div class='qd'>{it['d']}</div></div>"
                    for it in d["qd"]["items"])
    css = f""".qgrid{{position:absolute;left:76px;right:76px;top:556px;display:grid;grid-template-columns:1fr 1fr;gap:22px;z-index:4}}
.qcard{{background:#fff;border:1.5px solid #E4E4E4;border-radius:10px;padding:38px 34px;min-height:216px}}
.qi{{font-family:{sk['inner_head']};font-size:27px;color:{sk['inner_accent']};letter-spacing:3px}}
.qt{{font-family:{sk['inner_head']};font-size:44px;color:{sk['inner_ink']};margin-top:16px}}
.qd{{font-size:28px;line-height:1.55;color:{sk['inner_muted']};margin-top:12px}}
.closing{{position:absolute;left:76px;right:76px;bottom:148px;font-size:32px;line-height:1.7;color:{sk['inner_ink']};
  background:{sk['inner_accent']}22;border-radius:8px;padding:30px 36px;z-index:4}}
.lead{{font-size:34px;line-height:1.65;color:{sk['inner_muted']};margin-top:36px}}"""
    html = f"""<div class='ctext'>{top_head(sk, d['qd']['kicker'], d['qd']['title'])}<div class='lead'>{d['qd']['lead']}</div></div>
<div class='qgrid'>{cards}</div><div class='closing'>{d['qd']['closing']}</div>"""
    return wrap(sk, html, page, css)


def slide_stmt(sk, d, page):
    bl = "".join(f"<li>{b}</li>" for b in d["st"]["bullets"])
    css = f""".big{{font-family:{sk['inner_head']};font-size:96px;line-height:1.18;color:{sk['inner_ink']}}}
.sub{{font-size:34px;line-height:1.7;color:{sk['inner_muted']};margin-top:42px;border-left:6px solid {sk['inner_accent']};padding-left:24px}}
.bl{{margin-top:48px;list-style:none;z-index:4}}
.bl li{{font-size:33px;line-height:1.55;color:{sk['inner_ink']};position:relative;padding-left:38px;margin-bottom:24px}}
.bl li::before{{content:'';position:absolute;left:0;top:18px;width:15px;height:15px;background:{sk['inner_accent']};border-radius:3px}}"""
    html = f"""<div class='ctext'><div class='kicker'>{d['st']['kicker']}</div>
<div class='big'>{d['st']['big']}</div><div class='sub'>{d['st']['sub']}</div>
<ul class='bl'>{bl}</ul></div>"""
    return wrap(sk, html, page, css)


def slide_cta(sk, d, page):
    c = d["cta"]
    css = f""".lead2{{font-size:33px;line-height:1.7;color:{sk['inner_muted']};margin-top:30px}}
.hook{{margin-top:44px;background:{sk['inner_ink']};border-radius:12px;padding:42px 44px;color:#fff;display:flex;align-items:center;gap:44px}}
.hlk{{font-size:30px;color:#C9C9C9;letter-spacing:4px}}
.kw{{font-family:{sk['inner_head']};font-size:60px;color:{'#FFD84D' if sk['key'] in ('A','C','D','F') else '#E8C98A'};margin-top:6px;letter-spacing:2px}}
.hld{{font-size:27px;line-height:1.6;color:#EDEDED;max-width:500px}}
.sign{{margin-top:52px;display:flex;align-items:baseline;gap:20px}}
.hname{{font-family:{sk['inner_head']};font-size:32px;color:{sk['inner_ink']}}}
.hnote{{font-size:25px;color:{sk['inner_muted']};letter-spacing:1px}}"""
    kwblock = (f"<div><div class='hlk'>评论</div><div class='kw'>{c['kw']}</div></div>" if c.get('kw') else "")
    html = f"""<div class='ctext'>{top_head(sk, c['kicker'], c['title'])}
<div class='lead2'>{c['lead']}</div>
<div class='hook'>{kwblock}<div class='hld'>{c['hook']}</div></div>
<div class='sign'><span class='hname'>{sk['_handle']}</span><span class='hnote'>{c['note']}</span></div></div>"""
    return wrap(sk, html, page, css)


def top_head(sk, kicker, lines):
    size = 82
    n = len(lines)
    if n >= 3:
        size = 68
    joined = "<br/>".join(lines)
    return f"<div class='kicker'>{kicker}</div><h1 style='font-size:{size}px'>{joined}</h1>"


# ============ 渲染 ============
async def render(day):
    sk = SKIN[day["style"]].copy()
    sk["_handle"] = day["handle"]
    sk["_day"] = day["no"]
    pages = [COVERS[day["style"]](sk, day)]
    pages.append(slide_quote(sk, day, 2))
    pages.append(slide_chain(sk, day, 3))
    pages.append(slide_quad(sk, day, 4))
    pages.append(slide_stmt(sk, day, 5))
    pages.append(slide_cta(sk, day, 6))

    folder = os.path.join(OUT, "%02d_%s_%s" % (day["no"], day["date"], day["slug"]))
    os.makedirs(folder, exist_ok=True)
    names = ["01_封面", "02_问题", "03_方法", "04_判据", "05_一句话", "06_领取"]
    paths = []
    async with async_playwright() as p:
        b = await launch(p, headless=True)
        ctx = await b.new_context(viewport={"width": 1080, "height": 1440}, device_scale_factor=2)
        pg = await ctx.new_page()
        for i, html in enumerate(pages):
            hp = os.path.join(folder, f"_p{i+1}.html")
            open(hp, "w", encoding="utf-8").write(html)
            await pg.goto("file:///" + hp.replace("\\", "/"))
            await pg.wait_for_timeout(260)
            png = os.path.join(folder, "%s_%s.png" % (day["no"], names[i]))
            await pg.screenshot(path=png, type="png")
            paths.append(png)
        await b.close()
    # 清掉中间 html
    for f in os.listdir(folder):
        if f.startswith("_p") and f.endswith(".html"):
            os.remove(os.path.join(folder, f))
    return folder, paths

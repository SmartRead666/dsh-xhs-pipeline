from browser_launch import launch_persistent, launch
# -*- coding: utf-8 -*-
"""在 render_deck 基础上扩展：4 套实拍封面 + 对应内页皮肤"""
import os, urllib.parse
import deck_core as R

BASE = R.BASE
PH = R.PHOTOS

def P2(n):
    return "file:///" + urllib.parse.quote(os.path.join(PH, n).replace("\\", "/"))

FACES = R.FACES
COMMON = R.COMMON

# ---------------- 新皮肤 ----------------
SKIN = dict(R.SKIN)
SKIN.update({
    "G": dict(key="G", name="左文右双图", bg="#0E2A47", ink="#FFFFFF", dim="#8FAFD8", sub="#C9D9F2",
              accent="#FFD84D", head="Smiley", inner_bg="#FAFAF7", inner_ink="#0B0B0C",
              inner_muted="#6E6E6E", inner_accent="#1F5AE0", inner_mark="#B9C8FF",
              inner_head="Smiley", inner_bar_col="#0B0B0C", kw_color="#FFD84D"),
    "H": dict(key="H", name="上图下文", bg="#FBFCFE", ink="#0B0B0C", dim="#5B6E86", sub="#3E5470",
              accent="#1F5AE0", head="Smiley", inner_bg="#FAFAF7", inner_ink="#0B0B0C",
              inner_muted="#6E6E6E", inner_accent="#1F5AE0", inner_mark="#B9C8FF",
              inner_head="Smiley", inner_bar_col="#0B0B0C", kw_color="#FFD84D"),
    "J": dict(key="J", name="上图下色块", bg="#0E2A47", ink="#FFFFFF", dim="#9DC0FF", sub="#C9D9F2",
              accent="#FFD84D", head="Smiley", inner_bg="#FAFAF7", inner_ink="#0B0B0C",
              inner_muted="#6E6E6E", inner_accent="#12306B", inner_mark="#FFD84D",
              inner_head="Smiley", inner_bar_col="#0B0B0C", kw_color="#FFD84D"),
    "L": dict(key="L", name="杂志封面", bg="#0B0B0C", ink="#FFFFFF", dim="#8C8577", sub="#B8B1A3",
              accent="#FFD84D", head="SongH", inner_bg="#F7F3EA", inner_ink="#14110D",
              inner_muted="#7A6E5F", inner_accent="#9A7B3F", inner_mark="#E6D2A6",
              inner_head="SongV", inner_bar_col="#14110D", kw_color="#E8C98A"),
    "I": dict(key="I", name="渐变字", bg="#050A16", ink="#FFFFFF", dim="#7E8BA8", sub="#B9C6DE",
              accent="#7FD8FF", head="Smiley", inner_bg="#FAFAF7", inner_ink="#0B0B0C",
              inner_muted="#6E6E6E", inner_accent="#1F5AE0", inner_mark="#B9C8FF",
              inner_head="Smiley", inner_bar_col="#0B0B0C", kw_color="#FFD84D"),
})


# ---------------- 实拍封面 ----------------
def cover_G(sk, d):
    f = "".join("<div><b>%s</b>%s</div>" % (n, t) for n, t in d["facts"])
    return f"""<!doctype html><html><head><meta charset='utf-8'><style>{FACES}{COMMON}
.s{{background:{sk['bg']};color:#fff}}
.photo{{position:absolute;right:0;top:0;width:540px;height:1440px;display:flex;flex-direction:column;gap:6px}}
.photo .p1{{height:1010px;position:relative;overflow:hidden}}
.photo .p2{{height:424px;position:relative;overflow:hidden}}
.photo img{{width:100%;height:100%;object-fit:cover;object-position:center 36%;filter:saturate(.92) contrast(1.03)}}
.photo .p2 img{{object-position:center 48%}}
.photo .g{{position:absolute;inset:0;background:linear-gradient(90deg,rgba(14,42,71,.5),rgba(14,42,71,0) 28%)}}
.tag{{position:absolute;right:26px;top:44px;background:rgba(0,0,0,.55);color:#fff;font-size:19px;letter-spacing:2px;padding:9px 16px;z-index:3}}
.left{{position:absolute;left:0;top:0;width:540px;height:1440px;padding:66px 0 0 64px;color:#fff}}
.brand{{font-size:19px;letter-spacing:3px;color:{sk['dim']}}}
.kick{{font-size:21px;letter-spacing:6px;color:#7FD8FF;margin-top:104px}}
.h1{{font-family:Smiley;font-size:{R.fit2(d['h1'], 396, 118, 40)}px;line-height:1;margin-top:20px}}
.h2{{font-family:Smiley;font-size:{R.fit2(d['h2'], 396, 86, 40)}px;line-height:1.12;margin-top:4px;color:{sk['accent']}}}
.sub{{font-size:25px;line-height:1.66;color:{sk['sub']};margin-top:38px}}
.facts{{position:absolute;left:64px;bottom:190px}}
.facts div{{font-size:20px;color:{sk['dim']};margin-bottom:12px}}
.facts b{{font-family:Smiley;font-size:38px;color:#fff;margin-right:10px}}
.bot{{position:absolute;left:64px;bottom:96px;font-size:19px;letter-spacing:2px;color:#7396C4}}
</style></head><body><div class='s'>
<div class='photo'><div class='p1'><img src='{P2(d['photo'])}'/><div class='g'></div></div>
  <div class='p2'><img src='{P2(d.get('photo2') or d['photo'])}'/></div></div>
<div class='tag'>课堂实拍</div>
<div class='left'><div class='brand'>{d['brandtop']}</div><div class='kick'>{d['kicker']}</div>
  <div class='h1'>{d['h1']}</div><div class='h2'>{d['h2']}</div><div class='sub'>{d['sub']}</div></div>
<div class='facts'>{f}</div>
<div class='bot'>{d['handle']} · 左滑看方法 →</div>
</div></body></html>"""


def cover_H(sk, d):
    f = "".join("<div><b>%s</b>%s</div>" % (n, t) for n, t in d["facts"])
    return f"""<!doctype html><html><head><meta charset='utf-8'><style>{FACES}{COMMON}
.s{{background:#FBFCFE}}
.photo{{position:absolute;left:0;top:0;width:1080px;height:790px;overflow:hidden}}
.photo img{{width:100%;height:100%;object-fit:cover;object-position:center 45%;filter:saturate(.95) contrast(1.03)}}
.photo .shade{{position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.34) 0%,rgba(0,0,0,0) 26%,rgba(251,252,254,.10) 86%,#FBFCFE 100%)}}
.top{{position:absolute;left:64px;right:64px;top:50px;display:flex;justify-content:space-between;font-size:20px;letter-spacing:3px;color:rgba(255,255,255,.92);z-index:3}}
.badge{{position:absolute;left:64px;top:116px;background:{sk['accent']};color:#111;font-size:22px;letter-spacing:2px;padding:10px 20px;z-index:3}}
.bottom{{position:absolute;left:0;bottom:0;width:1080px;height:690px;padding:30px 68px 0;background:#FBFCFE}}
.kick{{font-size:21px;letter-spacing:6px;color:{sk['accent']}}}
.h1{{font-family:Smiley;font-size:{R.fit2(d['h1'], 930, 236, 40)}px;line-height:.9;color:#0B0B0C;margin-top:6px;letter-spacing:-4px}}
.h2{{font-family:Smiley;font-size:104px;line-height:1.08;color:#0B0B0C}}
.hl{{color:{sk['accent']}}}
.sub{{font-size:26px;line-height:1.6;color:{sk['sub']};margin-top:18px}}
.facts{{position:absolute;right:68px;bottom:36px;display:flex;gap:34px}}
.facts div{{font-size:18px;color:{sk['dim']};text-align:right}}
.facts b{{display:block;font-family:Smiley;font-size:38px;color:{sk['accent']}}}
.bot{{position:absolute;left:68px;bottom:40px;font-size:18px;letter-spacing:2px;color:#93A3B8}}
</style></head><body><div class='s'>
<div class='photo'><img src='{P2(d['photo'])}'/><div class='shade'></div></div>
<div class='top'><span>{d['brandtop']}</span><span>NO.{d['no']:02d} / 10</span></div>
<div class='badge'>第 {d['no']} 讲 · 课堂实拍</div>
<div class='bottom'><div class='kick'>{d['kicker']}</div><div class='h1'>{d['h1']}</div>
  <div class='h2'>{d['h2']}</div><div class='sub'>{d['sub']}</div>
  <div class='bot'>{d['handle']}</div><div class='facts'>{f}</div></div>
</div></body></html>"""


def cover_J(sk, d):
    f = "".join("<div><b>%s</b>%s</div>" % (n, t) for n, t in d["facts"])
    return f"""<!doctype html><html><head><meta charset='utf-8'><style>{FACES}{COMMON}
.s{{background:#0E2A47}}
.photo{{position:absolute;left:0;top:0;width:1080px;height:742px;overflow:hidden}}
.photo img{{width:100%;height:100%;object-fit:cover;object-position:center 42%;filter:saturate(.92) contrast(1.04)}}
.photo .shade{{position:absolute;inset:0;background:linear-gradient(180deg,rgba(6,16,32,.4),rgba(6,16,32,0) 40%)}}
.block{{position:absolute;left:0;bottom:0;width:1080px;height:758px;background:#12306B;color:#fff;padding:54px 70px 0;z-index:2}}
.kick{{font-size:22px;letter-spacing:7px;color:#9DC0FF}}
.h1{{font-family:Smiley;font-size:{R.fit2(d['h1'], 930, 206, 40)}px;line-height:.92;margin-top:8px}}
.h2{{font-family:Smiley;font-size:112px;line-height:1.06;color:{sk['accent']}}}
.hl{{color:{sk['accent']}}}
.sub{{font-size:27px;line-height:1.6;color:{sk['sub']};margin-top:24px}}
.statrow{{position:absolute;left:70px;bottom:44px;display:flex;gap:40px;align-items:flex-end}}
.statrow div{{font-size:18px;color:#9DC0FF}}
.statrow b{{font-family:Smiley;font-size:38px;color:#fff;display:block;margin-bottom:2px}}
.bot{{position:absolute;right:70px;bottom:48px;font-size:18px;letter-spacing:2px;color:#8FAFD8}}
.top{{position:absolute;left:70px;right:70px;top:44px;display:flex;justify-content:space-between;font-size:19px;letter-spacing:3px;color:rgba(255,255,255,.85);z-index:3}}
</style></head><body><div class='s'>
<div class='photo'><img src='{P2(d['photo'])}'/><div class='shade'></div></div>
<div class='top'><span>{d['brandtop']}</span><span>NO.{d['no']:02d} / 10</span></div>
<div class='block'><div class='kick'>{d['kicker']}</div><div class='h1'>{d['h1']}</div>
  <div class='h2'>{d['h2']}</div><div class='sub'>{d['sub']}</div>
  <div class='statrow'>{f}</div><div class='bot'>{d['handle']} · 左滑 →</div></div>
</div></body></html>"""


def cover_L(sk, d):
    return f"""<!doctype html><html><head><meta charset='utf-8'><style>{FACES}{COMMON}
.s{{background:#0B0B0C}}
.photo{{position:absolute;inset:0;overflow:hidden}}
.photo img{{width:100%;height:100%;object-fit:cover;object-position:center 24%;filter:saturate(.9) contrast(1.05)}}
.photo .shade{{position:absolute;inset:0;background:linear-gradient(180deg,rgba(6,12,22,.5) 0%,rgba(6,12,22,.04) 26%,rgba(6,12,22,.5) 64%,rgba(6,12,22,.95) 100%)}}
.frame{{position:absolute;left:34px;right:34px;top:34px;bottom:34px;border:1.5px solid rgba(255,255,255,.5)}}
.top{{position:absolute;left:64px;right:64px;top:60px;display:flex;justify-content:space-between;font-size:19px;letter-spacing:5px;color:rgba(255,255,255,.9);z-index:3}}
.head{{position:absolute;left:64px;right:64px;bottom:188px;z-index:3}}
.kick{{font-size:20px;letter-spacing:7px;color:{sk['accent']}}}
.h1{{font-family:SongH;font-size:{R.fit2(d['h1'], 930, 224, 40, ls=6)}px;line-height:1;color:#fff;letter-spacing:6px;margin-top:12px}}
.h2{{font-family:SongH;font-size:120px;line-height:1.1;color:#fff;letter-spacing:4px}}
.hl{{color:{sk['accent']}}}
.sub{{font-size:26px;line-height:1.6;color:rgba(255,255,255,.86);margin-top:22px;border-left:3px solid {sk['accent']};padding-left:20px}}
.bot{{position:absolute;left:64px;right:64px;bottom:76px;display:flex;justify-content:space-between;font-size:19px;letter-spacing:4px;color:rgba(255,255,255,.8);z-index:3}}
</style></head><body><div class='s'>
<div class='photo'><img src='{P2(d['photo'])}'/><div class='shade'></div></div>
<div class='frame'></div>
<div class='top'><span>{d['brandtop']}</span><span>NO.{d['no']:02d} / 10</span></div>
<div class='head'><div class='kick'>{d['kicker']}</div><div class='h1'>{d['h1']}</div>
  <div class='h2'>{d['h2']}</div><div class='sub'>{d['sub']}</div></div>
<div class='bot'><span>{d['handle']}</span><span>左滑看方法 →</span></div>
</div></body></html>"""


def cover_I(sk, d):
    f = "".join("<div><b>%s</b>%s</div>" % (n, t) for n, t in d["facts"])
    return f"""<!doctype html><html><head><meta charset='utf-8'><style>{FACES}{COMMON}
.s{{background:#050A16}}
.bg{{position:absolute;inset:0;overflow:hidden}}
.bg img{{width:100%;height:100%;object-fit:cover;filter:blur(34px) saturate(.35) brightness(.42);transform:scale(1.2)}}
.bg .veil{{position:absolute;inset:0;background:
  radial-gradient(90% 60% at 20% 12%,rgba(31,90,224,.55),transparent 62%),
  radial-gradient(70% 50% at 90% 88%,rgba(255,138,61,.22),transparent 60%),
  linear-gradient(180deg,rgba(4,8,16,.55),rgba(4,8,16,.9))}}
.top{{position:absolute;left:70px;right:70px;top:58px;display:flex;justify-content:space-between;font-size:20px;letter-spacing:4px;color:rgba(255,255,255,.72)}}
.mid{{position:absolute;left:66px;right:66px;top:206px}}
.kick{{font-size:23px;letter-spacing:8px;color:{sk['accent']}}}
.h1{{font-family:Smiley;font-size:{R.fit2(d['h1'], 940, 320, 40)}px;line-height:.88;letter-spacing:-8px;
  background:linear-gradient(100deg,#3E8BFF 0%,#7FE3FF 52%,#FFFFFF 100%);
  -webkit-background-clip:text;background-clip:text;color:transparent}}
.h2{{font-family:Smiley;font-size:{R.fit2(d['h2'], 940, 158, 40)}px;line-height:1.02;margin-top:8px;
  background:linear-gradient(100deg,#FFD84D 0%,#FF7A2F 100%);
  -webkit-background-clip:text;background-clip:text;color:transparent}}
.sub{{font-size:32px;line-height:1.6;color:rgba(255,255,255,.8);margin-top:34px;max-width:860px}}
.hr{{position:absolute;left:70px;right:70px;bottom:236px;height:1px;background:rgba(255,255,255,.16)}}
.facts{{position:absolute;left:70px;right:70px;bottom:170px;display:flex;gap:52px;font-size:20px;color:rgba(255,255,255,.58)}}
.facts b{{font-family:Smiley;font-size:46px;color:#fff;display:block;margin-bottom:2px}}
.bot{{position:absolute;left:70px;right:70px;bottom:88px;display:flex;justify-content:space-between;font-size:21px;letter-spacing:3px;color:rgba(255,255,255,.86)}}
</style></head><body><div class='s'>
<div class='bg'><img src='{P2(d['photo'])}'/><div class='veil'></div></div>
<div class='top'><span>{d['brandtop']}</span><span>NO.{d['no']:02d} / 10</span></div>
<div class='mid'><div class='kick'>{d['kicker']}</div><div class='h1'>{d['h1']}</div>
  <div class='h2'>{d['h2']}</div><div class='sub'>{d['sub']}</div></div>
<div class='hr'></div><div class='facts'>{f}</div>
<div class='bot'><span>{d['handle']}</span><span>左滑看方法 →</span></div>
</div></body></html>"""


COVERS = dict(R.COVERS)
COVERS.update({"G": cover_G, "H": cover_H, "J": cover_J, "L": cover_L, "I": cover_I})


def slide_cta(sk, d, page):
    c = d["cta"]
    kwc = sk.get("kw_color", "#E8C98A")
    css = f""".lead2{{font-size:33px;line-height:1.7;color:{sk['inner_muted']};margin-top:30px}}
.hook{{margin-top:44px;background:{sk['inner_ink']};border-radius:12px;padding:42px 44px;color:#fff;display:flex;align-items:center;gap:44px}}
.hlk{{font-size:30px;color:#C9C9C9;letter-spacing:4px}}
.kw{{font-family:{sk['inner_head']};font-size:60px;color:{kwc};margin-top:6px;letter-spacing:2px}}
.hld{{font-size:27px;line-height:1.6;color:#EDEDED;max-width:500px}}
.sign{{margin-top:52px;display:flex;align-items:baseline;gap:20px}}
.hname{{font-family:{sk['inner_head']};font-size:32px;color:{sk['inner_ink']}}}
.hnote{{font-size:25px;color:{sk['inner_muted']};letter-spacing:1px}}"""
    kwblock = (f"<div><div class='hlk'>评论</div><div class='kw'>{c['kw']}</div></div>" if c.get('kw') else "")
    html = f"""<div class='ctext'>{R.top_head(sk, c['kicker'], c['title'])}
<div class='lead2'>{c['lead']}</div>
<div class='hook'>{kwblock}<div class='hld'>{c['hook']}</div></div>
<div class='sign'><span class='hname'>{sk['_handle']}</span><span class='hnote'>{c['note']}</span></div></div>"""
    return R.wrap(sk, html, page, css)


async def render(day):
    sk = SKIN[day["style"]].copy()
    sk["_handle"] = day["handle"]
    sk["_day"] = day["no"]
    pages = [COVERS[day["style"]](sk, day)]
    pages.append(R.slide_quote(sk, day, 2))
    pages.append(R.slide_chain(sk, day, 3))
    pages.append(R.slide_quad(sk, day, 4))
    pages.append(R.slide_stmt(sk, day, 5))
    pages.append(slide_cta(sk, day, 6))

    folder = os.path.join(R.OUT, "%02d_%s_%s" % (day["no"], day["date"], day["slug"]))
    os.makedirs(folder, exist_ok=True)
    names = ["01_封面", "02_问题", "03_方法", "04_判据", "05_一句话", "06_领取"]
    from playwright.async_api import async_playwright
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
            png = os.path.join(folder, "%d_%s.png" % (day["no"], names[i]))
            await pg.screenshot(path=png, type="png")
            paths.append(png)
        await b.close()
    for f in os.listdir(folder):
        if f.startswith("_p") and f.endswith(".html"):
            os.remove(os.path.join(folder, f))
    return folder, paths

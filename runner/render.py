from browser_launch import launch_persistent, launch
# -*- coding: utf-8 -*-
"""
渲染一天的内容成 6 张 3:4 图 + 发布包

用法:
  python render.py --account peter --day examples/day01.json
  python render.py --account peter --day day.json --out D:/tmp/x
"""
import argparse, json, os, sys, asyncio

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def load_config(path=None):
    cfg = path or os.environ.get("XHS_CONFIG") or os.path.join(os.path.dirname(HERE), "config.json")
    if not os.path.exists(cfg):
        raise SystemExit("找不到配置文件：%s（先运行 setup.py 或复制 config.example.json）" % cfg)
    return json.load(open(cfg, encoding="utf-8")), os.path.dirname(os.path.abspath(cfg))


def find_account(cfg, slug):
    for a in cfg.get("accounts", []):
        if a.get("slug") == slug:
            return a
    raise SystemExit("配置里没有账号：%s" % slug)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--account", required=True)
    ap.add_argument("--day", required=True)
    ap.add_argument("--out", default="")
    ap.add_argument("--config", default="")
    args = ap.parse_args()

    cfg, root = load_config(args.config)
    acc = find_account(cfg, args.account)
    home = os.path.expanduser(cfg.get("home") or "~/xhs-workspace")
    os.environ["XHS_HOME"] = home
    if cfg.get("fonts_dir"):
        os.environ["XHS_FONTS"] = os.path.expanduser(cfg["fonts_dir"])

    import deck_core as C
    import deck_photo as P

    day = json.load(open(args.day, encoding="utf-8"))

    # —— 合规自检：出图前先卡一遍，避免生成违规结构 ——
    from compliance_check import check, format_report
    hits = check(day)
    print(format_report(hits), flush=True)
    blocking = [h for h in hits if h["level"] == "block"]
    if blocking and os.environ.get("XHS_FORCE") != "1":
        print("\n出图已中止：先按上面的建议改文案（确定要出图可加环境变量 XHS_FORCE=1）", flush=True)
        raise SystemExit(4)

    day.setdefault("handle", acc.get("handle") or acc.get("name"))
    day.setdefault("brandtop", acc.get("brand") or "FDE 实战营 · 验货笔记")
    day.setdefault("h2", day.get("h2", ""))

    style = day.get("style", "A")
    out_root = args.out or os.path.join(home, "output", acc["slug"])
    folder = os.path.join(out_root, "%02d_%s_%s" % (day["no"], day["date"], day["slug"]))
    os.makedirs(folder, exist_ok=True)

    async def run():
        pages = []
        sk = P.SKIN.get(style) or C.SKIN[style]
        sk = dict(sk)
        sk["_handle"] = day["handle"]
        sk["_day"] = day["no"]
        covers = P.COVERS if style in P.COVERS else C.COVERS
        pages.append(covers[style](sk, day))
        pages.append(C.slide_quote(sk, day, 2))
        pages.append(C.slide_chain(sk, day, 3))
        pages.append(C.slide_quad(sk, day, 4))
        pages.append(C.slide_stmt(sk, day, 5))
        pages.append(P.slide_cta(sk, day, 6))

        from playwright.async_api import async_playwright
        names = ["01_封面", "02_问题", "03_方法", "04_判据", "05_一句话", "06_领取"]
        paths = []
        async with async_playwright() as p:
            b = await launch(p, headless=True)
            ctx = await b.new_context(viewport={"width": 1080, "height": 1440}, device_scale_factor=2)
            pg = await ctx.new_page()
            for i, html in enumerate(pages):
                hp = os.path.join(folder, "_p%d.html" % (i + 1))
                open(hp, "w", encoding="utf-8").write(html)
                await pg.goto("file:///" + hp.replace("\\", "/"))
                await pg.wait_for_timeout(280)
                png = os.path.join(folder, "%d_%s.png" % (day["no"], names[i]))
                await pg.screenshot(path=png, type="png")
                paths.append(png)
            await b.close()
        for f in os.listdir(folder):
            if f.startswith("_p") and f.endswith(".html"):
                os.remove(os.path.join(folder, f))
        return paths

    paths = asyncio.run(run())

    # 发布包
    post = day.get("post") or {}
    pkg = {
        "account": acc.get("name"), "day": day["no"], "date": day["date"],
        "time": day.get("time", acc.get("default_time", "17:30")),
        "style": style,
        "title": post.get("title", ""), "body": post.get("body", ""),
        "tags": post.get("tags", []), "pinned_comment": post.get("pinned", ""),
        "images": [os.path.basename(p) for p in paths],
    }
    json.dump(pkg, open(os.path.join(folder, "publish.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    md = "# Day %02d · %s · 风格 %s\n\n## 标题\n**%s**（%d 字）\n\n## 正文\n%s\n\n## 标签\n%s\n\n## 置顶评论\n%s\n" % (
        day["no"], day["date"], style, pkg["title"], len(pkg["title"]), pkg["body"],
        " ".join("#" + t for t in pkg["tags"]), pkg["pinned_comment"])
    open(os.path.join(folder, "post.md"), "w", encoding="utf-8").write(md)

    print("OK", folder)
    for p in paths:
        print("  ", os.path.basename(p))


if __name__ == "__main__":
    main()

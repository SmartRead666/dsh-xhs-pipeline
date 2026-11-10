from browser_launch import launch_persistent, launch
# -*- coding: utf-8 -*-
"""
无头登录 sidecar：后台打开登录页，把二维码区域截图写到 state 目录；登录成功后写状态。
面板通过 /api/login-qr、/api/login-status 读取，全程不需要弹外部浏览器。

用法:
  python qr_login.py --account peter --site creator --state <dir> [--profile <dir>]
"""
import argparse, asyncio, json, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from xcfg import load_config, find_account, home_of, profile_of  # noqa

FIND_QR = """() => {
    let best = null;
    const vw = window.innerWidth, vh = window.innerHeight;
    for (const e of document.querySelectorAll('canvas, img, div')) {
        const r = e.getBoundingClientRect();
        if (r.width < 140 || r.width > 340) continue;
        if (Math.abs(r.width - r.height) > 10) continue;
        if (r.x < vw * 0.5) continue;            // 二维码在右半区
        if (r.top < 60 || r.bottom > vh - 20) continue;
        if (String(e.className).includes('circle')) continue;
        if (!best || r.width > best.w) best = { x: r.x, y: r.y, w: r.width, h: r.height };
    }
    return best;
}"""


def write_status(state, obj):
    tmp = os.path.join(state, "status.tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False)
    os.replace(tmp, os.path.join(state, "status.json"))


async def run(acc, site, state, profile):
    from playwright.async_api import async_playwright
    url = "https://creator.xiaohongshu.com/login" if site == "creator" else "https://www.xiaohongshu.com/login"
    qr_path = os.path.join(state, "qr.png")
    write_status(state, {"state": "starting", "ts": time.time()})
    async with async_playwright() as p:
        ctx = await launch_persistent(p, 
            profile, headless=True,
            viewport={"width": 1280, "height": 900},
            args=["--disable-blink-features=AutomationControlled"])
        await ctx.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")
        pg = ctx.pages[0] if ctx.pages else await ctx.new_page()
        await pg.goto(url, wait_until="domcontentloaded", timeout=60000)
        await pg.wait_for_timeout(3500)

        # 创作中心默认短信登录，点右上角二维码图标切到扫码
        if site == "creator":
            try:
                img = pg.locator("img.css-wemwzq").first
                if await img.count() > 0:
                    await img.click(force=True)
                    await pg.wait_for_timeout(1800)
            except Exception as e:
                print("qr toggle err", e, flush=True)

        write_status(state, {"state": "waiting", "ts": time.time(), "url": pg.url})
        deadline = time.time() + 600
        while time.time() < deadline:
            if "/login" not in pg.url:
                write_status(state, {"state": "ok", "ts": time.time(), "url": pg.url})
                await pg.wait_for_timeout(1200)
                break
            try:
                tmp = qr_path + ".tmp.png"
                box = None
                try:
                    box = await pg.evaluate(FIND_QR)
                except Exception:
                    box = None
                if box and box.get("w", 0) > 120:
                    pad = 18
                    await pg.screenshot(path=tmp, clip={
                        "x": max(0, box["x"] - pad), "y": max(0, box["y"] - pad),
                        "width": min(box["w"] + pad * 2, 1280), "height": min(box["h"] + pad * 2, 900)})
                else:
                    await pg.screenshot(path=tmp, clip={"x": 820, "y": 240, "width": 460, "height": 460})
                os.replace(tmp, qr_path)
            except Exception:
                pass
            await pg.wait_for_timeout(2000)
        else:
            write_status(state, {"state": "timeout", "ts": time.time()})
        await ctx.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--account", required=True)
    ap.add_argument("--site", choices=["creator", "main"], required=True)
    ap.add_argument("--state", required=True)
    ap.add_argument("--profile", default="")
    ap.add_argument("--config", default="")
    a = ap.parse_args()
    cfg, _ = load_config(a.config)
    acc = find_account(cfg, a.account)
    os.makedirs(a.state, exist_ok=True)
    prof = a.profile or profile_of(cfg, acc)
    asyncio.run(run(acc, a.site, a.state, prof))


if __name__ == "__main__":
    main()

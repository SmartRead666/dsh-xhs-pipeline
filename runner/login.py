from browser_launch import launch_persistent, launch
# -*- coding: utf-8 -*-
"""
登录（首次使用跑一次，之后登录态保存在该账号的浏览器目录里）

用法:
  python login.py --account peter            # 登录创作中心（发布用）
  python login.py --account peter --main     # 登录主站（看评论/私信用）
"""
import argparse, asyncio, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from xcfg import load_config, find_account, home_of, profile_of  # noqa


async def run(cfg, acc, main_site):
    from playwright.async_api import async_playwright
    prof = profile_of(cfg, acc)
    os.makedirs(prof, exist_ok=True)
    url = ("https://www.xiaohongshu.com/login" if main_site
           else "https://creator.xiaohongshu.com/login")
    async with async_playwright() as p:
        ctx = await launch_persistent(p, 
            prof, headless=False,
            viewport={"width": 1440, "height": 940},
            args=["--disable-blink-features=AutomationControlled", "--window-size=1440,940"])
        await ctx.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")
        pg = ctx.pages[0] if ctx.pages else await ctx.new_page()
        await pg.goto(url, wait_until="domcontentloaded", timeout=60000)
        await pg.wait_for_timeout(4000)
        print("请在弹出的窗口扫码登录（最长等 10 分钟）", flush=True)
        ok = False
        for i in range(200):
            if "/login" not in pg.url:
                ok = True
                break
            await pg.wait_for_timeout(3000)
        print("LOGIN_OK" if ok else "LOGIN_TIMEOUT", flush=True)
        await pg.wait_for_timeout(2500)
        await ctx.close()
        return 0 if ok else 3


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--account", required=True)
    ap.add_argument("--main", action="store_true", help="登录主站（评论/私信）")
    ap.add_argument("--config", default="")
    a = ap.parse_args()
    cfg, root = load_config(a.config)
    acc = find_account(cfg, a.account)
    sys.exit(asyncio.run(run(cfg, acc, a.main)))


if __name__ == "__main__":
    main()

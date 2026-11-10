from browser_launch import launch_persistent, launch
# -*- coding: utf-8 -*-
"""
同步平台状态到本地 publish.json
- 打开创作中心「笔记管理」，按标题匹配本地发布包
- 平台状态：未通过 / 审核中 / 定时发布 HH:MM / 已发布（显示发布时间）
用法: python sync_status.py --account peter
"""
import argparse, asyncio, glob, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from xcfg import load_config, find_account, home_of, profile_of  # noqa

TIME_RE = re.compile(r"(20\d{2}-\d{2}-\d{2} \d{2}:\d{2})")


async def fetch(pg):
    await pg.goto("https://creator.xiaohongshu.com/new/note-manager",
                  wait_until="domcontentloaded", timeout=60000)
    await pg.wait_for_timeout(6000)
    if "/login" in pg.url:
        return None
    return await pg.evaluate("""() => [...document.querySelectorAll('.note-card')].map(el => (el.innerText || '').trim())""")


def parse_card(text):
    lines = [x.strip() for x in text.split("\n") if x.strip()]
    status = None
    when = ""
    title = ""
    for ln in lines:
        if ln in ("未通过", "审核中", "已发布"):
            status = {"未通过": "rejected", "审核中": "reviewing", "已发布": "published"}[ln]
            continue
        if ln.startswith("定时发布"):
            status = "scheduled"
            continue
        m = TIME_RE.search(ln)
        if m and len(ln) <= 22:
            when = m.group(1)
            continue
        if not title and not ln.startswith("查看修改建议") and not re.fullmatch(r"[\d\s]+", ln):
            title = ln
    if status is None:
        status = "published" if when else "unknown"
    return title, status, when


async def run(cfg, acc):
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        ctx = await launch_persistent(p, 
            profile_of(cfg, acc), headless=True,
            viewport={"width": 1560, "height": 1000},
            args=["--disable-blink-features=AutomationControlled"])
        await ctx.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")
        pg = ctx.pages[0] if ctx.pages else await ctx.new_page()
        cards = await fetch(pg)
        await ctx.close()

    if cards is None:
        print("NEED_LOGIN")
        return 2

    remote = []
    for c in cards:
        t, st, when = parse_card(c)
        if t:
            remote.append({"title": t, "status": st, "when": when})

    home = home_of(cfg)
    changed = []
    for pj in glob.glob(os.path.join(home, "output", acc["slug"], "*", "publish.json")):
        data = json.load(open(pj, encoding="utf-8"))
        title = data.get("title", "")
        hit = None
        for r in remote:
            if r["title"] == title or (title and (title in r["title"] or r["title"] in title)):
                hit = r
                break
        if not hit:
            continue
        new_status = hit["status"]
        if new_status == "scheduled":
            data["status"] = "scheduled"
            data["scheduled_at"] = hit["when"]
        elif new_status == "published":
            data["status"] = "published"
            data["scheduled_at"] = hit["when"]
        elif new_status in ("rejected", "reviewing"):
            data["status"] = new_status
            if hit["when"]:
                data["checked_at"] = hit["when"]
        old = data.get("status")
        json.dump(data, open(pj, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=2)
        if old != data.get("status"):
            changed.append((os.path.basename(os.path.dirname(pj)), old, data.get("status"), hit["when"]))

    print("远程笔记 %d 条，本地更新 %d 条" % (len(remote), len(changed)))
    for c in changed:
        print("  %s: %s -> %s %s" % c)
    for r in remote:
        print("  [%s] %s %s" % (r["status"], r["title"], r["when"]))
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--account", required=True)
    ap.add_argument("--config", default="")
    a = ap.parse_args()
    cfg, _ = load_config(a.config)
    acc = find_account(cfg, a.account)
    sys.exit(asyncio.run(run(cfg, acc)))


if __name__ == "__main__":
    main()

from browser_launch import launch_persistent, launch
# -*- coding: utf-8 -*-
"""
改期 / 立即发布 / 重新提交
- 通过「笔记管理 → 编辑」进入发布页（带原内容）
- --time "YYYY-MM-DD HH:MM"  改定时时间
- --now                      关掉定时，立即发布
用法:
  python reschedule.py --account peter --title "AI项目ROI别只算省人" --time "2026-11-17 18:00"
  python reschedule.py --account peter --title "..." --now
"""
import argparse, asyncio, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from xcfg import load_config, find_account, home_of, profile_of  # noqa


async def need_verify(pg):
    try:
        return await pg.evaluate("() => document.body.innerText.includes('扫码验证')")
    except Exception:
        return False


async def wait_verify(pg, timeout=300):
    for _ in range(timeout // 3):
        body = ""
        try:
            body = await pg.evaluate("() => document.body.innerText")
        except Exception:
            pass
        if "扫码验证" not in body:
            return True
        if "已过期" in body:
            try:
                await pg.mouse.click(780, 540)
            except Exception:
                pass
        await pg.wait_for_timeout(3000)
    return False


async def click_submit(pg, labels):
    # 底部提交按钮在自定义元素 xhs-publish-btn 里（closed shadow DOM），用几何定位点它
    rect = await pg.evaluate("""() => {
        const el = document.querySelector('xhs-publish-btn');
        if (!el) return null;
        const r = el.getBoundingClientRect();
        return { x: r.x, y: r.y, w: r.width, h: r.height };
    }""")
    if rect and rect.get('w', 0) > 100:
        await pg.mouse.click(rect['x'] + rect['w'] * 0.63, rect['y'] + 48)
        return 'geometry'
    for label in labels:
        try:
            loc = pg.get_by_text(label, exact=True)
            if await loc.count() > 0:
                await loc.last.click(force=True, timeout=6000)
                return label
        except Exception:
            continue
    await pg.mouse.click(818, 918)
    return 'coord'


async def run(cfg, acc, title, when, now):
    from playwright.async_api import async_playwright
    prof = profile_of(cfg, acc)
    async with async_playwright() as p:
        ctx = await launch_persistent(p, 
            prof, headless=False,
            viewport={"width": 1560, "height": 1000},
            args=["--disable-blink-features=AutomationControlled", "--window-size=1560,1000"])
        await ctx.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")
        pg = ctx.pages[0] if ctx.pages else await ctx.new_page()
        await pg.goto("https://creator.xiaohongshu.com/new/note-manager",
                      wait_until="domcontentloaded", timeout=60000)
        await pg.wait_for_timeout(6000)
        if "/login" in pg.url:
            print("NEED_LOGIN")
            await ctx.close(); return 2

        # 找到标题匹配的卡片，点第二个操作按钮（编辑）
        ok = await pg.evaluate("""(title) => {
            const cards = [...document.querySelectorAll('.note-card')];
            for (const el of cards) {
                const t = (el.innerText || '').trim();
                if (!t || (title && !t.includes(title))) continue;
                const bs = el.querySelectorAll('.note-card__action-btn');
                if (bs.length >= 2) { bs[1].click(); return true; }
            }
            return false;
        }""", title)
        print("edit clicked:", ok, flush=True)
        if not ok:
            print("NOTE_NOT_FOUND")
            await ctx.close(); return 3

        await pg.wait_for_timeout(5000)
        print("URL:", pg.url, flush=True)
        if "/publish/update" not in pg.url:
            print("EDIT_OPEN_FAIL", pg.url)
            await ctx.close(); return 4

        # 底部按钮文案（更新页可能是「发布」「更新」）
        btns = await pg.evaluate("() => [...document.querySelectorAll('button')].map(b=>b.innerText.trim()).filter(Boolean)")
        print("buttons:", btns[:12], flush=True)

        if now:
            # 关掉定时开关
            await pg.evaluate("""() => {
                const sim = document.querySelector('.post-time-switch-container .d-switch-simulator');
                if (sim && sim.className.includes('checked')) sim.click();
            }""")
            await pg.wait_for_timeout(1500)
            label = await click_submit(pg, ["立即发布", "发布", "更新"])
            print("submit:", label, flush=True)
        else:
            # 确保定时开着并填入新时间
            await pg.evaluate("""() => {
                const sim = document.querySelector('.post-time-switch-container .d-switch-simulator');
                if (sim && !sim.className.includes('checked')) sim.click();
            }""")
            await pg.wait_for_timeout(1600)
            inp = pg.locator(".d-datepicker-input-filter input").first
            await inp.click()
            await pg.wait_for_timeout(300)
            await inp.fill(when)
            await pg.wait_for_timeout(300)
            await pg.keyboard.press("Enter")
            await pg.wait_for_timeout(1200)
            val = await inp.input_value()
            print("datetime:", val, flush=True)
            if val.strip()[:16] != when.strip():
                print("TIME_FAIL", val)
                await ctx.close(); return 1
            # 等日期浮层收起再点底部按钮
            await pg.wait_for_timeout(1300)
            label = await click_submit(pg, ["定时发布", "更新", "发布"])
            print("submit:", label, flush=True)

        await pg.wait_for_timeout(3000)
        if await need_verify(pg):
            print("NEED_VERIFY 请在窗口里扫码", flush=True)
            if not await wait_verify(pg):
                print("VERIFY_TIMEOUT")
                await ctx.close(); return 3
            await pg.wait_for_timeout(1500)
            await click_submit(pg, ["定时发布", "立即发布", "发布", "更新"])

        # 确认弹窗
        for lb in ["确定", "确认", "确认发布"]:
            try:
                loc = pg.get_by_text(lb, exact=True)
                if await loc.count() > 0 and await loc.last.is_visible():
                    await loc.last.click(force=True, timeout=4000)
                    break
            except Exception:
                pass

        ok2 = False
        for attempt in range(3):
            await pg.wait_for_timeout(1800)
            try:
                txt = await pg.evaluate("() => document.body.innerText")
            except Exception:
                txt = ""
            if ("更新成功" in txt) or ("发布成功" in txt) or ("定时发布成功" in txt):
                ok2 = True
                break
            if "note-manager" in pg.url and "publish/update" not in pg.url:
                ok2 = True
                break
            print("retry submit", attempt + 1, flush=True)
            r = await pg.evaluate("""() => { const el=document.querySelector('xhs-publish-btn'); if(!el) return null;
                const b=el.getBoundingClientRect(); return {x:b.x,y:b.y,w:b.width,h:b.height}; }""")
            if r:
                await pg.mouse.click(r["x"] + r["w"] / 2, r["y"] + 47 + attempt * 4)
            await pg.wait_for_timeout(1500)
        print("RESULT_OK:", ok2, flush=True)
        print("FINAL_URL:", pg.url, flush=True)
        await pg.wait_for_timeout(1200)
        await ctx.close()
        return 0 if ok2 else 5


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--account", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--time", default="")
    ap.add_argument("--now", action="store_true")
    ap.add_argument("--config", default="")
    a = ap.parse_args()
    cfg, _ = load_config(a.config)
    acc = find_account(cfg, a.account)
    if not a.now and not a.time:
        raise SystemExit("需要 --time 或 --now")
    sys.exit(asyncio.run(run(cfg, acc, a.title, a.time, a.now)))


if __name__ == "__main__":
    main()

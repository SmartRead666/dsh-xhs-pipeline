from browser_launch import launch_persistent, launch
# -*- coding: utf-8 -*-
"""
把某一天的发布包排期到小红书（支持扫码验证等待）

用法:
  python publish.py --account peter --day 01_2026-11-10_痛值愿 --time "2026-11-10 17:30"
  python publish.py --account peter --day <folder> --draft     # 只存草稿
  python publish.py --account peter --login                   # 只做登录

退出码: 0 成功 / 2 需要登录 / 3 需要扫码超时 / 1 其他失败
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
    for i in range(timeout // 3):
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


async def click_publish(pg):
    await pg.mouse.click(818, 918)
    await pg.wait_for_timeout(2200)


async def check_success(pg, tries=8):
    for _ in range(tries):
        try:
            txt = await pg.evaluate("() => document.body.innerText")
        except Exception:
            return False
        if "发布成功" in txt or "定时发布成功" in txt or "published=true" in pg.url:
            return True
        await pg.wait_for_timeout(1000)
    return False


async def run(cfg, acc, folder, when, draft_only, login_only):
    from playwright.async_api import async_playwright
    prof = profile_of(cfg, acc)
    os.makedirs(prof, exist_ok=True)
    async with async_playwright() as p:
        ctx = await launch_persistent(p, 
            prof, headless=False,
            viewport={"width": 1560, "height": 960},
            args=["--disable-blink-features=AutomationControlled", "--window-size=1560,960"])
        await ctx.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")
        pg = ctx.pages[0] if ctx.pages else await ctx.new_page()

        await pg.goto("https://creator.xiaohongshu.com/publish/publish?source=official",
                      wait_until="domcontentloaded", timeout=60000)
        await pg.wait_for_timeout(3500)
        if "/login" in pg.url:
            print("NEED_LOGIN 请在弹出的窗口里扫码登录创作中心，登录后重新运行本命令")
            return 2

        if login_only:
            print("LOGIN_OK")
            await pg.wait_for_timeout(1500)
            await ctx.close()
            return 0

        pkg = json.load(open(os.path.join(folder, "publish.json"), encoding="utf-8"))
        imgs = [os.path.join(folder, n) for n in pkg["images"]]

        await pg.evaluate("""() => {
            const els=[...document.querySelectorAll('.creator-tab')];
            const el=els.find(e=>e.textContent.trim()==='上传图文' && e.getBoundingClientRect().x>0);
            if(el) el.click();}""")
        await pg.wait_for_timeout(1800)
        for h in await pg.query_selector_all("input[type=file]"):
            aa = await h.get_attribute("accept") or ""
            if "jpg" in aa or "png" in aa:
                await h.set_input_files(imgs)
                break
        print("uploaded", len(imgs), flush=True)
        await pg.wait_for_timeout(12000)
        try:
            b = pg.get_by_text("我知道了", exact=True).first
            if await b.count() > 0:
                await b.click(force=True)
        except Exception:
            pass
        await pg.wait_for_timeout(900)

        ti = pg.locator("input[placeholder*='标题']").first
        await ti.click(force=True)
        await ti.fill(pkg["title"])
        ed = pg.locator(".ProseMirror").first
        await ed.click(force=True)
        await pg.wait_for_timeout(250)
        await pg.keyboard.insert_text(pkg["body"])
        await pg.wait_for_timeout(850)
        await pg.evaluate("""() => {
            const ed=document.querySelector('.ProseMirror'); ed.focus();
            const s=window.getSelection(), r=document.createRange();
            r.selectNodeContents(ed); r.collapse(false); s.removeAllRanges(); s.addRange(r);}""")
        await pg.wait_for_timeout(200)
        await pg.keyboard.press("Enter")
        for t in pkg.get("tags", []):
            await pg.keyboard.type("#" + t, delay=16)
            await pg.wait_for_timeout(520)
            await pg.keyboard.press("Space")
        await pg.wait_for_timeout(600)

        if draft_only:
            try:
                await pg.get_by_text("暂存离开", exact=True).last.click(force=True, timeout=8000)
                print("DRAFT_OK")
            except Exception as e:
                print("DRAFT_FAIL", e)
            await pg.wait_for_timeout(2000)
            await ctx.close()
            return 0

        await pg.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
        await pg.wait_for_timeout(700)
        await pg.evaluate("""() => {
            const sim=document.querySelector('.post-time-switch-container .d-switch-simulator');
            if(sim && !sim.classList.contains('checked')) sim.click();}""")
        await pg.wait_for_timeout(1600)
        inp = pg.locator(".d-datepicker-input-filter input").first
        await inp.click()
        await pg.wait_for_timeout(300)
        await inp.fill(when)
        await pg.wait_for_timeout(300)
        await pg.keyboard.press("Enter")
        await pg.wait_for_timeout(800)
        val = await inp.input_value()
        if val.strip()[:16] != when.strip():
            print("TIME_FAIL", val)
            await ctx.close()
            return 1

        await click_publish(pg)
        if await need_verify(pg):
            print("NEED_VERIFY 请扫描窗口中的二维码（最长等 5 分钟）", flush=True)
            if not await wait_verify(pg, timeout=300):
                print("VERIFY_TIMEOUT")
                await ctx.close()
                return 3
            await pg.wait_for_timeout(1500)
            if await need_verify(pg):
                await click_publish(pg)
            if not await check_success(pg):
                await click_publish(pg)
        ok = await check_success(pg)
        if ok:
            try:
                pj = os.path.join(folder, "publish.json")
                data = json.load(open(pj, encoding="utf-8"))
                data["scheduled_at"] = when
                data["status"] = "scheduled"
                json.dump(data, open(pj, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
            except Exception as e:
                print("记录排期失败", e, flush=True)
        print("PUBLISH_OK" if ok else "PUBLISH_UNKNOWN")
        await pg.wait_for_timeout(1500)
        await ctx.close()
        return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--account", required=True)
    ap.add_argument("--day", default="")
    ap.add_argument("--time", default="")
    ap.add_argument("--draft", action="store_true")
    ap.add_argument("--login", action="store_true")
    ap.add_argument("--config", default="")
    a = ap.parse_args()

    cfg, root = load_config(a.config)
    acc = find_account(cfg, a.account)
    os.environ["XHS_HOME"] = home_of(cfg)
    if a.login:
        folder = ""
    else:
        if not a.day:
            raise SystemExit("需要 --day <发布包目录>")
        folder = a.day if os.path.isabs(a.day) else os.path.join(home_of(cfg), "output", acc["slug"], a.day)
        if not os.path.isdir(folder):
            raise SystemExit("找不到发布包目录：%s" % folder)
        if not a.draft and not a.time:
            raise SystemExit("定时发布需要 --time 'YYYY-MM-DD HH:MM'")
        # —— 发布前合规自检：有 block 级风险就不发 ——
        pj = os.path.join(folder, "publish.json")
        if os.path.exists(pj):
            from compliance_check import check, format_report
            hits = check(json.load(open(pj, encoding="utf-8")))
            print(format_report(hits), flush=True)
            if [h for h in hits if h["level"] == "block"] and os.environ.get("XHS_FORCE") != "1":
                print("\n已中止发布：这条内容有违规风险，先改文案（确定要发可加 XHS_FORCE=1）", flush=True)
                raise SystemExit(4)
    sys.exit(asyncio.run(run(cfg, acc, folder, a.time, a.draft, a.login)))


if __name__ == "__main__":
    main()

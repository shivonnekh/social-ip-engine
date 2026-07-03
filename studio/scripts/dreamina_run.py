#!/usr/bin/env python3
"""
Generate Dreamina Image-to-Video for ai-tcm-ip tonsil stone campaign.
Extracts aiteam CapCut session cookies from Chrome Profile 22, injects into
a fresh Playwright browser, uploads image + prompt → generates → downloads video.

Usage: python3 scripts/dreamina_run.py --clip 1
"""

import argparse, os, sqlite3, shutil, subprocess, sys, tempfile, hashlib
from pathlib import Path

DREAMINA_URL = "https://dreamina.capcut.com/ai-tool/video/generate"
VIDEO_DIR    = Path(__file__).parent.parent / "campaigns/01-tonsil-stone/video"
CLIP_DIR     = Path(__file__).parent.parent / "campaigns/01-tonsil-stone/voice/segments"
IMG_DIR      = Path("/Users/shivonne/Downloads")
COOKIE_DB    = Path.home() / "Library/Application Support/Google/Chrome/Profile 22/Cookies"

JOBS = {
    1: (
        "ChatGPT Image Jun 22, 2026, 03_43_24 PM (1).png",
        "Traditional Chinese medicine clinic, brass vessel and herb tray on wooden desk, "
        "subtle camera push-in, warm amber candlelight flicker, cinematic slow zoom, "
        "linen fabric gentle sway, no faces",
    ),
    2: (
        "ChatGPT Image Jun 22, 2026, 03_43_24 PM (2).png",
        "Antique medicine cabinet with wooden drawers and glass herb jars, "
        "warm interior ambient lighting, gentle depth-of-field breathing effect, "
        "traditional calligraphy scrolls, slow cinematic drift, no faces",
    ),
    3: (
        "ChatGPT Image Jun 22, 2026, 03_43_24 PM (3).png",
        "TCM clinic scene, traditional linen garment soft fabric movement, "
        "medicine jar bokeh background, slow cinematic drift, "
        "wooden drawer cabinet detail, no faces",
    ),
    4: (
        "ChatGPT Image Jun 22, 2026, 05_26_32 PM.png",
        "Traditional Chinese apothecary interior, cupped hands holding dried herbs, "
        "warm amber lighting on linen sleeves, slow zoom in on hands and herb tray, "
        "calligraphy scroll background, no faces",
    ),
    5: (
        "ChatGPT Image Jun 22, 2026, 03_43_25 PM (5).png",
        "Ancient Chinese medicine clinic, open-palm gesture with traditional linen sleeves, "
        "dramatic slow motion, wooden cabinet with labelled herb jars, "
        "cinematic lighting, no faces",
    ),
}

# Domains we need cookies for
COOKIE_DOMAINS = ["dreamina.capcut.com", ".capcut.com", ".capcutapi.com", ".tiktok.com"]


def _extract_cookies() -> list[dict]:
    """Decrypt Profile 22 CapCut/Dreamina cookies using pycookiecheat."""
    from pycookiecheat import chrome_cookies

    all_cookies = []
    seen = set()

    for domain_url in [
        "https://dreamina.capcut.com",
        "https://www.capcut.com",
    ]:
        try:
            cookies = chrome_cookies(
                domain_url,
                cookie_file=str(COOKIE_DB),
                browser="Chrome",
            )
            for name, value in cookies.items():
                key = (domain_url, name)
                if key not in seen:
                    seen.add(key)
                    # Determine domain from URL
                    dom = ".capcut.com" if "capcut.com" in domain_url else domain_url.split("//")[1]
                    all_cookies.append({
                        "name": name,
                        "value": value,
                        "domain": dom,
                        "path": "/",
                        "httpOnly": False,
                        "secure": True,
                        "sameSite": "None",
                    })
        except Exception as e:
            print(f"[cookies] warn for {domain_url}: {e}")

    # Also pull from raw SQLite for any missing domains
    tmp = shutil.copy2(str(COOKIE_DB), tempfile.mktemp(suffix=".db"))
    try:
        con = sqlite3.connect(tmp)
        # We need the raw decrypted values from pycookiecheat, but let's
        # at least get the host_key for context
        con.close()
    finally:
        os.unlink(tmp)

    print(f"[cookies] extracted {len(all_cookies)} cookies")
    return all_cookies


def run(clip_num: int) -> bool:
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

    img_name, prompt = JOBS[clip_num]
    img_path = IMG_DIR / img_name
    out_path = VIDEO_DIR / f"seg{clip_num}_raw.mp4"
    VIDEO_DIR.mkdir(parents=True, exist_ok=True)
    ss = lambda n: str(VIDEO_DIR / f"dbg_c{clip_num}_{n}.png")

    if not img_path.exists():
        print(f"[err] image not found: {img_path}")
        return False

    print(f"\n{'='*60}")
    print(f"CLIP {clip_num}  |  {img_name[:50]}")
    print(f"PROMPT: {prompt[:70]}...")
    print("="*60)

    cookies = _extract_cookies()

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=[
                "--start-maximized",
                "--disable-blink-features=AutomationControlled",
            ],
        )
        ctx = browser.new_context(
            accept_downloads=True,
            viewport=None,  # use window size
        )

        # Inject cookies before navigating
        ctx.add_cookies(cookies)
        print(f"[pw] injected {len(cookies)} cookies")

        page = ctx.new_page()
        page.goto(DREAMINA_URL, wait_until="domcontentloaded", timeout=30_000)
        page.wait_for_timeout(3_000)
        page.screenshot(path=ss("01_loaded"))
        print(f"[pw] loaded: {page.title()}")

        # ── Check login state ──
        if page.query_selector("text=Continue with Google"):
            print("[pw] ⚠️  Not logged in — session cookie may have expired.")
            print("[pw]     Please log in manually in the browser (120s)...")
            try:
                page.wait_for_selector("textarea, [contenteditable]", timeout=120_000)
                print("[pw] ✅ Logged in!")
                page.wait_for_timeout(2_000)
            except PWTimeout:
                print("[pw] ❌ login timed out")
                return False

        # ── Upload image ──
        print(f"[pw] uploading image: {img_name[:40]}")
        fi = page.query_selector("input[type='file']")
        if not fi:
            page.screenshot(path=ss("02_no_input"))
            print("[pw] ❌ no file input")
            return False
        fi.set_input_files(str(img_path))
        page.wait_for_timeout(2_000)
        page.screenshot(path=ss("02_uploaded"))
        print("[pw] image uploaded")

        # ── Type prompt ──
        print("[pw] typing prompt...")
        ta = (
            page.query_selector("[contenteditable='true']") or
            page.query_selector("textarea") or
            page.query_selector("[placeholder*='idea' i]") or
            page.query_selector("[placeholder*='reference' i]")
        )
        if ta:
            ta.click()
            page.wait_for_timeout(300)
            page.keyboard.press("Meta+a")
            page.keyboard.press("Backspace")
            page.keyboard.type(prompt, delay=15)
            print(f"[pw] prompt typed")
        else:
            print("[pw] ⚠️  textarea not found, skipping prompt")
        page.wait_for_timeout(500)
        page.screenshot(path=ss("03_prompt"))

        # ── Duration: try to set max available ──
        page.keyboard.press("Escape")
        page.wait_for_timeout(400)
        for sel in ["button:has-text('5s')", "button:has-text('8s')", "button:has-text('10s')"]:
            el = page.query_selector(sel)
            if el and el.is_visible():
                print(f"[pw] opening duration menu (currently {el.text_content().strip()})...")
                el.click(force=True)
                page.wait_for_timeout(900)
                page.screenshot(path=ss("04_dur_menu"))
                for target in ["13s", "10s", "8s"]:
                    for opt_sel in [
                        f"li:has-text('{target}')",
                        f"[role='option']:has-text('{target}')",
                        f"button:has-text('{target}')",
                        f"span:has-text('{target}')",
                    ]:
                        opt = page.query_selector(opt_sel)
                        if opt and opt.is_visible():
                            opt.click(force=True)
                            print(f"[pw] duration → {target}")
                            break
                    else:
                        continue
                    break
                page.wait_for_timeout(400)
                page.keyboard.press("Escape")
                break

        # ── Click Generate (rightmost visible button in toolbar area) ──
        print("[pw] clicking Generate...")
        page.screenshot(path=ss("05_before_send"))
        result = page.evaluate("""() => {
            const buttons = Array.from(document.querySelectorAll('button'));
            // Toolbar is in top portion — use 70% of viewport height as threshold
            const threshold = window.innerHeight * 0.7;
            let cands = buttons.filter(b => {
                const r = b.getBoundingClientRect();
                return r.width > 0 && r.height > 0 && r.top > 30 && r.top < threshold;
            });
            if (!cands.length) {
                cands = buttons.filter(b => {
                    const r = b.getBoundingClientRect();
                    return r.width > 0 && r.height > 0;
                });
            }
            if (!cands.length) return 'no_buttons_at_all';
            const btn = cands.reduce((a, b) =>
                b.getBoundingClientRect().right > a.getBoundingClientRect().right ? b : a
            );
            const r = btn.getBoundingClientRect();
            btn.click();
            return `clicked x=${Math.round(r.x)} y=${Math.round(r.y)} wh=${Math.round(window.innerHeight)}`;
        }""")
        print(f"[pw] send: {result}")
        page.wait_for_timeout(3_000)
        page.screenshot(path=ss("06_after_send"))

        # ── Handle post-send login popup ──
        if page.query_selector("text=Continue with Google"):
            print("[pw] ⚠️  Login popup after Generate — waiting 120s for manual login...")
            try:
                page.wait_for_selector("textarea, [contenteditable]", timeout=120_000)
                print("[pw] ✅ logged in, re-clicking Generate...")
                page.wait_for_timeout(1_500)
                page.evaluate("""() => {
                    const buttons = Array.from(document.querySelectorAll('button'));
                    const threshold = window.innerHeight * 0.7;
                    let cands = buttons.filter(b => {
                        const r = b.getBoundingClientRect();
                        return r.width > 0 && r.height > 0 && r.top > 30 && r.top < threshold;
                    });
                    if (!cands.length) cands = buttons.filter(b => {
                        const r = b.getBoundingClientRect();
                        return r.width > 0 && r.height > 0;
                    });
                    if (cands.length) {
                        const btn = cands.reduce((a, b) =>
                            b.getBoundingClientRect().right > a.getBoundingClientRect().right ? b : a);
                        btn.click();
                    }
                }""")
                page.wait_for_timeout(3_000)
            except PWTimeout:
                print("[pw] ❌ login timed out")
                return False

        # ── Poll for Download button ──
        print("[pw] waiting for generation (up to 3 min)...")
        for i in range(180):
            page.wait_for_timeout(1_000)
            dl = page.query_selector(
                "button:has-text('Download'), a[download], "
                "[aria-label*='download' i], button[class*='download']"
            )
            if dl and dl.is_visible():
                print(f"[pw] ✅ download ready after {i+1}s")
                page.screenshot(path=ss("07_ready"))
                with page.expect_download(timeout=30_000) as dl_info:
                    dl.click()
                dl_info.value.save_as(str(out_path))
                print(f"[pw] 💾 saved → {out_path}")
                page.screenshot(path=ss("08_done"))
                browser.close()
                return True
            if i % 20 == 0:
                page.screenshot(path=ss(f"07_wait_{i}s"))
                print(f"[pw]   still generating... {i}s elapsed")

        print("[pw] ❌ timeout")
        page.screenshot(path=ss("09_timeout"))
        browser.close()
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--clip", type=int, required=True, choices=[1, 2, 3, 4, 5])
    args = ap.parse_args()
    sys.exit(0 if run(args.clip) else 1)


if __name__ == "__main__":
    main()

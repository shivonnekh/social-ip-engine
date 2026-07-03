#!/usr/bin/env python3
"""
Dreamina Image-to-Video via Playwright.
Flow: type prompt → upload image via + button → set duration → click send → download

Usage:
    python3 scripts/dreamina_i2v.py \
        --image "/path/to/image.png" \
        --prompt "Elderly TCM doctor explaining, subtle breathing, cinematic" \
        --duration 13 \
        --out campaigns/01-tonsil-stone/video/seg1.mp4
"""

import argparse
import os
import shutil
import sys
import tempfile
from pathlib import Path

CHROME_PATH = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
# AI team profile directory name
CHROME_PROFILE_DIR = "Profile 22"
DREAMINA_URL = "https://dreamina.capcut.com/ai-tool/video/generate"
CDP_PORT = 9223  # avoid conflict with any existing debugging port

# Motion prompt for TCM doctor scenes
DEFAULT_PROMPT = (
    "Elderly Chinese medicine doctor explaining calmly, "
    "subtle natural breathing and gentle hand gesture, "
    "warm clinic lighting, cinematic slow zoom"
)


def _launch_chrome_cdp() -> "subprocess.Popen":
    """Kill any existing Chrome, relaunch with remote debugging on CDP_PORT."""
    import subprocess, time

    # Kill existing Chrome gracefully
    subprocess.run(["pkill", "-x", "Google Chrome"], capture_output=True)
    time.sleep(2)

    proc = subprocess.Popen([
        CHROME_PATH,
        f"--remote-debugging-port={CDP_PORT}",
        f"--profile-directory={CHROME_PROFILE_DIR}",
        "--no-first-run",
        "--no-default-browser-check",
        "--start-maximized",
        DREAMINA_URL,
    ])
    time.sleep(4)  # give Chrome time to start
    print(f"[pw] Chrome launched (pid={proc.pid}) with Profile 22 on port {CDP_PORT}")
    return proc


def run(image_path: str, prompt: str, duration: int, out_path: str) -> bool:
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

    import subprocess as _sp

    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    ss = lambda name: str(out.parent / f"debug_{name}.png")  # noqa: E731

    chrome_proc = _launch_chrome_cdp()

    with sync_playwright() as p:
        print(f"[pw] connecting to Chrome via CDP on port {CDP_PORT}...")
        browser = p.chromium.connect_over_cdp(f"http://localhost:{CDP_PORT}")
        ctx = browser.contexts[0] if browser.contexts else browser.new_context(accept_downloads=True)
        page = ctx.pages[0] if ctx.pages else ctx.new_page()

        try:
            print(f"[pw] → {DREAMINA_URL}")
            page.goto(DREAMINA_URL, wait_until="domcontentloaded", timeout=30_000)
            page.wait_for_timeout(3_000)
            page.screenshot(path=ss("01_loaded"))
            print(f"[pw] loaded: {page.title()}")

            # ── Handle login dialog if present ────────────────────────────
            login_modal = page.query_selector("text=Continue with Google")
            if login_modal:
                print("[pw] ⚠️  LOGIN REQUIRED — Please log in to Dreamina in the browser window.")
                print("[pw]     Waiting up to 90 seconds for you to complete login...")
                try:
                    # Wait until we're on the main page (login modal gone)
                    page.wait_for_selector(
                        "textarea, [placeholder*='idea' i], [placeholder*='mention' i]",
                        timeout=90_000,
                    )
                    print("[pw] ✅ Logged in!")
                    page.wait_for_timeout(2_000)
                except PWTimeout:
                    print("[pw] ❌ Login timed out — please run again after logging in")
                    return False

            # ── 1. Click the "+" button to open file picker ──────────────
            print("[pw] clicking + to add image...")
            # The + is a small button left of the prompt area or inside it
            plus_btn = None
            for sel in [
                "button[aria-label*='image' i]",
                "button[aria-label*='upload' i]",
                "button[aria-label*='attach' i]",
                "label[class*='upload']",
                # The + icon button near the textarea
                ".image-upload-btn",
                "[class*='add-image']",
                # Generic: any button containing + symbol near input
                "button:has-text('+')",
            ]:
                try:
                    el = page.query_selector(sel)
                    if el and el.is_visible():
                        plus_btn = el
                        print(f"[pw] found + via {sel}")
                        break
                except Exception:
                    continue

            if plus_btn:
                # Set up file chooser handler before clicking
                with page.expect_file_chooser(timeout=5_000) as fc_info:
                    plus_btn.click()
                fc = fc_info.value
                fc.set_files(image_path)
                print(f"[pw] image set via file chooser: {image_path}")
            else:
                # Fallback: use hidden file input directly
                print("[pw] no + btn found, using hidden file input...")
                fi = page.query_selector("input[type='file']")
                if fi:
                    fi.set_input_files(image_path)
                    print("[pw] set_input_files done")
                else:
                    print("[pw] ERROR: no upload mechanism found")
                    page.screenshot(path=ss("02_no_upload"))
                    return False

            page.wait_for_timeout(2_000)
            page.screenshot(path=ss("02_after_upload"))

            # ── 2. Type the motion prompt ─────────────────────────────────
            print(f"[pw] typing prompt: {prompt[:50]}...")
            ta = page.query_selector("textarea") or page.query_selector("[contenteditable='true']")
            if ta:
                ta.click()
                page.keyboard.type(prompt, delay=20)
                page.wait_for_timeout(500)
            else:
                print("[pw] no textarea found — skipping prompt")
            page.screenshot(path=ss("03_prompt_typed"))

            # ── 3. Set duration ───────────────────────────────────────────
            print(f"[pw] setting duration to {duration}s...")
            # Dismiss any open overlay first
            page.keyboard.press("Escape")
            page.wait_for_timeout(500)

            # Find "5s" / duration button in the bottom toolbar
            dur_btn = None
            for sel in [
                "button:has-text('5s')",
                "button:has-text('8s')",
                "button:has-text('10s')",
                "[class*='duration']",
                "[aria-label*='duration' i]",
            ]:
                el = page.query_selector(sel)
                if el and el.is_visible():
                    dur_btn = el
                    print(f"[pw] found duration btn via {sel}: {el.text_content()}")
                    break

            if dur_btn:
                # Force click to bypass any overlay intercept
                dur_btn.click(force=True)
                page.wait_for_timeout(1_000)
                page.screenshot(path=ss("04_dur_menu"))

                # Look for duration options in dropdown/panel
                for opt_sel in [
                    f"[data-value='{duration}']",
                    f"button:has-text('{duration}s')",
                    f"li:has-text('{duration}s')",
                    f"[role='option']:has-text('{duration}s')",
                    f"span:has-text('{duration}s')",
                ]:
                    try:
                        opt = page.query_selector(opt_sel)
                        if opt and opt.is_visible():
                            opt.click(force=True)
                            print(f"[pw] duration set to {duration}s")
                            break
                    except Exception:
                        continue
                else:
                    # Pick the highest available number
                    opts = page.query_selector_all("li, [role='option'], button")
                    best = None
                    best_val = 0
                    for el in opts:
                        txt = (el.text_content() or "").strip()
                        if txt.endswith("s") and txt[:-1].isdigit():
                            v = int(txt[:-1])
                            if v > best_val:
                                best_val, best = v, el
                    if best:
                        best.click(force=True)
                        print(f"[pw] picked max duration: {best_val}s")

                page.wait_for_timeout(500)
                page.keyboard.press("Escape")  # close dropdown
                page.wait_for_timeout(300)
            else:
                print("[pw] duration button not found, keeping default")

            # ── 4. Click Send / Generate ──────────────────────────────────
            print("[pw] clicking Generate / Send...")
            page.screenshot(path=ss("05_before_send"))

            # Use JS to find the send button: rightmost button in top-half of page
            # (avoids accidentally clicking gallery items below)
            clicked = page.evaluate("""() => {
                const buttons = Array.from(document.querySelectorAll('button'));
                const vp_mid = window.innerHeight / 2;
                // Candidates: visible, in top half of page
                const candidates = buttons.filter(b => {
                    const r = b.getBoundingClientRect();
                    return r.width > 0 && r.height > 0 && r.top < vp_mid;
                });
                if (!candidates.length) return 'no_candidates';
                // Pick the rightmost one (send button is far right)
                const send = candidates.reduce((a, b) => {
                    return b.getBoundingClientRect().right > a.getBoundingClientRect().right ? b : a;
                });
                const r = send.getBoundingClientRect();
                send.click();
                return `clicked at x=${Math.round(r.x)} y=${Math.round(r.y)} text="${send.textContent.trim().slice(0,20)}"`;
            }""")
            print(f"[pw] JS send: {clicked}")
            print("[pw] send clicked — waiting for generation...")

            # ── 5. Wait for video + download ──────────────────────────────
            # Dreamina shows a progress indicator, then a download button
            page.wait_for_timeout(3_000)
            page.screenshot(path=ss("06_after_send"))

            # ── Handle login popup triggered by Generate click ────────────
            login_now = page.query_selector("text=Continue with Google")
            if login_now:
                print("[pw] ⚠️  LOGIN POPUP appeared after clicking Generate.")
                print("[pw]     Please log in to Dreamina in the browser window (90s)...")
                try:
                    page.wait_for_selector(
                        "textarea, [placeholder*='idea' i], [placeholder*='mention' i]",
                        timeout=90_000,
                    )
                    print("[pw] ✅ Logged in! Re-clicking Generate...")
                    page.wait_for_timeout(2_000)
                    # Re-click send after login
                    page.evaluate("""() => {
                        const buttons = Array.from(document.querySelectorAll('button'));
                        const vp_mid = window.innerHeight / 2;
                        const candidates = buttons.filter(b => {
                            const r = b.getBoundingClientRect();
                            return r.width > 0 && r.height > 0 && r.top < vp_mid;
                        });
                        if (!candidates.length) return;
                        const send = candidates.reduce((a, b) =>
                            b.getBoundingClientRect().right > a.getBoundingClientRect().right ? b : a
                        );
                        send.click();
                    }""")
                    print("[pw] Generate re-clicked after login")
                    page.wait_for_timeout(3_000)
                except PWTimeout:
                    print("[pw] ❌ Login timed out")
                    return False

            page.screenshot(path=ss("06_generating"))
            print("[pw] polling for download button (up to 3 min)...")
            deadline = 180
            for i in range(deadline):
                page.wait_for_timeout(1_000)
                dl_btn = page.query_selector(
                    "button:has-text('Download'), "
                    "a[download], "
                    "[aria-label*='download' i], "
                    "button[class*='download']"
                )
                if dl_btn and dl_btn.is_visible():
                    print(f"[pw] download button found after {i+1}s")
                    with page.expect_download(timeout=30_000) as dl_info:
                        dl_btn.click()
                    dl = dl_info.value
                    dl.save_as(str(out))
                    print(f"[pw] ✅ saved → {out}")
                    page.screenshot(path=ss("07_done"))
                    return True
                if i % 15 == 0:
                    page.screenshot(path=ss(f"07_wait_{i}s"))

            print("[pw] timeout waiting for download")
            page.screenshot(path=ss("08_timeout"))
            return False

        except Exception as e:
            print(f"[pw] exception: {e}")
            try:
                page.screenshot(path=ss("99_error"))
            except Exception:
                pass
            return False
        finally:
            try:
                browser.close()
            except Exception:
                pass
            # Leave Chrome running so user can continue using it


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", required=True)
    ap.add_argument("--prompt", default=DEFAULT_PROMPT)
    ap.add_argument("--duration", type=int, default=13)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    img = str(Path(args.image).expanduser().resolve())
    if not Path(img).exists():
        print(f"[error] image not found: {img}", file=sys.stderr)
        return 1

    ok = run(img, args.prompt, args.duration, args.out)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())


def setup_login():
    """Open browser and wait for user to log in to Dreamina. Run once to save session."""
    from playwright.sync_api import sync_playwright

    profile_dir = _ensure_profile()
    print("=" * 60)
    print("DREAMINA LOGIN SETUP")
    print("=" * 60)
    print(f"Profile: {profile_dir}")
    print()
    print("1. A Chrome window will open and go to Dreamina.")
    print("2. Log in with Google / TikTok / CapCut.")
    print("3. Once you see the main Dreamina page, press ENTER here.")
    print()
    input("Press ENTER to open the browser...")

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            profile_dir,
            executable_path=CHROME_PATH,
            headless=False,
            args=["--start-maximized"],
        )
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto(DREAMINA_URL, wait_until="domcontentloaded")
        print()
        print("Browser is open. Please log in to Dreamina now.")
        print("When you're logged in and see the main page, press ENTER here.")
        input("Press ENTER after login is complete...")
        print("[setup] Saving session and closing...")
        ctx.close()

    print("[setup] ✅ Login saved! You can now run the automation.")


if __name__ == "__main__":
    import argparse as _ap
    _parser = _ap.ArgumentParser()
    _parser.add_argument("--setup-login", action="store_true", help="Run login setup first")
    _parser.add_argument("--image")
    _parser.add_argument("--prompt", default=DEFAULT_PROMPT)
    _parser.add_argument("--duration", type=int, default=13)
    _parser.add_argument("--out")
    _args = _parser.parse_args()

    if _args.setup_login:
        setup_login()
    else:
        if not _args.image or not _args.out:
            print("Usage: --image <path> --out <path>  OR  --setup-login")
            raise SystemExit(1)
        img = str(Path(_args.image).expanduser().resolve())
        ok = run(img, _args.prompt, _args.duration, _args.out)
        raise SystemExit(0 if ok else 1)

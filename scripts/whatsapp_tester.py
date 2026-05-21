"""
WhatsApp Agent Tester
Automated conversation tester for TCM Jessica agent.
Sends RESTART, then simulates a patient consultation.
Logs full conversation for analysis.
"""

import asyncio
import json
import os
import re
import time
from datetime import datetime
from pathlib import Path

import anthropic
from playwright.async_api import async_playwright

# ── Config ────────────────────────────────────────────────────────────────────
AGENT_NUMBER = "+852 5241 7448"
LOG_DIR = Path(__file__).parent.parent / "data" / "test_logs"
MAX_TURNS = 20  # safety cap

PATIENT_SYSTEM_PROMPT = """You are a patient consulting a Traditional Chinese Medicine (TCM) WhatsApp chatbot.

Your background:
- 35-year-old woman
- Feeling tired all the time, poor sleep, occasional stomach bloating
- Heard about TCM from a friend, curious but slightly skeptical
- Cantonese speaker but comfortable with English/Chinese mix

Your job:
- Respond naturally as this patient would
- Answer the bot's questions honestly based on your symptoms
- Keep replies SHORT (1-3 sentences max) — this is WhatsApp
- If the bot asks for your name, say "Amy"
- If the bot asks for your age, say "35"
- Be slightly hesitant but cooperative
- Do NOT push for appointment — let the bot lead you there naturally
- Do NOT break character

Reply ONLY with what Amy would say. No meta-commentary."""

# ── Helpers ───────────────────────────────────────────────────────────────────

def setup_log():
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = LOG_DIR / f"test_{ts}.json"
    return log_file, []


def log_message(conversation: list, role: str, text: str):
    entry = {"role": role, "text": text, "time": datetime.now().isoformat()}
    conversation.append(entry)
    prefix = "🤖 AGENT" if role == "agent" else "👤 PATIENT"
    print(f"\n{prefix}: {text}")
    return entry


async def find_and_open_chat(page, number: str):
    """Search for the contact number and open the chat."""
    print(f"\n🔍 Searching for {number}...")

    # Use the specific search input field
    search_input = page.locator('input[data-tab="3"]')
    await search_input.wait_for(timeout=30000)
    await search_input.click()
    await asyncio.sleep(0.5)

    # Type the number
    await search_input.fill(number)
    await asyncio.sleep(2)

    # Look for the result and click it
    try:
        # Try clicking first result in list
        result = page.locator('div[role="listitem"]').first
        await result.wait_for(timeout=5000)
        await result.click()
        print(f"✅ Opened chat with {number}")
        await asyncio.sleep(1)
        return True
    except Exception:
        print(f"⚠️  Could not find {number} in search results.")
        print("   Make sure the number is saved or has chatted before.")
        return False


async def send_message(page, text: str):
    """Type and send a message in the open chat."""
    # Find the message box
    msg_box = page.locator('div[contenteditable="true"][data-tab="10"]')
    await msg_box.wait_for(timeout=10000)
    await msg_box.click()
    await asyncio.sleep(0.3)

    # Type the message
    await page.keyboard.type(text, delay=30)
    await asyncio.sleep(0.3)
    await page.keyboard.press("Enter")
    await asyncio.sleep(0.5)
    print(f"✉️  Sent: {text}")


async def wait_for_new_message(page, last_seen_count: int, timeout: int = 60) -> str | None:
    """Wait until a new incoming message appears and return its text."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        # Get all incoming message bubbles
        msgs = await page.locator(
            'div.message-in span.selectable-text span'
        ).all_inner_texts()

        if len(msgs) > last_seen_count:
            # New messages arrived — grab all new ones joined
            new_msgs = msgs[last_seen_count:]
            combined = " | ".join(m.strip() for m in new_msgs if m.strip())
            return combined, len(msgs)

        await asyncio.sleep(1.5)

    print("⏰ Timeout waiting for agent reply.")
    return None, last_seen_count


async def count_incoming_messages(page) -> int:
    msgs = await page.locator(
        'div.message-in span.selectable-text span'
    ).all_inner_texts()
    return len(msgs)


def generate_patient_reply(client: anthropic.Anthropic, conversation: list, agent_msg: str) -> str:
    """Use Claude to generate a realistic patient reply."""
    messages = []
    for entry in conversation:
        if entry["role"] == "agent":
            messages.append({"role": "user", "content": entry["text"]})
        elif entry["role"] == "patient":
            messages.append({"role": "assistant", "content": entry["text"]})

    # Add the latest agent message
    messages.append({"role": "user", "content": agent_msg})

    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=200,
        system=PATIENT_SYSTEM_PROMPT,
        messages=messages,
    )
    return response.content[0].text.strip()


def save_log(log_file: Path, conversation: list):
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(conversation, f, ensure_ascii=False, indent=2)
    print(f"\n📝 Log saved to: {log_file}")


def print_analysis_header():
    print("\n" + "="*60)
    print("📊 CONVERSATION COMPLETE — Check these:")
    print("="*60)
    print("1. Was the conversation logic reasonable / natural?")
    print("2. Did the agent recommend products?")
    print("3. Did the agent push for appointment booking?")
    print("="*60)


# ── Main ──────────────────────────────────────────────────────────────────────

async def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("⚠️  ANTHROPIC_API_KEY not set. Patient replies will be static.")

    client = anthropic.Anthropic(api_key=api_key) if api_key else None
    log_file, conversation = setup_log()

    async with async_playwright() as p:
        print("\n🚀 Opening Chrome with WhatsApp Web...")
        browser = await p.chromium.launch(
            headless=False,
            args=["--start-maximized"],
        )
        context = await browser.new_context(
            viewport={"width": 1400, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        page = await context.new_page()
        await page.goto("https://web.whatsapp.com")

        print("\n📱 Please scan the QR code to log in...")
        print("   Waiting up to 2 minutes...")

        # Wait for WhatsApp to fully load (search bar appears)
        try:
            await page.wait_for_selector('[data-tab="3"]', timeout=120000)
            print("✅ Logged in to WhatsApp Web!")
        except Exception:
            print("❌ Login timeout. Please try again.")
            await browser.close()
            return

        await asyncio.sleep(2)

        # Open the chat
        opened = await find_and_open_chat(page, AGENT_NUMBER)
        if not opened:
            print("❌ Could not open chat. Exiting.")
            await browser.close()
            return

        await asyncio.sleep(2)

        # ── Step 1: RESTART ────────────────────────────────────────────
        print("\n" + "="*60)
        print("🔄 Sending RESTART...")
        print("="*60)
        await send_message(page, "RESTART")
        log_message(conversation, "patient", "RESTART")

        baseline = await count_incoming_messages(page)
        print(f"   Waiting for agent response...")
        agent_reply, baseline = await wait_for_new_message(page, baseline, timeout=60)

        if agent_reply:
            log_message(conversation, "agent", agent_reply)
        else:
            print("⚠️  No reply to RESTART. Continuing anyway...")

        await asyncio.sleep(2)

        # ── Step 2: Opening greeting ───────────────────────────────────
        opening = "Hello 你好, 我想了解一下中医"
        await send_message(page, opening)
        log_message(conversation, "patient", opening)
        baseline = await count_incoming_messages(page)

        # ── Step 3: Conversation loop ──────────────────────────────────
        turn = 0
        while turn < MAX_TURNS:
            print(f"\n⏳ Waiting for agent reply (turn {turn + 1})...")
            agent_reply, baseline = await wait_for_new_message(page, baseline, timeout=90)

            if not agent_reply:
                print("⏰ No reply received. Ending test.")
                break

            log_message(conversation, "agent", agent_reply)

            # Check if conversation seems done (appointment booked / farewell)
            done_signals = ["再见", "bye", "appointment", "预约成功", "感谢", "thank you"]
            if any(sig.lower() in agent_reply.lower() for sig in done_signals):
                print("\n✅ Conversation reached a natural end.")
                break

            await asyncio.sleep(1.5)

            # Generate patient reply
            if client:
                patient_reply = generate_patient_reply(client, conversation, agent_reply)
            else:
                patient_reply = "好的，请继续"  # fallback

            await send_message(page, patient_reply)
            log_message(conversation, "patient", patient_reply)
            baseline = await count_incoming_messages(page)
            turn += 1

        # ── Done ───────────────────────────────────────────────────────
        save_log(log_file, conversation)
        print_analysis_header()

        print("\n🔓 Browser staying open for 60s so you can review...")
        await asyncio.sleep(60)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())

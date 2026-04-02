#!/usr/bin/env python3
"""
📚 İngilizce Öğrenme Botu
Her gün 09:00'da 10 kelime + gramer konusu gönderir.
"""

import asyncio
import logging
import httpx
import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from telegram import Bot
import os

# ─── YAPILANDIRMA ────────────────────────────────────────────────────────────
BOT_TOKEN      = "8766994041:AAHMATQ-P8VMPerZyyrXE1LZfQEjOBAq0bg"
CHAT_ID        = -1003839673622   # @alfatradersmentorship
TOPIC_ID       = 2
ANTHROPIC_KEY  = os.environ.get("ANTHROPIC_API_KEY", "")
TIMEZONE       = ZoneInfo("Europe/Istanbul")
SEND_HOUR      = 19
SEND_MIN       = 10

logging.basicConfig(format="%(asctime)s | %(levelname)s | %(message)s", level=logging.INFO)
log = logging.getLogger(__name__)

# ─── ANTHROPİC İSTEĞİ ────────────────────────────────────────────────────────
async def get_english_content():
    prompt = """Sen bir İngilizce öğretmenisin. Aşağıdaki formatta günlük İngilizce içerik oluştur.

Kurallar:
- 10 kelime üret: 7 tane B2 seviyesi, 3 tane C1 seviyesi
- Her kelime için: İngilizce kelime, türü (adj/v/n/adv), Türkçe anlamı, örnek İngilizce cümle, cümlenin Türkçe çevirisi
- 1 gramer konusu: basit anlatım + 3 örnek (İngilizce ve Türkçe)
- Gramer konuları sırayla farklı olsun (reported speech, conditionals, passive voice, relative clauses, modal verbs vb.)

SADECE JSON formatında yanıt ver, başka hiçbir şey yazma:
{
  "date": "bugünün tarihi",
  "words": [
    {
      "word": "kelime",
      "type": "adj",
      "turkish": "türkçe anlam",
      "sentence": "örnek cümle",
      "sentence_tr": "cümlenin türkçesi"
    }
  ],
  "grammar": {
    "topic": "konu adı",
    "explanation": "kısa açıklama",
    "examples": [
      {"en": "ingilizce örnek", "tr": "türkçe çeviri"}
    ]
  }
}"""

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": ANTHROPIC_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": "claude-haiku-4-5-20251001",
                    "max_tokens": 2000,
                    "messages": [{"role": "user", "content": prompt}]
                }
            )
            log.info(f"Anthropic yanıtı: {r.status_code} — {r.text[:300]}")
            text = r.json()["content"][0]["text"]
            text = text.replace("```json", "").replace("```", "").strip()
            return json.loads(text)
    except Exception as e:
        log.error(f"Anthropic hatası: {e}")
        return None

# ─── MESAJ FORMATI ────────────────────────────────────────────────────────────
def format_message(data):
    today = datetime.now(ZoneInfo("Europe/Istanbul")).strftime("%d %B %Y")
    msg = f"📚 *Günlük İngilizce — {today}*\n\n"
    msg += "🔤 *Bugünün Kelimeleri*\n\n"

    for i, w in enumerate(data["words"], 1):
        msg += f"{i}\\. *{w['word']}* _({w['type']})_ — {w['turkish']}\n"
        msg += f"   → _{w['sentence']}_\n"
        msg += f"   → _{w['sentence_tr']}_\n\n"

    msg += "━━━━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"📖 *Bugünün Gramer Konusu: {data['grammar']['topic']}*\n\n"
    msg += f"{data['grammar']['explanation']}\n\n"

    for ex in data["grammar"]["examples"]:
        msg += f"✅ _{ex['en']}_\n"
        msg += f"   _{ex['tr']}_\n\n"

    return msg

# ─── GÜNLÜK GÖNDERİM ─────────────────────────────────────────────────────────
async def send_daily(bot: Bot):
    log.info("İçerik hazırlanıyor...")
    data = await get_english_content()
    if not data:
        log.error("İçerik alınamadı!")
        return

    msg = format_message(data)
    await bot.send_message(
        chat_id=CHAT_ID,
        text=msg,
        parse_mode="MarkdownV2",
        message_thread_id=TOPIC_ID,
    )
    log.info("Günlük içerik gönderildi ✅")

async def daily_loop(bot: Bot):
    while True:
        try:
            now      = datetime.now(TIMEZONE)
            next_run = now.replace(hour=SEND_HOUR, minute=SEND_MIN, second=0, microsecond=0)
            if now >= next_run:
                next_run += timedelta(days=1)
            wait = (next_run - now).total_seconds()
            log.info(f"Sonraki gönderim: {next_run.strftime('%d-%m-%Y %H:%M')} TSİ")
            await asyncio.sleep(wait)
            await send_daily(bot)
        except Exception as e:
            log.error(f"Döngü hatası: {e}")
            await asyncio.sleep(60)

async def main():
    bot = Bot(token=BOT_TOKEN)
    log.info("İngilizce botu başladı ✅")
    await daily_loop(bot)

if __name__ == "__main__":
    asyncio.run(main())

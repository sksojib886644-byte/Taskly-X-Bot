import re
import json
import io
import telebot
from telebot import types
import openpyxl
import requests

BOT_TOKEN = "8812072288:AAFsl44BbG9O1O7z_9ng0yGfwJUKJ1r6rZg"
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# ইউজার স্টেট ও ডেটা সংরক্ষণ
user_states = {}
user_data = {}


def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_check = types.KeyboardButton("🔍 একাউন্ট চেক")
    btn_accs = types.KeyboardButton("📦 ACCSmarket সাবমিট")
    btn_sep = types.KeyboardButton("✂️ চিহ্ন বসানো")
    btn_token = types.KeyboardButton("🍪 কুকিজ থেকে টোকেন")
    btn_clear = types.KeyboardButton("🗑️ রিসেট")
    markup.add(btn_check, btn_accs, btn_sep, btn_token, btn_clear)
    return markup


def separator_menu():
    markup = types.InlineKeyboardMarkup(row_width=3)
    markup.add(
        types.InlineKeyboardButton("চিহ্ন: (:)", callback_data="sep::"),
        types.InlineKeyboardButton("চিহ্ন: (|)", callback_data="sep:|"),
        types.InlineKeyboardButton("চিহ্ন: (/)", callback_data="sep:/"),
        types.InlineKeyboardButton("চিহ্ন: (;)", callback_data="sep:;"),
        types.InlineKeyboardButton("চিহ্ন: (স্পেস)", callback_data="sep:SPACE"),
        types.InlineKeyboardButton("চিহ্ন: (নতুন লাইন)", callback_data="sep:NEWLINE"),
    )
    return markup


def accs_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("👤 ইউজারনেম বের করুন", callback_data="accs:usernames"),
        types.InlineKeyboardButton("♻️ ডুপ্লিকেট বাদ দিন", callback_data="accs:dedup"),
        types.InlineKeyboardButton("📊 XLSX ফাইল তৈরি", callback_data="accs:xlsx"),
        types.InlineKeyboardButton("📄 TXT ফাইল তৈরি", callback_data="accs:txt"),
    )
    return markup


def check_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📋 ফরম্যাট ভ্যালিডেট", callback_data="chk:format"),
        types.InlineKeyboardButton("🌐 লাইভ প্রোফাইল চেক", callback_data="chk:live"),
    )
    return markup


def extract_usernames(text):
    usernames = []
    for line in text.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        # username:password:2fa ফরম্যাট হলে প্রথম অংশ নেওয়া
        part = re.split(r"[:|\s]+", line)[0].strip()
        part = part.lstrip("@")
        if part:
            usernames.append(part)
    return usernames


def apply_separator(text, sep):
    lines = [ln.strip() for ln in text.strip().splitlines() if ln.strip()]
    output_lines = []
    for ln in lines:
        tokens = re.split(r"[:|;/,\t]+|\s+", ln)
        tokens = [t.strip() for t in tokens if t.strip()]
        if sep == "SPACE":
            output_lines.append(" ".join(tokens))
        elif sep == "NEWLINE":
            output_lines.append("\n".join(tokens))
        else:
            output_lines.append(sep.join(tokens))
    return "\n".join(output_lines)


def extract_tokens_from_cookies(raw_text):
    found = []
    raw_text = raw_text.strip()

    # ১) JSON আকারে কুকিজ থাকলে
    try:
        parsed = json.loads(raw_text)
        items = parsed if isinstance(parsed, list) else [parsed]
        for obj in items:
            if isinstance(obj, dict):
                name = str(obj.get("name", "")).lower()
                val = obj.get("value")
                if any(k in name for k in ["auth_token", "ct0", "token", "session"]):
                    if val:
                        found.append(f"{obj.get('name')}: {val}")
    except Exception:
        pass

    # ২) Header / Key=Value আকারে থাকলে
    patterns = [
        r"(?:auth_token|ct0|access_token|token)\s*=\s*([A-Za-z0-9_\-\.%]+)",
        r'"(?:auth_token|ct0|access_token|token)"\s*:\s*"([^"]+)"',
    ]
    for pat in patterns:
        for match in re.findall(pat, raw_text, flags=re.IGNORECASE):
            if match not in found:
                found.append(match)

    return found


def build_xlsx_bytes(lines):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Accounts"
    ws.append(["Account Data"])
    for ln in lines:
        ws.append([ln])
    bio = io.BytesIO()
    wb.save(bio)
    bio.seek(0)
    return bio


@bot.message_handler(commands=["start"])
def handle_start(message):
    uid = message.from_user.id
    user_states[uid] = None
    bot.send_message(
        message.chat.id,
        "স্বাগতম! নিচের যেকোনো বাটন চাপুন এবং আপনার লিস্ট বা কুকিজ পাঠান:\n\n"
        "• <b>একাউন্ট চেক</b>: ফরম্যাট বা লাইভ প্রোফাইল যাচাই\n"
        "• <b>ACCSmarket সাবমিট</b>: ইউজারনেম, ডুপ্লিকেট রিমুভ, XLSX/TXT\n"
        "• <b>চিহ্ন বসানো</b>: আলাদা চিহ্ন দিয়ে ফরম্যাট সাজানো\n"
        "• <b>কুকিজ থেকে টোকেন</b>: কুকিজ থেকে টোকেন আলাদা করা",
        reply_markup=main_menu(),
    )


@bot.message_handler(func=lambda m: m.text == "🗑️ রিসেট")
def handle_reset(message):
    uid = message.from_user.id
    user_states[uid] = None
    user_data.pop(uid, None)
    bot.send_message(message.chat.id, "সব ডেটা ও স্টেট রিসেট করা হয়েছে।", reply_markup=main_menu())


@bot.message_handler(func=lambda m: m.text == "🔍 একাউন্ট চেক")
def handle_check_btn(message):
    uid = message.from_user.id
    user_states[uid] = "WAITING_CHECK_INPUT"
    bot.send_message(
        message.chat.id,
        "একাউন্ট লিস্ট পাঠান (প্রতি লাইনে একটি করে):\n\n"
        "পাঠানোর পর নিচের চেক অপশন বেছে নিতে পারবেন।",
        reply_markup=check_menu(),
    )


@bot.message_handler(func=lambda m: m.text == "📦 ACCSmarket সাবমিট")
def handle_accs_btn(message):
    uid = message.from_user.id
    user_states[uid] = "WAITING_ACCS_INPUT"
    bot.send_message(
        message.chat.id,
        "ACCSmarket-এর জন্য একাউন্ট লিস্ট পাঠান:\n"
        "• ইউজারনেম বের করা\n"
        "• ডুপ্লিকেট বাদ দেওয়া\n"
        "• XLSX বা TXT ফাইল তৈরি",
        reply_markup=accs_menu(),
    )


@bot.message_handler(func=lambda m: m.text == "✂️ চিহ্ন বসানো")
def handle_sep_btn(message):
    uid = message.from_user.id
    user_states[uid] = "WAITING_SEP_INPUT"
    bot.send_message(
        message.chat.id,
        "যে লিস্টের মাঝে চিহ্ন বসাতে চান তা পাঠান, তারপর বাটন থেকে চিহ্ন সিলেক্ট করুন:",
        reply_markup=separator_menu(),
    )


@bot.message_handler(func=lambda m: m.text == "🍪 কুকিজ থেকে টোকেন")
def handle_token_btn(message):
    uid = message.from_user.id
    user_states[uid] = "WAITING_COOKIE_INPUT"
    bot.send_message(
        message.chat.id,
        "কুকিজ (JSON বা Cookie স্ট্রিং) পাঠান—আমি টোকেনগুলো বের করে দিচ্ছি।",
    )


@bot.message_handler(content_types=["text"])
def handle_text_input(message):
    uid = message.from_user.id
    text = message.text.strip()
    state = user_states.get(uid)

    if state == "WAITING_COOKIE_INPUT":
        tokens = extract_tokens_from_cookies(text)
        if not tokens:
            bot.send_message(message.chat.id, "কুকিজ থেকে কোনো টোকেন পাওয়া যায়নি।")
            return
        result = "\n".join(tokens)
        bot.send_message(message.chat.id, f"<b>পাওয়া টোকেন ({len(tokens)}):</b>\n<code>{result}</code>")
        return

    # সাধারণ লিস্ট সংরক্ষণ ও অপশন দেখানো
    user_data[uid] = text
    lines_count = len([ln for ln in text.splitlines() if ln.strip()])

    if state == "WAITING_SEP_INPUT":
        bot.send_message(
            message.chat.id,
            f"মোট <b>{lines_count}</b> লাইন রিসিভ হয়েছে। কোন চিহ্ন বসাবেন তা সিলেক্ট করুন:",
            reply_markup=separator_menu(),
        )
    elif state == "WAITING_ACCS_INPUT":
        bot.send_message(
            message.chat.id,
            f"মোট <b>{lines_count}</b> লাইন রিসিভ হয়েছে। কী করতে চান তা বেছে নিন:",
            reply_markup=accs_menu(),
        )
    else:
        bot.send_message(
            message.chat.id,
            f"মোট <b>{lines_count}</b> লাইন রিসিভ হয়েছে। নিচের যেকোনো বাটন চাপুন:",
            reply_markup=check_menu(),
        )


@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    uid = call.from_user.id
    data = call.data
    raw = user_data.get(uid, "")

    if not raw:
        bot.answer_callback_query(call.id, "আগে লিস্ট পাঠান!")
        return

    # ১) চিহ্ন বসানোর বাটন
    if data.startswith("sep:"):
        sep = data.split(":", 1)[1]
        formatted = apply_separator(raw, sep)
        bot.send_message(call.message.chat.id, f"<code>{formatted}</code>")
        bot.answer_callback_query(call.id, "চিহ্ন বসানো হয়েছে")
        return

    # ২) ACCSmarket বাটনগুলো
    if data.startswith("accs:"):
        action = data.split(":", 1)[1]
        lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]

        if action == "usernames":
            users = extract_usernames(raw)
            one_line = " ".join(users)
            col_a = "\n".join(users)
            bot.send_message(
                call.message.chat.id,
                f"<b>মোট ইউজারনেম: {len(users)}</b>\n\n"
                f"<b>এক লাইনে:</b>\n<code>{one_line}</code>\n\n"
                f"<b>A কলামে:</b>\n<code>{col_a}</code>",
            )
            bot.answer_callback_query(call.id, "ইউজারনেম বের করা হয়েছে")

        elif action == "dedup":
            unique_lines = list(dict.fromkeys(lines))
            removed = len(lines) - len(unique_lines)
            bot.send_message(
                call.message.chat.id,
                f"ডুপ্লিকেট বাদ দেওয়া হয়েছে (বাদ পড়েছে: <b>{removed}</b>, বাকি: <b>{len(unique_lines)}</b>):\n\n"
                f"<code>" + "\n".join(unique_lines) + "</code>",
            )
            bot.answer_callback_query(call.id, "ডুপ্লিকেট রিমুভ হয়েছে")

        elif action == "xlsx":
            xlsx_bio = build_xlsx_bytes(lines)
            bot.send_document(
                call.message.chat.id,
                xlsx_bio,
                visible_file_name="accsmarket_accounts.xlsx",
                caption="ACCSmarket সাবমিশনের জন্য XLSX ফাইল তৈরি হয়েছে।",
            )
            bot.answer_callback_query(call.id, "XLSX তৈরি হয়েছে")

        elif action == "txt":
            txt_bio = io.BytesIO("\n".join(lines).encode("utf-8"))
            txt_bio.seek(0)
            bot.send_document(
                call.message.chat.id,
                txt_bio,
                visible_file_name="accsmarket_accounts.txt",
                caption="TXT ফাইল তৈরি হয়েছে।",
            )
            bot.answer_callback_query(call.id, "TXT তৈরি হয়েছে")
        return

    # ৩) একাউন্ট চেক বাটনগুলো
    if data.startswith("chk:"):
        mode = data.split(":", 1)[1]
        lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]

        if mode == "format":
            valid = []
            invalid = []
            for ln in lines:
                parts = ln.split(":")
                if len(parts) >= 2 and all(p.strip() for p in parts[:2]):
                    valid.append(ln)
                else:
                    invalid.append(ln)
            bot.send_message(
                call.message.chat.id,
                f"<b>ফরম্যাট চেক রেজাল্ট:</b>\n"
                f"• সঠিক ফরম্যাট: <b>{len(valid)}</b>\n"
                f"• অসম্পূর্ণ/ভুল ফরম্যাট: <b>{len(invalid)}</b>"
                + (f"\n\n<code>" + "\n".join(invalid) + "</code>" if invalid else ""),
            )
            bot.answer_callback_query(call.id, "ফরম্যাট চেক সম্পন্ন")

        elif mode == "live":
            users = extract_usernames(raw)
            live_ok = []
            not_found = []
            for u in users[:25]:  # রেট লিমিট এড়াতে প্রথম ২৫টি দ্রুত চেক
                try:
                    r = requests.get(f"https://x.com/{u}", timeout=8, allow_redirects=True)
                    if r.status_code == 200:
                        live_ok.append(u)
                    else:
                        not_found.append(f"{u} (HTTP {r.status_code})")
                except Exception:
                    not_found.append(f"{u} (Error)")
            bot.send_message(
                call.message.chat.id,
                f"<b>লাইভ চেক (প্রথম {min(len(users), 25)}টি):</b>\n"
                f"• রেসপন্স পাওয়া গেছে: <b>{len(live_ok)}</b>\n"
                f"• সমস্যা/নেই: <b>{len(not_found)}</b>\n"
                + ("\n".join(not_found) if not_found else ""),
            )
            bot.answer_callback_query(call.id, "লাইভ চেক সম্পন্ন")


if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling(skip_pending=True)
        

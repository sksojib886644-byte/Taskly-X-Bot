import re
import json
import io
import telebot
from telebot import types
import openpyxl

BOT_TOKEN = "8812072288:AAGAnsCmP2-IdgLoe3U6jPsOwGZ-OjK6wbw"
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

user_states = {}
user_data = {}


def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_check = types.KeyboardButton("🔍 একাউন্ট চেক")
    btn_accs = types.KeyboardButton("📦 সাবমিট")
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
        types.InlineKeyboardButton("🛡️ নিরাপদ একাউন্ট চেক", callback_data="chk:safe"),
        types.InlineKeyboardButton("📋 ফরম্যাট ভ্যালিডেট", callback_data="chk:format"),
    )
    return markup


def extract_usernames(text):
    usernames = []
    for line in text.strip().splitlines():
        line = line.strip()
        if not line:
            continue
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


def parse_uploaded_file(file_bytes, filename):
    fname = (filename or "").lower()
    extracted_lines = []

    if fname.endswith(".xlsx"):
        wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
        for ws in wb.worksheets:
            for row in ws.iter_rows(values_only=True):
                if not row:
                    continue
                non_empty = [str(c).strip() for c in row if c is not None and str(c).strip()]
                if not non_empty:
                    continue
                if len(non_empty) == 1 and non_empty[0].lower() in ["account data", "accounts", "username", "usernames"]:
                    continue
                if len(non_empty) >= 3:
                    extracted_lines.append(":".join(non_empty[:3]))
                else:
                    extracted_lines.append(" ".join(non_empty))
    else:
        text = file_bytes.decode("utf-8", errors="ignore")
        for ln in text.splitlines():
            if ln.strip():
                extracted_lines.append(ln.strip())

    return "\n".join(extracted_lines)


def safe_account_audit(lines):
    """
    একাউন্টে লগইন বা সরাসরি X-এ হিট না করে নিরাপদে চেক করে
    যাতে ভালো একাউন্ট সাসপেন্ড হওয়ার ঝুঁকি না বাড়ে।
    """
    clean_ready = []
    flagged = []
    seen_users = set()

    for ln in lines:
        line = ln.strip()
        parts = line.split(":")
        user = parts[0].strip().lstrip("@") if parts else ""

        reasons = []
        if not re.match(r"^[A-Za-z0-9_]{1,15}$", user):
            reasons.append("অস্বাভাবিক ইউজারনেম")
        if user.lower() in seen_users:
            reasons.append("ডুপ্লিকেট ইউজারনেম")
        if len(parts) < 2 or not parts[1].strip():
            reasons.append("পাসওয়ার্ড নেই")
        if len(parts) < 3 or not re.sub(r"\s+", "", parts[2]):
            reasons.append("2FA কী নেই")

        if reasons:
            flagged.append(f"{line}  -->  ({', '.join(reasons)})")
        else:
            seen_users.add(user.lower())
            clean_ready.append(line)

    return clean_ready, flagged


def send_menu_for_state(chat_id, uid, lines_count, source_label="ডেটা"):
    state = user_states.get(uid)
    msg = f"{source_label} থেকে মোট <b>{lines_count}</b> লাইন রিসিভ হয়েছে। নিচের অপশন থেকে কাজ বেছে নিন:"

    if state == "WAITING_SEP_INPUT":
        bot.send_message(chat_id, msg, reply_markup=separator_menu())
    elif state == "WAITING_ACCS_INPUT":
        bot.send_message(chat_id, msg, reply_markup=accs_menu())
    else:
        bot.send_message(chat_id, msg, reply_markup=check_menu())


@bot.message_handler(commands=["start"])
def handle_start(message):
    uid = message.from_user.id
    user_states[uid] = None
    bot.send_message(
        message.chat.id,
        "স্বাগতম! টেক্সট লিস্ট অথবা <b>.xlsx / .txt</b> ফাইল পাঠান এবং নিচের বাটন ব্যবহার করুন:\n\n"
        "• <b>একাউন্ট চেক</b>: একাউন্ট সাসপেন্ডের ঝুঁকি ছাড়া নিরাপদ চেক ও ফরম্যাট যাচাই\n"
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
        "একাউন্ট লিস্ট বা <b>.xlsx / .txt</b> ফাইল পাঠান (একাউন্টে লগইন বা X-এ হিট করা হবে না):",
        reply_markup=check_menu(),
    )


@bot.message_handler(func=lambda m: m.text == "📦 ACCSmarket সাবমিট")
def handle_accs_btn(message):
    uid = message.from_user.id
    user_states[uid] = "WAITING_ACCS_INPUT"
    bot.send_message(
        message.chat.id,
        "ACCSmarket-এর জন্য একাউন্ট লিস্ট বা <b>.xlsx / .txt</b> ফাইল পাঠান:",
        reply_markup=accs_menu(),
    )


@bot.message_handler(func=lambda m: m.text == "✂️ চিহ্ন বসানো")
def handle_sep_btn(message):
    uid = message.from_user.id
    user_states[uid] = "WAITING_SEP_INPUT"
    bot.send_message(
        message.chat.id,
        "যে লিস্ট বা ফাইলের মাঝে চিহ্ন বসাতে চান তা পাঠান, তারপর বাটন থেকে চিহ্ন সিলেক্ট করুন:",
        reply_markup=separator_menu(),
    )


@bot.message_handler(func=lambda m: m.text == "🍪 কুকিজ থেকে টোকেন")
def handle_token_btn(message):
    uid = message.from_user.id
    user_states[uid] = "WAITING_COOKIE_INPUT"
    bot.send_message(
        message.chat.id,
        "কুকিজ (JSON বা Cookie স্ট্রিং) অথবা ফাইল পাঠান—আমি টোকেনগুলো বের করে দিচ্ছি।",
    )


@bot.message_handler(content_types=["document"])
def handle_document_input(message):
    uid = message.from_user.id
    doc = message.document
    try:
        file_info = bot.get_file(doc.file_id)
        downloaded = bot.download_file(file_info.file_path)

        if user_states.get(uid) == "WAITING_COOKIE_INPUT":
            text_data = downloaded.decode("utf-8", errors="ignore")
            tokens = extract_tokens_from_cookies(text_data)
            if not tokens:
                bot.send_message(message.chat.id, "ফাইল থেকে কোনো টোকেন পাওয়া যায়নি।")
                return
            bot.send_message(
                message.chat.id,
                f"<b>পাওয়া টোকেন ({len(tokens)}):</b>\n<code>" + "\n".join(tokens) + "</code>",
            )
            return

        parsed_text = parse_uploaded_file(downloaded, doc.file_name)
        lines_count = len([ln for ln in parsed_text.splitlines() if ln.strip()])

        if lines_count == 0:
            bot.send_message(message.chat.id, "ফাইলটি খালি বা পড়া যায়নি।")
            return

        user_data[uid] = parsed_text
        send_menu_for_state(message.chat.id, uid, lines_count, source_label=f"ফাইল ({doc.file_name})")

    except Exception as e:
        bot.send_message(message.chat.id, f"ফাইল প্রসেস করতে সমস্যা হয়েছে: <code>{e}</code>")


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

    user_data[uid] = text
    lines_count = len([ln for ln in text.splitlines() if ln.strip()])
    send_menu_for_state(message.chat.id, uid, lines_count, source_label="টেক্সট")


@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    uid = call.from_user.id
    data = call.data
    raw = user_data.get(uid, "")

    if not raw:
        bot.answer_callback_query(call.id, "আগে লিস্ট বা ফাইল পাঠান!")
        return

    if data.startswith("sep:"):
        sep = data.split(":", 1)[1]
        formatted = apply_separator(raw, sep)
        bot.send_message(call.message.chat.id, f"<code>{formatted}</code>")
        bot.answer_callback_query(call.id, "চিহ্ন বসানো হয়েছে")
        return

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

    if data.startswith("chk:"):
        mode = data.split(":", 1)[1]
        lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]

        if mode == "safe":
            clean_ready, flagged = safe_account_audit(lines)
            # ক্লিন লিস্ট সেভ রাখা যাতে পরের বাটনে সহজে ব্যবহার করা যায়
            if clean_ready:
                user_data[uid] = "\n".join(clean_ready)
            msg = (
                f"<b>নিরাপদ একাউন্ট চেক (সাসপেন্ডের ঝুঁকি ছাড়া):</b>\n"
                f"• রেডি / ক্লিন একাউন্ট: <b>{len(clean_ready)}</b>\n"
                f"• সমস্যাযুক্ত / চেক দরকার: <b>{len(flagged)}</b>"
            )
            if flagged:
                msg += "\n\n<b>সমস্যাযুক্ত লাইন:</b>\n<code>" + "\n".join(flagged[:30]) + "</code>"
            bot.send_message(call.message.chat.id, msg)
            bot.answer_callback_query(call.id, "নিরাপদ চেক সম্পন্ন")

        elif mode == "format":
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


if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling(skip_pending=True)

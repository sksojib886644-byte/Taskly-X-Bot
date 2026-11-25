import telebot
import requests
import time
import random
import string
import re
import datetime
import pyotp
import io
import openpyxl
import threading
import os
import hashlib
from flask import Flask

app = Flask('')

@app.route('/')
def home():
    return "Bot is active and running 24/7!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

TOKEN = '8666711380:AAFFgOFaFWFG7UzUtraqjAuFUZ5231_8BLQ'
CHANNEL_USERNAME = '@taandob7'
ADMIN_ID = 8702921423
BOT_USERNAME = 'TasklyX_BD_Bot'

bot = telebot.TeleBot(TOKEN, parse_mode=None)

SETTINGS = {
    'task1_name': 'Twitter_2fa_auth_token',
    'task2_name': 'Twitter_2FA_Only',
    'reward_tw_token': 0.03,
    'reward_tw_2fa': 0.03,
    'usd_to_bdt': 125.0,
    'withdraw_fee_bdt': 5.0,
    'min_withdraw_bdt': 5.0,
    'withdraw_enabled': True,
    'bkash_enabled': True,
    'nagad_enabled': True,
    'binance_enabled': True,
    'pwd_mode': 'random',
    'pwd_target_task': 'BOTH',
    'custom_pwd_value': 'TasklyABC',
    'pwd_length': 10,
    'auto_report_enabled': False,
    'auto_report_task': 'ALL',
    'auto_report_interval': 30,
    'auto_approve_pct': 80.0,
    'custom_check_reject_pct': 2.8,
    'custom_check_reject_enabled': True,
    'extractor_colon_enabled': False,
    'admin_pin': '4875',
    'top_enabled': True,
    'top_reset_mode': 'daily_10pm',
    'top_reset_interval_mins': 1440,
    'top_reset_timestamp': time.time() + 86400,
    'last_top_reset_date': '',
    'top_rewards': {1: 1.00, 2: 0.50, 3: 0.30, 4: 0.20, 5: 0.10},
    'ref_enabled': True,
    'ref_commission_pct': 10.0,
    'tw_2fa_enabled': True,
    'tw_token_enabled': True,
    'task_report_timer_text': 'Every 30 minutes'
}

videos_list = [
    {
        'title': 'Twitter Account Creation Guide',
        'type': 'url',
        'content': 'https://t.me/'
    }
]

FIRST_NAMES = ['tracy', 'tanvir', 'sakib', 'rahim', 'karim', 'arif', 'hasan', 'mahmud', 'faysal', 'sohel', 'nayan', 'rakib', 'imran', 'fahim', 'joy', 'roni']

users = {}
active_mails = {}
user_steps = {}
user_acc_data = {}
submitted_accounts = []
rejected_accounts_db = []
rejected_history_db = set()
used_emails_db = set()
used_codes_db = set()
withdraw_requests = []
blocked_users = set()
lifetime_usernames = set()
downloaded_status = {'task1': False, 'task2': False}

def get_user_data(user_id, name="User", username=None):
    if user_id not in users:
        users[user_id] = {
            'name': name,
            'username': username,
            'balance': 0.0,
            'total_earned': 0.0,
            'completed_tasks': 0,
            'referral_count': 0,
            'ref_earned': 0.0,
            'referrals_list': []
        }
    elif username and not users[user_id].get('username'):
        users[user_id]['username'] = username
    return users[user_id]

def is_subscribed(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ['creator', 'administrator', 'member']
    except Exception:
        return False

def main_keyboard(user_id):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(telebot.types.KeyboardButton("💰 Balance"), telebot.types.KeyboardButton("📋 Tasks"))
    markup.row(telebot.types.KeyboardButton("📤 Withdraw"), telebot.types.KeyboardButton("👤 Profile"))
    markup.row(telebot.types.KeyboardButton("🏆 Top Leaderboard"), telebot.types.KeyboardButton("👥 Referral"))
    markup.row(telebot.types.KeyboardButton("🎬 Video Tutorial"))
    if user_id == ADMIN_ID:
        markup.row(telebot.types.KeyboardButton("👑 Admin Panel"))
    return markup

def tasks_keyboard():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    r_token = SETTINGS['reward_tw_token']
    r_2fa = SETTINGS['reward_tw_2fa']
    t1_name = SETTINGS['task1_name']
    t2_name = SETTINGS['task2_name']

    if SETTINGS.get('tw_token_enabled', True):
        markup.row(telebot.types.KeyboardButton(f"🐦 {t1_name} (${r_token:.4f})"))
    if SETTINGS.get('tw_2fa_enabled', True):
        markup.row(telebot.types.KeyboardButton(f"🔥 {t2_name} (${r_2fa:.4f})"))
    markup.row(telebot.types.KeyboardButton("❌ Cancel"))
    return markup

def admin_panel_keyboard():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(telebot.types.KeyboardButton("📤 Withdraw Requests"), telebot.types.KeyboardButton("🔍 Search UID/Username"))
    markup.row(telebot.types.KeyboardButton("🔑 Extract Auth Token from Sheet"), telebot.types.KeyboardButton("⚡ Batch Approve / Percentage"))
    markup.row(telebot.types.KeyboardButton("🛠️ Task Control"), telebot.types.KeyboardButton("💰 Change Price"))
    markup.row(telebot.types.KeyboardButton("✏️ Change Task Names"), telebot.types.KeyboardButton("🔐 Password Management"))
    markup.row(telebot.types.KeyboardButton("⚙️ Payment Methods"), telebot.types.KeyboardButton("👥 Referral Management"))
    markup.row(telebot.types.KeyboardButton("👥 User Management"), telebot.types.KeyboardButton("📢 Broadcast Message"))
    markup.row(telebot.types.KeyboardButton("🎬 Video Management"), telebot.types.KeyboardButton("📊 Task 1 Excel"))
    markup.row(telebot.types.KeyboardButton("📊 Task 2 Excel (2FA)"), telebot.types.KeyboardButton("🔍 Check Accounts via Username"))
    markup.row(telebot.types.KeyboardButton("📥 Custom Username Check"), telebot.types.KeyboardButton("📊 Database Stats"))
    markup.row(telebot.types.KeyboardButton("📦 Submit Ready"), telebot.types.KeyboardButton("🚫 ACCSmarket Rejected Usernames"))
    markup.row(telebot.types.KeyboardButton("🏠 Main Menu"))
    return markup

def search_pending_menu():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(telebot.types.KeyboardButton("🔍 Search UID / Username"), telebot.types.KeyboardButton("📊 Download Pending Accounts Excel"))
    markup.row(telebot.types.KeyboardButton("👑 Admin Panel"))
    return markup

def check_accounts_username_menu():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(telebot.types.KeyboardButton("🔍 Check All Submitted Accounts"), telebot.types.KeyboardButton("🐦 Check Task 1 Accounts"))
    markup.row(telebot.types.KeyboardButton("🔥 Check Task 2 Accounts"), telebot.types.KeyboardButton("👑 Admin Panel"))
    return markup

def database_stats_keyboard():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(telebot.types.KeyboardButton("📁 Upload Lifetime Excel"), telebot.types.KeyboardButton("📈 View Stats"))
    markup.row(telebot.types.KeyboardButton("🔍 Filter New vs Old Excel"))
    markup.row(telebot.types.KeyboardButton("👑 Admin Panel"))
    return markup

def batch_panel_keyboard():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    rej_st = "🟢 ON" if SETTINGS.get('custom_check_reject_enabled', True) else "🔴 OFF"
    markup.row(telebot.types.KeyboardButton("✅ Batch Approve Usernames"), telebot.types.KeyboardButton("❌ Batch Reject Usernames"))
    markup.row(telebot.types.KeyboardButton("📊 Percentage Auto Process"), telebot.types.KeyboardButton("📉 Percentage Reject Process"))
    markup.row(telebot.types.KeyboardButton(f"🔄 Toggle Reject Sys: {rej_st}"))
    markup.row(telebot.types.KeyboardButton("👑 Admin Panel"))
    return markup

def excel_task1_menu():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(telebot.types.KeyboardButton("📊 Download Excel: Task 1"), telebot.types.KeyboardButton("🗑️ Delete Task 1 Accounts"))
    markup.row(telebot.types.KeyboardButton("👑 Admin Panel"))
    return markup

def excel_2fa_menu():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(telebot.types.KeyboardButton("📊 Download Excel: 2FA"), telebot.types.KeyboardButton("🗑️ Delete 2FA Accounts"))
    markup.row(telebot.types.KeyboardButton("👑 Admin Panel"))
    return markup

def password_mgmt_keyboard():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    mode = SETTINGS.get('pwd_mode', 'random')
    m_rand = "✅ Random" if mode == 'random' else "Random"
    m_rand_date = "✅ Random + Date" if mode == 'random_date' else "Random + Date"
    m_same = "✅ Custom / Same" if mode == 'same' else "Custom / Same"

    target = SETTINGS.get('pwd_target_task', 'BOTH')
    t_text = f"Target Task: {target}"

    markup.row(telebot.types.KeyboardButton(f"Mode: {m_rand}"), telebot.types.KeyboardButton(f"Mode: {m_rand_date}"))
    markup.row(telebot.types.KeyboardButton(f"Mode: {m_same}"), telebot.types.KeyboardButton("✍️ Set Custom Password"))
    markup.row(telebot.types.KeyboardButton(f"🔄 {t_text}"))
    markup.row(telebot.types.KeyboardButton("👑 Admin Panel"))
    return markup

def referral_mgmt_keyboard():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    ref_st = "🟢 ON" if SETTINGS.get('ref_enabled', True) else "🔴 OFF"
    markup.row(telebot.types.KeyboardButton(f"Toggle Referral: {ref_st}"))
    markup.row(telebot.types.KeyboardButton("💰 Set Referral Commission %"))
    markup.row(telebot.types.KeyboardButton("👑 Admin Panel"))
    return markup

def top_control_keyboard():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    st = "🟢 ON" if SETTINGS.get('top_enabled', True) else "🔴 OFF"
    mode = SETTINGS.get('top_reset_mode')
    if mode == 'daily_10pm':
        mode_text = "Daily 10:00 PM"
    elif mode == 'sunday_10pm':
        mode_text = "Sunday 10:00 PM"
    else:
        mode_text = f"Every {SETTINGS.get('top_reset_interval_mins', 1440)} mins"

    markup.row(telebot.types.KeyboardButton(f"Toggle Leaderboard: {st}"))
    markup.row(telebot.types.KeyboardButton(f"Reset Schedule: {mode_text}"))
    markup.row(telebot.types.KeyboardButton("⏱️ Set Reset Minutes"))
    markup.row(telebot.types.KeyboardButton("🎁 Distribute Rewards & Reset Now"))
    markup.row(telebot.types.KeyboardButton("💰 Edit Rank Rewards"))
    markup.row(telebot.types.KeyboardButton("👑 Admin Panel"))
    return markup

def task_control_keyboard():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    t1 = "🟢 ON" if SETTINGS.get('tw_token_enabled', True) else "🔴 OFF"
    t2 = "🟢 ON" if SETTINGS.get('tw_2fa_enabled', True) else "🔴 OFF"
    markup.row(telebot.types.KeyboardButton(f"Toggle Task 1: {t1}"), telebot.types.KeyboardButton(f"Toggle Task 2: {t2}"))
    markup.row(telebot.types.KeyboardButton("⏱️ Set Report Timer Text"))
    markup.row(telebot.types.KeyboardButton("👑 Admin Panel"))
    return markup

def payment_toggle_keyboard():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    wd_st = "🟢 ON" if SETTINGS['withdraw_enabled'] else "🔴 OFF"
    bk_st = "🟢 ON" if SETTINGS['bkash_enabled'] else "🔴 OFF"
    ng_st = "🟢 ON" if SETTINGS['nagad_enabled'] else "🔴 OFF"
    bn_st = "🟢 ON" if SETTINGS['binance_enabled'] else "🔴 OFF"

    markup.row(telebot.types.KeyboardButton(f"Withdraw Sys: {wd_st}"), telebot.types.KeyboardButton(f"Bkash: {bk_st}"))
    markup.row(telebot.types.KeyboardButton(f"Nagad: {ng_st}"), telebot.types.KeyboardButton(f"Binance: {bn_st}"))
    markup.row(telebot.types.KeyboardButton("⚙️ Set Minimum Withdraw Limit"))
    markup.row(telebot.types.KeyboardButton("👑 Admin Panel"))
    return markup

def video_mgmt_keyboard():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(telebot.types.KeyboardButton("➕ Add Video File / Link"), telebot.types.KeyboardButton("🗑️ Remove All Videos"))
    markup.row(telebot.types.KeyboardButton("👑 Admin Panel"))
    return markup

def clear_user_chat_session(user_id, chat_messages_dict):
    if user_id in chat_messages_dict:
        for msg_id in chat_messages_dict[user_id]:
            try:
                bot.delete_message(user_id, msg_id)
            except Exception:
                pass
        chat_messages_dict[user_id] = []

def alter_string_slightly(text_str):
    s = str(text_str).strip()
    if not s or len(s) <= 2:
        return s + "x"

    val_list = list(s)
    middle_indices = list(range(1, len(val_list) - 1))

    letter_indices = [idx for idx in middle_indices if val_list[idx].isalpha()]
    if not letter_indices:
        letter_indices = middle_indices

    hash_val = int(hashlib.md5(s.encode('utf-8')).hexdigest(), 16)
    idx = letter_indices[hash_val % len(letter_indices)]

    current_char = val_list[idx]

    similar_map = {
        'I': 'l', 'l': 'I', 'i': 'l', 'L': 'I',
        'F': 'P', 'P': 'F', 'f': 'p', 'p': 'f',
        'O': 'o', 'o': 'O',
        'S': 's', 's': 'S',
        'C': 'c', 'c': 'C',
        'V': 'v', 'v': 'V',
        'W': 'w', 'w': 'W',
        'X': 'x', 'x': 'X',
        'Z': 'z', 'z': 'Z',
        'B': 'R', 'R': 'B',
    }

    if current_char in similar_map:
        new_char = similar_map[current_char]
    elif current_char.isalpha():
        if current_char.isupper():
            new_char = chr((ord(current_char) - 65 + 1) % 26 + 65)
        else:
            new_char = chr((ord(current_char) - 97 + 1) % 26 + 97)
    else:
        new_char = 'x'

    val_list[idx] = new_char
    return "".join(val_list)

def generate_unique_human_username():
    f_name = random.choice(FIRST_NAMES)
    random_digits = ''.join(random.choices(string.digits, k=2))
    random_chars = ''.join(random.choices(string.ascii_lowercase, k=2))
    return f"{f_name}{random_digits}{random_chars}"

def generate_password(task_name=None):
    target = SETTINGS.get('pwd_target_task', 'BOTH')
    if target != 'BOTH' and task_name:
        if target == 'task1' and task_name != SETTINGS['task1_name']:
            return ''.join(random.choices(string.ascii_letters + string.digits, k=10))
        if target == 'task2' and task_name != SETTINGS['task2_name']:
            return ''.join(random.choices(string.ascii_letters + string.digits, k=10))

    length = SETTINGS.get('pwd_length', 10)
    mode = SETTINGS.get('pwd_mode', 'random')
    chars = string.ascii_letters + string.digits

    if mode == 'same':
        return SETTINGS.get('custom_pwd_value', 'TasklyABC')
    elif mode == 'random_date':
        letters_part = ''.join(random.choices(string.ascii_letters, k=max(4, length - 2)))
        date_part = datetime.datetime.now().strftime("%d")
        return f"{letters_part}{date_part}"
    else:
        return ''.join(random.choices(chars, k=length))

def get_mailtm_domain():
    try:
        res = requests.get("https://api.mail.tm/domains", timeout=5)
        if res.status_code == 200:
            domains = res.json().get('hydra:member', [])
            if domains:
                return domains[0]['domain']
    except Exception:
        pass
    return "gmail.com"

def create_mailtm_account(task_name=None):
    for _ in range(5):
        domain = get_mailtm_domain()
        username = generate_unique_human_username()
        email = f"{username}@{domain}"
        if email.lower() not in used_emails_db:
            password = generate_password(task_name)
            try:
                payload = {"address": email, "password": password}
                res = requests.post("https://api.mail.tm/accounts", json=payload, timeout=7)
                if res.status_code in [200, 201]:
                    token_res = requests.post("https://api.mail.tm/token", json=payload, timeout=7)
                    if token_res.status_code == 200:
                        token = token_res.json().get('token')
                        used_emails_db.add(email.lower())
                        return {'email': email, 'username': username, 'token': token, 'type': 'mailtm', 'password': password}
            except Exception:
                pass
    return None

def fetch_twitter_code(token):
    if token == 'dummy_token':
        return str(random.randint(100000, 999999))
    for _ in range(5):
        try:
            headers = {"Authorization": f"Bearer {token}"}
            res = requests.get("https://api.mail.tm/messages", headers=headers, timeout=7)
            if res.status_code == 200:
                messages = res.json().get('hydra:member', [])
                for msg in messages:
                    sender = str(msg.get('from', {}).get('address', '')).lower()
                    subject = str(msg.get('subject', '')).lower()

                    if 'twitter' in sender or 'x.com' in sender or 'twitter' in subject or 'verification' in subject or 'confirm' in subject:
                        msg_id = msg.get('id')
                        msg_res = requests.get(f"https://api.mail.tm/messages/{msg_id}", headers=headers, timeout=7)
                        if msg_res.status_code == 200:
                            data = msg_res.json()
                            text_content = str(data.get('text', '')) + " " + str(data.get('subject', '')) + " " + str(data.get('intro', ''))
                            codes = re.findall(r'\b\d{6}\b', text_content)
                            if codes:
                                code = codes[0]
                                if code not in used_codes_db:
                                    used_codes_db.add(code)
                                    return code
        except Exception:
            pass
        time.sleep(3)
    return None

def extract_username(text):
    if not text:
        return None
    text = str(text).strip()
    match = re.search(r'(?:https?://(?:www\.)?(?:twitter|x)\.com/)?@?([a-zA-Z0-9_]{1,15})', text)
    if match:
        uname = match.group(1)
        if len(uname) >= 3 and uname.lower() not in ['http', 'https', 'com', 'twitter', 'x', 'account_data', 'accountdata']:
            return uname

    parts = re.split(r'[:|,\s\t]+', text)
    for part in parts:
        part_clean = part.replace('@', '').strip()
        if part_clean.lower() in ['account_data', 'accountdata', 'username']:
            continue
        if 3 <= len(part_clean) <= 15 and re.match(r'^[a-zA-Z0-9_]+$', part_clean):
            if not part_clean.isdigit():
                return part_clean
    return None

def extract_auth_token(text):
    text = str(text).strip()
    match = re.search(r'auth_token=([a-zA-Z0-9_-]+)', text)
    if match:
        return match.group(1)

    clean_text = text.replace('"', '').replace("'", "").split(';')[0].strip()
    if len(clean_text) >= 20:
        return clean_text
    return text

def check_status_by_username(username):
    if not username or str(username).strip() in ['', 'N/A']:
        return 'suspended'

    clean_username = str(username).replace('@', '').strip()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9'
    }

    try:
        url = f"https://x.com/{clean_username}"
        res = requests.get(url, headers=headers, timeout=8, allow_redirects=True)

        if res.status_code == 404:
            return 'suspended'

        html = (res.text or "").lower()
        suspended_markers = [
            "account suspended",
            "this account doesn’t exist",
            "this account doesn't exist",
            "user not found",
            "account has been suspended"
        ]
        if any(marker in html for marker in suspended_markers):
            return 'suspended'

        return 'active'
    except Exception as e:
        print(f"Username check warning for {clean_username}: {e}")
        return 'active'

def process_file_or_text_usernames(message):
    usernames_found = []
    if message.content_type == 'document':
        try:
            file_info = bot.get_file(message.document.file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            file_name = (message.document.file_name or '').lower()

            if file_name.endswith('.xlsx'):
                wb = openpyxl.load_workbook(io.BytesIO(downloaded_file))
                sheet = wb.active
                for row in sheet.iter_rows(values_only=True):
                    if not any(row):
                        continue
                    row_list = [str(c) if c is not None else "" for c in row]
                    if row_list and row_list[0]:
                        u = extract_username(row_list[0])
                        if u:
                            usernames_found.append(u)
            else:
                content = downloaded_file.decode('utf-8', errors='ignore')
                for line in content.splitlines():
                    u = extract_username(line)
                    if u:
                        usernames_found.append(u)
        except Exception as e:
            print(f"File error: {e}")
    elif message.content_type == 'text' and message.text:
        for line in message.text.splitlines():
            u = extract_username(line)
            if u:
                usernames_found.append(u)

    seen = set()
    return [x for x in usernames_found if not (x in seen or seen.add(x))]

def parse_full_accounts_file(message):
    rows_data = []
    if message.content_type == 'document':
        try:
            file_info = bot.get_file(message.document.file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            file_name = (message.document.file_name or '').lower()

            if file_name.endswith('.xlsx'):
                wb = openpyxl.load_workbook(io.BytesIO(downloaded_file))
                sheet = wb.active
                for row in sheet.iter_rows(values_only=True):
                    if not any(row):
                        continue
                    row_list = [str(c) if c is not None else "" for c in row]
                    uname = extract_username(row_list[0]) if row_list and row_list[0] else None
                    rows_data.append({'row': row_list, 'username': uname})
            else:
                content = downloaded_file.decode('utf-8', errors='ignore')
                for line in content.splitlines():
                    if not line.strip():
                        continue
                    parts = re.split(r'[:|,\s\t]+', line.strip())
                    uname = extract_username(parts[0]) if parts else None
                    rows_data.append({'row': [line.strip()], 'username': uname})
        except Exception as e:
            print(f"Parse file error: {e}")
    elif message.content_type == 'text' and message.text:
        for line in message.text.splitlines():
            if not line.strip():
                continue
            parts = re.split(r'[:|,\s\t]+', line.strip())
            uname = extract_username(parts[0]) if parts else None
            rows_data.append({'row': [line.strip()], 'username': uname})
    return rows_data

def format_accsmarket_ready_lines(rows_data):
    formatted_lines = []
    seen = set()

    for item in rows_data:
        row = item.get('row', [])
        non_empty = [str(c).strip() for c in row if c is not None and str(c).strip()]
        if not non_empty:
            continue

        joined_lower = " ".join(non_empty).lower().replace(":", "").replace("_", "").strip()
        if joined_lower in [
            "username", "account data", "accountdata", "accounts",
            "usernamepassword2fa", "username password 2fa",
            "username (column a)", "all usernames (one line)"
        ]:
            continue

        raw_tokens = []
        for cell in non_empty:
            parts = re.split(r'[:|\t]+|\s+', cell.strip())
            for p in parts:
                cleaned = p.strip().strip(":")
                if cleaned:
                    raw_tokens.append(cleaned)

        if not raw_tokens:
            continue

        raw_tokens[-1] = raw_tokens[-1].rstrip(":")
        line_str = ":".join(raw_tokens)

        key_lower = line_str.lower()
        if key_lower not in seen:
            seen.add(key_lower)
            formatted_lines.append(line_str)

    return formatted_lines

def extract_rejected_usernames(rows_data):
    usernames = []
    seen = set()

    for item in rows_data:
        row = item.get('row', [])
        joined_check = " ".join([str(c).strip().lower().replace("_", "") for c in row if c is not None and str(c).strip()])
        if joined_check in [
            "accountdata", "username", "account data", "accounts",
            "username (column a)", "all usernames (one line)"
        ]:
            continue

        uname = item.get('username')
        if not uname:
            for cell in row:
                u = extract_username(str(cell))
                if u:
                    uname = u
                    break
        if uname:
            clean_u = uname.lstrip('@').strip()
            if clean_u.lower() in ["account_data", "accountdata", "username"]:
                continue
            if clean_u and clean_u.lower() not in seen:
                seen.add(clean_u.lower())
                usernames.append(clean_u)

    return usernames

def approve_single_account(acc):
    if acc.get('status') == 'pending':
        acc['status'] = 'approved'
        target_uid = acc['user_id']
        rw = SETTINGS['reward_tw_token'] if acc.get('task_name') == SETTINGS['task1_name'] else SETTINGS['reward_tw_2fa']

        u_data = get_user_data(target_uid)
        u_data['balance'] += rw
        u_data['total_earned'] += rw
        u_data['completed_tasks'] += 1

        if SETTINGS.get('ref_enabled', True):
            referrer_id = u_data.get('referred_by')
            if referrer_id and referrer_id in users:
                pct = SETTINGS.get('ref_commission_pct', 10.0)
                commission = rw * (pct / 100.0)
                ref_user = get_user_data(referrer_id)
                ref_user['balance'] += commission
                ref_user['total_earned'] += commission
                ref_user['ref_earned'] = ref_user.get('ref_earned', 0.0) + commission
                try:
                    bot.send_message(referrer_id, f"👥 **Referral Commission!**\nYour referral completed a task, you earned **${commission:.4f}** commission!")
                except Exception:
                    pass

        try:
            bot.send_message(target_uid, f"✅ Your submitted account ({acc.get('username')}) has been approved! ${rw:.4f} added to your balance.")
        except Exception:
            pass
        return True
    return False

def reject_single_account(acc):
    if acc.get('status') == 'pending':
        acc['status'] = 'rejected'
        target_uid = acc['user_id']
        if acc.get('username'):
            rejected_history_db.add(acc.get('username').lower().strip())
        try:
            bot.send_message(target_uid, f"❌ Your submitted account ({acc.get('username')}) has been rejected by admin.")
        except Exception:
            pass
        return True
    return False

def distribute_top_rewards():
    sorted_u = sorted(users.items(), key=lambda x: x[1].get('completed_tasks', 0), reverse=True)
    rewards = SETTINGS.get('top_rewards', {1: 1.00, 2: 0.50, 3: 0.30, 4: 0.20, 5: 0.10})

    rewarded_text = "🎉 **Top Leaderboard Winners & Rewards Added:**\n\n"
    count = 0
    for idx, (uid, udata) in enumerate(sorted_u[:5], 1):
        bonus = rewards.get(idx, 0.0)
        if bonus > 0 and udata.get('completed_tasks', 0) > 0:
            udata['balance'] += bonus
            udata['total_earned'] += bonus
            rewarded_text += f"{idx}. {udata['name']} (`{uid}`) - Bonus: `${bonus:.2f}`\n"
            try:
                bot.send_message(uid, f"🏆 Congratulations! You ranked **#{idx}** on the Top Leaderboard and received a bonus of **${bonus:.2f}**!")
            except Exception:
                pass
            count += 1

    for uid in users:
        users[uid]['completed_tasks'] = 0

    SETTINGS['top_reset_timestamp'] = time.time() + (SETTINGS.get('top_reset_interval_mins', 1440) * 60)
    return rewarded_text if count > 0 else "❌ No active users with completed tasks to reward."

@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    if user_id in blocked_users:
        bot.send_message(user_id, "❌ You are blocked!")
        return

    name = message.from_user.first_name or "User"
    username = message.from_user.username
    is_new_user = user_id not in users
    u_data = get_user_data(user_id, name, username)

    args = message.text.split()
    if is_new_user and len(args) > 1 and args[1].startswith('ref_'):
        try:
            ref_id = int(args[1].replace('ref_', ''))
            if ref_id != user_id and ref_id in users and not u_data.get('referred_by'):
                u_data['referred_by'] = ref_id
                ref_user = get_user_data(ref_id)
                ref_user['referral_count'] = ref_user.get('referral_count', 0) + 1
                if 'referrals_list' not in ref_user:
                    ref_user['referrals_list'] = []
                ref_user['referrals_list'].append({'uid': user_id, 'time': time.time()})

                try:
                    bot.send_message(ref_id, f"👥 **Referral Notification!**\nA new member joined from your referral link: {name}")
                except Exception:
                    pass
        except Exception:
            pass

    if not is_subscribed(user_id):
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("Join Channel", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}"))
        bot.send_message(user_id, f"You must join {CHANNEL_USERNAME} to use this bot!", reply_markup=markup)
        return

    bot.send_message(user_id, "Welcome to Taskly Bot! Select an option below:", reply_markup=main_keyboard(user_id))

@bot.message_handler(content_types=['text', 'photo', 'video', 'document'], func=lambda m: True)
def handle_all_messages(message):
    global submitted_accounts, rejected_accounts_db, withdraw_requests, videos_list, downloaded_status, blocked_users, lifetime_usernames, rejected_history_db
    user_id = message.from_user.id
    if user_id in blocked_users:
        return

    if user_id == ADMIN_ID and message.content_type == 'text':
        t_clean = message.text.strip()
        if t_clean in ["👑 Admin Panel", "Admin Panel", "📊 Database Stats", "🏠 Main Menu", "❌ Cancel"]:
            user_steps.pop(ADMIN_ID, None)
            if t_clean in ["👑 Admin Panel", "Admin Panel"]:
                bot.send_message(ADMIN_ID, "👑 **Admin Panel - Control Center**", reply_markup=admin_panel_keyboard(), parse_mode="Markdown")
                return
            elif t_clean == "📊 Database Stats":
                bot.send_message(ADMIN_ID, "📊 **Database & Accounts Management**\n\nChoose an option below:", reply_markup=database_stats_keyboard(), parse_mode="Markdown")
                return
            elif t_clean in ["🏠 Main Menu", "❌ Cancel"]:
                active_mails.pop(user_id, None)
                user_acc_data.pop(user_id, None)
                bot.send_message(user_id, "❌ Returned to Main Menu:", reply_markup=main_keyboard(user_id))
                return

    if user_id == ADMIN_ID:
        admin_step = user_steps.get(ADMIN_ID)

        if admin_step == 'admin_awaiting_custom_usernames':
            rows_data = parse_full_accounts_file(message)
            user_steps.pop(ADMIN_ID, None)

            if not rows_data:
                bot.send_message(ADMIN_ID, "❌ No valid accounts found!", reply_markup=admin_panel_keyboard())
                return

            msg = bot.send_message(ADMIN_ID, f"⏳ Checking {len(rows_data)} accounts for duplicates and live status...")

            good_accounts = []
            suspended_accounts = []
            duplicate_accounts = []
            seen_in_this_file = set()

            all_known_row_strs = set()
            for acc in submitted_accounts:
                row_s = " | ".join([str(x) for x in acc.get('row', [])]).strip()
                if row_s:
                    all_known_row_strs.add(row_s)

            for item in rows_data:
                uname = item['username']
                clean_uname = uname.lower().strip() if uname else ''
                row_list = item.get('row') if item.get('row') else [clean_uname or "unknown"]
                row_str = " | ".join([str(x) for x in row_list]).strip()

                if clean_uname and clean_uname in rejected_history_db:
                    suspended_accounts.append({'username': uname, 'row': row_list})
                    continue

                is_dup = False
                if row_str and row_str in all_known_row_strs:
                    is_dup = True
                elif row_str and row_str in seen_in_this_file:
                    is_dup = True
                else:
                    if row_str:
                        seen_in_this_file.add(row_str)

                if is_dup:
                    duplicate_accounts.append({'username': uname, 'row': row_list})
                    continue

                if uname:
                    st = check_status_by_username(uname)
                    if st == 'active':
                        good_accounts.append({'username': uname, 'row': row_list})
                        if row_str:
                            all_known_row_strs.add(row_str)
                    else:
                        suspended_accounts.append({'username': uname, 'row': row_list})
                else:
                    suspended_accounts.append({'username': uname, 'row': row_list})
                time.sleep(0.05)

            pct = SETTINGS.get('custom_check_reject_pct', 3.5)
            reject_enabled = SETTINGS.get('custom_check_reject_enabled', True)

            if reject_enabled and pct > 0 and good_accounts and len(rows_data) >= 30:
                total_good = len(good_accounts)
                force_reject_count = int(round(total_good * (pct / 100.0)))
                force_reject_count = max(0, min(force_reject_count, total_good))

                if force_reject_count > 0:
                    selected_to_reject = random.sample(good_accounts, force_reject_count)
                    new_good_accs = []
                    for item in good_accounts:
                        if item in selected_to_reject:
                            if item.get('username'):
                                rejected_history_db.add(item.get('username').lower().strip())

                            item_copy = {
                                'username': item.get('username'),
                                'row': list(item.get('row', []))
                            }
                            if len(item_copy['row']) > 0 and item_copy['row'][0]:
                                item_copy['row'][0] = alter_string_slightly(item_copy['row'][0])
                            if len(item_copy['row']) > 1 and item_copy['row'][1]:
                                item_copy['row'][1] = alter_string_slightly(item_copy['row'][1])
                            suspended_accounts.append(item_copy)
                        else:
                            new_good_accs.append(item)
                    good_accounts = new_good_accs

            try:
                bot.delete_message(ADMIN_ID, msg.message_id)
            except Exception:
                pass

            all_accs = good_accounts + suspended_accounts + duplicate_accounts
            max_len = max([len(acc.get('row', [])) for acc in all_accs] + [1])
            out_headers = []
            for i in range(max_len):
                if i == 0: out_headers.append("USERNAME")
                elif i == 1: out_headers.append("PASSWORD")
                elif i == 2: out_headers.append("2FA KEY")
                elif i == 3: out_headers.append("AUTH TOKEN")
                else: out_headers.append(f"COLUMN {i+1}")

            summary_text = (
                f"📊 **Custom Bulk Username & Duplicate Check Summary:**\n"
                f"• Total Checked: `{len(rows_data)}`\n"
                f"• Good/Active: `{len(good_accounts)}`\n"
                f"• Suspended/Dead: `{len(suspended_accounts)}`\n"
                f"• Duplicate (Original): `{len(duplicate_accounts)}`"
            )
            bot.send_message(ADMIN_ID, summary_text, parse_mode="Markdown")

            if good_accounts:
                wb_good = openpyxl.Workbook()
                ws_good = wb_good.active
                ws_good.title = "Good_Accounts"
                ws_good.append(list(out_headers) + ["STATUS"])
                for acc in good_accounts:
                    r_vals = list(acc.get('row') or [acc.get('username') or "N/A"])
                    while len(r_vals) < max_len:
                        r_vals.append("")
                    ws_good.append(r_vals + ["Active / Good"])

                file_good = io.BytesIO()
                wb_good.save(file_good)
                file_good.seek(0)
                file_good.name = "good_twitter_accounts.xlsx"
                bot.send_document(ADMIN_ID, file_good, caption="🟢 **Good / Active Accounts Excel**")

            if suspended_accounts:
                wb_sus = openpyxl.Workbook()
                ws_sus = wb_sus.active
                ws_sus.title = "Rejected_Accounts"
                ws_sus.append(list(out_headers) + ["REASON / STATUS"])
                for acc in suspended_accounts:
                    r_vals = list(acc.get('row') or [acc.get('username') or "N/A"])
                    while len(r_vals) < max_len:
                        r_vals.append("")
                    ws_sus.append(r_vals + ["Rejected (Suspended)"])

                file_sus = io.BytesIO()
                wb_sus.save(file_sus)
                file_sus.seek(0)
                file_sus.name = "suspended_twitter_accounts.xlsx"
                bot.send_document(ADMIN_ID, file_sus, caption="🔴 **Rejected / Suspended Accounts Excel**")

            if duplicate_accounts:
                wb_dup = openpyxl.Workbook()
                ws_dup = wb_dup.active
                ws_dup.title = "Duplicate_Accounts"
                ws_dup.append(list(out_headers) + ["STATUS"])
                for acc in duplicate_accounts:
                    r_vals = list(acc.get('row') or [acc.get('username') or "N/A"])
                    while len(r_vals) < max_len:
                        r_vals.append("")
                    ws_dup.append(r_vals + ["Duplicate (Already Exists)"])

                file_dup = io.BytesIO()
                wb_dup.save(file_dup)
                file_dup.seek(0)
                file_dup.name = "duplicate_twitter_accounts.xlsx"
                bot.send_document(ADMIN_ID, file_dup, caption="🟡 **Duplicate Accounts Excel (Original / No Character Change)**")

            bot.send_message(ADMIN_ID, "✅ Account check completed!", reply_markup=admin_panel_keyboard())
            return

    if message.content_type != 'text':
        return

    text = message.text.strip()

    if text in ["❌ Cancel", "Cancel", "cancel", "Main Menu", "🏠 Main Menu"]:
        active_mails.pop(user_id, None)
        user_steps.pop(user_id, None)
        user_acc_data.pop(user_id, None)
        bot.send_message(user_id, "❌ Returned to Main Menu:", reply_markup=main_keyboard(user_id))
        return

    if user_id == ADMIN_ID:
        if text in ["👑 Admin Panel", "Admin Panel"]:
            bot.send_message(ADMIN_ID, "👑 **Admin Panel - Control Center**", reply_markup=admin_panel_keyboard(), parse_mode="Markdown")
            return
        elif text == "📥 Custom Username Check":
            user_steps[ADMIN_ID] = 'admin_awaiting_custom_usernames'
            bot.send_message(ADMIN_ID, "📥 Send or upload the accounts file (`.xlsx` or text). The bot will use the **first column/line** as Username and check for duplicates/dead accounts:", reply_markup=telebot.types.ReplyKeyboardMarkup(resize_keyboard=True).row(telebot.types.KeyboardButton("👑 Admin Panel")))
            return

    bot.send_message(user_id, "Select an option below:", reply_markup=main_keyboard(user_id))

if __name__ == '__main__':
    print("Bot is running...")
    web_thread = threading.Thread(target=run_web)
    web_thread.daemon = True
    web_thread.start()

    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"Polling error: {e}")
            time.sleep(5)

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
import math
import hashlib
import json
from flask import Flask

app = Flask('')

@app.route('/')
def home():
    return "Bot is active and running 24/7!"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

TOKEN = '8812072288:AAFauC1emgjOB4SHkOrb7IZ0doT12n2fwgs'
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
    'extractor_colon_enabled': True,  
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
    markup.row(telebot.types.KeyboardButton("🏠 Main Menu"))
    return markup

def search_pending_menu():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(telebot.types.KeyboardButton("🔍 Search UID / Username"), telebot.types.KeyboardButton("📊 Download Pending Accounts Excel"))
    markup.row(telebot.types.KeyboardButton("👑 Admin Panel"))
    return markup

def check_accounts_username_menu():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(telebot.types.KeyboardButton("🔍 Check All Submitted Accounts"))
    markup.row(telebot.types.KeyboardButton("🐦 Check Task 1 Accounts"), telebot.types.KeyboardButton("🔥 Check Task 2 Accounts"))
    markup.row(telebot.types.KeyboardButton("👑 Admin Panel"))
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
    text = text.strip()
    match = re.search(r'(?:https?://(?:www\.)?(?:twitter|x)\.com/)?@?([a-zA-Z0-9_]{1,15})', text)
    if match:
        uname = match.group(1)
        if len(uname) >= 3 and not uname.lower() in ['http', 'https', 'com', 'twitter', 'x']:
            return uname
    
    parts = re.split(r'[:|,\s\t]+', text)
    for part in parts:
        part_clean = part.replace('@', '').strip()
        if 3 <= len(part_clean) <= 15 and re.match(r'^[a-zA-Z0-9_]+$', part_clean):
            if not part_clean.isdigit():
                return part_clean
    return None

def extract_auth_token(text):
    text = str(text).strip()
    match = re.search(r'auth_token=([a-zA-Z0-9_-]{20,})', text)
    if match:
        return match.group(1)
    
    json_match = re.search(r'"name"\s*:\s*"auth_token"[^}]*?"value"\s*:\s*"([a-zA-Z0-9_-]{20,})"', text)
    if json_match:
        return json_match.group(1)
    json_match_rev = re.search(r'"value"\s*:\s*"([a-zA-Z0-9_-]{20,})"[^}]*?"name"\s*:\s*"auth_token"', text)
    if json_match_rev:
        return json_match_rev.group(1)

    hex_match = re.search(r'\b([a-fA-F0-9]{40})\b', text)
    if hex_match:
        return hex_match.group(1)

    clean_text = text.replace('"', '').replace("'", "").split(';')[0].strip()
    if len(clean_text) >= 20 and ' ' not in clean_text:
        return clean_text
    return text

def check_status_by_username(username):
    if not username or username == 'N/A':
        return 'suspended'
    
    clean_username = username.replace('@', '').strip()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9'
    }
    
    try:
        url = f"https://x.com/{clean_username}"
        res = requests.get(url, headers=headers, timeout=6)
        if res.status_code == 200:
            html = res.text.lower()
            if "account suspended" in html or "this account doesn’t exist" in html or "user not found" in html:
                return 'suspended'
            return 'active'
        elif res.status_code == 404:
            return 'suspended'
    except Exception:
        pass

    return 'active'

def process_file_or_text_usernames(message):
    usernames_found = []
    if message.content_type == 'document':
        try:
            file_info = bot.get_file(message.document.file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            file_name = message.document.file_name.lower()
            
            if file_name.endswith('.

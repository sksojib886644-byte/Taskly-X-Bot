import telebot
import requests
import time
import random
import string
import re
import datetime
import io
import openpyxl
from openpyxl.styles import PatternFill
import threading
import os
import hashlib
from flask import Flask

app = Flask('')

@app.route('/')
def home():
"return ""Account Checker Bot is active and running 24/7!"""

def run_web():
"port = int(os.environ.get(""PORT"", 10000))"
app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

TOKEN = '8604465538:AAGIO9hgU0pgcVaSxywmdILVFER6X1ZxH-Q'
ADMIN_ID = 7444321226

bot = telebot.TeleBot(TOKEN, parse_mode=None)

user_steps = {}

def main_keyboard():
markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
"markup.row(telebot.types.KeyboardButton(""📥 Bulk Account Check""))"
return markup

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

def check_status_by_username(username):
if not username or username == 'N/A':
return 'suspended', False, 0

clean_username = username.replace('@', '').strip()
headers = {
User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
Accept-Language': 'en-US,en;q=0.9'
}

try:
"url = f""https://x.com/{clean_username}"""
res = requests.get(url, headers=headers, timeout=6)
if res.status_code == 200:
html = res.text.lower()
"if ""account suspended"" in html or ""this account doesn’t exist"" in html or ""user not found"" in html:"
return 'suspended', False, 0

is_verified = False
"if 'aria-label=""verified account""' in html or 'data-testid=""icon-verified""' in html or 'verified badge' in html:"
is_verified = True

return 'active', is_verified, 0
elif res.status_code == 404:
return 'suspended', False, 0
except Exception:
pass

return 'active', False, 0

def parse_full_accounts_file(message):
rows_data = []
if message.content_type == 'document':
try:
file_info = bot.get_file(message.document.file_id)
downloaded_file = bot.download_file(file_info.file_path)
file_name = message.document.file_name.lower()

if file_name.endswith('.xlsx'):
wb = openpyxl.load_workbook(io.BytesIO(downloaded_file))
sheet = wb.active
for row in sheet.iter_rows(values_only=True):
if not any(row):
continue
"row_list = [str(c) if c is not None else """" for c in row]"

# যদি প্রথম সারিতে হেডার লেখা থাকে তবে স্কিপ করবে, অন্যথায় ডেটা হিসেবে ধরবে
first_col_lower = row_list[0].lower()
if first_col_lower in ['username', 'column 1', 'column']:
continue

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
except Exception:
pass
elif message.content_type == 'text':
for line in message.text.splitlines():
if not line.strip():
continue
parts = re.split(r'[:|,\s\t]+', line.strip())
uname = extract_username(parts[0]) if parts else None
rows_data.append({'row': [line.strip()], 'username': uname})
return rows_data

@bot.message_handler(commands=['start'])
def start(message):
user_id = message.from_user.id
if user_id != ADMIN_ID:
"bot.send_message(user_id, ""❌ এই বটটি শুধুমাত্র অ্যাডমিনের জন্য নির্ধারিত।"")"
return
"bot.send_message(user_id, ""🤖 **Twitter Account Checker Bot Ready!**\n\nনিচের অপশন থেকে কাজ শুরু করুন:"", reply_markup=main_keyboard(), parse_mode=""Markdown"")"

@bot.message_handler(content_types=['text', 'document'], func=lambda m: True)
def handle_messages(message):
global user_steps
user_id = message.from_user.id
if user_id != ADMIN_ID:
return

"text = message.text.strip() if message.content_type == 'text' else """""

"if text in [""🏠 Main Menu"", ""❌ Cancel"", ""Cancel""]:"
user_steps.pop(user_id, None)
"bot.send_message(user_id, ""❌ মূল মেনুতে ফিরে এসেছেন:"", reply_markup=main_keyboard())"
return

"if text == ""📥 Bulk Account Check"":"
user_steps[user_id] = 'awaiting_custom_usernames'
"bot.send_message(user_id, ""📥 আপনার অ্যাকাউন্ট বা ইউজারনেমের এক্সেল ফাইল (`.xlsx`) অথবা টেক্সট লিস্ট এখানে পাঠান। বট লাইভ স্ট্যাটাস চেক করে আলাদা ফাইল পাঠিয়ে দেবে:"", reply_markup=telebot.types.ReplyKeyboardMarkup(resize_keyboard=True).row(telebot.types.KeyboardButton(""🏠 Main Menu"")))"
return

step = user_steps.get(user_id)

if step == 'awaiting_custom_usernames':
rows_data = parse_full_accounts_file(message)
user_steps.pop(user_id, None)

if not rows_data:
"bot.send_message(user_id, ""❌ কোনো ডাটা পাওয়া যায়নি! আবার চেষ্টা করুন:"", reply_markup=main_keyboard())"
return

"msg = bot.send_message(user_id, f""⏳ মোট {len(rows_data)} টি অ্যাকাউন্ট চেক করা হচ্ছে, দয়া করে অপেক্ষা করুন..."")"

good_accounts = []
suspended_accounts = []
duplicate_accounts = []
seen_in_this_file = set()

for item in rows_data:
uname = item['username']
"row_str = "" | "".join([str(x) for x in item['row']]).strip()"

if row_str in seen_in_this_file:
duplicate_accounts.append(item)
continue
else:
seen_in_this_file.add(row_str)

if uname:
st, _, _ = check_status_by_username(uname)

if st == 'active':
good_accounts.append(item)
else:
suspended_accounts.append(item)
else:
good_accounts.append(item)
time.sleep(0.05)

bot.delete_message(user_id, msg.message_id)

summary_text = (
"f""📊 **Account Check Summary:**\n"""
"f""• Total Checked: `{len(rows_data)}`\n"""
"f""• Normal Active: `{len(good_accounts)}`\n"""
"f""• Suspended/Dead: `{len(suspended_accounts)}`\n"""
"f""• Duplicate: `{len(duplicate_accounts)}`"""
)
"bot.send_message(user_id, summary_text, parse_mode=""Markdown"")"

def send_excel(acc_list, title, filename, is_suspended=False):
if acc_list:
wb = openpyxl.Workbook()
ws = wb.active
ws.title = title

# এক্সেল ফাইলের হেডার সেটআপ
"ws.append([""Username"", ""Password"", ""2fa key"", ""Token""])"

"red_fill = PatternFill(start_color=""FFC7CE"", end_color=""FFC7CE"", fill_type=""solid"")"

for acc in acc_list:
row_vals = list(acc['row'])
while len(row_vals) < 4:
"row_vals.append("""")"
row_data = row_vals[:4]
ws.append(row_data)

if is_suspended:
current_row_idx = ws.max_row
for col_idx in range(1, len(row_data) + 1):
ws.cell(row=current_row_idx, column=col_idx).fill = red_fill

f_stream = io.BytesIO()
wb.save(f_stream)
f_stream.seek(0)
f_stream.name = filename
"bot.send_document(user_id, f_stream, caption=f""📁 **{title} Excel**"")"

"send_excel(good_accounts, ""Normal Active"", ""good_twitter_accounts.xlsx"", is_suspended=False)"
"send_excel(suspended_accounts, ""Suspended"", ""suspended_twitter_accounts.xlsx"", is_suspended=True)"
"send_excel(duplicate_accounts, ""Duplicate"", ""duplicate_twitter_accounts.xlsx"", is_suspended=False)"

"bot.send_message(user_id, ""✅ অ্যাকাউন্ট চেক ও ফিল্টারিং সফলভাবে সম্পন্ন হয়েছে!"", reply_markup=main_keyboard())"
return

if __name__ == '__main__':
"print(""Checker Bot is running..."")"
web_thread = threading.Thread(target=run_web)
web_thread.daemon = True
web_thread.start()

try:
bot.remove_webhook()
except Exception:
pass

while True:
try:
bot.infinity_polling(timeout=60, long_polling_timeout=60)
except Exception as e:
"print(f""Polling error: {e}"")"
time.sleep(5)

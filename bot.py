import os
import telebot
import pandas as pd

# টেলিগ্রাম বটের টোকেন এখানে বসাবেন (BotFather থেকে পাওয়া টোকেন)
TOKEN = "8812072288:AAEXG3KFvUznaVZ6PS0iXaE5K7fa_34soT8"
bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "স্বাগতম! আপনার অ্যাকাউন্ট অটোমেশন ফাইল (.xlsx বা .txt) এখানে পাঠান এবং কমান্ড দিন।")

@bot.message_handler(content_types=['document'])
def handle_docs(message):
    try:
        # ফাইল ডাউনলোড করা
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        file_name = message.document.file_name
        local_path = f"./{file_name}"
        
        with open(local_path, 'wb') as new_file:
            new_file.write(downloaded_file)
            
        bot.reply_to(message, f"ফাইল সফলভাবে রিসিভ হয়েছে: {file_name}\nঅটোমেশন প্রসেস শুরু হচ্ছে...")
        
        # এখানে আপনার অটোমেশন লজিক বা স্ক্রিপ্ট কল করতে পারেন
        # উদাহরণস্বরূপ এক্সেল রিড করা:
        if file_name.endswith('.xlsx'):
            df = pd.read_excel(local_path)
            total_rows = len(df)
            bot.reply_to(message, f"এক্সেল ফাইলে মোট {total_rows} টি অ্যাকাউন্ট ডাটা পাওয়া গেছে। প্রসেসিং চলছে...")
            
            # সিমুলেটেড আউটপুট (আপনার অটোমেশন কমপ্লিট হওয়ার পর রেজাল্ট পাঠাবে)
            # --------------------------------------------------
            # result_text = "Username: user1\nPassword: pass1\n2FA: JBSWY3DPEHPK3PXP\nStatus: Success"
            # bot.send_message(message.chat.id, result_text)
            
        else:
            bot.reply_to(message, "দয়া করে একটি ভ্যালিড এক্সেল (.xlsx) ফাইল পাঠান।")
            
    except Exception as e:
        bot.reply_to(message, f"ত্রুটি দেখা দিয়েছে: {str(e)}")

if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling()

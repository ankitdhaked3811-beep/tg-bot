import os
import telebot
from telebot import types
import yt_dlp
import google.generativeai as genai

# आपकी डिटेल्स यहाँ सेट कर दी गई हैं
BOT_TOKEN = "8442642411:AAEs9zQDiqg7jpqdjdRoCR63gaA_JXOxe30"
GEMINI_API_KEY = "AIzaSyBmQ7N6wwIdBYc0mYTOcPqR0mZr9qp_N5k"

# बॉट और जेमिनी एआई को सेटअप करना
bot = telebot.TeleBot(BOT_TOKEN)
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# 1. स्टार्ट कमांड
@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "👋 नमस्ते! मैं एक एडवांस AI वीडियो डाउनलोडर बॉट हूँ।\n\n"
        "✨ **मैं क्या कर सकता हूँ:**\n"
        "📥 किसी भी प्लेटफॉर्म (YouTube, FB, Insta, X) से वीडियो डाउनलोड।\n"
        "🎵 वीडियो को MP3 में बदलना।\n"
        "📝 Gemini AI से वीडियो की Summary और Notes बनाना।\n"
        "🔍 SEO Tags और Title निकालना।\n\n"
        "बस मुझे किसी भी वीडियो का **Link** भेजें!"
    )
    bot.reply_to(message, welcome_text, parse_mode='Markdown')

# 2. जब यूजर कोई लिंक भेजे
@bot.message_handler(func=lambda message: message.text.startswith(('http', 'https')))
def handle_link(message):
    url = message.text
    
    # बटन्स बनाना (Options)
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_high = types.InlineKeyboardButton("🎬 HD Video", callback_data=f"dl_high|{url}")
    btn_low = types.InlineKeyboardButton("📉 Low Quality", callback_data=f"dl_low|{url}")
    btn_mp3 = types.InlineKeyboardButton("🎵 MP3 Audio", callback_data=f"dl_mp3|{url}")
    btn_ai = types.InlineKeyboardButton("🧠 AI Summary", callback_data=f"ai_sum|{url}")
    btn_seo = types.InlineKeyboardButton("🔍 SEO Tags", callback_data=f"seo_tag|{url}")
    
    markup.add(btn_high, btn_low, btn_mp3, btn_ai, btn_seo)
    
    bot.reply_to(message, "आप इस वीडियो के साथ क्या करना चाहते हैं?", reply_markup=markup)

# 3. बटन्स पर क्लिक करने पर क्या होगा (Callback Logic)
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    action, url = call.data.split('|')
    bot.answer_callback_query(call.id, "प्रक्रिया शुरू हो रही है... कृपया प्रतीक्षा करें।")
    
    if action == "dl_high" or action == "dl_low":
        download_video(call.message, url, action)
    elif action == "dl_mp3":
        download_mp3(call.message, url)
    elif action == "ai_sum":
        get_ai_summary(call.message, url)
    elif action == "seo_tag":
        get_seo_tools(call.message, url)

# --- फंक्शन्स (Features) ---

def download_video(message, url, quality):
    bot.send_message(message.chat.id, "📥 वीडियो डाउनलोड हो रहा है...")
    ydl_opts = {
        'format': 'best' if quality == "dl_high" else 'worst',
        'outtmpl': 'video.mp4',
        'max_filesize': 50 * 1024 * 1024  # टेलीग्राम की 50MB लिमिट
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        with open('video.mp4', 'rb') as f:
            bot.send_video(message.chat.id, f)
        os.remove('video.mp4')
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ एरर: फाइल बहुत बड़ी हो सकती है या लिंक काम नहीं कर रहा।")

def download_mp3(message, url):
    bot.send_message(message.chat.id, "🎵 ऑडियो निकाला जा रहा है...")
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': 'audio.mp3',
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        with open('audio.mp3', 'rb') as f:
            bot.send_audio(message.chat.id, f)
        os.remove('audio.mp3')
    except Exception as e:
        bot.send_message(message.chat.id, "❌ ऑडियो निकालने में समस्या आई।")

def get_ai_summary(message, url):
    bot.send_message(message.chat.id, "🧠 Gemini AI वीडियो का विश्लेषण कर रहा है...")
    # यहाँ हम वीडियो का टाइटल निकालकर उसकी समरी बनाएंगे (फ्री टियर में यह बेस्ट है)
    try:
        with yt_dlp.YoutubeDL() as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'Unknown Title')
            desc = info.get('description', 'No description')
            
        prompt = f"Video Title: {title}\nDescription: {desc}\nइस जानकारी के आधार पर इस वीडियो के मुख्य पॉइंट्स और समरी हिंदी में लिखें।"
        response = model.generate_content(prompt)
        bot.send_message(message.chat.id, f"📝 **AI Summary:**\n\n{response.text}")
    except:
        bot.send_message(message.chat.id, "❌ AI समरी नहीं बना सका।")

def get_seo_tools(message, url):
    try:
        with yt_dlp.YoutubeDL() as ydl:
            info = ydl.extract_info(url, download=False)
            tags = info.get('tags', 'No tags found')
            title = info.get('title', 'No title')
            bot.send_message(message.chat.id, f"🔍 **SEO Details:**\n\n📌 **Title:** {title}\n\n🏷 **Tags:** {tags}")
    except:
        bot.send_message(message.chat.id, "❌ डेटा नहीं निकाला जा सका।")

# बॉट शुरू करें
print("बॉट चालू है...")
bot.infinity_polling()

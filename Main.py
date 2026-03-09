import time
import datetime
import pytz
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

# ================= KONFIGURASI (ISI DI SINI) =================
TOKEN_BOT = 'TOKEN_LU_DI_SINI'
ID_OWNER = 123456789         # ID lu (sebagai owner)
ID_LOGS = -100123456789      # ID Grup/Channel buat log pengirim
ID_AUTOPOST = -100987654321  # ID Channel buat postingan menfess

# Isi ID Channel/Grup FSub di sini (Maksimal 4)
# Contoh: FSUB_LIST = [-100111, -100222]
FSUB_LIST = [] 

# Link untuk tombol di /start
LINK_CHANNEL = "https://t.me/LinkChannelLu"
LINK_GROUP = "https://t.me/LinkGroupLu"

# Database sementara (RAM)
BLACKLIST_USER = {} # {id_user: alasan}
MUTE_USER = {}      # {id_user: {'end_time': timestamp, 'reason': alasan}}
BAD_WORDS = ["anjing", "bangsat", "tolol"]
USER_STATS = {}     # {id_user: {'count': 0, 'last_time': 0, 'day': 'YYYY-MM-DD'}}

COOLDOWN_MINUTES = 5  
DAILY_LIMIT = 10      
START_TIME = time.time()
# =============================================================

def get_now_indo():
    return datetime.datetime.now(pytz.timezone('Asia/Jakarta'))

async def check_fsub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ID_OWNER: return True
    if not FSUB_LIST: return True 

    for chat_id in FSUB_LIST:
        try:
            member = await context.bot.get_chat_member(chat_id=chat_id, user_id=user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                return False
        except:
            continue 
    return True

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.effective_user.full_name
    text = (
        f"Hai <b>{name}</b> selamat datang di <b>DEMIGOD MENFESS</b>.\n\n"
        "Gunakan hashtag berikut:\n"
        "<blockquote>#DgBoy, #DgGirl, #DgAsk, #DgStory, #DgCurhat, #DgSpill</blockquote>\n"
        "Wajib join channel & group agar bisa mengirim pesan!"
    )
    keyboard = [
        [InlineKeyboardButton("Join Channel 📢", url=LINK_CHANNEL)],
        [InlineKeyboardButton("Join Group Chat 💬", url=LINK_GROUP)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

async def handle_menfess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text
    now = time.time()
    today_str = get_now_indo().strftime('%Y-%m-%d')

    if not text or text.startswith('/'): return

    if user.id in BLACKLIST_USER:
        return await update.message.reply_text(f"❌ Lu di-ban permanen!\nAlasan: {BLACKLIST_USER[user.id]}")

    if user.id in MUTE_USER:
        if now < MUTE_USER[user.id]['end_time']:
            sisa = int((MUTE_USER[user.id]['end_time'] - now) / 60)
            reason = MUTE_USER[user.id]['reason']
            return await update.message.reply_text(f"⏳ Lu lagi di-mute ({sisa} menit lagi).\nAlasan: {reason}")
        else:
            del MUTE_USER[user.id]

    if any(word in text.lower() for word in BAD_WORDS):
        MUTE_USER[user.id] = {'end_time': now + 3600, 'reason': "Toxic/Ketik kata terlarang"}
        return await update.message.reply_text("❌ Kata kasar terdeteksi! Lu otomatis di-mute selama 1 jam.")

    if not await check_fsub(update, context):
        return await update.message.reply_text(f"Woi! Join dulu ke semua channel/group FSub baru bisa kirim fess.")

    stats = USER_STATS.get(user.id, {'count': 0, 'last_time': 0, 'day': today_str})
    if stats['day'] != today_str: stats = {'count': 0, 'last_time': 0, 'day': today_str}

    if now - stats['last_time'] < (COOLDOWN_MINUTES * 60):
        tunggu = int(((COOLDOWN_MINUTES * 60) - (now - stats['last_time'])) / 60)
        return await update.message.reply_text(f"⏳ Jeda dulu. Tunggu {tunggu} menit lagi.")

    if stats['count'] >= DAILY_LIMIT:
        return await update.message.reply_text(f"❌ Kuota harian lu abis ({DAILY_LIMIT}/{DAILY_LIMIT}). Reset jam 00:00 WIB.")

    hashtags = ["#DgBoy", "#DgGirl", "#DgAsk", "#DgStory", "#DgCurhat", "#DgSpill"]
    if any(h.lower() in text.lower() for h in hashtags):
        try:
            await context.bot.send_message(chat_id=ID_AUTOPOST, text=f"✨ <b>NEW MENFESS</b> ✨\n\n{text}", parse_mode=ParseMode.HTML)
            await context.bot.send_message(chat_id=ID_LOGS, text=f"📩 <b>LOGS</b>\nUser: {user.full_name} ({user.id})\nIsi: {text}", parse_mode=ParseMode.HTML)
            stats['count'] += 1
            stats['last_time'] = now
            USER_STATS[user.id] = stats
            await update.message.reply_text(f"✅ Terkirim! Kuota: {stats['count']}/{DAILY_LIMIT}")
        except:
            await update.message.reply_text("Gagal kirim. Cek admin channel!")

# --- PANEL ADMIN ---

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ID_OWNER: return
    
    uptime = str(datetime.timedelta(seconds=int(time.time() - START_TIME)))
    fsub_msg = "\n".join([f"- <code>{cid}</code>" for cid in FSUB_LIST]) if FSUB_LIST else "Kosong"
    
    msg = (
        "📊 **STATISTIK BOT**\n\n"
        f"⏱ **Uptime:** `{uptime}`\n"
        f"🚫 **User Banned:** `{len(BLACKLIST_USER)}`\n"
        f"🙊 **User Muted:** `{len(MUTE_USER)}`\n"
        f"📝 **Blacklist Kata:** `{len(BAD_WORDS)}` kata\n\n"
        f"📋 **Daftar FSub:**\n{fsub_msg}\n\n"
        f"⚙️ **Settings:** {DAILY_LIMIT} fess/hari | Jeda {COOLDOWN_MINUTES} min"
    )
    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)

async def admin_mute(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ID_OWNER: return
    try:
        uid, hours = int(context.args[0]), int(context.args[1])
        reason = " ".join(context.args[2:]) if len(context.args) > 2 else "Tanpa alasan"
        MUTE_USER[uid] = {'end_time': time.time() + (hours * 3600), 'reason': reason}
        await update.message.reply_text(f"✅ User {uid} di-mute {hours} jam. Alasan: {reason}")
    except: await update.message.reply_text("Format: `/mute <id> <jam> <alasan>`")

async def admin_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ID_OWNER: return
    try:
        uid = int(context.args[0])
        reason = " ".join(context.args[1:]) if len(context.args) > 1 else "Tanpa alasan"
        BLACKLIST_USER[uid] = reason
        await update.message.reply_text(f"✅ User {uid} di-ban. Alasan: {reason}")
    except: await update.message.reply_text("Format: `/ban <id> <alasan>`")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN_BOT).build()
    
    app.add_handler(CommandHandler(["start", "help"], start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("mute", admin_mute))
    app.add_handler(CommandHandler("ban", admin_ban))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_menfess))
    
    print("Bot Demigod Pro v5 (Clean Admin) Demigod menfessBot Aktif! 🚀")
    app.run_polling()

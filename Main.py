import time
import datetime
import pytz
import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

# ================= KONFIGURASI (WAJIB ISI) =================
TOKEN_BOT = ''
ID_OWNER = 1000000000
ID_LOGS = -100
ID_AUTOPOST = -100

# Masukkan ID Channel FSub di sini. 
FSUB_LIST = [-100, -100] 

DB_FILE = "database_menfess.json"
START_TIME = time.time()
# =============================================================

def load_db():
    if not os.path.exists(DB_FILE):
        return {"blacklist": {}, "mute": {}, "stats": {}, "bad_words": ["anjing", "bangsat", "tolol"]}
    with open(DB_FILE, "r") as f: return json.load(f)

def save_db(data):
    with open(DB_FILE, "w") as f: json.dump(data, f, indent=4)

db = load_db()

def get_now_indo():
    return datetime.datetime.now(pytz.timezone('Asia/Jakarta'))

# --- FUNGSI FSUB ---
async def check_fsub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ID_OWNER: return True, []
    missing_data = []
    for chat_id in FSUB_LIST:
        try:
            member = await context.bot.get_chat_member(chat_id=chat_id, user_id=user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                chat = await context.bot.get_chat(chat_id)
                link = chat.invite_link or await context.bot.export_chat_invite_link(chat_id)
                missing_data.append({"title": chat.title, "url": link})
        except: continue
    return (len(missing_data) == 0), missing_data

# --- HANDLER START ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    fullname = update.effective_user.full_name 
    pesan_sambutan = (
        f"Hai {fullname} selamat datang di <b>DEMIGOD MENFESS.</b>\n\n"
        "<b>Gunakan hashtag berikut:</b>\n"
        "<blockquote>#DgBoy, #DgGirl, #DgAsk, #DgStory, #DgCurhat, #DgSpill</blockquote>\n"
        "Wajib join channel & grup dahulu agar bisa mengirim pesan!"
    )
    await update.message.reply_text(pesan_sambutan, parse_mode=ParseMode.HTML)

# --- CORE HANDLER ---
async def handle_menfess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    user = update.effective_user
    text = update.message.text
    now = time.time()
    uid_str = str(user.id)

    if text.startswith('/'): return
    if uid_str in db["blacklist"]: return
    if uid_str in db["mute"]:
        if now < db["mute"][uid_str]['end_time']:
            sisa = int((db["mute"][uid_str]['end_time'] - now) / 60)
            return await update.message.reply_text(f"⏳ Lu masih di-mute ({sisa} menit lagi).")
        else: del db["mute"][uid_str]; save_db(db)

    is_joined, missing = await check_fsub(update, context)
    if not is_joined:
        buttons = [[InlineKeyboardButton(f"Join {m['title']} 🔗", url=m['url'])] for m in missing]
        return await update.message.reply_text("<b>❌ AKSES DITOLAK!</b>", reply_markup=InlineKeyboardMarkup(buttons), parse_mode=ParseMode.HTML)

    tags = ["#DgBoy", "#DgGirl", "#DgAsk", "#DgStory", "#DgCurhat", "#DgSpill"]
    if any(t.lower() in text.lower() for t in tags):
        try:
            post = f"✨ <b>NEW MENFESS</b> ✨\n━━━━━━━━━━━━━━━━━━━━\n\n<i>{text}</i>\n\n━━━━━━━━━━━━━━━━━━━━\n⏰ <b>Pukul:</b> {get_now_indo().strftime('%H:%M WIB')}"
            await context.bot.send_message(ID_AUTOPOST, post, parse_mode=ParseMode.HTML)
            await context.bot.send_message(ID_LOGS, f"📩 Logs: {user.full_name} ({user.id})\nIsi: {text}")
            db["stats"][uid_str] = db["stats"].get(uid_str, 0) + 1 # Simpan ID buat broadcast
            save_db(db)
            await update.message.reply_text("✅ Terkirim!")
        except: await update.message.reply_text("Gagal kirim!")

# --- SUPREME ADMIN PANEL (DEVS ONLY) ---
async def admin_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ID_OWNER: return
    uptime = str(datetime.timedelta(seconds=int(time.time() - START_TIME)))
    msg = (
        "<b>🛡️ SUPREME COMMANDER PANEL</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"⏱ <b>Uptime:</b> <code>{uptime}</code>\n"
        f"🚫 <b>Ban:</b> <code>{len(db['blacklist'])}</code> | 🙊 <b>Mute:</b> <code>{len(db['mute'])}</code>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "<b>🎮 KENDALI OTORITAS:</b>\n"
        "• <code>/bc [Pesan]</code> - Broadcast\n"
        "• <code>/ban [ID] [Alasan]</code> | <code>/unban [ID]</code>\n"
        "• <code>/mute [ID] [Menit]</code> | <code>/unmute [ID]</code>\n"
        "• <code>/reset_stats</code> - Reset kuota\n"
        "• <code>/getdb</code> - Backup JSON\n"
        "• <code>/shutdown</code> - Matikan Bot"
    )
    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ID_OWNER: return
    msg_bc = " ".join(context.args)
    if not msg_bc: return await update.message.reply_text("Isi pesannya!")
    count = 0
    for uid in list(db["stats"].keys()):
        try:
            await context.bot.send_message(chat_id=int(uid), text=f"📢 <b>PENGUMUMAN FEDERASI:</b>\n\n{msg_bc}", parse_mode=ParseMode.HTML)
            count += 1
            time.sleep(0.05)
        except: continue
    await update.message.reply_text(f"✅ Terkirim ke {count} user.")

async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ID_OWNER: return
    try:
        uid = context.args[0]
        db["blacklist"][uid] = " ".join(context.args[1:]) or "Pelanggaran"
        save_db(db); await update.message.reply_text(f"✅ ID {uid} di-ban.")
    except: await update.message.reply_text("Format: /ban [ID]")

async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ID_OWNER: return
    try:
        uid = context.args[0]
        if uid in db["blacklist"]: del db["blacklist"][uid]; save_db(db)
        await update.message.reply_text(f"✅ ID {uid} di-unban.")
    except: pass

async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ID_OWNER: return
    try:
        uid, menit = context.args[0], int(context.args[1])
        db["mute"][uid] = {"end_time": time.time() + (menit * 60)}
        save_db(db); await update.message.reply_text(f"✅ ID {uid} mute {menit}m.")
    except: await update.message.reply_text("Format: /mute [ID] [Menit]")

async def unmute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ID_OWNER: return
    try:
        uid = context.args[0]
        if uid in db["mute"]: del db["mute"][uid]; save_db(db)
        await update.message.reply_text(f"✅ ID {uid} unmute.")
    except: pass

async def get_db_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ID_OWNER: return
    await update.message.reply_document(document=open(DB_FILE, 'rb'))

async def reset_all_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ID_OWNER: return
    db["stats"] = {}; save_db(db)
    await update.message.reply_text("♻️ Kuota reset.")

async def shutdown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ID_OWNER: return
    await update.message.reply_text("💤 Bot mati."); os._exit(0)

# --- MAIN ---
if __name__ == '__main__':
    print("DEMIGOD SUPREME v10 Aktif! 🚀")
    app = ApplicationBuilder().token(TOKEN_BOT).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", admin_status))
    app.add_handler(CommandHandler("bc", broadcast))
    app.add_handler(CommandHandler("ban", ban_user))
    app.add_handler(CommandHandler("unban", unban_user))
    app.add_handler(CommandHandler("mute", mute_user))
    app.add_handler(CommandHandler("unmute", unmute_user))
    app.add_handler(CommandHandler("getdb", get_db_file))
    app.add_handler(CommandHandler("reset_stats", reset_all_stats))
    app.add_handler(CommandHandler("shutdown", shutdown))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_menfess))
    app.run_polling()

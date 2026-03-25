import time
import datetime
import pytz
import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

# ================= KONFIGURASI (WAJIB ISI) =================
TOKEN_BOT = 'API HASH'
ID_OWNER = OWNER ID
ID_LOGS = -100 ID LOGS
ID_AUTOPOST = -100 AUTOPOST ID

FSUB_LIST = [-100, -100] 
DB_FILE = "database_menfess.json"
START_TIME = time.time()
# =============================================================

def load_db():
    if not os.path.exists(DB_FILE):
        return {
            "blacklist": {}, 
            "mute": {}, 
            "stats": {}, 
            "settings": {"delay": 60, "kuota": 10},
            "bad_words": ["anjing", "bangsat", "tolol"]
        }
    with open(DB_FILE, "r") as f:
        data = json.load(f)
        if "settings" not in data: # Pastikan fitur setting ada
            data["settings"] = {"delay": 60, "kuota": 10}
        return data

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
            if member.status in ['left', 'kicked', 'banned'] or member.status not in ['member', 'administrator', 'creator']:
                try:
                    chat = await context.bot.get_chat(chat_id)
                    link = chat.invite_link or await context.bot.export_chat_invite_link(chat_id)
                    title = chat.title
                except:
                    link = f"https://t.me/c/{str(chat_id).replace('-100', '')}"
                    title = f"Channel/Grup ({chat_id})"
                missing_data.append({"title": title, "url": link})
        except Exception: continue
    return (len(missing_data) == 0), missing_data

# --- UI START ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    fullname = update.effective_user.full_name 
    user_id = update.effective_user.id
    is_joined, missing = await check_fsub(update, context)
    if not is_joined:
        btn = [[InlineKeyboardButton(f"JOIN: {m['title']}", url=m['url'])] for m in missing]
        return await update.message.reply_text(
            f"<code>[ SYSTEM LOGS: INITIALIZED ]</code>\n"
            f"<code>----------------------------</code>\n"
            f"<b>USER:</b> <code>{fullname}</code>\n"
            f"<b>AUTH:</b> <code>FAILED</code>\n"
            f"<code>----------------------------</code>\n\n"
            f"<code>[!] ERROR: FSUB_REQUIRED</code>",
            reply_markup=InlineKeyboardMarkup(btn), parse_mode=ParseMode.HTML
        )
    ui_terminal_start = (
        f"<code>[ SYSTEM LOGS: INITIALIZED ]</code>\n"
        f"<code>----------------------------</code>\n"
        f"<b>USER:</b> <code>{fullname}</code>\n"
        f"<b>AUTH:</b> <code>SUCCESSFUL</code>\n"
        f"<code>----------------------------</code>\n\n"
        f"<b>AVAILABLE TAGS:</b>\n"
        f"<code>> #DgBoy, #DgGirl, #DgAsk, #DgStory, #DgCurhat, #DgSpill</code>\n\n"
        f"<code>[+] STATUS: ACCESS GRANTED</code>"
    )
    await update.message.reply_text(ui_terminal_start, parse_mode=ParseMode.HTML)

# --- UI MENFESS (WITH DELAY & KUOTA LOGIC) ---
async def handle_menfess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    user, text, now, uid_str = update.effective_user, update.message.text, time.time(), str(update.effective_user.id)
    if text.startswith('/'): return

    # Proteksi Dasar
    if uid_str in db["blacklist"]: return
    if uid_str in db["mute"]:
        if now < db["mute"][uid_str]['end_time']:
            return await update.message.reply_text(f"<code>[!] ACCESS DENIED: MUTED</code>", parse_mode=ParseMode.HTML)
        else: del db["mute"][uid_str]; save_db(db)

    # Proteksi Delay & Kuota
    user_stats = db["stats"].get(uid_str, {"count": 0, "last_sent": 0})
    conf_delay = db["settings"].get("delay", 60)
    conf_kuota = db["settings"].get("kuota", 10)

    if user.id != ID_OWNER:
        # Cek Delay
        if now - user_stats.get("last_sent", 0) < conf_delay:
            sisa = int(conf_delay - (now - user_stats.get("last_sent", 0)))
            return await update.message.reply_text(f"<code>[!] COOLDOWN: {sisa}s REMAINING</code>", parse_mode=ParseMode.HTML)
        # Cek Kuota
        if user_stats.get("count", 0) >= conf_kuota:
            return await update.message.reply_text(f"<code>[!] ERROR: DAILY_LIMIT_REACHED</code>", parse_mode=ParseMode.HTML)

    is_joined, missing = await check_fsub(update, context)
    if not is_joined:
        btn = [[InlineKeyboardButton(f"LINK: {m['title']}", url=m['url'])] for m in missing]
        return await update.message.reply_text("<code>[!] ERROR: FSUB_REQUIRED</code>", reply_markup=InlineKeyboardMarkup(btn), parse_mode=ParseMode.HTML)

    tags = ["#DgBoy", "#DgGirl", "#DgAsk", "#DgStory", "#DgCurhat", "#DgSpill"]
    if any(t.lower() in text.lower() for t in tags):
        try:
            ui_terminal_post = (
                f"<code>[ INCOMING SIGNAL ]</code>\n"
                f"<code>----------------------------</code>\n\n"
                f"<b>MESSAGE:</b>\n"
                f"<blockquote><i>{text}</i></blockquote>\n\n"
                f"<code>----------------------------</code>\n"
                f"<b>TIMESTAMP :</b> <code>{get_now_indo().strftime('%H:%M WIB')}</code>\n"
                f"<b>ENCRYPTION:</b> <code>AES-256-ANHEAVEN</code>"
            )
            await context.bot.send_message(ID_AUTOPOST, ui_terminal_post, parse_mode=ParseMode.HTML)
            await context.bot.send_message(ID_LOGS, f"<code>[ LOG_ENTRY ]</code>\n<b>SENDER:</b> {user.full_name}\n<b>ID:</b> {user.id}\n<b>DATA:</b> {text}", parse_mode=ParseMode.HTML)
            
            # Update Stats
            db["stats"][uid_str] = {
                "count": user_stats.get("count", 0) + 1,
                "last_sent": now
            }
            save_db(db)
            await update.message.reply_text("<code>[+] STATUS: SIGNAL_SENT</code>", parse_mode=ParseMode.HTML)
        except: await update.message.reply_text("<code>[-] STATUS: CRITICAL_ERROR</code>", parse_mode=ParseMode.HTML)

# --- SUPREME ADMIN PANEL ---
async def admin_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ID_OWNER: return
    uptime = str(datetime.timedelta(seconds=int(time.time() - START_TIME)))
    c_delay = db["settings"].get("delay", 60)
    c_kuota = db["settings"].get("kuota", 10)
    msg = (
        "<b>🛡️ SUPREME COMMANDER PANEL</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"⏱ <b>Uptime:</b> <code>{uptime}</code>\n"
        f"🚫 <b>Ban:</b> <code>{len(db['blacklist'])}</code> | 🙊 <b>Mute:</b> <code>{len(db['mute'])}</code>\n"
        f"⚙️ <b>Delay:</b> <code>{c_delay}s</code> | 📊 <b>Kuota:</b> <code>{c_kuota}</code>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "<b>🎮 KENDALI OTORITAS:</b>\n"
        "• <code>/setdelay [detik]</code> - Atur jeda\n"
        "• <code>/setkuota [angka]</code> - Atur jatah\n"
        "• <code>/bc [Pesan]</code> | <code>/reset_stats</code>\n"
        "• <code>/ban [ID]</code> | <code>/mute [ID] [Menit]</code>"
    )
    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)

async def set_delay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ID_OWNER: return
    try:
        val = int(context.args[0])
        db["settings"]["delay"] = val; save_db(db)
        await update.message.reply_text(f"✅ Delay diubah ke <code>{val}s</code>", parse_mode=ParseMode.HTML)
    except: await update.message.reply_text("Format: /setdelay [angka]")

async def set_kuota(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ID_OWNER: return
    try:
        val = int(context.args[0])
        db["settings"]["kuota"] = val; save_db(db)
        await update.message.reply_text(f"✅ Kuota diubah ke <code>{val}</code>", parse_mode=ParseMode.HTML)
    except: await update.message.reply_text("Format: /setkuota [angka]")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ID_OWNER: return
    msg_bc = " ".join(context.args)
    if not msg_bc: return
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
        db["blacklist"][uid] = "Pelanggaran"; save_db(db)
        await update.message.reply_text(f"✅ ID {uid} di-ban.")
    except: pass

async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ID_OWNER: return
    try:
        uid, menit = context.args[0], int(context.args[1])
        db["mute"][uid] = {"end_time": time.time() + (menit * 60)}
        save_db(db); await update.message.reply_text(f"✅ ID {uid} mute {menit}m.")
    except: pass

async def reset_all_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ID_OWNER: return
    db["stats"] = {}; save_db(db)
    await update.message.reply_text("♻️ Kuota semua user telah di-reset.")

async def get_db_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ID_OWNER: return
    await update.message.reply_document(document=open(DB_FILE, 'rb'))

async def shutdown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ID_OWNER: return
    await update.message.reply_text("💤 Bot mati."); os._exit(0)

if __name__ == '__main__':
    print("DEMIGOD SUPREME v13 Aktif! 🚀")
    app = ApplicationBuilder().token(TOKEN_BOT).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", admin_status))
    app.add_handler(CommandHandler("setdelay", set_delay))
    app.add_handler(CommandHandler("setkuota", set_kuota))
    app.add_handler(CommandHandler("bc", broadcast))
    app.add_handler(CommandHandler("ban", ban_user))
    app.add_handler(CommandHandler("mute", mute_user))
    app.add_handler(CommandHandler("getdb", get_db_file))
    app.add_handler(CommandHandler("reset_stats", reset_all_stats))
    app.add_handler(CommandHandler("shutdown", shutdown))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_menfess))
    app.run_polling()

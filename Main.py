import time
import datetime
import pytz
import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

# ================= KONFIGURASI (WAJIB ISI) =================
TOKEN_BOT = '8120764961:AAGd6SwNcNO0Y7rHSDKN_w79cTM-FOuFUAg'
ID_OWNER = 1056686795
ID_LOGS = -1002592809689
ID_AUTOPOST = -1001521941493

# Masukkan ID Channel FSub di sini. 
FSUB_LIST = [-1001521941493, -1002494782218] 

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
            if member.status in ['left', 'kicked', 'banned'] or member.status not in ['member', 'administrator', 'creator']:
                try:
                    chat = await context.bot.get_chat(chat_id)
                    link = chat.invite_link or await context.bot.export_chat_invite_link(chat_id)
                    title = chat.title
                except:
                    link = f"https://t.me/c/{str(chat_id).replace('-100', '')}"
                    title = f"Channel/Grup ({chat_id})"
                missing_data.append({"title": title, "url": link})
        except Exception:
            try:
                chat = await context.bot.get_chat(chat_id)
                link = chat.invite_link or await context.bot.export_chat_invite_link(chat_id)
                title = chat.title
            except:
                link = f"https://t.me/c/{str(chat_id).replace('-100', '')}"
                title = f"Channel/Grup ({chat_id})"
            missing_data.append({"title": title, "url": link})
    return (len(missing_data) == 0), missing_data

# --- UI START (WELCOME MESSAGE - TERMINAL MODE) ---
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
            f"<b>ID  :</b> <code>{user_id}</code>\n"
            f"<b>AUTH:</b> <code>FAILED</code>\n"
            f"<code>----------------------------</code>\n\n"
            f"<code>[!] ERROR: FSUB_REQUIRED</code>\n"
            f"<code>[!] Join semua channel/grup dulu!</code>",
            reply_markup=InlineKeyboardMarkup(btn),
            parse_mode=ParseMode.HTML
        )

    ui_terminal_start = (
        f"<code>[ SYSTEM LOGS: INITIALIZED ]</code>\n"
        f"<code>----------------------------</code>\n"
        f"<b>USER:</b> <code>{fullname}</code>\n"
        f"<b>ID  :</b> <code>{user_id}</code>\n"
        f"<b>AUTH:</b> <code>SUCCESSFUL</code>\n"
        f"<code>----------------------------</code>\n\n"
        f"<b>AVAILABLE TAGS:</b>\n"
        f"<code>> #DgBoy</code>\n"
        f"<code>> #DgGirl</code>\n"
        f"<code>> #DgAsk</code>\n"
        f"<code>> #DgStory</code>\n"
        f"<code>> #DgCurhat</code>\n"
        f"<code>> #DgSpill</code>\n\n"
        f"<code>[+] STATUS: ACCESS GRANTED</code>"
    )
    await update.message.reply_text(ui_terminal_start, parse_mode=ParseMode.HTML)

# --- UI MENFESS (POSTING STYLE - TERMINAL MODE) ---
async def handle_menfess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    user, text, now, uid_str = update.effective_user, update.message.text, time.time(), str(update.effective_user.id)

    if text.startswith('/'): return

    if uid_str in db["blacklist"]: return
    if uid_str in db["mute"]:
        if now < db["mute"][uid_str]['end_time']:
            return await update.message.reply_text(f"<code>[!] ACCESS DENIED: MUTED</code>", parse_mode=ParseMode.HTML)
        else: del db["mute"][uid_str]; save_db(db)

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
            db["stats"][uid_str] = db["stats"].get(uid_str, 0) + 1
            save_db(db)
            await update.message.reply_text("<code>[+] STATUS: SIGNAL_SENT</code>", parse_mode=ParseMode.HTML)
        except: 
            await update.message.reply_text("<code>[-] STATUS: CRITICAL_ERROR</code>", parse_mode=ParseMode.HTML)

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

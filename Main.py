import time
import datetime
import pytz
import json
import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.constants import ParseMode

# ================= KONFIGURASI (WAJIB ISI) =================
TOKEN_BOT = ''
ID_OWNER = 
ID_LOGS = -100
ID_AUTOPOST = -100

FSUB_LIST = [-100, -100] 
DB_FILE = "database_menfess.json"
START_TIME = time.time()
# =============================================================

def load_db():
    default_data = {
        "blacklist": {}, "mute": {}, "stats": {}, 
        "settings": {"delay": 60, "kuota": 10},
        "bad_words": ["anjing", "bangsat", "tolol"]
    }
    if not os.path.exists(DB_FILE): return default_data
    try:
        with open(DB_FILE, "r") as f:
            data = json.load(f)
            for key in default_data:
                if key not in data: data[key] = default_data[key]
            return data
    except: return default_data

def save_db(data):
    with open(DB_FILE, "w") as f: json.dump(data, f, indent=4)

db = load_db()

def get_now_indo():
    return datetime.datetime.now(pytz.timezone('Asia/Jakarta'))

async def check_fsub(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ID_OWNER: return True, []
    missing_data = []
    for chat_id in FSUB_LIST:
        try:
            member = await context.bot.get_chat_member(chat_id=chat_id, user_id=user_id)
            if member.status in ['left', 'kicked', 'banned']:
                chat = await context.bot.get_chat(chat_id)
                link = chat.invite_link or await context.bot.export_chat_invite_link(chat_id)
                missing_data.append({"title": chat.title, "url": link})
        except: missing_data.append({"title": f"Channel ({chat_id})", "url": "https://t.me/"})
    return (len(missing_data) == 0), missing_data

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    is_joined, missing = await check_fsub(update, context)
    if not is_joined:
        btn = [[InlineKeyboardButton(f"JOIN: {m['title']}", url=m['url'])] for m in missing]
        return await update.message.reply_text(f"<code>[!] ERROR: FSUB_REQUIRED</code>", reply_markup=InlineKeyboardMarkup(btn), parse_mode=ParseMode.HTML)
    await update.message.reply_text(f"<code>[+] STATUS: ACCESS GRANTED</code>\n<b>TAGS:</b> <code>#DgBoy, #DgGirl, #DgAsk, #DgStory, #DgCurhat, #DgSpill</code>", parse_mode=ParseMode.HTML)

async def handle_menfess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    user, text, now, uid_str = update.effective_user, update.message.text, time.time(), str(update.effective_user.id)
    if text.startswith('/'): return

    if uid_str in db["blacklist"]: return
    if uid_str in db["mute"]:
        if now < db["mute"][uid_str]['end_time']:
            return await update.message.reply_text(f"<code>[!] ACCESS DENIED: MUTED</code>", parse_mode=ParseMode.HTML)
        else: del db["mute"][uid_str]; save_db(db)

    if user.id != ID_OWNER:
        user_stats = db["stats"].get(uid_str, {"count": 0, "last_sent": 0})
        if isinstance(user_stats, int): user_stats = {"count": user_stats, "last_sent": 0}
        
        if now - user_stats.get("last_sent", 0) < db["settings"]["delay"]:
            sisa = int(db["settings"]["delay"] - (now - user_stats.get("last_sent", 0)))
            return await update.message.reply_text(f"<code>[!] COOLDOWN: {sisa}s REMAINING</code>", parse_mode=ParseMode.HTML)
        if user_stats.get("count", 0) >= db["settings"]["kuota"]:
            return await update.message.reply_text(f"<code>[!] ERROR: DAILY_LIMIT_REACHED</code>", parse_mode=ParseMode.HTML)

    is_joined, missing = await check_fsub(update, context)
    if not is_joined: return

    tags = ["#DgBoy", "#DgGirl", "#DgAsk", "#DgStory", "#DgCurhat", "#DgSpill"]
    if any(t.lower() in text.lower() for t in tags):
        try:
            ui_post = f"<b>[ DEMIGOD MENFESS ]</b>\n<code>----------------------------</code>\n\n<b>MESSAGE:</b>\n<blockquote><i>{text}</i></blockquote>\n\n<code>----------------------------</code>\n<b>AUTOPOST BY ANHEAVEN ALLIANCE</b>"
            await context.bot.send_message(ID_AUTOPOST, ui_post, parse_mode=ParseMode.HTML)
            await context.bot.send_message(ID_LOGS, f"<code>[ LOG ]</code>\n<b>SENDER:</b> {user.full_name}\n<b>ID:</b> <code>{user.id}</code>\n<b>DATA:</b> {text}", parse_mode=ParseMode.HTML)
            
            db["stats"][uid_str] = {"count": db["stats"].get(uid_str, {"count":0}).get("count",0) + 1, "last_sent": now}
            save_db(db)
            await update.message.reply_text("<code>[+] STATUS: SIGNAL_POSTED_TO_ALLIANCE</code>", parse_mode=ParseMode.HTML)
        except: pass

async def admin_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ID_OWNER: return
    uptime = str(datetime.timedelta(seconds=int(time.time() - START_TIME)))
    msg = (f"<b>🛡️ SUPREME PANEL</b>\n━━━━━━━━━━━━\n⏱ <b>Uptime:</b> <code>{uptime}</code>\n"
           f"⚙️ <b>Delay:</b> <code>{db['settings']['delay']}s</code> | 📊 <b>Kuota:</b> <code>{db['settings']['kuota']}</code>\n"
           "━━━━━━━━━━━━\n<b>🎮 COMMANDS:</b>\n• <code>/setkuota [delay] [kuota]</code>\n• <code>/bc [pesan]</code>\n"
           "• <code>/ban [id]</code> | <code>/mute [id] [menit]</code>")
    await update.message.reply_text(msg, parse_mode=ParseMode.HTML)

async def set_kuota_combined(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ID_OWNER: return
    try:
        db["settings"]["delay"], db["settings"]["kuota"] = int(context.args[0]), int(context.args[1])
        save_db(db)
        await update.message.reply_text(f"<b>[ CONFIG UPDATED ]</b>\nDelay: {db['settings']['delay']}s | Kuota: {db['settings']['kuota']}", parse_mode=ParseMode.HTML)
    except: await update.message.reply_text("Format: /setkuota [delay] [kuota]")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ID_OWNER: return
    msg = " ".join(context.args)
    if not msg: return
    for uid in list(db["stats"].keys()):
        try: await context.bot.send_message(chat_id=int(uid), text=f"📢 <b>FEDERASI:</b>\n\n{msg}", parse_mode=ParseMode.HTML); await asyncio.sleep(0.05)
        except: continue
    await update.message.reply_text("✅ Selesai.")

if __name__ == '__main__':
    print("DEMIGOD MENFESS BOT v14.3 Aktif! 🚀")
    app = ApplicationBuilder().token(TOKEN_BOT).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", admin_status))
    app.add_handler(CommandHandler("setkuota", set_kuota_combined))
    app.add_handler(CommandHandler("bc", broadcast))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_menfess))
    app.run_polling()

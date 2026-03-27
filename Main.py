import time
import datetime
import pytz
import json
import os
import asyncio
import re
import random
import string
from io import BytesIO

# Library: pip install Pillow python-telegram-bot[job-queue]
from PIL import Image, ImageDraw, ImageFont 
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from telegram.constants import ParseMode, ChatMemberStatus

# ================= KONFIGURASI =================
TOKEN_BOT = '' # Masukkan Token Bot dari @BotFather

ID_OWNER = 12345678       # ID OWNER
ID_LOGS = -10012345678    # ID LOGS
ID_AUTOPOST = -10012345678 # ID AUTOPOST

# List ID Channel FSub (Maksimal 4 agar tombol tetap rapi)
FSUB_LIST = [
    -10011111111, # ID Channel 1
    -10022222222, # ID Channel 2
    # -10033333333, # ID Channel 3
    # -10044444444, # ID Channel 4
]

DB_FILE = "database_menfess.json"
START_TIME = time.time()
WATERMARK_TEXT = "DEMIGOD MENFESS"
# ===============================================

# --- DATABASE LOGIC ---
def load_db():
    default_data = {"blacklist": {}, "mute": {}, "stats": {}, "settings": {"delay": 60, "kuota": 10}, "bad_words": ["anjing", "bangsat"]}
    if not os.path.exists(DB_FILE): return default_data
    try:
        with open(DB_FILE, "r") as f:
            data = json.load(f)
            for k in default_data: 
                if k not in data: data[k] = default_data[k]
            return data
    except: return default_data

def save_db(data):
    with open(DB_FILE, "w") as f: json.dump(data, f, indent=4)

db = load_db()
def get_now_indo(): return datetime.datetime.now(pytz.timezone('Asia/Jakarta'))

# --- FUNGSI CEK FSUB (MULTI-CHANNEL) ---
async def check_fsub(user_id, context):
    not_joined = []
    for cid in FSUB_LIST:
        try:
            member = await context.bot.get_chat_member(cid, user_id)
            if member.status in [ChatMemberStatus.LEFT, ChatMemberStatus.BANNED]:
                not_joined.append(cid)
        except:
            not_joined.append(cid) # Jika bot bukan admin/error, anggap belum join
    return not_joined

# --- FITUR MENU NAVIGASI ---
async def menu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    is_owner = (user.id == ID_OWNER)
    
    if is_owner:
        text = (
            f"👑 <b>ADMIN COMMAND CENTER</b>\n"
            f"<code>----------------------------</code>\n"
            f"📊 /stats | ℹ️ /info | 📢 /bc\n"
            f"🛡️ /ban, /unban, /mute, /unmute\n"
            f"<code>----------------------------</code>"
        )
        keyboard = [[InlineKeyboardButton("📂 Backup Database", callback_data="p_backup")]]
    else:
        text = (
            f"👋 <b>HALO {user.first_name.upper()}!</b>\n"
            f"<code>----------------------------</code>\n"
            f"Gunakan tag: #DgBoy, #DgGirl, #DgAsk, #DgStory, #DgCurhat, #DgSpill\n\n"
            f"Bantuan: /info"
            f"<code>----------------------------</code>"
        )
        keyboard = [[InlineKeyboardButton("🌐 Cek Channel", url="https://t.me/AnheavenAlliance")]]

    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

# --- CALLBACK UNTUK BACKUP ---
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.from_user.id != ID_OWNER: return
    if query.data == "p_backup":
        with open(DB_FILE, 'rb') as f:
            await context.bot.send_document(chat_id=ID_OWNER, document=f, caption="📄 Manual Backup DB")
        await query.answer("Backup terkirim!")

# --- FITUR STATS ---
async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ID_OWNER: return
    uptime = str(datetime.timedelta(seconds=int(time.time() - START_TIME)))
    text = (
        f"📊 <b>DEMIGOD STATISTICS</b>\n"
        f"<code>----------------------------</code>\n"
        f"👥 Users: {len(db['stats'])}\n"
        f"🚫 Banned: {len(db['blacklist'])}\n"
        f"⏳ Uptime: {uptime}\n"
        f"<code>----------------------------</code>"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

# --- FITUR INFO ---
async def info_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat, msg = update.effective_chat, update.message
    if msg.reply_to_message:
        target = msg.reply_to_message.from_user
        try:
            full_user = await context.bot.get_chat(target.id)
            text = (
                f"👤 <b>USER INFO</b>\n"
                f"Nama: {target.full_name}\n"
                f"ID: <code>{target.id}</code>\n"
                f"Bio: {full_user.bio if full_user.bio else '-'}"
            )
        except: text = "❌ Gagal mengambil info."
        await msg.reply_text(text, parse_mode=ParseMode.HTML)
    else:
        await msg.reply_text(f"ℹ️ <b>CHAT INFO</b>\nName: {chat.title}\nID: <code>{chat.id}</code>", parse_mode=ParseMode.HTML)

# --- BROADCAST & MODERASI ---
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ID_OWNER or not context.args: return
    msg_text = " ".join(context.args)
    users = list(db["stats"].keys())
    for uid in users:
        try:
            await context.bot.send_message(chat_id=int(uid), text=f"📢 <b>PENGUMUMAN</b>\n\n{msg_text}", parse_mode=ParseMode.HTML)
            await asyncio.sleep(0.05)
        except: pass
    await update.message.reply_text("✅ Selesai!")

async def mod_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ID_OWNER or not update.message.reply_to_message: return
    match = re.search(r"UID: (\d+)", update.message.reply_to_message.text)
    if not match: return
    target_id = match.group(1)
    cmd = update.message.text.split()[0].lower()
    
    if cmd == "/ban": db["blacklist"][target_id] = True; msg = "🚫 BANNED"
    elif cmd == "/unban": db["blacklist"].pop(target_id, None); msg = "✅ UNBANNED"
    elif cmd == "/mute":
        end = time.time() + (int(context.args[0])*60) if context.args else time.time() + 3110400000
        db["mute"][target_id] = {"end_time": end}; msg = "🔇 MUTED"
    elif cmd == "/unmute": db["mute"].pop(target_id, None); msg = "🔊 UNMUTED"
        
    save_db(db); await update.message.reply_text(f"{msg}: <code>{target_id}</code>", parse_mode=ParseMode.HTML)

# --- WATERMARK ---
def add_watermark(image_bytes):
    try:
        img = Image.open(BytesIO(image_bytes)).convert("RGBA")
        draw = ImageDraw.Draw(img)
        font = ImageFont.load_default()
        draw.text((10, img.height-25), WATERMARK_TEXT, fill=(255,255,255,150), font=font)
        out = BytesIO(); img.convert("RGB").save(out, format="JPEG"); out.seek(0)
        return out
    except: return BytesIO(image_bytes)

# --- HANDLER UTAMA ---
async def handle_menfess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user, msg = update.effective_user, update.message
    text = msg.text or msg.caption or ""
    uid_str = str(user.id)

    if text.startswith('/') or uid_str in db["blacklist"]: return
    
    # Check Mute
    if uid_str in db["mute"] and time.time() < db["mute"][uid_str]['end_time']:
        return await msg.reply_text("<code>[!] MUTED</code>", parse_mode=ParseMode.HTML)

    # Check FSub (Multi-Channel)
    not_joined = await check_fsub(user.id, context)
    if not_joined:
        btn_list = []
        for cid in not_joined:
            try:
                chat = await context.bot.get_chat(cid)
                link = chat.invite_link or f"https://t.me/{chat.username}"
                btn_list.append(InlineKeyboardButton(f"Join {chat.title}", url=link))
            except: continue
        
        # Susun tombol 2 baris (maksimal 4 tombol)
        keyboard = [btn_list[i:i + 2] for i in range(0, len(btn_list), 2)]
        return await msg.reply_text(
            "❌ <b>AKSES DITOLAK</b>\n\nKamu harus bergabung ke channel sponsor di bawah ini terlebih dahulu!",
            reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML
        )

    # Proses Posting
    tags = ["#DgBoy", "#DgGirl", "#DgAsk", "#DgStory", "#DgCurhat", "#DgSpill"]
    if any(t.lower() in text.lower() for t in tags):
        msg_id_code = f"#Gm{random.randint(1000, 9999)}"
        try:
            channel = await context.bot.get_chat(ID_AUTOPOST)
            cap = f"<b>[ DEMIGOD MENFESS ]</b>\n\n{text}\n\n<b>ID:</b> {msg_id_code}"
            
            if msg.photo:
                p_file = await msg.photo[-1].get_file()
                p_bytes = await p_file.download_as_bytearray()
                proc_img = await asyncio.to_thread(add_watermark, p_bytes)
                sent = await context.bot.send_photo(ID_AUTOPOST, photo=InputFile(proc_img), caption=cap, parse_mode=ParseMode.HTML)
            else:
                sent = await context.bot.send_message(ID_AUTOPOST, cap, parse_mode=ParseMode.HTML)

            post_link = f"https://t.me/{channel.username}/{sent.message_id}" if channel.username else f"https://t.me/c/{str(ID_AUTOPOST)[4:]}/{sent.message_id}"
            await context.bot.send_message(ID_LOGS, f"UID: <code>{user.id}</code>\nCODE: {msg_id_code}\nDATA: {text}", parse_mode=ParseMode.HTML)
            
            db["stats"][uid_str] = db["stats"].get(uid_str, {"count":0})
            db["stats"][uid_str]["count"] += 1; save_db(db)
            
            await msg.reply_text(f"✅ **Terkirim di {channel.title}**", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Cek Postingan 🔗", url=post_link)]]), parse_mode=ParseMode.HTML)
        except Exception as e: await msg.reply_text(f"Error: {e}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN_BOT).build()
    app.add_handler(CommandHandler("menu", menu_cmd))
    app.add_handler(CommandHandler("stats", stats_cmd))
    app.add_handler(CommandHandler("info", info_cmd))
    app.add_handler(CommandHandler("bc", broadcast))
    app.add_handler(CallbackQueryHandler(button_callback))
    for c in ["ban", "unban", "mute", "unmute"]: app.add_handler(CommandHandler(c, mod_action))
    app.add_handler(MessageHandler((filters.TEXT | filters.PHOTO | filters.VIDEO) & (~filters.COMMAND), handle_menfess))
    print("Bot v25.0 Aktif!")
    app.run_polling()

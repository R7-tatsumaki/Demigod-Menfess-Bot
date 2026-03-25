# --- UI START (WELCOME MESSAGE - TERMINAL MODE) ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    fullname = update.effective_user.full_name 
    user_id = update.effective_user.id
    
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
        f"<code>[!] STATUS: WAJIB JOIN FSUB</code>"
    )
    await update.message.reply_text(ui_terminal_start, parse_mode=ParseMode.HTML)

# --- UI MENFESS (POSTING STYLE - TERMINAL MODE) ---
async def handle_menfess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    user, text, now, uid_str = update.effective_user, update.message.text, time.time(), str(update.effective_user.id)

    if text.startswith('/'): return

    # --- PROTEKSI (Blacklist/Mute) ---
    if uid_str in db["blacklist"]: return
    if uid_str in db["mute"]:
        if now < db["mute"][uid_str]['end_time']:
            return await update.message.reply_text(f"<code>[!] ACCESS DENIED: MUTED</code>", parse_mode=ParseMode.HTML)
        else: del db["mute"][uid_str]; save_db(db)

    # --- CEK FSUB ---
    is_joined, missing = await check_fsub(update, context)
    if not is_joined:
        btn = [[InlineKeyboardButton(f"LINK: {m['title']}", url=m['url'])] for m in missing]
        return await update.message.reply_text("<code>[!] ERROR: FSUB_REQUIRED</code>", reply_markup=InlineKeyboardMarkup(btn), parse_mode=ParseMode.HTML)

    # --- PROSES KIRIM ---
    tags = ["#DgBoy", "#DgGirl", "#DgAsk", "#DgStory", "#DgCurhat", "#DgSpill"]
    if any(t.lower() in text.lower() for t in tags):
        try:
            # Tampilan di Channel (Postingan)
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
            
            # Logs untuk Owner
            await context.bot.send_message(ID_LOGS, f"<code>[ LOG_ENTRY ]</code>\n<b>SENDER:</b> {user.full_name}\n<b>ID:</b> {user.id}\n<b>DATA:</b> {text}", parse_mode=ParseMode.HTML)
            
            db["stats"][uid_str] = db["stats"].get(uid_str, 0) + 1
            save_db(db)
            
            await update.message.reply_text("<code>[+] STATUS: SIGNAL_SENT</code>", parse_mode=ParseMode.HTML)
        except: 
            await update.message.reply_text("<code>[-] STATUS: CRITICAL_ERROR</code>", parse_mode=ParseMode.HTML)

import os
import json
import asyncio
from flask import Flask
from threading import Thread
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ================= SERVER =================
app = Flask('')
@app.route('/')
def home(): return "Bot is Live!"

def run(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
def keep_alive(): Thread(target=run).start()

# ================= CONFIG =================
BOT_TOKEN = "8653750221:AAHc-BZI3lXNRyJ3xOa9SGuFOK_3uJcqPco"
ADMIN_ID = 7132741918
SUPPORT = "@BOYSPROOF"
AD_LINK = "https://omg10.com/4/10903029" 

CHANNELS = ["@Sumanearningtrickk", "@PaisaBachaoDealssss", "@EarnBazaarrr"]
CHANNEL_LINKS = ["https://t.me/Sumanearningtrickk", "https://t.me/PaisaBachaoDealssss", "https://t.me/EarnBazaarrr"]

DATA_FILE = "users.json"
CODES_FILE = "codes.txt"

# ================= HELPERS =================
def load_users():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except: return {}
    return {}

def save_users(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def load_codes():
    if os.path.exists(CODES_FILE):
        with open(CODES_FILE, "r") as f:
            return [c.strip() for c in f.readlines() if c.strip()]
    return []

def save_codes(c_list):
    with open(CODES_FILE, "w") as f:
        f.write("\n".join(c_list))

# ================= LOGIC =================
async def is_joined(bot, user_id):
    if user_id == ADMIN_ID: return True
    for ch in CHANNELS:
        try:
            m = await bot.get_chat_member(chat_id=ch, user_id=user_id)
            if m.status not in ["member", "administrator", "creator"]: return False
        except: continue
    return True

def main_menu():
    kb = [["💰 Balance", "👥 Refer Earn"], ["🎁 Bonus", "💸 Withdraw"], ["🆘 Support"]]
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    uid = str(user_id)
    
    # 1. Join Check
    if not await is_joined(context.bot, user_id):
        btn = [[InlineKeyboardButton(f"🔔 Join Channel {i+1}", url=l)] for i, l in enumerate(CHANNEL_LINKS)]
        btn.append([InlineKeyboardButton("✅ Verify Joined", callback_data="verify")])
        await update.message.reply_text("🔒 **Access Restricted**\n\nJoin channels to use bot:", reply_markup=InlineKeyboardMarkup(btn))
        return

    users = load_users()
    
    # 2. New User & Refer Logic
    if uid not in users:
        users[uid] = {"balance": 0, "refs": []}
        
        if context.args:
            ref_id = str(context.args[0])
            # Check if referrer exists and is not the same user
            if ref_id in users and ref_id != uid:
                # Add 1 coin to referrer
                users[ref_id]["balance"] += 1
                if "refs" not in users[ref_id]: users[ref_id]["refs"] = []
                users[ref_id]["refs"].append(uid)
                
                # Notify Referrer
                try:
                    await context.bot.send_message(chat_id=int(ref_id), text=f"🔔 **New Refer!**\nUser {uid} joined. You got +1 coin!")
                except: pass
        
        save_users(users) # Save data for new user

    await update.message.reply_text("🎉 **Welcome to Myntra Bot**", reply_markup=main_menu())

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    uid = str(update.effective_user.id)
    users = load_users()
    
    if uid not in users: 
        users[uid] = {"balance": 0, "refs": []}
        save_users(users)

    if text == "💰 Balance":
        await update.message.reply_text(f"💰 **Balance:** {users[uid].get('balance', 0)} coins")
        
    elif text == "👥 Refer Earn":
        bot_info = await context.bot.get_me()
        link = f"https://t.me/{bot_info.username}?start={uid}"
        await update.message.reply_text(f"👥 **Refer & Earn**\n\n🔥 1 Refer = 1 Coin\n🎁 3 Refer = 1 Code\n\n🔗 Your Link: {link}")
        
    elif text == "🎁 Bonus":
        btn = InlineKeyboardMarkup([[InlineKeyboardButton("🎁 Claim Bonus", url=AD_LINK)]])
        await update.message.reply_text("Watch ad to get bonus:", reply_markup=btn)
        
    elif text == "💸 Withdraw":
        codes = load_codes()
        if users[uid].get("balance", 0) < 3:
            await update.message.reply_text("❌ Minimum 3 coins required!")
            return
        if not codes:
            await update.message.reply_text("❌ Code limited over. Wait for new stock.")
            return

        # Success - Coin Cut
        my_code = codes.pop(0)
        users[uid]["balance"] -= 3
        save_codes(codes)
        save_users(users)
        
        btn = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Verify Code", url=AD_LINK)]])
        await update.message.reply_text(f"✅ **Withdraw Success!**\n\n🎁 Code: `{my_code}`\n\n3 Coins cut.", reply_markup=btn, parse_mode="Markdown")
            
    elif text == "🆘 Support":
        await update.message.reply_text(f"📞 Support: {SUPPORT}")

# ================= ADMIN =================
async def addcode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    new_c = " ".join(context.args)
    if new_c:
        c_list = load_codes()
        c_list.append(new_c)
        save_codes(c_list)
        await update.message.reply_text(f"✅ Added! Total: {len(c_list)}")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    txt = " ".join(context.args)
    users = load_users()
    for u in users:
        try: await context.bot.send_message(chat_id=int(u), text=txt)
        except: continue
    await update.message.reply_text("Broadcast Done!")

def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("addcode", addcode))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(CallbackQueryHandler(start, pattern="verify"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu))
    keep_alive()
    application.run_polling()

if __name__ == '__main__':
    main()

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

# ================= FAKE SERVER FOR RENDER =================
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# ================= CONFIG =================
BOT_TOKEN = "8653750221:AAFT-Yt-EaW-8tN1wl6MlRpZELtc4OcqxfY"
ADMIN_ID = 7132741918
SUPPORT = "@BOYSPROOF"
AD_LINK = "https://omg10.com/4/10903029" 

CHANNELS = ["@Sumanearningtrickk", "@PaisaBachaoDealssss", "@EarnBazaarrr"]
CHANNEL_LINKS = [
    "https://t.me/Sumanearningtrickk",
    "https://t.me/PaisaBachaoDealssss",
    "https://t.me/EarnBazaarrr",
]

DATA_FILE = "users.json"
CODES_FILE = "codes.txt"

# ================= DATA HELPERS =================
def load_users():
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        return {}
    except:
        return {}

def save_users(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

def load_codes():
    try:
        if os.path.exists(CODES_FILE):
            with open(CODES_FILE, "r") as f:
                content = f.read().splitlines()
                return [c for c in content if c.strip()]
        return []
    except:
        return []

def save_codes(c):
    with open(CODES_FILE, "w") as f:
        f.write("\n".join(c))

# ================= LOGIC =================
async def is_joined(bot, user_id):
    for ch in CHANNELS:
        try:
            m = await bot.get_chat_member(ch, user_id)
            if m.status not in ["member", "administrator", "creator"]:
                return False
        except:
            return False
    return True

def join_buttons():
    btn = [[InlineKeyboardButton(f"🔔 Join Channel {i+1}", url=l)] for i, l in enumerate(CHANNEL_LINKS)]
    btn.append([InlineKeyboardButton("✅ Verify Joined", callback_data="verify")])
    return InlineKeyboardMarkup(btn)

def main_menu():
    kb = [["💰 Balance", "👥 Refer Earn"], ["🎁 Bonus", "💸 Withdraw"], ["🆘 Support"]]
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    uid = str(user_id)
    
    users = load_users()
    await update.message.reply_text("⏳ Checking...", reply_markup=ReplyKeyboardRemove())

    if not await is_joined(context.bot, user_id):
        await update.message.reply_text("🔒 Access Restricted\n\nJoin all channels👇", reply_markup=join_buttons())
        return

    if uid not in users:
        users[uid] = {"balance": 0, "refs": []}
        if context.args:
            ref = context.args[0]
            if ref != uid and ref in users and uid not in users[ref]["refs"]:
                users[ref]["balance"] += 1
                users[ref]["refs"].append(uid)
    
    save_users(users)
    await update.message.reply_text(
        "🎉 Welcome to Myntra Free Code Bot\nInvite karo aur free code pao!", 
        reply_markup=main_menu()
    )

async def verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if await is_joined(context.bot, q.from_user.id):
        await q.message.reply_text("✅ Joined Successfully!", reply_markup=main_menu())
    else:
        await q.message.reply_text("❌ Join sab channels!", reply_markup=join_buttons())

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    uid = str(update.effective_user.id)
    
    users = load_users()
    if uid not in users: 
        users[uid] = {"balance": 0, "refs": []}

    if text == "💰 Balance":
        await update.message.reply_text(f"💰 Your Balance: {users[uid]['balance']} coins")
        
    elif text == "👥 Refer Earn":
        link = f"https://t.me/{context.bot.username}?start={uid}"
        await update.message.reply_text(f"👥 Refer & Earn\n\n🔥 1 Refer = 1 Coin\n🎁 3 Refer = 1 Myntra Code\n\n🔗 Link: {link}")
        
    elif text == "🎁 Bonus":
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🎁 Claim Bonus (Watch Ad)", url=AD_LINK)]])
        await update.message.reply_text("🔥 **Daily Bonus!**\n\nWatch ad to get bonus.", reply_markup=keyboard, parse_mode="Markdown")
        
    elif text == "💸 Withdraw":
        codes = load_codes()
        if users[uid]["balance"] < 3:
            await update.message.reply_text("❌ Minimum 3 coins required!")
            return
        if not codes:
            await update.message.reply_text("❌ Code limited over. Wait and withdrawal again after new stock.")
            return

        code_to_give = codes.pop(0)
        users[uid]["balance"] -= 3
        save_users(users)
        save_codes(codes)

        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Open Myntra Code", url=AD_LINK)]])
        await update.message.reply_text(
            f"💸 **Withdraw Success!**\n\n🎁 Your Code: `{code_to_give}`\n\nVerification ke liye button dabayein.",
            reply_markup=keyboard, parse_mode="Markdown"
        )
            
    elif text == "🆘 Support":
        await update.message.reply_text(f"📞 Support: {SUPPORT}")

# ================= ADMIN COMMANDS =================

async def addcode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    new_code = " ".join(context.args)
    if new_code:
        current_codes = load_codes()
        current_codes.append(new_code)
        save_codes(current_codes)
        await update.message.reply_text(f"✅ Code added! Total stock: {len(current_codes)}")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    msg_text = " ".join(context.args)
    if not msg_text:
        await update.message.reply_text("Usage: /broadcast [Your Message]")
        return

    users = load_users()
    count = 0
    await update.message.reply_text(f"📢 Sending message to {len(users)} users...")

    for uid in users:
        try:
            await context.bot.send_message(chat_id=int(uid), text=msg_text)
            count += 1
            await asyncio.sleep(0.05) # Rate limit se bachne ke liye
        except:
            continue
    
    await update.message.reply_text(f"✅ Broadcast Done! Sent to {count} users.")

# ================= RUN =================
def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("addcode", addcode))
    application.add_handler(CommandHandler("broadcast", broadcast)) # Naya Command
    
    application.add_handler(CallbackQueryHandler(verify, pattern="verify"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu))
    
    print("Bot is starting...")
    application.run_polling()

if __name__ == '__main__':
    keep_alive()
    main()

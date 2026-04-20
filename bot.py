import os
import json
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
# Token ko Render ke 'Environment Variables' mein 'BOT_TOKEN' naam se save karein
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8653750221:AAFT-Yt-EaW-8tN1wl6MlRpZELtc4OcqxfY")

CHANNELS = ["@Sumanearningtrickk", "@PaisaBachaoDealssss", "@EarnBazaarrr"]
CHANNEL_LINKS = [
    "https://t.me/Sumanearningtrickk",
    "https://t.me/PaisaBachaoDealssss",
    "https://t.me/EarnBazaarrr",
]

ADMIN_ID = 7132741918
SUPPORT = "@BOYSPROOF"
DATA_FILE = "users.json"
CODES_FILE = "codes.txt"

# ================= DATA HELPERS =================
def load_users():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_users(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

def load_codes():
    try:
        with open(CODES_FILE, "r") as f:
            return f.read().splitlines()
    except:
        return []

def save_codes(c):
    with open(CODES_FILE, "w") as f:
        f.write("\n".join(c))

users = load_users()
codes = load_codes()

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
    await update.message.reply_text(""🔥 Welcome to Myntra Free Code Bot!\nInvite karo aur free code pao 💸"", reply_markup=main_menu())

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
    if uid not in users: users[uid] = {"balance": 0, "refs": []}

    if text == "💰 Balance":
        await update.message.reply_text(f"💰 {users[uid]['balance']} coins")
    elif text == "👥 Refer Earn":
        link = f"https://t.me/{context.bot.username}?start={uid}"
        await update.message.reply_text(f"👥 Refer & Earn\n\n"🔥 1 Refer = 1 Coin\n🎁 3 Refer = 1 Myntra Code"\n\n{link}")
    elif text == "🎁 Bonus":
        await update.message.reply_text("🎁 Coming soon")
    elif text == "💸 Withdraw":
        if users[uid]["balance"] >= 3 and codes:
            code = codes.pop(0)
            users[uid]["balance"] -= 3
            save_codes(codes)
            save_users(users)
            await update.message.reply_text(f"🎁 Code:\n{code}")
        else:
            await update.message.reply_text("❌ Not enough coins or no codes.")
    elif text == "🆘 Support":
        await update.message.reply_text(f"📞 Support: {SUPPORT}")

async def addcode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        code = " ".join(context.args)
        if code:
            codes.append(code)
            save_codes(codes)
            await update.message.reply_text("✅ Code added")

# ================= RUN =================
def main():
    # Application build
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("addcode", addcode))
    application.add_handler(CallbackQueryHandler(verify, pattern="verify"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu))

    print("Bot is starting...")
    application.run_polling()

if __name__ == '__main__':
    keep_alive()
    main()

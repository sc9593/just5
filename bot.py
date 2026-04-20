import logging
import json
from telegram import (
    Update, ReplyKeyboardMarkup,
    InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

# ====== SETTINGS ======
BOT_TOKEN = "8653750221:AAFT-Yt-EaW-8tN1wl6MlRpZELtc4OcqxfY"
CHANNEL_USERNAME = "@Sumanearningtrickk"
ADMIN_ID = 7132741918

DATA_FILE = "users.json"
CODES_FILE = "codes.txt"

logging.basicConfig(level=logging.INFO)

# ====== LOAD/SAVE ======
def load_users():
    try:
        with open(DATA_FILE) as f:
            return json.load(f)
    except:
        return {}

def save_users(d):
    with open(DATA_FILE, "w") as f:
        json.dump(d, f)

def load_codes():
    try:
        with open(CODES_FILE) as f:
            return f.read().splitlines()
    except:
        return []

def save_codes(c):
    with open(CODES_FILE, "w") as f:
        f.write("\n".join(c))

users = load_users()
codes = load_codes()

# ====== UI ======
def main_menu():
    kb = [["🚀 Invite"], ["💰 Balance"], ["🎁 Withdraw"]]
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

def join_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Join Channel", url="https://t.me/Sumanearningtrickk")],
        [InlineKeyboardButton("✅ I Joined", callback_data="verify")]
    ])

# ====== START ======
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # हमेशा पहले join UI दिखाओ (ऊपर inline)
    await update.message.reply_text(
        "⚠️ पहले चैनल जॉइन करो, फिर Verify दबाओ:",
        reply_markup=join_kb()
    )

# ====== VERIFY (simple/manual) ======
async def verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    uid = str(q.from_user.id)

    # user create + referral
    if uid not in users:
        users[uid] = {"balance": 0, "ref": 0}

        if context.args:
            ref = context.args[0]
            if ref != uid and ref in users:
                users[ref]["balance"] += 1
                users[ref]["ref"] += 1

    save_users(users)

    # नीचे menu (reply keyboard)
    await q.message.reply_text(
        "✅ Verified! अब नीचे से options use करो 👇",
        reply_markup=main_menu()
    )

# ====== BUTTON HANDLER ======
async def handle_msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    uid = str(update.effective_user.id)

    if text == "🚀 Invite":
        bot = (await context.bot.get_me()).username
        link = f"https://t.me/{bot}?start={uid}"
        await update.message.reply_text(
            f"🔗 Your Link:\n{link}\n\n1 referral = 1 coin"
        )

    elif text == "💰 Balance":
        bal = users.get(uid, {}).get("balance", 0)
        await update.message.reply_text(f"💰 Balance: {bal} coins")

    elif text == "🎁 Withdraw":
        bal = users.get(uid, {}).get("balance", 0)

        if bal < 3:
            await update.message.reply_text("❌ Minimum 3 coins required")
            return

        if not codes:
            await update.message.reply_text("⚠️ Codes out of stock")
            return

        code = codes.pop(0)
        users[uid]["balance"] -= 3

        save_users(users)
        save_codes(codes)

        await update.message.reply_text(f"🎉 Your Code:\n{code}")

# ====== ADMIN ======
async def add_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    try:
        c = context.args[0]
        codes.append(c)
        save_codes(codes)
        await update.message.reply_text("✅ Code added")
    except:
        await update.message.reply_text("Use: /addcode CODE123")

# ====== RUN ======
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addcode", add_code))
    app.add_handler(CallbackQueryHandler(verify, pattern="verify"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_msg))

    print("🚀 Bot Running...")
    app.run_polling()

if __name__ == "__main__":
    main()
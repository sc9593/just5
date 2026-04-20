import os
from flask import Flask
from threading import Thread

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
import json
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

# ================= CONFIG =================
BOT_TOKEN = "8653750221:AAFT-Yt-EaW-8tN1wl6MlRpZELtc4OcqxfY"

CHANNELS = [
    "@Sumanearningtrickk",
    "@PaisaBachaoDealssss",
    "@EarnBazaarrr",
]

CHANNEL_LINKS = [
    "https://t.me/Sumanearningtrickk",
    "https://t.me/PaisaBachaoDealssss",
    "https://t.me/EarnBazaarrr",
]

ADMIN_ID = 7132741918
SUPPORT = "@BOYSPROOF"

DATA_FILE = "users.json"
CODES_FILE = "codes.txt"

# ================= DATA =================
def load_users():
    try:
        return json.load(open(DATA_FILE))
    except:
        return {}

def save_users(data):
    json.dump(data, open(DATA_FILE, "w"))

def load_codes():
    try:
        return open(CODES_FILE).read().splitlines()
    except:
        return []

def save_codes(c):
    open(CODES_FILE, "w").write("\n".join(c))

users = load_users()
codes = load_codes()

# ================= JOIN CHECK =================
async def is_joined(bot, user_id):
    for ch in CHANNELS:
        try:
            m = await bot.get_chat_member(ch, user_id)
            if m.status not in ["member", "administrator", "creator"]:
                return False
        except:
            return False
    return True

# ================= BUTTONS =================
def join_buttons():
    btn = []
    for i, link in enumerate(CHANNEL_LINKS):
        btn.append([InlineKeyboardButton(f"🔔 Join Channel {i+1}", url=link)])
    btn.append([InlineKeyboardButton("✅ Verify Joined", callback_data="verify")])
    return InlineKeyboardMarkup(btn)

def main_menu():
    kb = [
        ["💰 Balance", "👥 Refer Earn"],
        ["🎁 Bonus", "💸 Withdraw"],
        ["🆘 Support"],
    ]
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    uid = str(user_id)

    # 🔒 hide old keyboard
    await update.message.reply_text("⏳ Checking...", reply_markup=ReplyKeyboardRemove())

    # 🔥 FORCE JOIN
    if not await is_joined(context.bot, user_id):
        await update.message.reply_text(
            "🔒 Access Restricted\n\nJoin all channels👇 then click Verify",
            reply_markup=join_buttons(),
        )
        return

    # user create
    if uid not in users:
        users[uid] = {"balance": 0, "refs": []}

        # referral
        if context.args:
            ref = context.args[0]
            if ref != uid and ref in users:
                if uid not in users[ref]["refs"]:
                    users[ref]["balance"] += 1
                    users[ref]["refs"].append(uid)

    save_users(users)

    await update.message.reply_text(
        "🎉 Welcome!",
        reply_markup=main_menu(),
    )

# ================= VERIFY =================
async def verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    user_id = q.from_user.id

    if await is_joined(context.bot, user_id):
        await q.message.reply_text(
            "✅ Joined Successfully!",
            reply_markup=main_menu(),
        )
    else:
        await q.message.reply_text(
            "❌ Join sab channels!",
            reply_markup=join_buttons(),
        )

# ================= MENU =================
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    uid = str(update.effective_user.id)

    if uid not in users:
        users[uid] = {"balance": 0, "refs": []}

    # balance
    if text == "💰 Balance":
        await update.message.reply_text(f"💰 {users[uid]['balance']} coins")

    # refer
    elif text == "👥 Refer Earn":
        link = f"https://t.me/{context.bot.username}?start={uid}"
        await update.message.reply_text(
            f"👥 Refer & Earn\n\n1 Refer = 1 Coin\n3 Refer = 1 Code 🎁\n\n{link}"
        )

    # bonus
    elif text == "🎁 Bonus":
        await update.message.reply_text("🎁 Coming soon")

    # withdraw
    elif text == "💸 Withdraw":
        if users[uid]["balance"] >= 3:
            if codes:
                code = codes.pop(0)
                save_codes(codes)
                users[uid]["balance"] -= 3
                save_users(users)
                await update.message.reply_text(f"🎁 Code:\n{code}")
            else:
                await update.message.reply_text("❌ No codes")
        else:
            await update.message.reply_text("❌ Need 3 coins")

    # support
    elif text == "🆘 Support":
        await update.message.reply_text(f"📞 {SUPPORT}")

# ================= ADMIN =================
async def addcode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    code = " ".join(context.args)
    codes.append(code)
    save_codes(codes)
    await update.message.reply_text("✅ Code added")

# ================= RUN =================
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addcode", addcode))
    app.add_handler(CommandHandler("verify", verify))
   app.add_handler(CallbackQueryHandler(verify, pattern="verify"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu))

    print("Bot is starting...")
    app.run_polling()

if __name__ == '__main__':
    keep_alive()  # Ye Flask server start karega (Step 1 wala code zarur upar dal dena)
    main()        # Ye bot start karega

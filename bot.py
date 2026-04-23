import os
import json
import logging
import asyncio
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

# Logging setup
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

# ================= SERVER (For Render) =================
app = Flask('')
@app.route('/')
def home(): return "Bot is Online!"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
def keep_alive(): Thread(target=run).start()

# ================= CONFIGURATION =================
BOT_TOKEN = "8653750221:AAHx4A_npTXnorIqHHP6tCKGgOVwRyQ9QZw"
ADMIN_ID = 7132741918
SUPPORT = "@BOYSPROOF"
AD_LINK = "https://omg10.com/4/10903029"
UPI_ID = "paytmqr1qqff9il6x@paytm"
PAYEE_NAME = "Suman Chowdhury"
QR_IMAGE_URL = "https://i.postimg.cc/VNxwYmcZ/Paytm-QRcode-1758815347919.png"

WITHDRAW_COST = 8
REFER_REWARD = 1
CHANNELS = ["@Sumanearningtrickk", "@PaisaBachaoDealssss", "@EarnBazaarrr"]
CHANNEL_LINKS = ["https://t.me/Sumanearningtrickk", "https://t.me/PaisaBachaoDealssss", "https://t.me/EarnBazaarrr"]

DATA_FILE = "database.json"
PAID_STOCK_FILE = "paid_stock.txt"
FREE_STOCK_FILE = "free_stock.txt"

# ================= DATABASE HELPERS =================
def load_db():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f: return json.load(f)
        except: return {"users": {}}
    return {"users": {}}

def save_db(data):
    with open(DATA_FILE, "w") as f: json.dump(data, f, indent=4)

def get_stock(filename):
    if os.path.exists(filename):
        with open(filename, "r") as f: return [c.strip() for c in f.readlines() if c.strip()]
    return []

def save_stock(filename, codes):
    with open(filename, "w") as f: f.write("\n".join(codes))

# ================= LOGIC =================
async def is_joined(bot, user_id):
    if user_id == ADMIN_ID: return True
    for ch in CHANNELS:
        try:
            m = await bot.get_chat_member(chat_id=ch, user_id=user_id)
            if m.status not in ["member", "administrator", "creator"]: return False
        except: return False
    return True

def main_menu():
    return ReplyKeyboardMarkup([["🛒 Buy Code"], ["💰 Balance", "👥 Refer Earn"], ["🎁 Bonus", "💸 Free Withdraw"], ["🆘 Support"]], resize_keyboard=True)

def join_buttons():
    btn = [[InlineKeyboardButton(f"🔔 Join Channel {i+1}", url=l)] for i, l in enumerate(CHANNEL_LINKS)]
    btn.append([InlineKeyboardButton("✅ Verify Joined", callback_data="verify")])
    return InlineKeyboardMarkup(btn)

# ================= HANDLERS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    db = load_db()
    if uid not in db["users"]:
        db["users"][uid] = {"balance": 0, "state": "NORMAL", "referred_by": None, "joined": False}
        if context.args: db["users"][uid]["referred_by"] = str(context.args[0])
        save_db(db)

    if not await is_joined(context.bot, int(uid)):
        await update.message.reply_text("🔒 **Access Restricted!**\nSare channels join karo.", reply_markup=join_buttons())
        return
    await update.message.reply_text(f"👋 **Welcome {update.effective_user.first_name}!**", reply_markup=main_menu())

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    text = update.message.text
    db = load_db()
    user = db["users"].get(uid, {"balance": 0, "state": "NORMAL"})

    # State Check for UTR
    if user.get("state") == "WAIT_UTR":
        await context.bot.send_message(chat_id=ADMIN_ID, text=f"🚨 **NEW PAYMENT**\n👤 User: `{uid}`\n🔢 UTR: `{text}`\n\nApprove: `/approve {uid}`\nReject: `/reject {uid}`")
        db["users"][uid]["state"] = "NORMAL"
        save_db(db)
        await update.message.reply_text("⏳ **Verify ho raha hai...** Admin check karke code bhej raha hai.")
        return

    if text == "🛒 Buy Code":
        stock = len(get_stock(PAID_STOCK_FILE))
        btn = [[InlineKeyboardButton("🛍️ Buy Now", callback_data="buy_confirm")]]
        await update.message.reply_text(f"🛒 **Myntra 50% Off Code**\n\n🔥 Stock: {stock}\n💰 Price: ₹80", reply_markup=InlineKeyboardMarkup(btn))

    elif text == "💰 Balance":
        await update.message.reply_text(f"💰 Balance: {user['balance']} Coins")

    elif text == "👥 Refer Earn":
        bot_un = (await context.bot.get_me()).username
        await update.message.reply_text(f"👥 **Refer & Earn**\n\n1 Refer = 1 Coin\nLink: `https://t.me/{bot_un}?start={uid}`", parse_mode="Markdown")

    elif text == "💸 Free Withdraw":
        stock = get_stock(FREE_STOCK_FILE)
        if user["balance"] < WITHDRAW_COST:
            await update.message.reply_text(f"❌ Minimum {WITHDRAW_COST} Coins chahiye!")
        elif not stock:
            await update.message.reply_text("❌ Free stock khali hai!")
        else:
            code = stock.pop(0)
            db["users"][uid]["balance"] -= WITHDRAW_COST
            save_stock(FREE_STOCK_FILE, stock); save_db(db)
            await update.message.reply_text(f"✅ **Withdraw Success!**\nCode: `{code}`")

    elif text == "🆘 Support":
        await update.message.reply_text(f"🆘 Support: {SUPPORT}")

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    uid = str(q.from_user.id)
    await q.answer()
    db = load_db()

    if q.data == "verify":
        if await is_joined(context.bot, int(uid)):
            ref = db["users"][uid].get("referred_by")
            if ref and not db["users"][uid].get("joined") and ref in db["users"]:
                db["users"][ref]["balance"] += REFER_REWARD
                db["users"][uid]["joined"] = True
                save_db(db)
                try: await context.bot.send_message(chat_id=int(ref), text="👥 **Refer Counted!** +1 Coin!")
                except: pass
            await q.message.delete()
            await context.bot.send_message(chat_id=int(uid), text="✅ Verified!", reply_markup=main_menu())

    elif q.data == "buy_confirm":
        msg = f"🧾 **Payment Details**\n\nUPI: `{UPI_ID}`\nName: {PAYEE_NAME}\n\nPay karke **✅ I Paid** dabayein."
        btn = [[InlineKeyboardButton("✅ I Paid", callback_data="ipaid")]]
        try: await context.bot.send_photo(chat_id=int(uid), photo=QR_IMAGE_URL, caption=msg, reply_markup=InlineKeyboardMarkup(btn))
        except: await context.bot.send_message(chat_id=int(uid), text=msg, reply_markup=InlineKeyboardMarkup(btn))

    elif q.data == "ipaid":
        # YAHAN CHANGE KIYA HAI - State update pehle
        db["users"][uid]["state"] = "WAIT_UTR"
        save_db(db)
        await context.bot.send_message(chat_id=int(uid), text="📝 **Ab apna 12-digit UTR ID (Transaction ID) bhejein:**")

# ================= ADMIN =================
async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        user_id = context.args[0]
        qty = int(context.args[1]) if len(context.args) > 1 else 1
        stock = get_stock(PAID_STOCK_FILE)
        if len(stock) >= qty:
            codes = [stock.pop(0) for _ in range(qty)]
            save_stock(PAID_STOCK_FILE, stock)
            await context.bot.send_message(chat_id=int(user_id), text="✅ **Payment Approved!**\nCode:\n" + "\n".join([f"`{c}`" for c in codes]), parse_mode="Markdown")
            await update.message.reply_text(f"✅ Bhej diya {user_id} ko.")
        else: await update.message.reply_text("Stock Low!")
    except: await update.message.reply_text("Use: /approve USER_ID 1")

async def reject(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        user_id = context.args[0]
        await context.bot.send_message(chat_id=int(user_id), text="❌ **Payment Rejected!** Admin se baat karein.")
        await update.message.reply_text(f"Rejected {user_id}")
    except: pass

async def addpaid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    if context.args:
        cur = get_stock(PAID_STOCK_FILE); cur.extend(context.args); save_stock(PAID_STOCK_FILE, cur)
        await update.message.reply_text(f"✅ Added {len(context.args)} paid stock.")

def main():
    keep_alive()
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("approve", approve))
    application.add_handler(CommandHandler("reject", reject))
    application.add_handler(CommandHandler("addpaid", addpaid))
    application.add_handler(CallbackQueryHandler(callback_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__': main()

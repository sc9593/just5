import os
import json
import logging
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ================= SERVER =================
app = Flask('')
@app.route('/')
def home(): return "Bot is Online!"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
def keep_alive(): Thread(target=run).start()

# ================= CONFIG =================
BOT_TOKEN = "8653750221:AAHx4A_npTXnorIqHHP6tCKGgOVwRyQ9QZw"
ADMIN_ID = 7132741918
QR_IMAGE_URL = "https://i.ibb.co/VNxwYmcZ/Paytm-QRcode.png" 
UPI_ID = "paytmqr1qqff9il6x@paytm"
PAYEE_NAME = "Suman Chowdhury"

# Files
DATA_FILE = "users_data.json"
PAID_STOCK = "paid_codes.txt"

# ================= DATABASE HELPERS =================
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f: return json.load(f)
    return {"users": {}}

def save_data(data):
    with open(DATA_FILE, "w") as f: json.dump(data, f, indent=4)

def get_paid_stock():
    if os.path.exists(PAID_STOCK):
        with open(PAID_STOCK, "r") as f: return [c.strip() for c in f.readlines() if c.strip()]
    return []

def save_paid_stock(codes):
    with open(PAID_STOCK, "w") as f: f.write("\n".join(codes))

# ================= HANDLERS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    first_name = update.effective_user.first_name
    data = load_data()

    if uid not in data["users"]:
        data["users"][uid] = {"balance": 0, "state": "NORMAL", "referred_by": None}
        # Refer Logic
        if context.args:
            ref_id = str(context.args[0])
            if ref_id in data["users"] and ref_id != uid:
                data["users"][ref_id]["balance"] += 1
                data["users"][uid]["referred_by"] = ref_id
                try:
                    await context.bot.send_message(chat_id=int(ref_id), text=f"👥 **Naya Refer!**\n{first_name} ne join kiya. +1 Coin mila!")
                except: pass
        save_data(data)

    kb = [["🛒 Buy Code"], ["💰 Balance", "👥 Refer Earn"], ["🎁 Bonus", "💸 Free Withdraw"], ["🆘 Support"]]
    await update.message.reply_text(f"👋 **Welcome {first_name}!**", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    uid = str(update.effective_user.id)
    data = load_data()
    
    if uid not in data["users"]: return

    # State check for UTR
    if data["users"][uid].get("state") == "WAIT_UTR":
        await context.bot.send_message(chat_id=ADMIN_ID, text=f"🚨 **NEW PAYMENT**\nUser: `{uid}`\nUTR: `{text}`\n\nApprove: `/approve {uid} 1`")
        data["users"][uid]["state"] = "NORMAL"
        save_data(data)
        await update.message.reply_text("✅ **UTR Received!** Admin verify karke code bhej raha hai.")
        return

    if text == "🛒 Buy Code":
        stock = len(get_paid_stock())
        if stock == 0:
            await update.message.reply_text("❌ Abhi stock nahi hai, wait karo.")
            return
        btn = [[InlineKeyboardButton("1 Code - ₹80", callback_data="buy_1")]]
        await update.message.reply_text(f"🛒 Stock: {stock}\n\nQuantity select karein:", reply_markup=InlineKeyboardMarkup(btn))

    elif text == "💰 Balance":
        bal = data["users"][uid]["balance"]
        await update.message.reply_text(f"💰 **Aapka Balance:** {bal} Coins")

    elif text == "👥 Refer Earn":
        bot_username = (await context.bot.get_me()).username
        link = f"https://t.me/{bot_username}?start={uid}"
        await update.message.reply_text(f"👥 **Refer & Earn**\n\n1 Refer = 1 Coin\n\n🔗 Link: `{link}`", parse_mode="Markdown")

    elif text == "🆘 Support":
        await update.message.reply_text("🆘 Support: @BOYSPROOF")

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = str(q.from_user.id)
    
    if q.data.startswith("buy_"):
        qty = q.data.split("_")[1]
        total = int(qty) * 80
        msg = f"🧾 **Order Summary**\nTotal: ₹{total}\n\nUPI: `{UPI_ID}`\nName: {PAYEE_NAME}\n\nPay karke niche button dabayein."
        btn = [[InlineKeyboardButton("✅ I Paid", callback_data="ipaid")]]
        await q.message.delete()
        try:
            await context.bot.send_photo(chat_id=int(uid), photo=QR_IMAGE_URL, caption=msg, reply_markup=InlineKeyboardMarkup(btn), parse_mode="Markdown")
        except:
            await context.bot.send_message(chat_id=int(uid), text=msg, reply_markup=InlineKeyboardMarkup(btn), parse_mode="Markdown")

    elif q.data == "ipaid":
        data = load_data()
        data["users"][uid]["state"] = "WAIT_UTR"
        save_data(data)
        await context.bot.send_message(chat_id=int(uid), text="📝 **Ab apna 12-digit UTR ID (Transaction ID) bhejein:**")

# ================= ADMIN COMMANDS =================
async def addpaid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        codes = context.args
        if codes:
            current = get_paid_stock()
            current.extend(codes)
            save_paid_stock(current)
            await update.message.reply_text(f"✅ {len(codes)} Codes added!")

async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        try:
            user_id, qty = context.args[0], int(context.args[1])
            stock = get_paid_stock()
            if len(stock) >= qty:
                given = [stock.pop(0) for _ in range(qty)]
                save_paid_stock(stock)
                await context.bot.send_message(chat_id=int(user_id), text="✅ **Approved!**\nCode: " + "\n".join(given))
                await update.message.reply_text("Bhej diya!")
        except: pass

def main():
    keep_alive()
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("addpaid", addpaid))
    application.add_handler(CommandHandler("approve", approve))
    application.add_handler(CallbackQueryHandler(callback_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__': main()

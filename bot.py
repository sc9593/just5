import os
import json
import logging
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ================= SERVER (Keep Alive) =================
app = Flask('')
@app.route('/')
def home(): return "Bot is Online!"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
def keep_alive(): Thread(target=run).start()

# ================= CONFIG =================
BOT_TOKEN = "8653750221:AAHx4A_npTXnorIqHHP6tCKGgOVwRyQ9QZw"
ADMIN_ID = 7132741918
QR_IMAGE_URL = "https://i.postimg.cc/VNxwYmcZ/Paytm-QRcode-1758815347919.png"
UPI_ID = "paytmqr1qqff9il6x@paytm"
PAYEE_NAME = "Suman Chowdhury"

# Files for Data
FREE_FILE = "free_codes.txt"
PAID_FILE = "paid_codes.txt"
USERS_FILE = "users.json"

# ================= HELPERS =================
def get_stock(filename):
    if os.path.exists(filename):
        with open(filename, "r") as f: return [c.strip() for c in f.readlines() if c.strip()]
    return []

def save_stock(filename, codes):
    with open(filename, "w") as f: f.write("\n".join(codes))

# ================= HANDLERS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [["🛒 Buy Code"], ["💰 Balance", "👥 Refer Earn"], ["🎁 Bonus", "💸 Free Withdraw"], ["🆘 Support"]]
    await update.message.reply_text(f"👋 **Welcome!**\n\nAbhi Myntra Codes Stock mein hain.", reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True))

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    uid = str(update.effective_user.id)
    
    if text == "🛒 Buy Code":
        stock_count = len(get_stock(PAID_FILE))
        if stock_count == 0:
            await update.message.reply_text("❌ **Abhi stock nahi hai!**\nThoda wait karo, admin code add kar raha hai.")
            return
            
        btn = [[InlineKeyboardButton("1", callback_data="buy_1"), InlineKeyboardButton("2", callback_data="buy_2")]]
        await update.message.reply_text(f"🛒 **Myntra 50% Off**\nStock Available: {stock_count}\n\nQuantity select karein:", reply_markup=InlineKeyboardMarkup(btn))

    elif text == "💰 Balance":
        await update.message.reply_text("💰 Aapka balance yahan show hoga.")

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    
    if q.data.startswith("buy_"):
        qty = q.data.split("_")[1]
        total = int(qty) * 80
        msg = f"🧾 **Order Summary**\nQty: {qty}\nTotal: ₹{total}\n\n🏦 **Pay to:** `{UPI_ID}`\n👤 **Name:** {PAYEE_NAME}\n\nPayment ke baad UTR bhejein."
        
        # QR Code send karne ka sahi tarika
        try:
            await context.bot.send_photo(chat_id=q.from_user.id, photo=QR_IMAGE_URL, caption=msg, parse_mode="Markdown")
        except:
            await context.bot.send_message(chat_id=q.from_user.id, text=f"⚠️ QR Load nahi hua. Pay to: `{UPI_ID}`\n\n{msg}", parse_mode="Markdown")

# ================= ADMIN =================
async def addpaid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        new_codes = context.args
        if new_codes:
            current = get_stock(PAID_FILE)
            current.extend(new_codes)
            save_stock(PAID_FILE, current)
            await update.message.reply_text(f"✅ {len(new_codes)} codes add ho gaye! Total: {len(current)}")

async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        try:
            user_id = context.args[0]
            qty = int(context.args[1])
            stock = get_stock(PAID_FILE)
            
            if len(stock) >= qty:
                given = [stock.pop(0) for _ in range(qty)]
                save_stock(PAID_FILE, stock)
                code_text = "\n".join([f"`{c}`" for c in given])
                await context.bot.send_message(chat_id=int(user_id), text=f"✅ **Payment Approved!**\n\nAapke Codes:\n{code_text}", parse_mode="Markdown")
                await update.message.reply_text("Done!")
            else:
                await update.message.reply_text("❌ Stock khatam ho gaya! Pehle /addpaid karo.")
        except:
            await update.message.reply_text("Format: `/approve USER_ID QTY`")

def main():
    keep_alive()
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("addpaid", addpaid))
    application.add_handler(CommandHandler("approve", approve))
    application.add_handler(CallbackQueryHandler(callback_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    # Traffic handle karne ke liye simple polling
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__': main()

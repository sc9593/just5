import os
import json
import logging
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

# Error Logging
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

# QR Code Link (Maine update kiya hai taaki load ho sake)
QR_IMAGE_URL = "https://i.ibb.co/VNxwYmcZ/Paytm-QRcode.png" 
UPI_ID = "paytmqr1qqff9il6x@paytm"
PAYEE_NAME = "Suman Chowdhury"

# Data Files
PAID_FILE = "paid_codes.txt"

# ================= HELPERS =================
def get_stock():
    if os.path.exists(PAID_FILE):
        with open(PAID_FILE, "r") as f:
            return [c.strip() for c in f.readlines() if c.strip()]
    return []

def save_stock(codes):
    with open(PAID_FILE, "w") as f:
        f.write("\n".join(codes))

# ================= HANDLERS =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [
        ["🛒 Buy Code"],
        ["💰 Balance", "👥 Refer Earn"],
        ["🎁 Bonus", "💸 Free Withdraw"],
        ["🆘 Support"]
    ]
    await update.message.reply_text(
        f"👋 **Welcome Mithun!**\n\nAbhi Myntra 50% Off codes stock mein hain. Kharidne ke liye niche button dabayein.",
        reply_markup=ReplyKeyboardMarkup(kb, resize_keyboard=True)
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text == "🛒 Buy Code":
        all_codes = get_stock()
        stock_count = len(all_codes)
        
        if stock_count == 0:
            await update.message.reply_text("❌ **Sorry! Abhi Stock Khali Hai.**\n\nAdmin thodi der mein naye codes add karega. Tab tak wait karein.")
            return

        btn = [[InlineKeyboardButton("1 Code", callback_data="buy_1"), InlineKeyboardButton("2 Code", callback_data="buy_2")]]
        await update.message.reply_text(
            f"🛒 **Myntra 50% Off**\n🔥 Stock Available: {stock_count}\n💰 Price: ₹80/code\n\nKitne codes chahiye?",
            reply_markup=InlineKeyboardMarkup(btn)
        )
    
    elif text == "🆘 Support":
        await update.message.reply_text("🆘 Support: @myntracodes\nKoi bhi problem ho toh yahan msg karein.")

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    
    if q.data.startswith("buy_"):
        qty = q.data.split("_")[1]
        total = int(qty) * 80
        
        msg = (f"🧾 **Order Summary**\n"
               f"🔢 Quantity: {qty}\n"
               f"💰 Total Amount: **₹{total}**\n\n"
               f"🏦 **Payment Details:**\n"
               f"👤 Name: `{PAYEE_NAME}`\n"
               f"🔗 UPI ID: `{UPI_ID}`\n\n"
               f"⚠️ **Payment karne ke baad UTR (Transaction ID) chat mein bhejein.**")
        
        # QR Code Try
        try:
            # Agar image load nahi hui toh bot crash nahi hoga
            await context.bot.send_photo(chat_id=q.from_user.id, photo=QR_IMAGE_URL, caption=msg, parse_mode="Markdown")
        except Exception as e:
            # Backup message agar QR fail ho jaye
            await context.bot.send_message(chat_id=q.from_user.id, text=f"⚠️ QR Load Error! Please use UPI ID: `{UPI_ID}`\n\n{msg}", parse_mode="Markdown")

# ================= ADMIN COMMANDS =================
async def addpaid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    new_codes = context.args
    if not new_codes:
        await update.message.reply_text("Format: `/addpaid code1 code2 code3`")
        return
    
    current = get_stock()
    current.extend(new_codes)
    save_stock(current)
    await update.message.reply_text(f"✅ {len(new_codes)} Codes add ho gaye!\n📊 Total Stock: {len(current)}")

async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        user_id = context.args[0]
        qty = int(context.args[1])
        stock = get_stock()
        
        if len(stock) >= qty:
            codes_to_give = [stock.pop(0) for _ in range(qty)]
            save_stock(stock)
            
            final_codes = "\n".join([f"`{c}`" for c in codes_to_give])
            await context.bot.send_message(chat_id=int(user_id), text=f"✅ **Payment Approved!**\n\nAapke Codes Ye Rahe:\n\n{final_codes}\n\nThank you for buying!", parse_mode="Markdown")
            await update.message.reply_text(f"✅ User {user_id} ko {qty} code bhej diye gaye.")
        else:
            await update.message.reply_text(f"❌ Stock mein sirf {len(stock)} codes hain. Pehle `/addpaid` karein.")
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
    
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()

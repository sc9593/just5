import os
import json
import logging
from flask import Flask
from threading import Thread
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ================= ERROR TRACKER =================
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ================= SERVER (Keep Alive) =================
app = Flask('')
@app.route('/')
def home(): return "Bot is Online (No Firebase Mode)!"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
def keep_alive(): Thread(target=run).start()

# ================= CONFIG =================
BOT_TOKEN = "8653750221:AAHx4A_npTXnorIqHHP6tCKGgOVwRyQ9QZw"
ADMIN_ID = 7132741918
SUPPORT = "@myntracodes"
AD_LINK = "https://omg10.com/4/10903029"

UPI_ID = "paytmqr1qqff9il6x@paytm"
PAYEE_NAME = "Suman Chowdhury"
QR_IMAGE_URL = "https://i.postimg.cc/VNxwYmcZ/Paytm-QRcode-1758815347919.png"

WITHDRAW_COST = 8
REFER_REWARD = 1
DATA_FILE = "users.json"
FREE_CODES_FILE = "free_codes.txt"
PAID_CODES_FILE = "paid_codes.txt"

# ================= DATA HELPERS =================
def load_users():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f: return json.load(f)
        except: return {}
    return {}

def save_users(data):
    with open(DATA_FILE, "w") as f: json.dump(data, f, indent=4)

def load_codes(filename):
    if os.path.exists(filename):
        with open(filename, "r") as f: return [c.strip() for c in f.readlines() if c.strip()]
    return []

def save_codes(filename, c_list):
    with open(filename, "w") as f: f.write("\n".join(c_list))

# ================= HANDLERS =================
def main_menu():
    kb = [["🛒 Buy Code"], ["💰 Balance", "👥 Refer Earn"], ["🎁 Bonus", "💸 Free Withdraw"], ["🆘 Support"]]
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    first_name = update.effective_user.first_name or "User"
    users = load_users()
    
    if uid not in users:
        users[uid] = {"balance": 0, "state": "NORMAL", "name": first_name}
        if context.args:
            ref_id = str(context.args[0])
            if ref_id in users and ref_id != uid:
                users[ref_id]["balance"] += REFER_REWARD
                try:
                    await context.bot.send_message(chat_id=int(ref_id), text=f"🔔 **Refer Success!** +{REFER_REWARD} coin mila.")
                except: pass
        save_users(users)

    await update.message.reply_text(f"🎉 **Welcome {first_name}!**", reply_markup=main_menu())

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    uid = str(update.effective_user.id)
    users = load_users()
    
    if uid not in users: return
    state = users[uid].get("state", "NORMAL")

    if state == "WAIT_UTR":
        admin_msg = f"🚨 **NEW PAYMENT**\nUser: `{uid}`\nUTR: `{text}`\n\n✅ `/approve {uid} QTY` | ❌ `/reject {uid}`"
        await context.bot.send_message(chat_id=ADMIN_ID, text=admin_msg)
        users[uid]["state"] = "NORMAL"
        save_users(users)
        await update.message.reply_text("⏳ **Review mein hai!** Verification ke baad code mil jayega.")
        return

    if text == "🛒 Buy Code":
        btn = [[InlineKeyboardButton("1", callback_data="qty_1"), InlineKeyboardButton("2", callback_data="qty_2")],
               [InlineKeyboardButton("3", callback_data="qty_3"), InlineKeyboardButton("5", callback_data="qty_5")]]
        await update.message.reply_text(f"🛒 **Myntra 50% Off**\nPrice: ₹80/code\nSelect Quantity:", reply_markup=InlineKeyboardMarkup(btn))

    elif text == "💰 Balance":
        await update.message.reply_text(f"💰 **Balance:** {users[uid].get('balance', 0)} coins")
        
    elif text == "👥 Refer Earn":
        bot_info = await context.bot.get_me()
        await update.message.reply_text(f"👥 1 Refer = 1 Coin\nLink: `t.me/{bot_info.username}?start={uid}`")
        
    elif text == "💸 Free Withdraw":
        stock = load_codes(FREE_CODES_FILE)
        if users[uid].get("balance", 0) < WITHDRAW_COST:
            await update.message.reply_text(f"❌ {WITHDRAW_COST} coins chahiye!")
            return
        if not stock:
            await update.message.reply_text("❌ No Stock!")
            return
        code = stock.pop(0)
        users[uid]["balance"] -= WITHDRAW_COST
        save_codes(FREE_CODES_FILE, stock)
        save_users(users)
        await update.message.reply_text(f"✅ **Code:** `{code}`")
            
    elif text == "🆘 Support":
        await update.message.reply_text(f"🆘 Support: {SUPPORT}")

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = str(q.from_user.id)
    users = load_users()

    if q.data.startswith("qty_"):
        qty = q.data.split("_")[1]
        total = 80 * int(qty)
        users[uid]["state"] = f"PAYING_{qty}_{total}"
        save_users(users)
        
        msg = f"🧾 **Order Summary**\nQty: {qty}\nTotal: ₹{total}\n\nPay to: `{UPI_ID}`\nName: {PAYEE_NAME}\n\nTap 'I Paid' after payment."
        btn = [[InlineKeyboardButton("✅ I Paid", callback_data="ipaid")]]
        await q.message.delete()
        try:
            await context.bot.send_photo(chat_id=int(uid), photo=QR_IMAGE_URL, caption=msg, reply_markup=InlineKeyboardMarkup(btn), parse_mode="Markdown")
        except:
            await context.bot.send_message(chat_id=int(uid), text=msg, reply_markup=InlineKeyboardMarkup(btn), parse_mode="Markdown")

    elif q.data == "ipaid":
        users[uid]["state"] = "WAIT_UTR"
        save_users(users)
        await q.message.reply_text("📝 **Apna 12-digit UTR ID bhejein:**")

# ================= ADMIN =================
async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        try:
            t_uid, qty = context.args[0], int(context.args[1])
            s = load_codes(PAID_CODES_FILE)
            if len(s) >= qty:
                codes = [s.pop(0) for _ in range(qty)]
                save_codes(PAID_CODES_FILE, s)
                await context.bot.send_message(chat_id=int(t_uid), text="✅ **Approved!** Codes:\n" + "\n".join(codes))
                await update.message.reply_text("Done!")
            else: await update.message.reply_text("Stock low!")
        except: await update.message.reply_text("/approve <UID> <QTY>")

def main():
    keep_alive()
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("approve", approve))
    application.add_handler(CallbackQueryHandler(callback_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    print("🚀 Bot starting in Polling Mode (No Firebase)...")
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__': main()

import os
import json
import logging
import firebase_admin
from firebase_admin import credentials, db
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

# ================= FIREBASE SETUP =================
if not firebase_admin._apps:
    try:
        env_key = os.environ.get("FIREBASE_KEY")
        if env_key:
            # Render Environment se key uthayega
            cred = credentials.Certificate(json.loads(env_key))
        else:
            # Agar environment me nahi hai to file check karega
            cred = credentials.Certificate("firebase-key.json")
        
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://myntrabot-f4498-default-rtdb.firebaseio.com/'
        })
        print("✅ Firebase Connected!")
    except Exception as e:
        print(f"❌ Firebase Error: {e}")

users_ref = db.reference('users')
free_codes_ref = db.reference('free_codes')
paid_codes_ref = db.reference('paid_codes')
store_ref = db.reference('store_config')

# ================= CONFIG =================
BOT_TOKEN = "8653750221:AAHx4A_npTXnorIqHHP6tCKGgOVwRyQ9QZw"
ADMIN_ID = 7132741918
SUPPORT = "@myntracodes"
AD_LINK = "https://omg10.com/4/10903029"

UPI_ID = "paytmqr1qqff9il6x@paytm"
PAYEE_NAME = "Suman Chowdhury"
QR_IMAGE_URL = "https://i.postimg.cc/VNxwYmcZ/Paytm-QRcode-1758815347919.png"

RENDER_URL = "https://just5.onrender.com"
WITHDRAW_COST = 8
REFER_REWARD = 1

# ================= HANDLERS =================

def main_menu():
    kb = [["🛒 Buy Code"], ["💰 Balance", "👥 Refer Earn"], ["🎁 Bonus", "💸 Free Withdraw"], ["🆘 Support"]]
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    first_name = update.effective_user.first_name or "User"
    
    user = users_ref.child(uid).get()
    if not user:
        users_ref.child(uid).set({"balance": 0, "refs": [], "state": "NORMAL", "name": first_name})
        if context.args:
            ref_id = str(context.args[0])
            referrer = users_ref.child(ref_id).get()
            if referrer and ref_id != uid:
                new_bal = referrer.get("balance", 0) + REFER_REWARD
                users_ref.child(ref_id).update({"balance": new_bal})
                try:
                    await context.bot.send_message(chat_id=int(ref_id), text=f"🔔 **Refer Success!** +{REFER_REWARD} coin mila.")
                except: pass

    await update.message.reply_text(f"🎉 **Welcome {first_name}!**", reply_markup=main_menu())

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    uid = str(update.effective_user.id)
    user = users_ref.child(uid).get() or {}
    state = user.get("state", "NORMAL")

    if state == "WAIT_UTR":
        admin_msg = f"🚨 **NEW PAYMENT**\nUser: `{uid}`\nUTR: `{text}`\n\n✅ `/approve {uid} QTY` | ❌ `/reject {uid}`"
        await context.bot.send_message(chat_id=ADMIN_ID, text=admin_msg)
        users_ref.child(uid).update({"state": "NORMAL"})
        await update.message.reply_text("⏳ **Review mein hai!** Jaldi code mil jayega.")
        return

    if text == "🛒 Buy Code":
        config = store_ref.get() or {"price": 80}
        btn = [[InlineKeyboardButton("1", callback_data="qty_1"), InlineKeyboardButton("2", callback_data="qty_2")],
               [InlineKeyboardButton("3", callback_data="qty_3"), InlineKeyboardButton("5", callback_data="qty_5")]]
        await update.message.reply_text(f"🛒 **Myntra 50% Off**\nPrice: ₹{config['price']}\nSelect Qty:", reply_markup=InlineKeyboardMarkup(btn))

    elif text == "💰 Balance":
        await update.message.reply_text(f"💰 **Balance:** {user.get('balance', 0)} coins")
        
    elif text == "👥 Refer Earn":
        bot_info = await context.bot.get_me()
        await update.message.reply_text(f"👥 1 Refer = 1 Coin\nLink: `t.me/{bot_info.username}?start={uid}`")
        
    elif text == "💸 Free Withdraw":
        stock = free_codes_ref.get() or []
        if user.get("balance", 0) < WITHDRAW_COST:
            await update.message.reply_text(f"❌ {WITHDRAW_COST} coins chahiye!")
            return
        if not stock:
            await update.message.reply_text("❌ No Stock!")
            return
        code = stock.pop(0)
        users_ref.child(uid).update({"balance": user["balance"] - WITHDRAW_COST})
        free_codes_ref.set(stock)
        await update.message.reply_text(f"✅ **Code:** `{code}`")
            
    elif text == "🆘 Support":
        await update.message.reply_text(f"🆘 Support: {SUPPORT}")

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = str(q.from_user.id)
    if q.data.startswith("qty_"):
        qty = q.data.split("_")[1]
        config = store_ref.get() or {"price": 80}
        total = config["price"] * int(qty)
        users_ref.child(uid).update({"state": f"PAYING_{qty}_{total}"})
        msg = f"🧾 **Order Summary**\nQty: {qty}\nTotal: ₹{total}\n\nPay to: `{UPI_ID}`\nName: {PAYEE_NAME}\n\nTap 'I Paid' after payment."
        btn = [[InlineKeyboardButton("✅ I Paid", callback_data="ipaid")]]
        await q.message.delete()
        try: await q.message.reply_photo(photo=QR_IMAGE_URL, caption=msg, reply_markup=InlineKeyboardMarkup(btn))
        except: await q.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(btn))

    elif q.data == "ipaid":
        users_ref.child(uid).update({"state": "WAIT_UTR"})
        await q.message.reply_text("📝 **Apna 12-digit UTR ID bhejein:**")

# ================= ADMIN COMMANDS =================
async def admin_approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        try:
            t_uid, qty = context.args[0], int(context.args[1])
            s = paid_codes_ref.get() or []
            if len(s) >= qty:
                codes = [s.pop(0) for _ in range(qty)]
                paid_codes_ref.set(s)
                await context.bot.send_message(chat_id=int(t_uid), text="✅ **Approved!** Codes:\n" + "\n".join(codes))
                await update.message.reply_text("Done!")
            else: await update.message.reply_text("Stock low!")
        except: await update.message.reply_text("/approve <UID> <QTY>")

def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("approve", admin_approve))
    application.add_handler(CallbackQueryHandler(callback_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    PORT = int(os.environ.get("PORT", 10000))
    print(f"🚀 Webhook starting on port {PORT}")
    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=RENDER_URL,
        drop_pending_updates=True
    )

if __name__ == '__main__':
    main()

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

# ================= SAFE FIREBASE SETUP =================
print("🔄 Firebase connect kar raha hoon...")
try:
    if not firebase_admin._apps:
        if os.path.exists("firebase-key.json"):
            cred = credentials.Certificate("firebase-key.json")
        else:
            env_key = os.environ.get("FIREBASE_KEY")
            if env_key:
                cred = credentials.Certificate(json.loads(env_key))
            else:
                raise Exception("Firebase Password missing hai.")
        
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://myntrabot-f4498-default-rtdb.firebaseio.com/'
        })
        print("🔥 Firebase 100% Connected!")
except Exception as e:
    print(f"❌ FIREBASE ERROR: {e}")

try:
    users_ref = db.reference('users')
    free_codes_ref = db.reference('free_codes')
    paid_codes_ref = db.reference('paid_codes')
    store_ref = db.reference('store_config')
    FIREBASE_WORKING = True
except:
    FIREBASE_WORKING = False

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
CHANNELS = ["@Sumanearningtrickk", "@PaisaBachaoDealssss", "@EarnBazaarrr"]
CHANNEL_LINKS = ["https://t.me/Sumanearningtrickk", "https://t.me/PaisaBachaoDealssss", "https://t.me/EarnBazaarrr"]

# AAPKA RENDER URL (Dhyan se check karna yahi hai na)
RENDER_URL = "https://just5.onrender.com"

# ================= LOGIC =================
async def is_joined(bot, user_id):
    # TEMPORARY BYPASS: Abhi ke liye ye channel check bypass kar dega taaki aap bot test kar sako
    return True

def main_menu():
    return ReplyKeyboardMarkup([["🛒 Buy Code"], ["💰 Balance", "👥 Refer Earn"], ["🎁 Bonus", "💸 Free Withdraw"], ["🆘 Support"]], resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not FIREBASE_WORKING:
        await update.message.reply_text("⚠️ **System Error:** Firebase connect nahi hua hai.")
        return
        
    uid = str(update.effective_user.id)
    first_name = update.effective_user.first_name or "New User"
    user = users_ref.child(uid).get()
    
    if not user:
        users_ref.child(uid).set({"balance": 0, "refs": [], "referred_by": "None", "state": "NORMAL", "name": first_name})
        if context.args:
            ref_id = str(context.args[0])
            referrer = users_ref.child(ref_id).get()
            if referrer and ref_id != uid and referrer.get("referred_by") != uid:
                users_ref.child(uid).update({"referred_by": ref_id})
                new_bal = referrer.get("balance", 0) + REFER_REWARD
                refs_list = referrer.get("refs") or []
                if uid not in refs_list:
                    refs_list.append(uid)
                    users_ref.child(ref_id).update({"balance": new_bal, "refs": refs_list})
                    try:
                        await context.bot.send_message(chat_id=int(ref_id), text=f"🔔 **Naya Refer!**\n*{first_name}* ne aapke link se join kiya. Aapko **+{REFER_REWARD} coin** mil gaya!", parse_mode="Markdown")
                    except: pass

    # Channel check bypassed hai, isliye direct menu khulega
    await update.message.reply_text(f"🎉 **Welcome {first_name}!**", reply_markup=main_menu(), parse_mode="Markdown")

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not FIREBASE_WORKING: return
    q = update.callback_query
    await q.answer()
    data = q.data
    uid = str(q.from_user.id)
            
    if data.startswith("qty_"):
        qty = int(data.split("_")[1])
        config = store_ref.get() or {"price": 80}
        total = config["price"] * qty
        users_ref.child(uid).update({"state": f"PAYING_{qty}_{total}"})
        msg = (f"🧾 **Order Summary**\n\n📦 Product: Myntra 50% Off\n🔢 Quantity: {qty}\n💰 **Total: ₹{total}**\n\n"
               f"🏦 **Payment Details:**\n👤 Name: `{PAYEE_NAME}`\n🔗 UPI ID: `{UPI_ID}` (Tap to copy)\n\n"
               f"⚠️ *Payment ke baad '✅ I Paid' dabayein.*")
        btn = [[InlineKeyboardButton("✅ I Paid", callback_data="ipaid")]]
        await q.message.delete()
        try: 
            await context.bot.send_photo(chat_id=int(uid), photo=QR_IMAGE_URL, caption=msg, reply_markup=InlineKeyboardMarkup(btn), parse_mode="Markdown")
        except: 
            await context.bot.send_message(chat_id=int(uid), text=f"[📷 QR Code]({QR_IMAGE_URL})\n\n{msg}", reply_markup=InlineKeyboardMarkup(btn), parse_mode="Markdown")

    elif data == "ipaid":
        user = users_ref.child(uid).get()
        state = user.get("state", "") if user else ""
        if state.startswith("PAYING_"):
            users_ref.child(uid).update({"state": state.replace("PAYING_", "WAIT_UTR_")})
            await q.message.reply_text("📝 **Apna 12-digit UTR / Transaction ID bhejein:**")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not FIREBASE_WORKING: return
    text = update.message.text
    uid = str(update.effective_user.id)
    first_name = update.effective_user.first_name or "User"
    
    user = users_ref.child(uid).get()
    if not user: 
        users_ref.child(uid).set({"balance": 0, "refs": [], "state": "NORMAL", "name": first_name})
        user = users_ref.child(uid).get()

    state = user.get("state", "NORMAL")

    if state.startswith("WAIT_UTR_"):
        _, qty, total = state.split("_")
        admin_msg = (f"🚨 **NEW PAYMENT UTR** 🚨\n\n👤 User: {first_name} (`{uid}`)\n📦 Item: Myntra 50% Off\n🔢 Qty: {qty}\n💰 Amount: ₹{total}\n🧾 **UTR:** `{text}`\n\n"
                     f"✅ `/approve {uid} {qty}`\n❌ `/reject {uid}`")
        try: await context.bot.send_message(chat_id=ADMIN_ID, text=admin_msg, parse_mode="Markdown")
        except: pass
        users_ref.child(uid).update({"state": "NORMAL"})
        await update.message.reply_text("⏳ **Review mein hai!** Payment verify hone ke baad code mil jayega.")
        return

    if text == "🛒 Buy Code":
        config = store_ref.get() or {"price": 80}
        btn = [[InlineKeyboardButton("1", callback_data="qty_1"), InlineKeyboardButton("2", callback_data="qty_2")],
               [InlineKeyboardButton("3", callback_data="qty_3"), InlineKeyboardButton("5", callback_data="qty_5")]]
        await update.message.reply_text(f"🛒 **Myntra 50% off Code**\nPrice: ₹{config['price']}/code\n\n**Select Quantity:**", reply_markup=InlineKeyboardMarkup(btn), parse_mode="Markdown")

    elif text == "💰 Balance":
        await update.message.reply_text(f"💰 **Balance:** {user.get('balance', 0)} coins")
        
    elif text == "👥 Refer Earn":
        bot_info = await context.bot.get_me()
        link = f"https://t.me/{bot_info.username}?start={uid}"
        await update.message.reply_text(f"👥 **Refer & Earn**\n\n🔥 1 Refer = 1 Coin\n🎁 {WITHDRAW_COST} Refer = 1 Free Code\n\n🔗 Link: `{link}`", parse_mode="Markdown")
        
    elif text == "🎁 Bonus":
        btn = InlineKeyboardMarkup([[InlineKeyboardButton("🎁 Claim Bonus", url=AD_LINK)]])
        await update.message.reply_text("Bonus ke liye ad dekhein:", reply_markup=btn)
        
    elif text == "💸 Free Withdraw":
        stock = free_codes_ref.get() or []
        if user.get("balance", 0) < WITHDRAW_COST:
            await update.message.reply_text(f"❌ {WITHDRAW_COST} coins chahiye!")
            return
        if not stock:
            await update.message.reply_text("❌ Stock khali hai!")
            return

        my_code = stock.pop(0)
        users_ref.child(uid).update({"balance": user["balance"] - WITHDRAW_COST})
        free_codes_ref.set(stock)
        btn = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Verify Code", url=AD_LINK)]])
        await update.message.reply_text(f"✅ **Withdraw Success!**\n\n🎁 **Code:** `{my_code}`\n\n⚠️ {WITHDRAW_COST} Coins cut.", reply_markup=btn, parse_mode="Markdown")
            
    elif text == "🆘 Support":
        await update.message.reply_text(f"📞 Contact: {SUPPORT}")

# ================= ADMIN COMMANDS =================
async def addfree(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID or not FIREBASE_WORKING: return
    new_c = " ".join(context.args)
    if new_c:
        s = free_codes_ref.get() or []
        s.append(new_c)
        free_codes_ref.set(s)
        await update.message.reply_text(f"✅ Free Stock Added! Total: {len(s)}")

async def addpaid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID or not FIREBASE_WORKING: return
    new_c = " ".join(context.args)
    if new_c:
        s = paid_codes_ref.get() or []
        s.append(new_c)
        paid_codes_ref.set(s)
        await update.message.reply_text(f"✅ Store Stock Added! Total: {len(s)}")

async def setprice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID or not FIREBASE_WORKING: return
    try:
        store_ref.set({"price": int(context.args[0])})
        await update.message.reply_text(f"✅ Price updated to ₹{context.args[0]}")
    except:
        await update.message.reply_text("❌ Use format: /setprice 60")

async def stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID or not FIREBASE_WORKING: return
    await update.message.reply_text(f"📊 **Stock Report**\n🎁 Free: {len(free_codes_ref.get() or [])}\n🛒 Paid: {len(paid_codes_ref.get() or [])}")

async def approve_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID or not FIREBASE_WORKING: return
    try:
        target_uid, qty = context.args[0], int(context.args[1])
        paid_stock = paid_codes_ref.get() or []
        if len(paid_stock) < qty:
            await update.message.reply_text(f"❌ Stock kam hai! Sirf {len(paid_stock)} bache hain.")
            return
            
        codes_to_give = [paid_stock.pop(0) for _ in range(qty)]
        paid_codes_ref.set(paid_stock)
        
        await context.bot.send_message(chat_id=int(target_uid), text=f"✅ **Payment Approved!**\nCodes:\n" + "\n".join([f"`{c}`" for c in codes_to_give]), parse_mode="Markdown")
        await update.message.reply_text(f"✅ Approved! Sent {qty} codes. Remaining: {len(paid_stock)}")
    except: await update.message.reply_text("❌ Format Error. Use: /approve <USER_ID> <QTY>")

async def reject_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID or not FIREBASE_WORKING: return
    try:
        await context.bot.send_message(chat_id=int(context.args[0]), text="❌ **Payment Rejected**\nWe could not verify your UTR.")
        await update.message.reply_text("🚫 Order Rejected.")
    except: pass

def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("addfree", addfree))
    application.add_handler(CommandHandler("addpaid", addpaid))
    application.add_handler(CommandHandler("setprice", setprice))
    application.add_handler(CommandHandler("stock", stock))
    application.add_handler(CommandHandler("approve", approve_order))
    application.add_handler(CommandHandler("reject", reject_order))
    application.add_handler(CallbackQueryHandler(callback_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    print("🚀 Webhook Starting...")
    PORT = int(os.environ.get("PORT", "10000"))
    
    application.run_webhook(
        listen="0.0.0.0",
        port=PORT,
        webhook_url=RENDER_URL,
        drop_pending_updates=True
    )

if __name__ == '__main__': 
    main()

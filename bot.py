import os
import asyncio
import logging
import firebase_admin
from firebase_admin import credentials, db
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

# ================= ERROR TRACKER =================
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    print(f"❌❌❌ BOT ERROR: {context.error}")

# ================= FIREBASE SETUP =================
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase-key.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://myntrabot-f4498-default-rtdb.firebaseio.com/'
    })

users_ref = db.reference('users')
free_codes_ref = db.reference('free_codes')
paid_codes_ref = db.reference('paid_codes')
store_ref = db.reference('store_config')

# ================= SERVER =================
app = Flask('')
@app.route('/')
def home(): return "Bot is Live (FIREBASE CONNECTED)!"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
def keep_alive(): Thread(target=run).start()

# ================= CONFIG =================
BOT_TOKEN = "8653750221:AAHx4A_npTXnorIqHHP6tCKGgOVwRyQ9QZw"
ADMIN_ID = 7132741918
SUPPORT = "@myntracodes"
AD_LINK = "https://omg10.com/4/10903029"

# PAYMENT DETAILS
UPI_ID = "paytmqr1qqff9il6x@paytm"
PAYEE_NAME = "Suman Chowdhury"
QR_IMAGE_URL = "https://i.postimg.cc/VNxwYmcZ/Paytm-QRcode-1758815347919.png"

# REFERRAL RULES
WITHDRAW_COST = 8
REFER_REWARD = 1

# CHANNELS
CHANNELS = ["@Sumanearningtrickk", "@PaisaBachaoDealssss", "@EarnBazaarrr"]
CHANNEL_LINKS = ["https://t.me/Sumanearningtrickk", "https://t.me/PaisaBachaoDealssss", "https://t.me/EarnBazaarrr"]

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
    kb = [
        ["🛒 Buy Code"],
        ["💰 Balance", "👥 Refer Earn"], 
        ["🎁 Bonus", "💸 Free Withdraw"], 
        ["🆘 Support"]
    ]
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

def join_buttons():
    btn = [[InlineKeyboardButton(f"🔔 Join Channel {i+1}", url=l)] for i, l in enumerate(CHANNEL_LINKS)]
    btn.append([InlineKeyboardButton("✅ Verify Joined", callback_data="verify")])
    return InlineKeyboardMarkup(btn)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    uid = str(user_id)
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

    if not await is_joined(context.bot, user_id):
        await update.message.reply_text("🔒 **Access Restricted**\nJoin channels to use bot👇", reply_markup=join_buttons(), parse_mode="Markdown")
        return
    await update.message.reply_text(f"🎉 **Welcome {first_name}!**", reply_markup=main_menu(), parse_mode="Markdown")

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data
    uid = str(q.from_user.id)
    
    if data == "verify":
        if await is_joined(context.bot, q.from_user.id):
            await q.message.delete()
            await context.bot.send_message(chat_id=q.from_user.id, text="✅ **Verification Successful!**", reply_markup=main_menu(), parse_mode="Markdown")
        else:
            await q.message.reply_text("❌ Sabhi channels join karke Verify dabayein.")
            
    # BUY FLOW - STEP 1 (Show QR)
    elif data.startswith("qty_"):
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
            await context.bot.send_message(chat_id=int(uid), text=f"[📷 Click Here to View QR]({QR_IMAGE_URL})\n\n{msg}", reply_markup=InlineKeyboardMarkup(btn), parse_mode="Markdown", disable_web_page_preview=False)

    elif data == "ipaid":
        user = users_ref.child(uid).get()
        state = user.get("state", "") if user else ""
        if state.startswith("PAYING_"):
            users_ref.child(uid).update({"state": state.replace("PAYING_", "WAIT_UTR_")})
            await q.message.reply_text("📝 **Apna 12-digit UTR / Transaction ID bhejein:**")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    uid = str(update.effective_user.id)
    first_name = update.effective_user.first_name or "User"
    
    user = users_ref.child(uid).get()
    if not user: 
        users_ref.child(uid).set({"balance": 0, "refs": [], "state": "NORMAL", "name": first_name})
        user = users_ref.child(uid).get()

    state = user.get("state", "NORMAL")

    # --- UTR SUBMIT TO ADMIN ---
    if state.startswith("WAIT_UTR_"):
        _, qty, total = state.split("_")
        
        admin_msg = (f"🚨 **NEW PAYMENT UTR** 🚨\n\n👤 User: {first_name} (`{uid}`)\n📦 Item: Myntra 50% Off\n🔢 Qty: {qty}\n💰 Amount: ₹{total}\n🧾 **UTR:** `{text}`\n\n"
                     f"✅ To Approve send:\n`/approve {uid} {qty}`\n\n"
                     f"❌ To Reject send:\n`/reject {uid}`")
        try:
            await context.bot.send_message(chat_id=ADMIN_ID, text=admin_msg, parse_mode="Markdown")
        except: pass
        users_ref.child(uid).update({"state": "NORMAL"})
        await update.message.reply_text("⏳ **Review mein hai!** Payment verify hone ke baad aapko code bhej diya jayega.")
        return

    if not await is_joined(context.bot, update.effective_user.id):
        await update.message.reply_text("🔒 Join channels👇", reply_markup=join_buttons())
        return

    # --- STORE MENU ---
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
    if update.effective_user.id != ADMIN_ID: return
    new_c = " ".join(context.args)
    if new_c:
        s = free_codes_ref.get() or []
        s.append(new_c)
        free_codes_ref.set(s)
        await update.message.reply_text(f"✅ Added to Free Stock! Total: {len(s)}")

async def addpaid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    new_c = " ".join(context.args)
    if new_c:
        s = paid_codes_ref.get() or []
        s.append(new_c)
        paid_codes_ref.set(s)
        await update.message.reply_text(f"✅ Added to Store Stock! Total: {len(s)}")

async def setprice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        new_price = int(context.args[0])
        store_ref.set({"price": new_price})
        await update.message.reply_text(f"✅ Store Price updated to ₹{new_price}")
    except:
        await update.message.reply_text("❌ Error. Use format: /setprice 60")

async def stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    free_stock = len(free_codes_ref.get() or [])
    paid_stock = len(paid_codes_ref.get() or [])
    await update.message.reply_text(f"📊 **Stock Report**\n\n🎁 Free Codes: {free_stock}\n🛒 Paid Codes (Store): {paid_stock}", parse_mode="Markdown")

async def approve_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        target_uid = context.args[0]
        qty = int(context.args[1])
        
        paid_stock = paid_codes_ref.get() or []
        if len(paid_stock) < qty:
            await update.message.reply_text(f"❌ Stock kam hai! Aapke paas sirf {len(paid_stock)} paid code bache hain.")
            return
            
        codes_to_give = []
        for _ in range(qty):
            codes_to_give.append(paid_stock.pop(0))
        paid_codes_ref.set(paid_stock)
        
        code_text = "\n".join([f"`{c}`" for c in codes_to_give])
        
        await context.bot.send_message(chat_id=int(target_uid), text=f"✅ **Payment Approved!**\n\nHere are your codes:\n{code_text}\n\nThank you for purchasing!", parse_mode="Markdown")
        await update.message.reply_text(f"✅ Approved! Sent {qty} codes to {target_uid}. Remaining paid stock: {len(paid_stock)}")
    except Exception as e: 
        await update.message.reply_text("❌ Format Error. Use: /approve <USER_ID> <QTY>")

async def reject_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        await context.bot.send_message(chat_id=int(context.args[0]), text="❌ **Payment Rejected**\n\nWe could not verify your UTR. Please contact support.")
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
    
    application.add_error_handler(error_handler)
    
    keep_alive()
    print("🤖 Bot is starting up with Firebase...")
    
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__': 
    main()

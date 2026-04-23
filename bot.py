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
def home(): return "Bot is Online and Stable!"
def run(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
def keep_alive(): Thread(target=run).start()

# ================= CONFIGURATION =================
BOT_TOKEN = "8653750221:AAHx4A_npTXnorIqHHP6tCKGgOVwRyQ9QZw"
ADMIN_ID = 7132741918
SUPPORT = "@myntracodes"
AD_LINK = "https://omg10.com/4/10903029"
UPI_ID = "paytmqr1qqff9il6x@paytm"
PAYEE_NAME = "Suman Chowdhury"
QR_IMAGE_URL = "https://i.postimg.cc/VNxwYmcZ/Paytm-QRcode-1758815347919.png"

# Rules
WITHDRAW_COST = 8
REFER_REWARD = 1
CHANNELS = ["@Sumanearningtrickk", "@PaisaBachaoDealssss", "@EarnBazaarrr"]
CHANNEL_LINKS = ["https://t.me/Sumanearningtrickk", "https://t.me/PaisaBachaoDealssss", "https://t.me/EarnBazaarrr"]

# Files
DATA_FILE = "database.json"
PAID_STOCK_FILE = "paid_stock.txt"
FREE_STOCK_FILE = "free_stock.txt"

# ================= DATABASE HELPERS =================
def load_db():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f: return json.load(f)
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
        if context.args:
            db["users"][uid]["referred_by"] = str(context.args[0])
        save_db(db)

    if not await is_joined(context.bot, int(uid)):
        await update.message.reply_text("🔒 **Access Restricted!**\nSare channels join karo tabhi bot chalega.", reply_markup=join_buttons())
        return

    await update.message.reply_text(f"👋 **Welcome {update.effective_user.first_name}!**", reply_markup=main_menu())

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    text = update.message.text
    db = load_db()

    if not await is_joined(context.bot, int(uid)):
        await update.message.reply_text("🔒 Join channels first!", reply_markup=join_buttons())
        return

    user = db["users"].get(uid, {"balance": 0, "state": "NORMAL"})

    # Admin Broadcast
    if uid == str(ADMIN_ID) and text.startswith("/broadcast"):
        msg = text.replace("/broadcast", "").strip()
        count = 0
        for user_id in db["users"]:
            try:
                await context.bot.send_message(chat_id=int(user_id), text=f"📢 **Announcement:**\n\n{msg}")
                count += 1
            except: pass
        await update.message.reply_text(f"✅ Sent to {count} users.")
        return

    # Handle UTR
    if user["state"] == "WAIT_UTR":
        admin_msg = (f"🚨 **NEW PAYMENT**\n👤 User: `{uid}`\n🔢 UTR: `{text}`\n\n"
                     f"Approve: `/approve {uid} 1`\nReject: `/reject {uid}`")
        await context.bot.send_message(chat_id=ADMIN_ID, text=admin_msg)
        db["users"][uid]["state"] = "NORMAL"
        save_db(db)
        await update.message.reply_text("⏳ **Verify ho raha hai...**\nAdmin check karke code bhej raha hai, thoda wait karo.")
        return

    if text == "🛒 Buy Code":
        stock = len(get_stock(PAID_STOCK_FILE))
        msg = f"🛒 **Myntra 50% Off Code**\n\n🔥 Stock: {stock}\n💰 Price: ₹80\n\nKharidne ke liye niche click karein:"
        btn = [[InlineKeyboardButton("🛍️ Buy Now", callback_data="buy_confirm")]]
        await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(btn))

    elif text == "💰 Balance":
        await update.message.reply_text(f"💰 **Aapka Balance:** {user['balance']} Coins")

    elif text == "👥 Refer Earn":
        bot_un = (await context.bot.get_me()).username
        msg = (f"👥 **Refer & Earn**\n\n"
               f"🔥 1 Refer = {REFER_REWARD} Coin\n"
               f"🎁 8 Refer = 1 Myntra Code\n\n"
               f"🔗 Your Link: `https://t.me/{bot_un}?start={uid}`")
        await update.message.reply_text(msg, parse_mode="Markdown")

    elif text == "🎁 Bonus":
        btn = [[InlineKeyboardButton("🎁 Claim Bonus", url=AD_LINK)]]
        await update.message.reply_text("Ad dekho aur bonus pao:", reply_markup=InlineKeyboardMarkup(btn))

    elif text == "💸 Free Withdraw":
        stock = get_stock(FREE_STOCK_FILE)
        if user["balance"] < WITHDRAW_COST:
            await update.message.reply_text(f"❌ Minimum {WITHDRAW_COST} Refer chahiye!")
        elif not stock:
            await update.message.reply_text("❌ Free stock khali hai, wait karo!")
        else:
            code = stock.pop(0)
            db["users"][uid]["balance"] -= WITHDRAW_COST
            save_stock(FREE_STOCK_FILE, stock)
            save_db(db)
            await update.message.reply_text(f"✅ **Withdraw Success!**\n\nCode: `{code}`", parse_mode="Markdown")

    elif text == "🆘 Support":
        await update.message.reply_text(f"🆘 Support: {SUPPORT}")

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    uid = str(q.from_user.id)
    db = load_db()
    await q.answer()

    if q.data == "verify":
        if await is_joined(context.bot, int(uid)):
            # REFERRAL CREDIT ON JOIN
            referrer = db["users"][uid].get("referred_by")
            if referrer and not db["users"][uid].get("joined"):
                if referrer in db["users"]:
                    db["users"][referrer]["balance"] += REFER_REWARD
                    db["users"][uid]["joined"] = True
                    save_db(db)
                    try: await context.bot.send_message(chat_id=int(referrer), text="👥 **Refer Counted!** User ne channel join kar liya hai.")
                    except: pass
            
            await q.message.delete()
            await context.bot.send_message(chat_id=int(uid), text="✅ **Verified!** Ab aap bot use kar sakte hain.", reply_markup=main_menu())
        else:
            await q.message.reply_text("❌ Abhi bhi join nahi kiya!")

    elif q.data == "buy_confirm":
        msg = f"🧾 **Payment Details**\n\nUPI: `{UPI_ID}`\nName: {PAYEE_NAME}\n\nPay karke **I Paid** button dabayein."
        btn = [[InlineKeyboardButton("✅ I Paid", callback_data="ipaid")]]
        try: await context.bot.send_photo(chat_id=int(uid), photo=QR_IMAGE_URL, caption=msg, reply_markup=InlineKeyboardMarkup(btn), parse_mode="Markdown")
        except: await context.bot.send_message(chat_id=int(uid), text=msg, reply_markup=InlineKeyboardMarkup(btn), parse_mode="Markdown")

    elif q.data == "ipaid":
        db["users"][uid]["state"] = "WAIT_UTR"
        save_db(db)
        await context.bot.send_message(chat_id=int(uid), text="📝 **Ab apna 12-digit UTR ID bhejein:**")

# ================= ADMIN COMMANDS =================
async def addpaid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    codes = context.args
    if codes:
        cur = get_stock(PAID_STOCK_FILE)
        cur.extend(codes); save_stock(PAID_STOCK_FILE, cur)
        await update.message.reply_text(f"✅ {len(codes)} Paid stock added.")

async def addfree(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    codes = context.args
    if codes:
        cur = get_stock(FREE_STOCK_FILE)
        cur.extend(codes); save_stock(FREE_STOCK_FILE, cur)
        await update.message.reply_text(f"✅ {len(codes)} Free stock added.")

async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    try:
        user_id, qty = context.args[0], int(context.args[1])
        stock = get_stock(PAID_STOCK_FILE)
        if len(stock) >= qty:
            given = [stock.pop(0) for _ in range(qty)]
            save_stock(PAID_STOCK_FILE, stock)
            await context.bot.send_message(chat_id=int(user_id), text="✅ **Payment Approved!**\n\nCode: " + "\n".join([f"`{c}`" for c in given]), parse_mode="Markdown")
            await update.message.reply_text("Bhej diya!")
        else: await update.message.reply_text("Stock Low!")
    except: pass

async def stock_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    p = len(get_stock(PAID_STOCK_FILE))
    f = len(get_stock(FREE_STOCK_FILE))
    await update.message.reply_text(f"📊 **Current Stock:**\n🛒 Paid: {p}\n🎁 Free: {f}")

# ================= MAIN =================
def main():
    keep_alive()
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("addpaid", addpaid))
    application.add_handler(CommandHandler("addfree", addfree))
    application.add_handler(CommandHandler("approve", approve))
    application.add_handler(CommandHandler("stock", stock_check))
    application.add_handler(CallbackQueryHandler(callback_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__': main()
        

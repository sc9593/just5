import os
import json
import asyncio
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

# ================= FIREBASE INITIALIZATION =================
# Dhyan rahe: firebase-key.json GitHub par honi chahiye
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase-key.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://myntrabot-f4498-default-rtdb.firebaseio.com/'
    })

users_ref = db.reference('users')
codes_ref = db.reference('codes')

# ================= FAKE SERVER FOR RENDER =================
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

# ================= CONFIG =================
BOT_TOKEN = "8653750221:AAHc-BZI3lXNRyJ3xOa9SGuFOK_3uJcqPco"
ADMIN_ID = 7132741918
SUPPORT = "@BOYSPROOF"
AD_LINK = "https://omg10.com/4/10903029" 

# Aapka sahi channel list
CHANNELS = ["@Sumanearningtrickk", "@PaisaBachaoDealssss", "@EarnBazaarrr"]
CHANNEL_LINKS = [
    "https://t.me/Sumanearningtrickk",
    "https://t.me/PaisaBachaoDealssss",
    "https://t.me/EarnBazaarrr",
]

# ================= LOGIC =================
async def is_joined(bot, user_id):
    for ch in CHANNELS:
        try:
            m = await bot.get_chat_member(ch, user_id)
            if m.status not in ["member", "administrator", "creator"]:
                return False
        except:
            return False
    return True

def join_buttons():
    btn = [[InlineKeyboardButton(f"🔔 Join Channel {i+1}", url=l)] for i, l in enumerate(CHANNEL_LINKS)]
    btn.append([InlineKeyboardButton("✅ Verify Joined", callback_data="verify")])
    return InlineKeyboardMarkup(btn)

def main_menu():
    kb = [["💰 Balance", "👥 Refer Earn"], ["🎁 Bonus", "💸 Withdraw"], ["🆘 Support"]]
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    uid = str(user_id)
    
    await update.message.reply_text("⏳ Checking...", reply_markup=ReplyKeyboardRemove())

    if not await is_joined(context.bot, user_id):
        await update.message.reply_text("🔒 Access Restricted\n\nJoin all channels👇", reply_markup=join_buttons())
        return

    user_data = users_ref.child(uid).get()
    if not user_data:
        user_data = {"balance": 0, "refs": []}
        if context.args:
            ref_id = context.args[0]
            referrer = users_ref.child(ref_id).get()
            if referrer and ref_id != uid:
                # Use .get() with default to prevent errors
                old_bal = referrer.get("balance", 0)
                old_refs = referrer.get("refs", [])
                if uid not in old_refs:
                    old_refs.append(uid)
                    users_ref.child(ref_id).update({
                        "balance": old_bal + 1,
                        "refs": old_refs
                    })
        
        users_ref.child(uid).set(user_data)

    await update.message.reply_text(
        "🎉 Welcome to Myntra Free Code Bot\nInvite karo aur free code pao!", 
        reply_markup=main_menu()
    )

async def verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if await is_joined(context.bot, q.from_user.id):
        await q.message.reply_text("✅ Joined Successfully!", reply_markup=main_menu())
    else:
        await q.message.reply_text("❌ Join sab channels!", reply_markup=join_buttons())

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    uid = str(update.effective_user.id)
    user = users_ref.child(uid).get()
    
    if not user: user = {"balance": 0, "refs": []}

    if text == "💰 Balance":
        await update.message.reply_text(f"💰 Your Balance: {user.get('balance', 0)} coins")
        
    elif text == "👥 Refer Earn":
        link = f"https://t.me/{context.bot.username}?start={uid}"
        await update.message.reply_text(f"👥 Refer & Earn\n\n🔥 1 Refer = 1 Coin\n🎁 3 Refer = 1 Myntra Code\n\n🔗 Link: {link}")
        
    elif text == "🎁 Bonus":
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🎁 Claim Bonus (Watch Ad)", url=AD_LINK)]])
        await update.message.reply_text("🔥 **Daily Bonus!**\n\nWatch ad to get bonus.", reply_markup=keyboard, parse_mode="Markdown")
        
    elif text == "💸 Withdraw":
        stock = codes_ref.get()
        if user.get("balance", 0) < 3:
            await update.message.reply_text("❌ Minimum 3 coins required!")
            return
        if not stock:
            await update.message.reply_text("❌ Code limited over. Wait and withdrawal again after new stock.")
            return

        code_to_give = stock.pop(0)
        codes_ref.set(stock) 
        users_ref.child(uid).update({"balance": user["balance"] - 3})

        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Open Myntra Code", url=AD_LINK)]])
        await update.message.reply_text(
            f"💸 **Withdraw Success!**\n\n🎁 Your Code: `{code_to_give}`\n\nVerification ke liye button dabayein.",
            reply_markup=keyboard, parse_mode="Markdown"
        )
            
    elif text == "🆘 Support":
        await update.message.reply_text(f"📞 Support: {SUPPORT}")

# ================= ADMIN COMMANDS =================

async def addcode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    new_code = " ".join(context.args)
    if new_code:
        current_codes = codes_ref.get()
        if not current_codes: current_codes = []
        current_codes.append(new_code)
        codes_ref.set(current_codes)
        await update.message.reply_text(f"✅ Code added! Total stock: {len(current_codes)}")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    msg_text = " ".join(context.args)
    if not msg_text:
        await update.message.reply_text("Usage: /broadcast [Message]")
        return

    all_users = users_ref.get()
    if not all_users: return
    
    count = 0
    await update.message.reply_text(f"📢 Sending broadcast...")

    for user_id in all_users:
        try:
            await context.bot.send_message(chat_id=int(user_id), text=msg_text)
            count += 1
            await asyncio.sleep(0.05)
        except:
            continue
    
    await update.message.reply_text(f"✅ Sent to {count} users.")

# ================= RUN =================
def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("addcode", addcode))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(CallbackQueryHandler(verify, pattern="verify"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu))
    print("Bot is starting...")
    application.run_polling()

if __name__ == '__main__':
    keep_alive()
    main()

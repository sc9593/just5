import os
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
try:
    if not firebase_admin._apps:
        cred = credentials.Certificate("firebase-key.json")
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://myntrabot-f4498-default-rtdb.firebaseio.com/'
        })
    users_ref = db.reference('users')
    codes_ref = db.reference('codes')
    print("✅ Firebase Connected!")
except Exception as e:
    print(f"❌ Firebase Error: {e}")

# ================= RENDER SERVER =================
app = Flask('')
@app.route('/')
def home(): return "Bot is running!"

def run(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
def keep_alive(): Thread(target=run).start()

# ================= CONFIG =================
BOT_TOKEN = "8653750221:AAHc-BZI3lXNRyJ3xOa9SGuFOK_3uJcqPco"
ADMIN_ID = 7132741918
SUPPORT = "@BOYSPROOF"
AD_LINK = "https://omg10.com/4/10903029" 

CHANNELS = ["@Sumanearningtrickk", "@PaisaBachaoDealssss", "@EarnBazaarrr"]
CHANNEL_LINKS = [
    "https://t.me/Sumanearningtrickk",
    "https://t.me/PaisaBachaoDealssss",
    "https://t.me/EarnBazaarrr",
]

# ================= LOGIC =================
async def is_joined(bot, user_id):
    if user_id == ADMIN_ID: return True
    for ch in CHANNELS:
        try:
            m = await bot.get_chat_member(chat_id=ch, user_id=user_id)
            if m.status not in ["member", "administrator", "creator"]:
                return False
        except Exception as e:
            print(f"Error checking {ch}: {e}")
            continue # Agar error aaye toh skip karo taki bot stuck na ho
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
            if ref_id != uid:
                ref_data = users_ref.child(ref_id).get()
                if ref_data:
                    old_refs = ref_data.get("refs", [])
                    if uid not in old_refs:
                        old_refs.append(uid)
                        users_ref.child(ref_id).update({
                            "balance": ref_data.get("balance", 0) + 1,
                            "refs": old_refs
                        })
        users_ref.child(uid).set(user_data)

    await update.message.reply_text("🎉 Welcome to Myntra Free Code Bot\nInvite karo aur free code pao!", reply_markup=main_menu())

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
        await update.message.reply_text(f"💰 Balance: {user.get('balance', 0)} coins")
        
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

        code = stock.pop(0)
        codes_ref.set(stock)
        users_ref.child(uid).update({"balance": user["balance"] - 3})

        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Open Myntra Code", url=AD_LINK)]])
        await update.message.reply_text(f"💸 **Withdraw Success!**\n\n🎁 Your Code: `{code}`\n\n3 coins cut ho gaye hain.", reply_markup=keyboard, parse_mode="Markdown")
            
    elif text == "🆘 Support":
        await update.message.reply_text(f"📞 Support: {SUPPORT}")

# ================= ADMIN =================
async def addcode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    c = " ".join(context.args)
    if c:
        s = codes_ref.get() or []
        s.append(c)
        codes_ref.set(s)
        await update.message.reply_text(f"✅ Code added! Total: {len(s)}")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    txt = " ".join(context.args)
    if not txt: return
    all_u = users_ref.get() or {}
    await update.message.reply_text("📢 Sending...")
    count = 0
    for u in all_u:
        try:
            await context.bot.send_message(chat_id=int(u), text=txt)
            count += 1
            await asyncio.sleep(0.05)
        except: continue
    await update.message.reply_text(f"✅ Sent to {count} users.")

def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("addcode", addcode))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(CallbackQueryHandler(verify, pattern="verify"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu))
    keep_alive()
    application.run_polling()

if __name__ == '__main__':
    main()
                    

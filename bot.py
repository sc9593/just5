import os
import json
import asyncio
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

# ================= FAKE SERVER FOR RENDER =================
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

DATA_FILE = "users.json"
CODES_FILE = "codes.txt"

# ================= DATA HELPERS =================
def load_users():
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        return {}
    except: return {}

def save_users(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

def load_codes():
    try:
        if os.path.exists(CODES_FILE):
            with open(CODES_FILE, "r") as f:
                return [c.strip() for c in f.readlines() if c.strip()]
        return []
    except: return []

def save_codes(c):
    with open(CODES_FILE, "w") as f:
        f.write("\n".join(c))

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
            continue # Agar error aaye toh skip karo
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
    
    # "Checking..." hata kar seedha check logic
    if not await is_joined(context.bot, user_id):
        await update.message.reply_text("🔒 **Access Restricted**\n\nBot use karne ke liye hamare channels join karein👇", reply_markup=join_buttons(), parse_mode="Markdown")
        return

    users = load_users()
    if uid not in users:
        users[uid] = {"balance": 0, "refs": []}
        if context.args:
            ref_id = context.args[0]
            if ref_id != uid and ref_id in users:
                if uid not in users[ref_id].get("refs", []):
                    users[ref_id]["balance"] += 1
                    users[ref_id]["refs"].append(uid)
        save_users(users)

    await update.message.reply_text("🎉 **Welcome to Myntra Free Code Bot**\nInvite karo aur free code pao!", reply_markup=main_menu(), parse_mode="Markdown")

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
    users = load_users()
    if uid not in users: users[uid] = {"balance": 0, "refs": []}

    if text == "💰 Balance":
        await update.message.reply_text(f"💰 Balance: {users[uid]['balance']} coins")
        
    elif text == "👥 Refer Earn":
        link = f"https://t.me/{context.bot.username}?start={uid}"
        await update.message.reply_text(f"👥 **Refer & Earn**\n\n🔥 1 Refer = 1 Coin\n🎁 3 Refer = 1 Myntra Code\n\n🔗 Link: {link}", parse_mode="Markdown")
        
    elif text == "🎁 Bonus":
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🎁 Claim Bonus (Watch Ad)", url=AD_LINK)]])
        await update.message.reply_text("🔥 **Daily Bonus!**\n\nWatch ad to get bonus.", reply_markup=keyboard, parse_mode="Markdown")
        
    elif text == "💸 Withdraw":
        codes = load_codes()
        if users[uid]["balance"] < 3:
            await update.message.reply_text("❌ Minimum 3 coins required!")
            return
        if not codes:
            await update.message.reply_text("❌ Code limited over. Wait and withdrawal again after new stock.")
            return

        code = codes.pop(0)
        users[uid]["balance"] -= 3
        save_codes(codes)
        save_users(users)

        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Open Myntra Code", url=AD_LINK)]])
        await update.message.reply_text(f"💸 **Withdraw Success!**\n\n🎁 Your Code: `{code}`\n\nVerification ke liye button dabayein.", reply_markup=keyboard, parse_mode="Markdown")
            
    elif text == "🆘 Support":
        await update.message.reply_text(f"📞 Support: {SUPPORT}")

# ================= ADMIN COMMANDS =================
async def addcode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    c = " ".join(context.args)
    if c:
        s = load_codes()
        s.append(c)
        save_codes(s)
        await update.message.reply_text(f"✅ Code added! Total: {len(s)}")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    txt = " ".join(context.args)
    if not txt: return
    u_list = load_users()
    await update.message.reply_text(f"📢 Sending to {len(u_list)} users...")
    count = 0
    for u in u_list:
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
    

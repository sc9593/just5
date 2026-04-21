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

# ================= SERVER FOR RENDER =================
app = Flask('')
@app.route('/')
def home(): return "Bot is Live!"

def run(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
def keep_alive(): Thread(target=run).start()

# ================= CONFIGURATION =================
BOT_TOKEN = "8653750221:AAHc-BZI3lXNRyJ3xOa9SGuFOK_3uJcqPco"
ADMIN_ID = 7132741918
SUPPORT = "@BOYSPROOF"
AD_LINK = "https://omg10.com/4/10903029" 

CHANNELS = ["@Sumanearningtrickk", "@PaisaBachaoDealssss", "@EarnBazaarrr"]
CHANNEL_LINKS = [
    "https://t.me/Sumanearningtrickk",
    "https://t.me/PaisaBachaoDealssss",
    "https://t.me/EarnBazaarrr"
]

DATA_FILE = "users.json"
CODES_FILE = "codes.txt"

# ================= DATA HELPERS =================
def load_users():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except: return {}
    return {}

def save_users(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

def load_codes():
    if os.path.exists(CODES_FILE):
        with open(CODES_FILE, "r") as f:
            return [c.strip() for c in f.readlines() if c.strip()]
    return []

def save_codes(c_list):
    with open(CODES_FILE, "w") as f:
        f.write("\n".join(c_list))

# ================= LOGIC =================
async def is_joined(bot, user_id):
    if user_id == ADMIN_ID: return True
    for ch in CHANNELS:
        try:
            m = await bot.get_chat_member(chat_id=ch, user_id=user_id)
            if m.status not in ["member", "administrator", "creator"]:
                return False
        except: continue
    return True

def main_menu():
    kb = [["💰 Balance", "👥 Refer Earn"], ["🎁 Bonus", "💸 Withdraw"], ["🆘 Support"]]
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    uid = str(user_id)
    
    # Channel Join Check
    if not await is_joined(context.bot, user_id):
        btn = [[InlineKeyboardButton(f"🔔 Join Channel {i+1}", url=l)] for i, l in enumerate(CHANNEL_LINKS)]
        btn.append([InlineKeyboardButton("✅ Verify Joined", callback_data="verify")])
        await update.message.reply_text("🔒 **Access Restricted**\n\nBot use karne ke liye join karein👇", 
                                       reply_markup=InlineKeyboardMarkup(btn), parse_mode="Markdown")
        return

    users = load_users()
    if uid not in users:
        users[uid] = {"balance": 0, "refs": []}
        # Refer Logic
        if context.args:
            ref_id = context.args[0]
            if ref_id in users and ref_id != uid:
                if uid not in users[ref_id].get("refs", []):
                    users[ref_id]["balance"] += 1
                    users[ref_id]["refs"].append(uid)
                    try:
                        await context.bot.send_message(chat_id=int(ref_id), text="🔔 **Naya Refer!**\nApko 1 coin mil gaya hai.")
                    except: pass
        save_users(users)

    await update.message.reply_text("🎉 **Welcome to Myntra Free Code Bot**\nInvite karo aur free code pao!", 
                                   reply_markup=main_menu(), parse_mode="Markdown")

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    uid = str(update.effective_user.id)
    users = load_users()
    
    if uid not in users: users[uid] = {"balance": 0, "refs": []}

    if text == "💰 Balance":
        await update.message.reply_text(f"💰 **Your Balance:** {users[uid]['balance']} coins", parse_mode="Markdown")
        
    elif text == "👥 Refer Earn":
        bot_info = await context.bot.get_me()
        link = f"https://t.me/{bot_info.username}?start={uid}"
        await update.message.reply_text(f"👥 **Refer & Earn**\n\n🔥 1 Refer = 1 Coin\n🎁 3 Refer = 1 Myntra Code\n\n🔗 Link: {link}", parse_mode="Markdown")
        
    elif text == "🎁 Bonus":
        btn = InlineKeyboardMarkup([[InlineKeyboardButton("🎁 Watch Ad to Claim", url=AD_LINK)]])
        await update.message.reply_text("🔥 **Daily Bonus!**\nNiche button par click karke ad dekhein:", reply_markup=btn, parse_mode="Markdown")
        
    elif text == "💸 Withdraw":
        codes = load_codes()
        # 1. Balance Check
        if users[uid]["balance"] < 3:
            await update.message.reply_text("❌ **Balance Low!**\nWithdraw ke liye 3 coins chahiye.", parse_mode="Markdown")
            return
        
        # 2. Stock Check
        if not codes:
            await update.message.reply_text("❌ **Code limited over.**\nWait and withdrawal again after new stock.", parse_mode="Markdown")
            return

        # 3. Success - Coin Cut and Code Give
        my_code = codes.pop(0)
        users[uid]["balance"] -= 3
        save_codes(codes)
        save_users(users)

        btn = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Verify & Open Code", url=AD_LINK)]])
        await update.message.reply_text(f"💸 **Withdraw Success!**\n\n🎁 Your Code: `{my_code}`\n\n3 Coins cut ho gaye hain.", 
                                       reply_markup=btn, parse_mode="Markdown")
            
    elif text == "🆘 Support":
        await update.message.reply_text(f"📞 **Support:** {SUPPORT}\nKoi problem ho toh contact karein.", parse_mode="Markdown")

# ================= ADMIN COMMANDS =================
async def addcode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    new_code = " ".join(context.args)
    if new_code:
        all_c = load_codes()
        all_c.append(new_code)
        save_codes(all_c)
        await update.message.reply_text(f"✅ Code added! Total stock: {len(all_c)}")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    msg = " ".join(context.args)
    if not msg: return
    u_data = load_users()
    await update.message.reply_text(f"📢 Sending to {len(u_data)} users...")
    count = 0
    for u in u_data:
        try:
            await context.bot.send_message(chat_id=int(u), text=msg)
            count += 1
            await asyncio.sleep(0.05)
        except: continue
    await update.message.reply_text(f"✅ Sent to {count} users.")

# ================= MAIN RUN =================
def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("addcode", addcode))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(CallbackQueryHandler(start, pattern="verify"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu))
    
    keep_alive()
    print("Bot is Starting...")
    application.run_polling()

if __name__ == '__main__':
    main()
                                                       

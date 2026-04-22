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

# ================= SERVER =================
app = Flask('')
@app.route('/')
def home(): return "Bot is Live!"

def run(): app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))
def keep_alive(): Thread(target=run).start()

# ================= CONFIG (STABLE COIN LOGIC) =================
BOT_TOKEN = "8653750221:AAHc-BZI3lXNRyJ3xOa9SGuFOK_3uJcqPco"
ADMIN_ID = 7132741918
SUPPORT = "@BOYSPROOF"
AD_LINK = "https://omg10.com/4/10903029" 

CHANNELS = ["@Sumanearningtrickk", "@PaisaBachaoDealssss", "@EarnBazaarrr"]
CHANNEL_LINKS = ["https://t.me/Sumanearningtrickk", "https://t.me/PaisaBachaoDealssss", "https://t.me/EarnBazaarrr"]

DATA_FILE = "users.json"
CODES_FILE = "codes.txt"

# Yahan se aap kabhi bhi coin rules change kar sakte hain
WITHDRAW_COST = 4
REFER_REWARD = 1

# ================= HELPERS =================
def load_users():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except: return {}
    return {}

def save_users(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

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
        except Exception:
            return False
    return True

def main_menu():
    kb = [["💰 Balance", "👥 Refer Earn"], ["🎁 Bonus", "💸 Withdraw"], ["🆘 Support"]]
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

def join_buttons():
    btn = [[InlineKeyboardButton(f"🔔 Join Channel {i+1}", url=l)] for i, l in enumerate(CHANNEL_LINKS)]
    btn.append([InlineKeyboardButton("✅ Verify Joined", callback_data="verify")])
    return InlineKeyboardMarkup(btn)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    uid = str(user_id)
    users = load_users()
    
    # === STRICT DUPLICATE REFERRAL CHECK ===
    if uid not in users:
        # Naya user create karte waqt 'referred_by' track karenge
        users[uid] = {"balance": 0, "refs": [], "referred_by": None}
        
        if context.args:
            ref_id = str(context.args[0])
            # Check: Referrer exist karta ho, khud ko refer na kar raha ho, aur ye user pehle refer na hua ho
            if ref_id in users and ref_id != uid and users[uid]["referred_by"] is None:
                
                users[uid]["referred_by"] = ref_id # Mark as permanently referred
                users[ref_id]["balance"] += REFER_REWARD
                
                if "refs" not in users[ref_id]: 
                    users[ref_id]["refs"] = []
                    
                if uid not in users[ref_id]["refs"]:
                    users[ref_id]["refs"].append(uid)
                    
                    try:
                        await context.bot.send_message(
                            chat_id=int(ref_id), 
                            text=f"🔔 **Naya Refer!**\nEk naye user ne aapke link se start kiya hai. Aapko **+{REFER_REWARD} coin** mil gaya!",
                            parse_mode="Markdown"
                        )
                    except Exception as e: 
                        print(f"Message send error: {e}")
        
        save_users(users)

    # === JOIN CHECK ===
    if not await is_joined(context.bot, user_id):
        await update.message.reply_text(
            "🔒 **Access Restricted**\n\nBot use karne ke liye saare channels join karein👇", 
            reply_markup=join_buttons(), 
            parse_mode="Markdown"
        )
        return

    await update.message.reply_text("🎉 **Welcome to Myntra Free Code Bot**", reply_markup=main_menu(), parse_mode="Markdown")

async def verify_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    user_id = q.from_user.id
    
    if await is_joined(context.bot, user_id):
        await q.message.delete()
        await context.bot.send_message(chat_id=user_id, text="✅ **Verification Successful!**\nAapka swagat hai.", reply_markup=main_menu(), parse_mode="Markdown")
    else:
        await q.message.reply_text("❌ Aapne abhi tak saare channels join nahi kiye hain. Join karke wapas Verify dabayein.")

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    uid = str(update.effective_user.id)
    users = load_users()
    
    # Safety check
    if uid not in users: 
        users[uid] = {"balance": 0, "refs": [], "referred_by": None}
        save_users(users)

    if not await is_joined(context.bot, update.effective_user.id):
        await update.message.reply_text("🔒 Access Restricted. Bot use karne ke liye saare channels join karein👇", reply_markup=join_buttons())
        return

    if text == "💰 Balance":
        await update.message.reply_text(f"💰 **Your Balance:** {users[uid].get('balance', 0)} coins", parse_mode="Markdown")
        
    elif text == "👥 Refer Earn":
        bot_info = await context.bot.get_me()
        link = f"https://t.me/{bot_info.username}?start={uid}"
        await update.message.reply_text(f"👥 **Refer & Earn**\n\n🔥 1 Refer = {REFER_REWARD} Coin\n🎁 {WITHDRAW_COST} Refer = 1 Myntra Code\n\n🔗 Your Link: `{link}`", parse_mode="Markdown")
        
    elif text == "🎁 Bonus":
        btn = InlineKeyboardMarkup([[InlineKeyboardButton("🎁 Claim Bonus", url=AD_LINK)]])
        await update.message.reply_text("Watch ad to get bonus:", reply_markup=btn)
        
    elif text == "💸 Withdraw":
        codes = load_codes()
        if users[uid].get("balance", 0) < WITHDRAW_COST:
            await update.message.reply_text(f"❌ **Balance Low!**\nMinimum {WITHDRAW_COST} coins chahiye withdrawal ke liye.", parse_mode="Markdown")
            return
        if not codes:
            await update.message.reply_text("❌ **Code limited over.**\nWait and withdrawal again after new stock.", parse_mode="Markdown")
            return

        # Coin Cut & Code Send
        my_code = codes.pop(0)
        users[uid]["balance"] -= WITHDRAW_COST
        save_codes(codes)
        save_users(users)
        
        btn = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Verify Code", url=AD_LINK)]])
        await update.message.reply_text(f"✅ **Withdraw Success!**\n\n🎁 Your Code: `{my_code}`\n\n⚠️ {WITHDRAW_COST} Coins cut ho gaye hain.", reply_markup=btn, parse_mode="Markdown")
            
    elif text == "🆘 Support":
        await update.message.reply_text(f"📞 Support: {SUPPORT}")

# ================= ADMIN =================
async def addcode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    new_c = " ".join(context.args)
    if new_c:
        c_list = load_codes()
        c_list.append(new_c)
        save_codes(c_list)
        await update.message.reply_text(f"✅ Code Added! Total Stock: {len(c_list)}")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    txt = " ".join(context.args)
    if not txt: return
    users = load_users()
    count = 0
    await update.message.reply_text("📢 Sending Broadcast...")
    for u in users:
        try: 
            await context.bot.send_message(chat_id=int(u), text=txt)
            count += 1
            await asyncio.sleep(0.05)
        except: continue
    await update.message.reply_text(f"✅ Broadcast Done! Sent to {count} users.")

def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("addcode", addcode))
    application.add_handler(CommandHandler("broadcast", broadcast))
    
    application.add_handler(CallbackQueryHandler(verify_button, pattern="verify"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu))
    
    keep_alive()
    application.run_polling()

if __name__ == '__main__':
    main()
        

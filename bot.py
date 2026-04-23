import os
import json
import asyncio
import logging
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

# ================= SERVER =================
app = Flask('')
@app.route('/')
def home(): return "Bot is Live (NO FIREBASE)!"
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

# STORE ITEMS
STORE_ITEMS = {
    "m50": {"name": "Myntra 50% off Code", "price": 80},
    "m100": {"name": "Myntra 100 Off on 649", "price": 20},
    "combo": {"name": "Myntra Combo(100+100)", "price": 55}
}

DATA_FILE = "users.json"
CODES_FILE = "codes.txt"

file_lock = asyncio.Lock()

# ================= DATA HELPERS =================
async def load_users():
    async with file_lock:
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r") as f: return json.load(f)
            except: return {}
        return {}

async def save_users(data):
    async with file_lock:
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
    
    users = await load_users()
    
    if uid not in users:
        users[uid] = {"balance": 0, "refs": [], "referred_by": "None", "state": "NORMAL", "name": first_name}
        
        if context.args:
            ref_id = str(context.args[0])
            if ref_id in users and ref_id != uid and users.get(uid, {}).get("referred_by") != ref_id:
                users[uid]["referred_by"] = ref_id
                users[ref_id]["balance"] += REFER_REWARD
                if "refs" not in users[ref_id]: users[ref_id]["refs"] = []
                if uid not in users[ref_id]["refs"]:
                    users[ref_id]["refs"].append(uid)
                    try:
                        await context.bot.send_message(
                            chat_id=int(ref_id), 
                            text=f"🔔 **Naya Refer!**\n*{first_name}* ne aapke link se join kiya. Aapko **+{REFER_REWARD} coin** mil gaya!",
                            parse_mode="Markdown"
                        )
                    except: pass
        await save_users(users)

    if not await is_joined(context.bot, user_id):
        await update.message.reply_text("🔒 **Access Restricted**\nJoin channels to use bot👇", reply_markup=join_buttons(), parse_mode="Markdown")
        return

    await update.message.reply_text(f"🎉 **Welcome {first_name}!**", reply_markup=main_menu(), parse_mode="Markdown")

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data
    uid = str(q.from_user.id)
    
    users = await load_users()
    
    if data == "verify":
        if await is_joined(context.bot, q.from_user.id):
            await q.message.delete()
            await context.bot.send_message(chat_id=q.from_user.id, text="✅ **Verification Successful!**", reply_markup=main_menu(), parse_mode="Markdown")
        else:
            await q.message.reply_text("❌ Sabhi channels join karke Verify dabayein.")
            
    elif data.startswith("buy_"):
        item_code = data.split("_")[1]
        item = STORE_ITEMS[item_code]
        btn = [[InlineKeyboardButton("1", callback_data=f"qty_{item_code}_1"), InlineKeyboardButton("2", callback_data=f"qty_{item_code}_2")],
               [InlineKeyboardButton("3", callback_data=f"qty_{item_code}_3"), InlineKeyboardButton("5", callback_data=f"qty_{item_code}_5")],
               [InlineKeyboardButton("⬅️ Back", callback_data="store_menu")]]
        await q.edit_message_text(f"🛒 **{item['name']}**\nPrice: ₹{item['price']}/code\n\n**Quantity select karein:**", reply_markup=InlineKeyboardMarkup(btn), parse_mode="Markdown")

    elif data.startswith("qty_"):
        _, item_code, qty = data.split("_")
        qty = int(qty)
        item = STORE_ITEMS[item_code]
        total = item['price'] * qty
        
        users[uid]["state"] = f"PAYING_{item_code}_{qty}_{total}"
        await save_users(users)
        
        msg = (f"🧾 **Order Summary**\n\n📦 Product: {item['name']}\n🔢 Quantity: {qty}\n💰 **Total: ₹{total}**\n\n"
               f"🏦 **Payment Details:**\n👤 Name: `{PAYEE_NAME}`\n🔗 UPI ID: `{UPI_ID}` (Tap to copy)\n\n"
               f"⚠️ *Payment ke baad '✅ I Paid' dabayein.*")
        
        btn = [[InlineKeyboardButton("✅ I Paid", callback_data="ipaid")]]
        await q.message.delete()
        await context.bot.send_photo(chat_id=int(uid), photo=QR_IMAGE_URL, caption=msg, reply_markup=InlineKeyboardMarkup(btn), parse_mode="Markdown")

    elif data == "ipaid":
        state = users.get(uid, {}).get("state", "")
        if state.startswith("PAYING_"):
            users[uid]["state"] = state.replace("PAYING_", "WAIT_UTR_")
            await save_users(users)
            await q.message.reply_text("📝 **Apna 12-digit UTR / Transaction ID bhejein:**")

    elif data == "store_menu":
        btn = [[InlineKeyboardButton(STORE_ITEMS[k]["name"] + f" | ₹{STORE_ITEMS[k]['price']}", callback_data=f"buy_{k}")] for k in STORE_ITEMS]
        await q.edit_message_text("🛍️ **Select Product:**", reply_markup=InlineKeyboardMarkup(btn), parse_mode="Markdown")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    uid = str(update.effective_user.id)
    first_name = update.effective_user.first_name or "User"
    
    users = await load_users()
    if uid not in users: 
        users[uid] = {"balance": 0, "refs": [], "state": "NORMAL", "name": first_name}
        await save_users(users)

    state = users[uid].get("state", "NORMAL")

    # UTR Submission to Admin
    if state.startswith("WAIT_UTR_"):
        _, item_code, qty, total = state.split("_")
        item_name = STORE_ITEMS[item_code]["name"]
        admin_msg = (f"🚨 **NEW PAYMENT**\n👤 User: {first_name} (`{uid}`)\n📦 Item: {item_name}\n💰 Amount: ₹{total}\n🧾 **UTR:** `{text}`\n\n"
                     f"✅ `/approve {uid} CODE` | ❌ `/reject {uid}`")
        try:
            await context.bot.send_message(chat_id=ADMIN_ID, text=admin_msg, parse_mode="Markdown")
        except: pass
        users[uid]["state"] = "NORMAL"
        await save_users(users)
        await update.message.reply_text("⏳ **Review mein hai!** 5-20 min mein code mil jayega.")
        return

    # Check join status for menu items
    if not await is_joined(context.bot, update.effective_user.id):
        await update.message.reply_text("🔒 Join channels👇", reply_markup=join_buttons())
        return

    if text == "🛒 Buy Code":
        btn = [[InlineKeyboardButton(STORE_ITEMS[k]["name"] + f" | ₹{STORE_ITEMS[k]['price']}", callback_data=f"buy_{k}")] for k in STORE_ITEMS]
        await update.message.reply_text("🛍️ **Store Catalog:**", reply_markup=InlineKeyboardMarkup(btn), parse_mode="Markdown")

    elif text == "💰 Balance":
        await update.message.reply_text(f"💰 **Balance:** {users[uid].get('balance', 0)} coins")
        
    elif text == "👥 Refer Earn":
        bot_info = await context.bot.get_me()
        link = f"https://t.me/{bot_info.username}?start={uid}"
        await update.message.reply_text(f"👥 **Refer & Earn**\n\n🔥 1 Refer = 1 Coin\n🎁 {WITHDRAW_COST} Refer = 1 Free Code\n\n🔗 Link: `{link}`", parse_mode="Markdown")
        
    elif text == "🎁 Bonus":
        btn = InlineKeyboardMarkup([[InlineKeyboardButton("🎁 Claim Bonus", url=AD_LINK)]])
        await update.message.reply_text("Bonus ke liye ad dekhein:", reply_markup=btn)
        
    elif text == "💸 Free Withdraw":
        stock = load_codes()
        if users[uid].get("balance", 0) < WITHDRAW_COST:
            await update.message.reply_text(f"❌ {WITHDRAW_COST} coins chahiye!")
            return
        if not stock:
            await update.message.reply_text("❌ Stock khali hai!")
            return

        my_code = stock.pop(0)
        users[uid]["balance"] -= WITHDRAW_COST
        save_codes(stock)
        await save_users(users)
        await update.message.reply_text(f"✅ **Code:** `{my_code}`", parse_mode="Markdown")
            
    elif text == "🆘 Support":
        await update.message.reply_text(f"📞 Contact: {SUPPORT}")

# ================= ADMIN =================
async def addfreecode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        new_c = " ".join(context.args)
        if new_c:
            s = load_codes()
            s.append(new_c)
            save_codes(s)
            await update.message.reply_text(f"✅ Added! Total Stock: {len(s)}")

async def approve_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        try:
            target_uid, code = context.args[0], " ".join(context.args[1:])
            await context.bot.send_message(chat_id=int(target_uid), text=f"✅ **Approve!** Code: `{code}`", parse_mode="Markdown")
            await update.message.reply_text("Done!")
        except: pass

async def reject_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        try:
            await context.bot.send_message(chat_id=int(context.args[0]), text="❌ **Rejected!** Payment verify nahi hui.")
            await update.message.reply_text("Done!")
        except: pass

def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("addcode", addfreecode))
    application.add_handler(CommandHandler("approve", approve_order))
    application.add_handler(CommandHandler("reject", reject_order))
    
    application.add_handler(CallbackQueryHandler(callback_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    application.add_error_handler(error_handler)
    
    keep_alive()
    print("🤖 Bot is starting up...")
    
    # Ye purane fass gaye messages ko udayega aur naye se start karega
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__': 
    main()

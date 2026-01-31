from telethon import TelegramClient, events, utils, types
from collections import Counter
import asyncio

# ---------------- SOZLAMALAR ----------------
# my.telegram.org saytidan olingan ma'lumotlarni shu yerga yozing
API_ID = 38877471             # O'zingizning API ID raqamingiz
API_HASH = 'a367ad3543c805cd03da594b2ebd779d' # O'zingizning API HASH kodingiz
BOT_TOKEN = '8279362143:AAHb3Kd9CURGcg0eRBVenVlqOUDXqaR3gYY' # Bot tokeni
SESSION_NAME = 'bot_session_new' # Sessiya nomi (yangi fayl yaratish uchun o'zgartirildi)

# Nechta eng aktiv odamni chaqirish kerak?
TOP_ACTIVE_COUNT = 500


# Tahlil qilish uchun oxirgi nechta xabar olinadi?
MESSAGE_LIMIT = 30000
# --------------------------------------------

# To'xtatish bayrog'i (har bir guruh uchun alohida)
stop_flags = {}

client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

@client.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    """
    /start buyrug'iga javob.
    """
    await event.reply("👋 **Assalomu alaykum!**\n\nMen guruhdagi eng aktiv a'zolarni aniqlab, ularni belgilab beruvchi botman.\n\n🚀 **Ishlatish uchun:**\n1. Meni guruhga qo'shing.\n2. Menga **Admin** huquqini bering (xabarlarni o'qish uchun).\n3. Guruhda `/aktiv` deb yozing.")

@client.on(events.ChatAction)
async def on_join(event):
    """
    Bot guruhga qo'shilganda avtomatik salom beradi.
    """
    if event.user_joined or event.user_added:
        me = await client.get_me()
        # Agar qo'shilganlar orasida botning o'zi bo'lsa
        if me.id in event.user_ids:
            await event.reply("👋 **Assalomu alaykum!**\n\nMeni guruhga qo'shganingiz uchun rahmat!\n\nMen guruhdagi eng aktiv a'zolarni aniqlab beraman.\nIshlatish uchun menga **Admin** huquqini bering va `/aktiv` deb yozing.")

@client.on(events.NewMessage(pattern=r'(?i)/cengel'))
async def cancel_handler(event):
    """
    Jarayonni to'xtatish (/cengel).
    """
    if not event.is_group:
        return

    # Admin ekanligini tekshirish
    perms = await client.get_permissions(event.chat_id, event.sender_id)
    if not perms.is_admin:
        await event.reply("⛔ Kechirasiz, bu buyruq faqat guruh adminlari uchun!")
        return

    # To'xtatish signalini berish
    stop_flags[event.chat_id] = True
    await event.reply("🛑 **Jarayon to'xtatilmoqda...**")

@client.on(events.NewMessage(pattern=r'(?i)/top'))
async def top_handler(event):
    """
    Guruhdagi eng ko'p yozgan 20 ta odamni ro'yxatini chiqarish (/top).
    """
    if not event.is_group:
        await event.reply("❌ Bu buyruq faqat guruhlarda ishlaydi!")
        return

    # Botning o'zi admin ekanligini tekshirish
    bot_perms = await client.get_permissions(event.chat_id, 'me')
    if not bot_perms.is_admin:
        await event.reply("⚠️ **Diqqat:** Bot guruhda **Admin** emas!\n\nStatistikani hisoblash uchun botga admin huquqini bering.")
        return

    status_msg = await event.reply(f"📊 **Top 20 statistika** hisoblanmoqda...\nOxirgi {MESSAGE_LIMIT} ta xabar tahlil qilinmoqda, iltimos kuting.")

    user_ids = []
    try:
        async for message in client.iter_messages(event.chat_id, limit=MESSAGE_LIMIT):
            if message.sender_id:
                user_ids.append(message.sender_id)
    except Exception as e:
        if "API access for bot users is restricted" in str(e):
            await status_msg.edit("⚠️ **Xatolik:** Bot oddiy guruhlarda tarixni o'qiy olmaydi. Iltimos, guruhni **Superguruh**ga aylantiring.")
        else:
            await status_msg.edit(f"⚠️ Xatolik: {str(e)}")
        return

    if not user_ids:
        await status_msg.edit("❌ **Xabarlar topilmadi.**\nBot guruh tarixini o'qiy olmadi yoki guruhda xabarlar yo'q.")
        return

    # Top 20 talikni aniqlash
    top_users = Counter(user_ids).most_common(20)

    text = "🏆 **Guruhdagi eng aktiv 20 ta a'zo:**\n\n"
    
    for i, (user_id, count) in enumerate(top_users, 1):
        try:
            user = await client.get_entity(user_id)
            name = utils.get_display_name(user).replace("_", "\\_").replace("*", "\\*").replace("`", "\\`")
            text += f"**{i}.** {name} — **{count}** ta xabar\n"
        except:
            text += f"**{i}.** Foydalanuvchi ({user_id}) — **{count}** ta xabar\n"
            
    await status_msg.edit(text)

@client.on(events.NewMessage(pattern=r'(?i)/statistika'))
async def stats_handler(event):
    """
    Guruh statistikasi: a'zolar soni va xabarlar soni (/statistika).
    """
    if not event.is_group:
        await event.reply("❌ Bu buyruq faqat guruhlarda ishlaydi!")
        return

    status_msg = await event.reply("📊 **Statistika hisoblanmoqda...**")

    try:
        # A'zolar va xabarlar sonini olish
        participants = await client.get_participants(event.chat_id, limit=0)
        
        msg_count = "Aniqlab bo'lmadi 🔒"
        try:
            history = await client.get_messages(event.chat_id, limit=0)
            msg_count = history.total
        except:
            pass

        await status_msg.edit(
            f"📊 **Guruh Statistikasi**\n\n"
            f"👥 **Jami a'zolar:** {participants.total}\n"
            f"✉️ **Jami xabarlar:** {msg_count}"
        )
    except Exception as e:
        await status_msg.edit(f"⚠️ Xatolik: {str(e)}")

@client.on(events.NewMessage(pattern=r'(?i)/aktiv'))
async def handler(event):
    """
    Guruhda /aktiv deb yozilganda ishlaydi.
    """
    # Faqat guruhlarda ishlashi uchun tekshiruv
    if not event.is_group:
        await event.reply("❌ Bu buyruq faqat guruhlarda ishlaydi!")
        return

    # Admin ekanligini tekshirish
    perms = await client.get_permissions(event.chat_id, event.sender_id)
    if not perms.is_admin:
        await event.reply("⛔ Kechirasiz, bu buyruq faqat guruh adminlari uchun!")
        return

    # Botning o'zi admin ekanligini tekshirish
    bot_perms = await client.get_permissions(event.chat_id, 'me')
    if not bot_perms.is_admin:
        await event.reply("⚠️ **Diqqat:** Bot guruhda **Admin** emas!\n\nXabarlarni o'qish va foydalanuvchilarni belgilash uchun botga admin huquqini bering.")
        return

    status_msg = await event.reply(f"🔍 Guruhdagi oxirgi {MESSAGE_LIMIT} ta xabar tahlil qilinmoqda... Iltimos kuting.")
    
    user_ids = []
    most_active = []
    
    # Guruh tarixini o'qish
    try:
        async for message in client.iter_messages(event.chat_id, limit=MESSAGE_LIMIT):
            if message.sender_id:
                user_ids.append(message.sender_id)
        
        # Agar tarix muvaffaqiyatli o'qilsa
        if user_ids:
            most_active = Counter(user_ids).most_common(TOP_ACTIVE_COUNT)
            
    except Exception as e:
        if "API access for bot users is restricted" in str(e):
            await status_msg.edit("⚠️ **Tarixni o'qib bo'lmadi (Oddiy guruh).**\n\nBot a'zolar ro'yxatidan foydalanib odamlarni belgilaydi.")
            await asyncio.sleep(2)
            # Fallback: A'zolarni olish
            participants = await client.get_participants(event.chat_id, limit=TOP_ACTIVE_COUNT)
            most_active = [(user.id, 0) for user in participants]
        else:
            await status_msg.edit(f"⚠️ **Xatolik yuz berdi!**\n\nTexnik xato: `{str(e)}`")
            return

    if not most_active:
        await status_msg.edit("❌ **Hech kim topilmadi.**\n\nBot guruh a'zolarini aniqlay olmadi.")
        return
    
    await status_msg.delete()
    await client.send_message(event.chat_id, f"📢 **Eng aktiv {len(most_active)} ta foydalanuvchi chaqirilmoqda:**")
    
    # Jarayon boshlanishidan oldin to'xtatish bayrog'ini o'chiramiz
    stop_flags[event.chat_id] = False
    
    # Ularni bittalab chaqirish (tag qilish)
    for user_id, count in most_active:
        # To'xtatish buyrug'i berilganligini tekshirish
        if stop_flags.get(event.chat_id, False):
            await client.send_message(event.chat_id, "🛑 **Jarayon admin tomonidan to'xtatildi.**")
            break
            
        try:
            # Foydalanuvchi ma'lumotlarini olish
            user = await client.get_entity(user_id)
            
            # Agar bot yoki o'chirilgan akkaunt bo'lsa, o'tkazib yuboramiz
            if hasattr(user, 'bot') and user.bot:
                continue
            if hasattr(user, 'deleted') and user.deleted:
                continue

            name = utils.get_display_name(user) or 'Foydalanuvchi'
            
            # Tag qilish (mention)
            mention_text = f"[{name}](tg://user?id={user_id})"
            
            if count > 0:
                msg_text = f"🏅 {mention_text}, siz guruhda juda aktivsiz!\n📊 Yozgan xabarlaringiz: {count} ta"
            else:
                msg_text = f"👋 {mention_text},."

            await client.send_message(
                event.chat_id, 
                msg_text,
                parse_mode='md',
                link_preview=False
            )
            
            # Spam bo'lmasligi uchun 2 soniya kutish
            await asyncio.sleep(2)
            
        except Exception as e:
            print(f"Foydalanuvchini utag qilishda xatolik: {e}")

print("Bot ishga tushdi. Guruhga kiring va /aktiv deb yozing.")

async def main():
    await client.start(bot_token=BOT_TOKEN)
    await client.run_until_disconnected()

if __name__ == '__main__':
    asyncio.run(main())

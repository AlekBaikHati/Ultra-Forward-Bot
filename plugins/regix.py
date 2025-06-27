# Jishu Developer 
# Don't Remove Credit 🥺
# Telegram Channel @Madflix_Bots
# Backup Channel @JishuBotz
# Developer @JishuDeveloper

import os
import sys 
import math
import time
import asyncio 
import logging
from .utils import STS
from database import db 
from .test import CLIENT , start_clone_bot
from config import Config, temp
from translation import Translation
from pyrogram import Client, filters 
from pyrogram.types import InputMediaPhoto, InputMediaVideo, InputMediaDocument, InputMediaAudio
from pyrogram.errors import FloodWait, MessageNotModified, RPCError
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, Message 

CLIENT = CLIENT()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
TEXT = Translation.TEXT

@Client.on_callback_query(filters.regex(r'^start_public'))
async def pub_(bot, message):
    user = message.from_user.id
    temp.CANCEL[user] = False
    frwd_id = message.data.split("_")[2]
    if temp.lock.get(user) and str(temp.lock.get(user))=="True":
        return await message.answer("Please Wait Until Previous Task Complete", show_alert=True)
    sts = STS(frwd_id)
    if not sts.verify():
        await message.answer("Your Are Clicking On My Old Button", show_alert=True)
        return await message.message.delete()
    i = sts.get(full=True)
    if i.TO in temp.IS_FRWD_CHAT:
        return await message.answer("In Target Chat A Task Is Progressing. Please Wait Until Task Complete", show_alert=True)
    m = await msg_edit(message.message, "Verifying Your Data's, Please Wait.")
    _bot, caption, forward_tag, data, protect, button = await sts.get_data(user)
    if not _bot:
        return await msg_edit(m, "You Didn't Added Any Bot. Please Add A Bot Using /settings !", wait=True)
    try:
        client = await start_clone_bot(CLIENT.client(_bot))
    except Exception as e:
        return await m.edit(e)
    await msg_edit(m, "Processing...")
    try:
        await client.get_messages(sts.get("FROM"), sts.get("limit"))
    except:
        await msg_edit(m, f"Source Chat May Be A Private Channel / Group. Use Userbot (User Must Be Member Over There) Or  If Make Your [Bot](t.me/{_bot['username']}) An Admin Over There", retry_btn(frwd_id), True)
        return await stop(client, user)
    try:
        k = await client.send_message(i.TO, "Testing")
        await k.delete()
    except:
        await msg_edit(m, f"Please Make Your [UserBot / Bot](t.me/{_bot['username']}) Admin In Target Channel With Full Permissions", retry_btn(frwd_id), True)
        return await stop(client, user)
    temp.forwardings += 1
    await db.add_frwd(user)
    await send(client, user, "🩷 Forwarding Started")
    sts.add(time=True)
    sleep = 1 if _bot['is_bot'] else 10
    await msg_edit(m, "Processing...") 
    temp.IS_FRWD_CHAT.append(i.TO)
    temp.lock[user] = locked = True
    if locked:
        try:
            MSG = []
            pling = 0
            if not hasattr(temp, "media_group_buffer"):
                temp.media_group_buffer = {}

            await edit(m, 'Progressing', 10, sts)
            print(f"Starting Forwarding Process... From :{sts.get('FROM')} To: {sts.get('TO')} Total: {sts.get('limit')} Skip: {sts.get('skip')})")
            async for message in client.iter_messages(
                chat_id=sts.get('FROM'), 
                limit=int(sts.get('limit')), 
                offset=int(sts.get('skip') or 0)
            ):
                if await is_cancelled(client, user, m, sts):
                    return
                if pling % 20 == 0: 
                    await edit(m, 'Progressing', 10, sts)
                pling += 1
                sts.add('fetched')
                if message == "DUPLICATE":
                    sts.add('duplicate')
                    continue 
                elif message == "FILTERED":
                    sts.add('filtered')
                    continue 
                if message.empty or message.service:
                    sts.add('deleted')
                    continue

                if forward_tag:
                    MSG.append(message.id)
                    notcompleted = len(MSG)
                    completed = sts.get('total') - sts.get('fetched')
                    if notcompleted >= 100 or completed <= 100:
                        await forward(client, MSG, m, sts, protect)
                        sts.add('total_files', notcompleted)
                        await asyncio.sleep(10)
                        MSG = []
                else:
                    group_id = message.media_group_id
                    if group_id:
                        buffer = temp.media_group_buffer.setdefault(group_id, [])
                        buffer.append(message)
                        if len(buffer) >= 10:  # asumsi batas maksimum album
                            await send_album(client, buffer, caption, button, sts, m)
                            del temp.media_group_buffer[group_id]
                    else:
                        new_caption = custom_caption(message, caption)
                        details = {
                            "msg_id": message.id,
                            "media": media(message),
                            "caption": new_caption,
                            "button": button,
                            "protect": protect
                        }
                        await copy(client, details, m, sts)
                        sts.add('total_files')
                        await asyncio.sleep(sleep)

            # flush album buffer if any left
            for group_id, group_msgs in temp.media_group_buffer.items():
                await send_album(client, group_msgs, caption, button, sts, m)
            temp.media_group_buffer.clear()

        except Exception as e:
            await msg_edit(m, f'<b>Error :</b>\n<code>{e}</code>', wait=True)
            temp.IS_FRWD_CHAT.remove(sts.TO)
            return await stop(client, user)
        temp.IS_FRWD_CHAT.remove(sts.TO)
        await send(client, user, "🎉 Forwarding Completed")
        await edit(m, 'Completed', "completed", sts) 
        await stop(client, user)

async def send_album(bot, messages, caption_template, button, sts, m):
    media_list = []
    for i, msg in enumerate(messages):
        file_id = media(msg)
        caption = custom_caption(msg, caption_template) if i == 0 else None
        media_type = msg.media.value.upper() if msg.media else None

        if not file_id or not media_type:
            continue

        try:
            if media_type == "PHOTO":
                media_obj = InputMediaPhoto(media=file_id, caption=caption, parse_mode="html")
            elif media_type == "VIDEO":
                media_obj = InputMediaVideo(media=file_id, caption=caption, parse_mode="html")
            elif media_type == "DOCUMENT":
                media_obj = InputMediaDocument(media=file_id, caption=caption, parse_mode="html")
            elif media_type == "AUDIO":
                media_obj = InputMediaAudio(media=file_id, caption=caption, parse_mode="html")
            else:
                continue
            media_list.append(media_obj)
        except Exception as e:
            print(f"Error building media object: {e}")
            continue

    if media_list:
        try:
            await bot.send_media_group(
                chat_id=sts.get("TO"),
                media=media_list,
                protect_content=getattr(messages[0], "protect_content", False)
            )
            sts.add("total_files", len(media_list))
        except FloodWait as e:
            await edit(m, "Progressing", e.value, sts)
            await asyncio.sleep(e.value)
            await send_album(bot, messages, caption_template, button, sts, m)
        except Exception as e:
            print(f"Error sending album: {e}")
            for msg in messages:
                details = {
                    "msg_id": msg.id,
                    "media": media(msg),
                    "caption": custom_caption(msg, caption_template),
                    "button": button,
                    "protect": getattr(msg, "protect_content", False)
                }
                await copy(bot, details, m, sts)

async def copy(bot, msg, m, sts):
    try:                                  
        if msg.get("media") and msg.get("caption"):
            await bot.send_cached_media(
                chat_id=sts.get('TO'),
                file_id=msg.get("media"),
                caption=msg.get("caption"),
                reply_markup=msg.get('button'),
                protect_content=msg.get("protect"))
        else:
            await bot.copy_message(
                chat_id=sts.get('TO'),
                from_chat_id=sts.get('FROM'),    
                caption=msg.get("caption"),
                message_id=msg.get("msg_id"),
                reply_markup=msg.get('button'),
                protect_content=msg.get("protect"))
    except FloodWait as e:
        await edit(m, 'Progressing', e.value, sts)
        await asyncio.sleep(e.value)
        await edit(m, 'Progressing', 10, sts)
        await copy(bot, msg, m, sts)
    except Exception as e:
        print(e)
        sts.add('deleted')

async def forward(bot, msg, m, sts, protect):
    try:                             
        await bot.forward_messages(
            chat_id=sts.get('TO'),
            from_chat_id=sts.get('FROM'), 
            protect_content=protect,
            message_ids=msg)
    except FloodWait as e:
        await edit(m, 'Progressing', e.value, sts)
        await asyncio.sleep(e.value)
        await edit(m, 'Progressing', 10, sts)
        await forward(bot, msg, m, sts, protect)
PROGRESS = """
📈 Percetage : {0} %

♻️ Fetched : {1}

🔥 Forwarded : {2}

🫠 Remaining : {3}

📊 Status : {4}

⏳️ ETA : {5}
"""

async def msg_edit(msg, text, button=None, wait=None):
    try:
        return await msg.edit(text, reply_markup=button)
    except MessageNotModified:
        pass 
    except FloodWait as e:
        if wait:
            await asyncio.sleep(e.value)
            return await msg_edit(msg, text, button, wait)

async def edit(msg, title, status, sts):
    i = sts.get(full=True)
    status_text = 'Forwarding' if status == 10 else f"Sleeping {status} s" if str(status).isnumeric() else status
    percentage = "{:.0f}".format(float(i.fetched) * 100 / float(i.total or 1))

    now = time.time()
    diff = int(now - i.start)
    speed = sts.divide(i.fetched, diff)
    elapsed_time = round(diff) * 1000
    time_to_completion = round(sts.divide(i.total - i.fetched, int(speed or 1))) * 1000
    estimated_total_time = elapsed_time + time_to_completion  
    progress = "▰{0}{1}".format(
        ''.join(["▰" for _ in range(math.floor(int(percentage) / 10))]),
        ''.join(["▱" for _ in range(10 - math.floor(int(percentage) / 10))])
    )
    button =  [[InlineKeyboardButton(title, f'fwrdstatus#{status_text}#{estimated_total_time}#{percentage}#{i.id}')]]
    eta = TimeFormatter(milliseconds=estimated_total_time)
    text = TEXT.format(i.fetched, i.total_files, i.duplicate, i.deleted, i.skip, status_text, percentage, eta, progress)

    if status_text in ["cancelled", "completed"]:
        button.append([
            InlineKeyboardButton('📢 Updates', url='https://t.me/Madflix_Bots'),
            InlineKeyboardButton('💬 Support', url='https://t.me/MadflixBots_Support')
        ])
    else:
        button.append([InlineKeyboardButton('✖️ Cancel ✖️', 'terminate_frwd')])
    await msg_edit(msg, text, InlineKeyboardMarkup(button))

async def is_cancelled(client, user, msg, sts):
    if temp.CANCEL.get(user) == True:
        temp.IS_FRWD_CHAT.remove(sts.TO)
        await edit(msg, "Cancelled", "completed", sts)
        await send(client, user, "❌ Forwarding Process Cancelled")
        await stop(client, user)
        return True 
    return False 

async def stop(client, user):
    try:
        await client.stop()
    except:
        pass 
    await db.rmve_frwd(user)
    temp.forwardings -= 1
    temp.lock[user] = False 

async def send(bot, user, text):
    try:
        await bot.send_message(user, text=text)
    except:
        pass 
def custom_caption(msg, caption):
    if msg.media:
        media = getattr(msg, msg.media.value, None)
        if media:
            file_name = getattr(media, 'file_name', '')
            file_size = getattr(media, 'file_size', '')
            fcaption = getattr(msg, 'caption', '')
            if fcaption:
                fcaption = fcaption.html
            if caption:
                return caption.format(filename=file_name, size=get_size(file_size), caption=fcaption)
            return fcaption
    return None

def get_size(size):
    try:
        size = float(size)
    except:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size >= 1024.0 and i < len(units) - 1:
        i += 1
        size /= 1024.0
    return "%.2f %s" % (size, units[i]) 

def media(msg):
    if msg.media:
        media_obj = getattr(msg, msg.media.value, None)
        if media_obj:
            return getattr(media_obj, 'file_id', None)
    return None 

def TimeFormatter(milliseconds: int) -> str:
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = ((str(days) + "d, ") if days else "") + \
        ((str(hours) + "h, ") if hours else "") + \
        ((str(minutes) + "m, ") if minutes else "") + \
        ((str(seconds) + "s, ") if seconds else "") + \
        ((str(milliseconds) + "ms, ") if milliseconds else "")
    return tmp[:-2]

def retry_btn(id):
    return InlineKeyboardMarkup([[InlineKeyboardButton('♻️ Retry ♻️', f"start_public_{id}")]])

@Client.on_callback_query(filters.regex(r'^terminate_frwd$'))
async def terminate_frwding(bot, m):
    user_id = m.from_user.id 
    temp.lock[user_id] = False
    temp.CANCEL[user_id] = True 
    await m.answer("Forwarding Cancelled !", show_alert=True)

@Client.on_callback_query(filters.regex(r'^fwrdstatus'))
async def status_msg(bot, msg):
    _, status, est_time, percentage, frwd_id = msg.data.split("#")
    sts = STS(frwd_id)
    if not sts.verify():
        fetched = forwarded = remaining = 0
    else:
        fetched = sts.get('fetched')
        forwarded = sts.get('total_files')
        remaining = fetched - forwarded
    est_time = TimeFormatter(milliseconds=int(est_time))
    return await msg.answer(PROGRESS.format(percentage, fetched, forwarded, remaining, status, est_time), show_alert=True)

@Client.on_callback_query(filters.regex(r'^close_btn$'))
async def close(bot, update):
    await update.answer()
    await update.message.delete()
    try:
        await update.message.reply_to_message.delete()
    except:
        pass

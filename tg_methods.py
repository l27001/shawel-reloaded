import builtins, os, telebot
import config
from methods import Methods
from telebot.types import InputMediaPhoto
builtins.Mysql = Methods.Mysql()
builtins.dir_path = os.path.dirname(os.path.realpath(__file__))
telebot.apihelper.ENABLE_MIDDLEWARE = True
builtins.bot = telebot.TeleBot(config.tg_info['access_token'])

def get_user(id_):
    user = Mysql.query("SELECT * FROM tg_users WHERE tgid = %s", id_)
    if(user is not None):
        return user
    else:
        Mysql.query("INSERT INTO tg_users (`tgid`) VALUES (%s)", id_)
        return Mysql.query("SELECT * FROM tg_users WHERE tgid = %s", id_)

def get_chat(id_):
    chat = Mysql.query("SELECT * FROM tg_chats WHERE id = %s", id_)
    if(chat is not None):
        return chat
    else:
        Mysql.query("INSERT INTO tg_chats (`id`) VALUES (%s)", id_)
        return Mysql.query("SELECT * FROM tg_chats WHERE id = %s", id_)

def toggle_subscribe(id_, sub):
    if(sub == 0):
        Mysql.query("UPDATE tg_users SET subscribe = 1 WHERE tgid = %s", id_)
        return 1
    else:
        Mysql.query("UPDATE tg_users SET subscribe = 0 WHERE tgid = %s", id_)
        return 0

def toggle_chat_subscribe(id_, sub):
    if(sub == 0):
        Mysql.query("UPDATE tg_chats SET subscribe = 1 WHERE id = %s", id_)
        return 1
    else:
        Mysql.query("UPDATE tg_chats SET subscribe = 0 WHERE id = %s", id_)
        return 0

def setting_get(*args, **kwargs):
    return Methods.setting_get(*args, **kwargs)

def setting_set(*args, **kwargs):
    return Methods.setting_set(*args, **kwargs)

def setting_del(*args, **kwargs):
    return Methods.setting_del(*args, **kwargs)

def log(prefix, text):
    Methods.log(prefix, text)

def send_to_users(prefix, dir, txt):
    files = []; to_send = []
    for file in sorted(os.listdir(dir)):
        files.append(open(dir+"/"+file, "rb"))
    for f in files:
        to_send.append(InputMediaPhoto(f))
    file_ids = []
    for n in bot.send_media_group(-1001716874276, to_send, True):
        file_ids.append(n.photo[-1].file_id)
    bot.send_message(-1001716874276, txt, "HTML", disable_notification=False)
    setting_set(f"tg_{prefix}", ','.join(file_ids))
    users = Mysql.query("SELECT tgid FROM tg_users WHERE subscribe = 1", fetch="all")
    for user in users:
        to_send = []
        try:
            for n in file_ids:
                to_send.append(InputMediaPhoto(n))
            bot.send_media_group(user['tgid'], to_send, True)
            bot.send_message(user['tgid'], txt, "HTML", disable_notification=False)
        except Exception as e:
            log("TG_ERR", str(e)+" | User: "+user['tgid'])
    chats = Mysql.query("SELECT id FROM tg_chats WHERE subscribe = 1", fetch="all")
    for chat in chats:
        to_send = []
        try:
            for n in file_ids:
                to_send.append(InputMediaPhoto(n))
            bot.send_media_group(chat['id'], to_send, True)
            bot.send_message(chat['id'], txt, "HTML", disable_notification=False)
        except Exception as e:
            log("TG_ERR", str(e)+" | Chat: "+chat['id'])
    for f in files: f.close()

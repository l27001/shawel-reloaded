import datetime, re, timeit, json

from config import vk_info
from methods import Methods
from exceptions import *
from decorators import *
from parse import parse

class Commands:

    def __init__(self, response):
        today = datetime.datetime.now()
        if(DEBUG == True):
            extime = timeit.default_timer()
            print(today.strftime("%H:%M:%S %d.%m.%Y") + ": " + str(response))
        if(response['type'] != 'message_new'):
            if(response['type'] == 'message_deny'):
                Mysql.query("UPDATE users SET subscribe = 0 WHERE vkid = %s", (response['object']['user_id']))
            Methods.log('Message', f"Получен неизвестный тип события {response['type']}")
            return None
        obj = response['object']['message']
        client_info = response['object']['client_info']
        if 'reply_message' in obj:
            replid = obj['reply_message']['from_id']
        else:
            replid = ''
        from_id = obj['from_id']
        chat_id = obj['peer_id']
        text = obj['text']
        if('action' in obj):
            if(obj['action']['type'] == 'chat_invite_user' and str(obj['action']['member_id']) == '-' + vk_info['groupid']):
                keyb = Methods.construct_keyboard(b0=Methods.make_button(label="/помощь", color="primary"), b1=Methods.make_button(label="/рассылка", color="positive"), b2=Methods.make_button(label="/расписание", color="secondary"), b3=Methods.make_button(label="/звонки", color="secondary"), inline="true")
                Methods.send(chat_id, "Привет! Я бот Щавель, я слежу за расписанием и могу присылать расписание как по вашему запросу, так и при его обновлении на сайте.\nСписок команд можно получить введя команду /помощь\nЧтобы подписаться на рассылку расписания используйте команду /рассылка", keyboard=keyb)
        if(from_id < 1 or text == ''):
            return None
        user = Methods.users_get(from_id)
        user = user[0]['last_name']+" "+user[0]['first_name']
        if(chat_id == from_id):
            who = f"от {user}[{from_id}]"
        else:
            who = f"в {chat_id} от {user}[{from_id}]"
        userinfo = Mysql.query("SELECT * FROM users WHERE vkid=%s", (from_id))
        if(userinfo == None):
            Mysql.query("INSERT INTO users (`vkid`) VALUES (%s)", (from_id))
            userinfo = Mysql.query("SELECT * FROM users WHERE vkid=%s", (from_id))
        tolog = text.replace("\n",r" \n ")
        if(chat_id > 2000000000):
            inline = "true"
        else:
            inline = str(client_info['inline_keyboard']).lower()
        Methods.log("Message", f"'{tolog}' {who}")
        if('payload' in obj):
            try:
                obj['payload'] = json.loads(obj['payload'])
                if('command' in obj['payload'] and obj['payload']['command'] == "internal_command"):
                    if(obj['payload']['action']['type'] == "intent_unsubscribe"):
                        Mysql.query(f"UPDATE users SET subscribe='0' WHERE vkid='{from_id}'")
                        Methods.send(from_id, "Вы отписались от рассылки обновлений расписания.\nДля повторной подписки используйте команду '/рассылка'", keyboard=Methods.construct_keyboard(b1=Methods.make_button(type_="intent_subscribe",peer_id=from_id,intent="non_promo_newsletter",label="Подписаться"),inline=inline))
                    elif(obj['payload']['action']['type'] == "intent_subscribe"):
                        Mysql.query(f"UPDATE users SET subscribe='1' WHERE vkid='{from_id}'")
                        Methods.send(from_id, "Вы подписались на рассылку обновлений расписания.\nДля отписки используйте команду '/рассылка'", keyboard=Methods.construct_keyboard(b2=Methods.make_button(type_="intent_unsubscribe",peer_id=from_id,intent="non_promo_newsletter",label="Отписаться"),inline=inline))
                    return None
            except TypeError: pass
            userinfo.update({'payload':obj['payload']})
        text = text.split(' ')
        if(re.match(rf"\[(club|public){vk_info['groupid']}\|(@|\*){scrname}\]", text[0])):
            text.pop(0)
        if(chat_id > 2000000000):
            chatinfo = Mysql.query(f"SELECT * FROM chats WHERE id = '{chat_id}' LIMIT 1")
            if(chatinfo == None):
                Mysql.query(f"INSERT INTO chats (`id`) VALUES ({chat_id})")
                chatinfo = Mysql.query(f"SELECT * FROM chats WHERE id = '{chat_id}' LIMIT 1")
            userinfo.update({'chatinfo':chatinfo})
            if(text[0][0] != '/'):
                return None
        text[0] = text[0].lower()
        text[0] = text[0].replace('/','')
        userinfo.update({'replid':replid, 'chat_id':chat_id, 'from_id':from_id, 'attachments':obj['attachments'], 'inline':inline})
        try:
            if(cmds.get(text[0]) == None):
                raise CommandNotFound
                return None
            else:
                cmds[text[0]](userinfo, text[1:])
        except CommandNotFound as e:
            if(DEBUG):
                Methods.log("Message", e.__str__())
            if(chat_id < 2000000000):
                keyb = Methods.construct_keyboard(b1=Methods.make_button(label="/рассылка", color="positive"), b2=Methods.make_button(label="/помощь", color="secondary"), inline=inline)
                Methods.send(chat_id, "👎🏻 Не понял.", keyboard=keyb)
        except Exception as e:
            Methods.log("ERROR", f"Непредвиденная ошибка. {e}")
            Methods.send(chat_id, "⚠ Произошла непредвиденная ошибка.\nОбратитесь к @l27001", attachment="photo-183256712_457239206")
            raise e
        if(DEBUG == True):
            Methods.log("Debug", f"Время выполнения: {timeit.default_timer()-extime}")
 
    def info(userinfo, text):
        """Выводит информацию о пользователе из БД. Если не указан пользователь, выведет информацию о текущем."""
        if(len(text) < 1):
            text.insert(0, str(userinfo['from_id']))
        t = re.findall(r'\[.*\|', text[0])
        try:
            t = t[0].replace("[", "").replace("|", "")
        except IndexError:
            t = text[0]
        if('payload' in userinfo):
            t = userinfo['payload']
        try:
            uinfo = Methods.users_get(t)
        except Exception as e:
            if(e.code == 113):
                Methods.send(userinfo['chat_id'], "⚠ Invalid user_id")
                return 0
        name = f"[id{uinfo[0]['id']}|{uinfo[0]['last_name']} {uinfo[0]['first_name']}]"
        uinfo = Mysql.query("SELECT * FROM users WHERE vkid=%s", (uinfo[0]['id']))
        if(uinfo == None):
            Methods.send(userinfo['chat_id'], "⚠ Пользователь не найден в БД")
            return 0
        if(uinfo['subscribe'] == 0):
            subscribe = 'Рассылка: Не подписан'
        else:
            subscribe = 'Рассылка: Подписан'
        if(userinfo['chat_id'] != userinfo['from_id']):
            ch = f"Chat-ID: {userinfo['chat_id']}"
        else:
            ch = ''
        keyb = Methods.construct_keyboard(b1=Methods.make_button(label="/рассылка", color="primary"), b2=Methods.make_button(label="/расписание", color="secondary"), inline=userinfo['inline'])
        Methods.send(userinfo['chat_id'], f"Имя: {name}\nVKID: {uinfo['vkid']}\nDostup: {uinfo['dostup']}\n{subscribe}\n{ch}", keyboard=keyb, disable_mentions=1)

    def raspisanie(userinfo, text):
        """Присылает последнее расписание"""
        post = Methods.setting_get('rasp_post')
        keyb = ''
        attachment = ''
        if(post is None):
            text = "Раписания нет."
        elif(userinfo['subscribe'] == 1 or userinfo['chat_id'] > 2000000000):
            text = "Последнее расписание:"
            attachment = f"wall-{vk_info['groupid']}_{post}"
        else:
            text = "Вы можете подписаться на рассылку раписания с помощью кнопки ниже."
            keyb = Methods.construct_keyboard(b1=Methods.make_button(type_="intent_subscribe",peer_id=userinfo['from_id'],intent="non_promo_newsletter",label="Подписаться"),inline=userinfo['inline'])
            attachment = f"wall-{vk_info['groupid']}_{post}"
        Methods.send(userinfo['chat_id'], text, attachment, keyboard=keyb)

    def zvonki(userinfo, text):
        """Отправляет расписание звонков"""
        post = Methods.setting_get('zvonki_post')
        if(post is not None):
            text = "Актуальное расписание звонков:"
            attachment = f"wall-{vk_info['groupid']}_{post}"
        else:
            text = "Расписания звонков нет."
            attachment = ''
        Methods.send(userinfo['chat_id'], text, attachment)

    def subscribe(userinfo, text):
        """Подписаться/Отписаться от рассылки обновлений расписания"""
        if(userinfo['chat_id'] == userinfo['from_id']):
            if(userinfo['subscribe'] == 0):
                Methods.send(userinfo['chat_id'], "Вы не подписаны", keyboard=Methods.construct_keyboard(b1=Methods.make_button(type_="intent_subscribe",peer_id=userinfo['from_id'],intent="non_promo_newsletter",label="Подписаться"),inline=userinfo['inline']))
            else:
                Methods.send(userinfo['chat_id'], "Вы подписаны", keyboard=Methods.construct_keyboard(b2=Methods.make_button(type_="intent_unsubscribe",peer_id=userinfo['from_id'],intent="non_promo_newsletter",label="Отписаться"),inline=userinfo['inline']))
        else:
            if(userinfo['chatinfo']['subscribe'] != 1):
                Mysql.query("UPDATE `chats` SET subscribe=1 WHERE id=%s", (userinfo['chat_id']))
                Methods.send(userinfo['chat_id'], "Вы подписали беседу на рассылку обновлений расписания.\nДля рассылки лично вам напишите боту в ЛС.")
            else:
                Mysql.query("UPDATE `chats` SET subscribe=0 WHERE id=%s", (userinfo['chat_id']))
                Methods.send(userinfo['chat_id'], "Вы отписали беседу от рассылки обновлений расписания.\nДля рассылки лично вам напишите боту в ЛС.")

    def help(userinfo, text):
        """Помощь"""
        out = []
        prev = None
        for i,n in cmds.items():
            if(n == prev):
                continue
            prev = n
            if(n.__doc__ == None or n.__doc__ == ''):
                continue
            else:
                doc = n.__doc__
            out.append(f'/{i} - {doc}')
        keyb = Methods.construct_keyboard(b1=Methods.make_button(label="/рассылка", color="primary"), b2=Methods.make_button(label="/расписание", color="secondary"), b3=Methods.make_button(label="/звонки", color="secondary"), inline=userinfo['inline'])
        Methods.send(userinfo['chat_id'], '\n'.join(out), keyboard=keyb)

    @dostup1_needed
    def parser(userinfo, text):
        """Принудительный запуск парсера обновлений расписания"""
        Methods.send(userinfo['chat_id'], "✅ Парсер был запущен принудительно. Ожидайте результат.")
        res = parse({'rasp': 0}, True)
        if(res == 10):
            Methods.send(userinfo['chat_id'], "⚠ Парсер уже работает.")
        elif(res == 11):
            Methods.send(userinfo['chat_id'], "ℹ️ Парсер не обнаружил обновлений.")
        else:
            Methods.send(userinfo['chat_id'], "⚠ Парсер вернул неизвестный код, за дополнительной информацией обратитесь к логу.")

cmds = {
    'info':Commands.info, 'инфо':Commands.info,
    'help':Commands.help, 'помощь':Commands.help, 'хелп':Commands.help,
    'рассылка':Commands.subscribe, 'подписаться':Commands.subscribe, 'отписаться':Commands.subscribe,
    'расписание':Commands.raspisanie,
    'звонки':Commands.zvonki,
    'парсер':Commands.parser
}

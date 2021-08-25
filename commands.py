import datetime, re, timeit, json

from config import vk_info
from methods import Methods

class Commands:

    def __init__(self, response):
        today = datetime.datetime.now()
        if(DEBUG == True):
            extime = timeit.default_timer()
            print(today.strftime("%H:%M:%S %d.%m.%Y")+ ": "+str(response))
        obj = response['object']['message']
        client_info = response['object']['client_info']
        if 'reply_message' in obj:
            replid = obj['reply_message']['from_id']
        else:
            replid = ''
        from_id = obj['from_id']
        chat_id = obj['peer_id']
        text = obj['text']
        if(from_id < 1 or text == ''):
            return None
        user = Methods.users_get(from_id)
        user = user[0]['last_name']+" "+user[0]['first_name']
        if(chat_id == from_id):
            who = f"от {user}[{str(from_id)}]"
        else:
            who = f"в {str(chat_id)} от {user}[{str(from_id)}]"
        userinfo = Mysql.query("SELECT * FROM users WHERE vkid=%s", (from_id))
        if(userinfo == None):
            Mysql.query("INSERT INTO users (`vkid`) VALUES (%s)", (from_id))
            userinfo = Mysql.query("SELECT * FROM users WHERE vkid=%s", (from_id))
        tolog = text.replace("\n",r" \n ")
        Methods.log("Message", f"'{tolog}' {who}")
        if(chat_id > 2000000000 and text[0] != '/'):
            return None
        if('payload' in obj):
            try:
                obj['payload'] = json.loads(obj['payload'])
                if('command' in obj['payload'] and obj['payload']['command'] == "internal_command"):
                    inline = Methods.check_keyboard(client_info['inline_keyboard'])
                    if(obj['payload']['action']['type'] == "intent_unsubscribe"):
                        Mysql.query(f"UPDATE users SET subscribe='0' WHERE vkid='{from_id}'")
                        Methods.send(from_id, "Вы отписались от рассылки обновлений расписания.\nДля повторной подписки используйте команду '/рассылка'", keyboard=Methods.construct_keyboard(b1=Methods.make_button(type="intent_subscribe",peer_id=from_id,intent="non_promo_newsletter",label="Подписаться"),inline=inline))
                    elif(obj['payload']['action']['type'] == "intent_subscribe"):
                        Mysql.query(f"UPDATE users SET subscribe='1' WHERE vkid='{from_id}'")
                        Methods.send(from_id, "Вы подписались на рассылку обновлений расписания.\nДля отписки используйте команду '/рассылка'", keyboard=Methods.construct_keyboard(b2=Methods.make_button(type="intent_unsubscribe",peer_id=from_id,intent="non_promo_newsletter",label="Отписаться"),inline=inline))
                    return None
            except TypeError: pass
            userinfo.update({'payload':obj['payload']})
        text = text.split(' ')
        if(re.match(rf"\[(club|public){vk_info['groupid']}\|(@|\*){scrname}\]", text[0])):
            text.pop(0)
        elif(chat_id > 2000000000):
            chatinfo = Mysql.query(f"SELECT * FROM chats WHERE id = '{chat_id}' LIMIT 1")
            if(chatinfo == None):
                Mysql.query(f"INSERT INTO chats (`id`) VALUES ({chat_id})")
                chatinfo = Mysql.query(f"SELECT * FROM chats WHERE id = '{chat_id}' LIMIT 1")
            userinfo.update({'chatinfo':chatinfo})
        text[0] = text[0].lower()
        text[0] = text[0].replace('/','')
        userinfo.update({'replid':replid,'chat_id':chat_id, 'from_id':from_id, 'attachments':obj['attachments'], 'inline':client_info['inline_keyboard']})
        if(cmds.get(text[0]) == None):
            if(chat_id < 2000000000):
                Methods.send(chat_id, "👎🏻 Не понял.")
            return None
        else:
            try:
                cmds[text[0]](userinfo, text[1:])
            except Exception as e:
                Methods.log("ERROR", f"Непредвиденная ошибка. {str(e)}")
                Methods.send(chat_id, "⚠ Произошла непредвиденная ошибка.\nОбратитесь к @l27001", attachment="photo-**ID**_457239188")
                raise e
        if(DEBUG == True):
            Methods.log("Debug", f"Время выполнения: {str(timeit.default_timer()-extime)}")
 
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
        keyb = Methods.construct_keyboard(b1=Methods.make_button(label="/рассылка", color="primary"))
        Methods.send(userinfo['chat_id'], f"Имя: {name}\nVKID: {uinfo['vkid']}\nDostup: {uinfo['dostup']}\n{subscribe}\n{ch}", keyboard=keyb, disable_mentions=1)

    def raspisanie(userinfo, text):
        """Присылает последнее расписание"""
        rasp = Mysql.query("SELECT rasp FROM vk")['rasp']
        if(userinfo['subscribe'] == 1 or userinfo['chat_id'] > 2000000000):
            text = "https://shawel.ezdomain.ru\n\nПоследнее расписание:"
            keyb = ''
        else:
            text = "https://shawel.ezdomain.ru\n\nВы можете подписаться на рассылку раписания с помощью кнопки ниже."
            keyb = Methods.construct_keyboard(b1=Methods.make_button(type="intent_subscribe",peer_id=userinfo['from_id'],intent="non_promo_newsletter",label="Подписаться"),inline=Methods.check_keyboard(userinfo['inline']))
        if(rasp == ''):
            text = "Раписания нет."
        Methods.send(userinfo['chat_id'], text, rasp, keyboard=keyb)

    def zvonki(userinfo, text):
        """Отправляет расписание звонков"""
        data = Mysql.query("SELECT zvonki FROM vk")['zvonki']
        if(data != ''):
            text = "Актуальное расписание звонков:\n\nhttps://shawel.ezdomain.ru/zvonki"
        else:
            text = "Расписания звонков нет."
        Methods.send(userinfo['chat_id'],text,attachment=data)

    def subscribe(userinfo, text):
        """Подписаться/Отписаться от рассылки актуального расписания"""
        if(userinfo['chat_id'] == userinfo['from_id']):
            if(userinfo['subscribe'] == 0):
                Methods.send(userinfo['chat_id'],"Вы не подписаны", keyboard=Methods.construct_keyboard(b1=Methods.make_button(type="intent_subscribe",peer_id=userinfo['from_id'],intent="non_promo_newsletter",label="Подписаться"),inline=Methods.check_keyboard(userinfo['inline'])))
            else:
                Methods.send(userinfo['chat_id'],"Вы подписаны", keyboard=Methods.construct_keyboard(b2=Methods.make_button(type="intent_unsubscribe",peer_id=userinfo['from_id'],intent="non_promo_newsletter",label="Отписаться"),inline=Methods.check_keyboard(userinfo['inline'])))
        else:
            if(userinfo['chatinfo']['subscribe'] != 1):
                Mysql.query("UPDATE `chats` SET subscribe=1 WHERE id=%s", (userinfo['chat_id']))
                Methods.send(userinfo['chat_id'],"Вы подписали беседу на рассылку обновлений расписания.\nДля рассылки лично вам напишите боту в ЛС.")
            else:
                Mysql.query("UPDATE `chats` SET subscribe=0 WHERE id=%s", (userinfo['chat_id']))
                Methods.send(userinfo['chat_id'],"Вы отписали беседу от рассылки обновлений расписания.\nДля рассылки лично вам напишите боту в ЛС.")

    def help(userinfo, text):
        """Помощь"""
        out = []
        prev = None
        for i,n in cmds.items():
            if(n == prev):
                continue
            prev = n
            if(n.__doc__ == None or n.__doc__ == ''):
                doc = "Нет описания"
            else:
                doc = n.__doc__
            out.append(f'/{i} - {doc}')
        Methods.send(userinfo['chat_id'], '\n'.join(out))

cmds = {
    'info':Commands.info, 'инфо':Commands.info,
    'help':Commands.help, 'помощь':Commands.help, 'хелп':Commands.help,
    'рассылка':Commands.subscribe, 'подписаться':Commands.subscribe, 'отписаться':Commands.subscribe,
    'расписание':Commands.raspisanie,
    'звонки':Commands.zvonki
}
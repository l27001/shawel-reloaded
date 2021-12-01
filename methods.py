import re, requests, datetime, os, random, timeit, pymysql
from pymysql.err import OperationalError, InterfaceError
import config

headers = {
    'User-Agent': "ShawelBot/Methods"
}

class Methods:

    def make_button(color="primary",type_="text",**kwargs):
        a = []
        for name,data in kwargs.items():
            a.append('"'+name+'":"'+str(data)+'"')
        kk = ",".join(a)
        if(type_ != "intent_unsubscribe" and type_ != "intent_subscribe"):
            return"{\"color\":\""+color+"\",\"action\":{\"type\":\""+type_+"\","+kk+"}}"
        else:
            return"{\"action\":{\"type\":\""+type_+"\","+kk+"}}"

    def construct_keyboard(inline="false",one_time="false",**kwargs):
        a = []
        for n in kwargs:
            a.append("["+kwargs[n]+"]")
        kx = f'"buttons":{a},"inline":{inline},"one_time":{one_time}'
        kx = '{'+kx+'}'
        return re.sub(r"[']",'',kx)

    def log(prefix,message,timestamp=True):
        now = datetime.datetime.now()
        if(timestamp == True):
            message = f"({now.strftime('%H:%M:%S')}) [{prefix}] {message}"
        else:
            message = f"[{prefix}] {message}"
        print(message)
        with open(dir_path+"/shawel.log", 'a', encoding='utf-8') as f:
            f.write(message+"\n")

    def users_get(user_id,fields=''):
        try:
            return api.users.get(user_ids=user_id,fields=fields)
        except:
            return api.users.get(user_ids=user_id,fields=fields)

    class Mysql:

        def __init__(self):
            self.con = Methods.Mysql.make_con()

        def query(self,query,variables=(),fetch="one",time=False):
            if(time == True):
                extime = timeit.default_timer()
            try:
                cur = self.con.cursor()
                cur.execute(query, variables)
            except (InterfaceError,OperationalError):
                self.con = Methods.Mysql.make_con()
                cur = self.con.cursor()
                cur.execute(query, variables)
            if(fetch == "one"):
                data = cur.fetchone()
            else:
                data = cur.fetchall()
            if(time == True):
                Methods.log("Debug",f"Время запроса к MySQL: {str(timeit.default_timer()-extime)}")
            return data

        def make_con(self=None):
            return pymysql.connect(host=config.db['host'],
                user=config.db['user'],
                password=config.db['password'],
                db=config.db['database'],
                charset='utf8mb4',
                autocommit=True,
                cursorclass=pymysql.cursors.DictCursor)

        def close(self):
            self.con.close()

    def send(peer_id,message='',attachment='',keyboard='{"buttons":[]}',disable_mentions=0,intent="default"):
        return api.messages.send(peer_id=peer_id,random_id=random.randint(1,2147400000),message=message,attachment=attachment,keyboard=keyboard,disable_mentions=disable_mentions,intent=intent)

    def mass_send(peer_ids,message='',attachment='',keyboard='{"buttons":[]}',disable_mentions=0,intent="default"):
        return api.messages.send(peer_ids=peer_ids,random_id=random.randint(1,2147400000),message=message,attachment=attachment,keyboard=keyboard,disable_mentions=disable_mentions,intent=intent)

    def upload_img(peer_id, file):
        if(Methods.is_message_allowed(peer_id) == 1):
            srvv = api.photos.getMessagesUploadServer(peer_id=peer_id)['upload_url']
        else:
            srvv = api.photos.getMessagesUploadServer(peer_id=331465308)['upload_url']
        no = requests.post(srvv, files={
                    'file': open(file, 'rb')
                }).json()
        if(no['photo'] == '[]'):
            return 1
        response = api.photos.saveMessagesPhoto(photo=no['photo'],server=no['server'],hash=no['hash'])
        return f"photo{response[0]['owner_id']}_{response[0]['id']}_{response[0]['access_key']}"

    def upload_img_post(file):
        srv = user_api.photos.getWallUploadServer()['upload_url']
        response = requests.post(srv, files={
                    'file': open(file, 'rb')
                }).json()
        response = user_api.photos.saveWallPhoto(photo=response['photo'],server=response['server'],hash=response['hash'])
        return f"photo{response[0]['owner_id']}_{response[0]['id']}"

    def wall_post(message='',attachments='',from_group=1,signed=0,close_comments=0):
        return user_api.wall.post(owner_id="-"+config.vk_info['groupid'],message=message,attachments=attachments,from_group=from_group,signed=signed,close_comments=close_comments)

    def wall_del(id_):
        try:
            return user_api.wall.delete(owner_id="-"+config.vk_info['groupid'],post_id=id_)
        except Exception as e:
            if(e.code): return e.code
            else: raise Exception(e)

    def wall_pin(id_):
        return user_api.wall.pin(owner_id="-"+config.vk_info['groupid'],post_id=id_)

    def download_img(url, file):
        p = requests.get(url, headers=headers)
        with open(file, "wb") as out:
            out.write(p.content)
        return file

    def is_message_allowed(id_):
        return api.messages.isMessagesFromGroupAllowed(user_id=id_,group_id=config.vk_info['groupid'])['is_allowed']

    def check_name(name):
        return api.utils.resolveScreenName(screen_name=name)

    def del_message(message_ids,delete_for_all=1,group_id=config.vk_info['groupid']):
        return api.messages.delete(message_ids=message_ids,delete_for_all=1,group_id=config.vk_info['groupid'])

    def check_keyboard(inline):
        if(inline):
            return "true"
        else:
            return "false"

    def setting_set(setting, value='NULL'):
        setting = str(setting).replace(' ', '_')
        return Mysql.query("INSERT INTO settings (name, value) VALUES(%s, %s) ON DUPLICATE KEY UPDATE value=%s", (setting, value, value))

    def setting_get(setting):
        setting = str(setting).replace(' ', '_')
        res = Mysql.query("SELECT value FROM settings WHERE name = %s", (setting))
        if(res['value'] == "True"): return True
        elif(res['value'] == "False"): return False
        elif(res is not None and res['value'] != 'NULL'): return res['value']
        else: return None

    def setting_delete(setting):
        setting = str(setting).replace(' ', '_')
        Mysql.query("DELETE FROM settings WHERE name = %s", (setting))


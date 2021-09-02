#!/usr/bin/python3
from bs4 import BeautifulSoup
import requests as req
import subprocess,time,os,datetime,schedule,shutil
from PIL import Image
from methods import Methods
from config import tmp_dir
dir_path = os.path.dirname(os.path.realpath(__file__))

headers = {
    'User-Agent': 'ShawelBot/Parser'
}

def check(dir_):
    for name in sorted(os.listdir(f'{tmp_dir}/parse/{dir_}')):
        im = Image.open(f'{tmp_dir}/parse/{dir_}/{name}')
        white = 0
        for n in im.getdata():
            if(n == (255,255,255)):
                white += 1
        percent = white/(im.size[0]*im.size[1])
        if(percent >= 0.99):
            os.remove(f'{tmp_dir}/parse/{dir_}/{name}')

def parse_rasp(soup ,mode=0):
    Methods.log("Parser", "Парсер выполняет проверку...")
    src = soup.find("iframe")['src']
    if(os.path.isdir(tmp_dir+"/parse/rasp") == False):
        os.makedirs(tmp_dir+"/parse/rasp")
    date = datetime.datetime.today().strftime("%H:%M:%S %d.%m.%Y")
    Mysql.query(f"UPDATE vk SET `rasp-checked`='{date}'")
    if(mode == 0):
        res = Mysql.query("SELECT rasp_last FROM vk")['rasp_last']
    else:
        res = None
    if(res != src):
        with req.get(src, stream=True, headers=headers) as r:
            with open(tmp_dir+"/parse/raspisanie.pdf", "wb") as f:
                shutil.copyfileobj(r.raw, f)
        p = subprocess.Popen(["pdftoppm",tmp_dir+"/parse/raspisanie.pdf",tmp_dir+"/parse/rasp/out","-png"], stdout=subprocess.DEVNULL)
        p.wait()
        check("rasp")
        attach = []
        Mysql.query("DELETE FROM imgs WHERE mark='rasp'")
        for n in sorted(os.listdir(tmp_dir+"/parse/rasp")):
            attach.append(Methods.upload_img('331465308',tmp_dir+'/parse/rasp/'+n))
            with open(tmp_dir+'/parse/rasp/'+n, 'rb') as f:
                blob = f.read()
            Mysql.query("INSERT INTO imgs (`image`,`type`,`size`,`mark`) VALUES (%s, %s, %s, %s)", (blob, n.split('.')[-1], os.path.getsize(tmp_dir+'/parse/rasp/'+n), 'rasp'))
        txt = 'Новое расписание\nОбнаружено в '+date+'\nДля отписки используйте команду \'/рассылка\''
        if(mode == 0):
            rasp = Mysql.query("SELECT COUNT(id) FROM `chats` WHERE subscribe='1'")
            i = 0
            while i < rasp['COUNT(id)']:
                a = []
                r = Mysql.query("SELECT id FROM `chats` WHERE subscribe='1' LIMIT "+str(i)+", 50", fetch="all")
                for n in r:
                    a.append(str(n['id']))
                a = ",".join(a)
                Methods.mass_send(peer_ids=a,message=txt,attachment=attach)
                i+=50
                time.sleep(1)
            rasp = Mysql.query("SELECT vkid,subscribe FROM users WHERE subscribe>='1'", fetch="all")
            i = 0
            for n in rasp:
                Methods.send(n['vkid'],message=txt,attachment=attach,keyboard=Methods.construct_keyboard(b2=Methods.make_button(type_="intent_unsubscribe",peer_id=n['vkid'],intent="non_promo_newsletter",label="Отписаться"),inline="true"),intent="non_promo_newsletter")
                i+=1
                time.sleep(.5)
        else:
            Methods.send(331465308,message=txt,attachment=attach)
        Mysql.query("UPDATE vk SET `rasp-updated`=%s, `rasp`=%s, `rasp_last`=%s", (date, ','.join(attach), src))
        for n in os.listdir(tmp_dir+"/parse/rasp"):
            os.remove(tmp_dir+"/parse/rasp/"+n)
        Methods.log("Parser", "Обнаружено новое расписание.")
    else:
        Methods.log("Parser", "Новое расписание не было обнаружено.")

def parse_zvonki(soup, mode=0):
    Methods.log("ZvonkiParser", "Парсер выполняет проверку...")
    src = soup.findAll("iframe")[-1]['src']
    if(os.path.isdir(tmp_dir+"/parse/zvonki") == False):
        os.makedirs(tmp_dir+"/parse/zvonki")
    date = datetime.datetime.today().strftime("%H:%M:%S %d.%m.%Y")
    if(mode == 0):
        res = Mysql.query("SELECT zvonki_last FROM vk")['zvonki_last']
    else:
        res = None
    if(res != src):
        with req.get(src, stream=True, headers=headers) as r:
            with open(tmp_dir+"/parse/zvonki.pdf", "wb") as f:
                shutil.copyfileobj(r.raw, f)
        p = subprocess.Popen(["pdftoppm",tmp_dir+"/parse/zvonki.pdf",tmp_dir+"/parse/zvonki/out","-png","-thinlinemode","shape"], stdout=subprocess.DEVNULL)
        p.wait()
        check("zvonki")
        attach = []
        Mysql.query("DELETE FROM imgs WHERE mark='zvonki'")
        for n in sorted(os.listdir(tmp_dir+"/parse/zvonki")):
            attach.append(Methods.upload_img('331465308',tmp_dir+'/parse/zvonki/'+n))
            with open(tmp_dir+'/parse/zvonki/'+n, 'rb') as f:
                blob = f.read()
            Mysql.query("INSERT INTO imgs (`image`,`type`,`size`,`mark`) VALUES (%s, %s, %s, %s)", (blob, n.split('.')[-1], os.path.getsize(tmp_dir+'/parse/zvonki/'+n), 'zvonki'))
        txt = 'Новое расписание звонков\nОбнаружено в '+date+'\nДля отписки используйте команду \'/рассылка\''
        if(mode == 0):
            rasp = Mysql.query("SELECT COUNT(id) FROM `chats` WHERE subscribe='1'")
            i = 0
            while i < rasp['COUNT(id)']:
                a = []
                r = Mysql.query("SELECT id FROM `chats` WHERE subscribe='1' LIMIT "+str(i)+", 50", fetch="all")
                for n in r:
                    a.append(str(n['id']))
                a = ",".join(a)
                Methods.mass_send(peer_ids=a,message=txt,attachment=attach)
                i+=50
                time.sleep(1)
            rasp = Mysql.query("SELECT vkid,subscribe FROM users WHERE subscribe>='1'", fetch="all")
            i = 0
            for n in rasp:
                Methods.send(n['vkid'],message=txt,attachment=attach,keyboard=Methods.construct_keyboard(b2=Methods.make_button(type_="intent_unsubscribe",peer_id=n['vkid'],intent="non_promo_newsletter",label="Отписаться"),inline="true"),intent="non_promo_newsletter")
                i+=1
                time.sleep(.5)
        else:
            Methods.send(331465308,message=txt,attachment=attach)
        Mysql.query("UPDATE vk SET zvonki=%s, zvonki_last=%s", (','.join(attach), src))
        for n in os.listdir(tmp_dir+"/parse/zvonki"):
            os.remove(tmp_dir+"/parse/zvonki/"+n)
        Methods.log("ZvonkiParser", "Обнаружено новое расписание звонков.")
    else:
        Methods.log("ZvonkiParser", "Новое расписание звонков не было обнаружено.")

def run_parse():
    try:
        resp = req.get("https://engschool9.ru/content/raspisanie.html", headers=headers)
        if(resp.status_code != 200):
            Methods.log("Parser", f"Неожиданный код ответа: {resp.status_code}")
        else:
            soup = BeautifulSoup(resp.text, 'html.parser')
            parse_rasp(soup)
            parse_zvonki(soup)
    except KeyboardInterrupt:
        exit()
    except Exception as e:
        Methods.log("Parser-ERROR", f"Произошла ошибка.\n\n{e}")
        Methods.send(331465308, f"С парсером что-то не так!\n\n{e}")

if(__name__ == '__main__'):
    Mysql = Methods.Mysql()
    try:
        run_parse()
    finally:
        Mysql.close() 

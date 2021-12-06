#!/usr/bin/python3
from bs4 import BeautifulSoup
import requests as req
from time import sleep
import os, subprocess
from datetime import datetime
from PIL import Image, UnidentifiedImageError
from methods import Methods
from config import tmp_dir, vk_info

headers = {
    'User-Agent': 'ShawelBot/Parser_v2.1'
}
for_parse = {
    'rasp': 0,
    #'zvonki': 2
}

def check(dir_):
    for name in sorted(os.listdir(f'{tmp_dir}/parse/{dir_}')):
        try: im = Image.open(f'{tmp_dir}/parse/{dir_}/{name}')
        except UnidentifiedImageError: continue
        white = 0
        for n in im.getdata():
            if((n[0] == 255 and n[1] == 255 and n[2] == 255) or n == (255, 0)):
                white += 1
        percent = white/(im.size[0]*im.size[1])
        if(percent >= 0.995):
            os.remove(f'{tmp_dir}/parse/{dir_}/{name}')

def parse(for_parse, manual = False):
    if(os.path.isdir(tmp_dir + '/parse') != True):
        os.makedirs(tmp_dir + '/parse')
    if(os.path.isfile(tmp_dir + '/parse/parser.tmp')):
        return 10
    Mysql = Methods.Mysql()
    Methods.log("Parser", "Парсер выполняет проверку...")
    page = req.get("https://engschool9.ru/content/raspisanie.html", headers=headers)
    if(page.status_code != 200):
        Methods.log("Parser", f"Получен неожиданный http код {self.page.status_code}")
        return self.page.status_code
    now = datetime.now()
    date = now.strftime("%H:%M %d.%m.%Y")
    page = BeautifulSoup(page.text, 'html.parser')
    iframes = page.findAll("iframe")
    with open(tmp_dir + '/parse/parser.tmp', 'w') as f:
        f.write('')
    try:
        for prefix, cnt in for_parse.items():
            curdir = tmp_dir+"/parse/"+prefix
            if(os.path.isdir(curdir) == False):
                os.makedirs(curdir)
            res = Methods.setting_get(f'{prefix}_last')
            if(res == iframes[cnt]['src']):
                if(manual):
                    return 11
                continue
            with open(f"{tmp_dir}/parse/{prefix}.pdf", "wb") as f:
                r = req.get(iframes[cnt]['src'], stream=True)
                if(r.status_code != 200):
                    Methods.log("WARN", f"Парсер [{prefix}] не может загрузить файл {iframes[cnt]['src']}. Код: {r.status_code}")
                    continue
                for chunk in r.iter_content(chunk_size = 1024):
                    if(chunk): f.write(chunk)
            subprocess.Popen(["convert", "-colorspace", "RGB", "-density", "200", f"{tmp_dir}/parse/{prefix}.pdf", f"{curdir}/out.png"], stdout=subprocess.DEVNULL).wait()
            files_count = len(os.listdir(curdir))
            check(prefix)
            attach = []
            for img in sorted(os.listdir(curdir)):
                attach.append(Methods.upload_img_post(f"{curdir}/{img}"))
            txt = 'Зафиксировано обновление\nДля отписки используйте команду \'/рассылка\''
            # post_pre = Methods.setting_get('post_pre')
            # if(post_pre != '' and post_pre != None):
                # Methods.wall_del(post_pre)
            post_id = Methods.wall_post(f"Файл: {iframes[cnt]['src'].split('/')[-1]}\nВремя: {date}\nИзображений: {len(attach)}/{files_count}",attachments=attach)['post_id']
            if(for_parse[prefix] == 2):
                Methods.wall_pin(post_id)
            Methods.setting_set(f'{prefix}_post', post_id)
            attach = f"wall-{vk_info['groupid']}_{post_id}"
            i = 0; i_limit = 50
            users = Mysql.query("SELECT vkid FROM `users` WHERE subscribe = 1 LIMIT %s, %s", (i, i_limit), fetch="all")
            while users:
                send_users = []
                for user in users:
                    send_users.append(str(user['vkid']))
                send_users = ",".join(send_users)
                Methods.mass_send(send_users, message=txt, attachment=attach, keyboard=Methods.construct_keyboard(b1=Methods.make_button(label="Отписаться", color="negative"), one_time="true"), intent="non_promo_newsletter")
                i += i_limit
                sleep(.3)
                users = Mysql.query("SELECT vkid FROM `users` WHERE subscribe = 1 LIMIT %s, %s", (i, i_limit), fetch="all")
            i = 0
            chats = Mysql.query("SELECT id FROM `chats` WHERE subscribe = 1 LIMIT %s, %s", (i, i_limit), fetch="all")
            while chats:
                send_chats = []
                for chat in chats:
                    send_chats.append(str(chat['id']))
                send_chats = ",".join(send_chats)
                Methods.mass_send(send_chats, message=txt, attachment=attach)
                i += i_limit
                sleep(.3)
                chats = Mysql.query("SELECT id FROM `chats` WHERE subscribe = 1 LIMIT %s, %s", (i, i_limit), fetch="all")
            Methods.setting_set(f'{prefix}_last', iframes[cnt]['src'])
            Methods.log(f"{prefix.title()}Parser", "Зафиксировано обновление")
    finally:
        for root, dirs, files in os.walk(tmp_dir+"/parse", topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        Mysql.close()

def run():
    while True:
        if(datetime.now().minute % 10 == 0):
            try:
                parse(for_parse)
            except Exception as e:
                Methods.log("ERROR", e)
        sleep(60)

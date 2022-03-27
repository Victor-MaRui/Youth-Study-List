'''

youth_study_list.py
North_China_Electric_Power_University
SIE_EEE1902

Created by 马瑞 on 2021/10/18.
Copyright 2021年 马瑞. All rights reserved.

'''
import os
import time
import requests
import json
from PIL import Image
from io import BytesIO
d = os.path.dirname(__file__)
csv_path = os.path.join(d,"青年大学习未完成人员名单.csv")
img_path = os.path.join(d,'verify.png')
if os.name == 'posix':
    csv_path = '/www/wwwroot/siteRoot/youthStudy/青年大学习未完成人员名单.csv'
    img_path = '/www/wwwroot/siteRoot/youthStudy/verify.png'

def update_youthdata(s, account, password):#更新团员数据
    print("开始更新团员数据...")
    youthdata = {}
    classinfo = {}
    print("尝试获取团组织ID...")
    res = eval(s.get("https://bgapi.54heb.com/organization/getOrganizeMess").text)
    if res["msg"] != "success":
        print("需要登录。")
        verify = verify_failure(s, account, password)
        while verify:
            print("验证码错误。")
            verify = verify_failure(s, account, password)
        print("尝试获取团组织ID...")
        res = eval(s.get("https://bgapi.54heb.com/organization/getOrganizeMess").text)
    oid = str(res['data']['id'])
    print("尝试获取团支部人数...")
    res = eval(s.get("https://bgapi.54heb.com/work/getOrgMember?oid={}&page=1&rows=15&type=1".format(oid)).text)["data"]["data"]
    for item in res:
        classinfo[item["name"]]={"count":item["count"]}
        print("{}：{}人".format(item["name"],item["count"]))
    print("获取团支部人数成功！\n尝试获取团支部ID...")
    res = s.get("https://bgapi.54heb.com/young/getotherlists?type=4&id={}".format(oid)).text
    res = eval(res.replace("true","True").replace("false","False"))["data"]
    for item in res:
        classinfo[item["name"]]["id"]=str(item["id"])
        print("{}ID:{}".format(item["name"],str(item["id"])))
    print("获取团支部ID成功！\n尝试获取团员数据...")
    for info in classinfo:
        print("正在获取{}团员数据...".format(info))
        res = s.get("https://bgapi.54heb.com/regiment?page=1&rows={}&keyword=&oid={}&leagueStatus=&goHomeStatus=&memberCardStatus=&isPartyMember=&age_type=&ageOption=&isAll=&keywords=".format(classinfo[info]["count"],classinfo[info]["id"])).text.replace("null","None").replace("false","False")
        datalist = eval(res)["data"]["data"]
        youthdata[info] = []
        memcount = 0
        for data in datalist:
            youthdata[info].append(data)
            memcount += 1
            print("{}：{}".format(info,data["realname"]))
        youthdata[info].append(memcount)
        print("获取{}数据成功，共{:d}名团员！".format(info, memcount))
    classinfo.clear()
    print("团员数据获取成功！")
    return youthdata

def verify_failure(s, account, password):#登录冀e青春
    print("正在获取验证码...")
    res = s.get("https://bgapi.54heb.com/login/verify").content
    img = Image.open(BytesIO(res))
    img.save(img_path,'png')
    if os.name == "nt": img.show()
    else: print(img_path)
    verifypass = input("请输入验证码：\n")
    params = {"account":account,"pass":password,"verify":verifypass,"is_quick":0}
    print("登陆中...")
    res = eval(s.post("https://bgapi.54heb.com/admin/login",data=params).text)
    if res["msg"] == "success":
        s.headers.update({'token': res["data"][0]["token"]})
        print("登陆成功！")
        cookies = requests.utils.dict_from_cookiejar(s.cookies)
        headers = dict(s.headers)
        with open(os.path.join(d,"cookies.txt"), "w", encoding="utf-8") as f:
            f.writelines([json.dumps(cookies) + '\n',json.dumps(headers)])
            f.close()
        return False
    else:
        return True

def show_dnStudy(mebdata):
    dnStudy = []
    studySum = []
    tdfcount = 0
    tcscount = 0
    for branch in mebdata.keys():
        if True in tuple(map(lambda x: x in branch, stop_words)): continue
        ldStatus = '已完成'
        cscount = mebdata[branch][-1]
        tcscount += cscount
        bhData = list(filter(lambda x:x["isStudy"]=="否", mebdata[branch][:-1]))
        dfcount = cscount - len(bhData)
        tdfcount += dfcount
        try:
            cpRatio = float(dfcount)/float(cscount)*100
        except:
            cpRatio = 0
        for data in bhData:
            if data["realname"] in ldList: ldStatus = '未完成'
            dnStudy.append("{},{}".format(branch, data["realname"]))
        studySum.append("{}完成人数{:d}/{:d}，比例{:.2f}%，团支书{}。".format(branch, dfcount, cscount, cpRatio, ldStatus))
    print("\n\n\n青年大学习未完成名单\n"+'\n'.join(dnStudy)+'\n\n总览\n'+'\n'.join(studySum))
    print("当前组织总完成人数{:d}/{:d}，比例{:.2f}%。\n\n".format(tdfcount, tcscount, float(tdfcount)/float(tcscount)*100))

def save_dnStudy(mebdata):
    dnStudy = []
    for branch in mebdata.keys():
        if True in tuple(map(lambda x: x in branch, stop_words)): continue
        bhData = list(filter(lambda x:x["isStudy"]=="否", mebdata[branch][:-1]))
        for data in bhData:
            dnStudy.append("{},{}\n".format(branch, data["realname"]))
    title = input("请输入本期青年大学习期数\n")
    dnStudy.insert(0, "班级,姓名\n")
    dnStudy.insert(0, title+'\n')
    try:
        with open(csv_path, 'r', encoding="utf-8") as f:
            fileData = f.readlines()
            for i in range(max(len(fileData),len(dnStudy))):
                if i == 0:
                    if fileData[i] == '\ufeff':
                        dnStudy[i] = fileData[i] + dnStudy[i]
                        continue
                    try:
                        dnStudy[i] = fileData[i].replace('\n',',,'+dnStudy[i])
                    except:
                        dnStudy[0] = '\ufeff' + dnStudy[0]
                elif i < min(len(fileData),len(dnStudy)):
                    dnStudy[i] = fileData[i].replace('\n',','*(dnStudy[0].count(',')-fileData[i].count(','))+dnStudy[i])
                elif len(dnStudy) < len(fileData):
                    dnStudy.append(fileData[i])
                else:
                    dnStudy[i] = ','*dnStudy[0].count(',')+dnStudy[i]
    except:
        print('File not found, creating...')
    with open(csv_path, 'w', encoding="utf-8") as f:
        f.writelines(dnStudy)
    print("储存完成！\n已储存到{}\n".format(csv_path))

def save_youthdata(memdata):
    with open(os.path.join(d,"youthdata.txt"), "w", encoding="utf-8") as f:
            f.writelines([json.dumps(memdata)])
            f.close()
    print("储存完成！\n已储存到{}\n".format(os.path.join(d,"youthdata.txt")))

def getmtime(flag=False):
    try:
        data_time = os.path.getmtime(os.path.join(d,"youthdata.txt"))
        diff_time = round(time.time() - data_time)
    except:
        diff_time = 0
    m_tm, s_tm = divmod(diff_time, 60)
    h_tm, m_tm = divmod(m_tm, 60)
    d_tm, h_tm = divmod(h_tm, 24)
    if flag:
        print("\n团员资料已加载！\n上次于UTC {}，\n{:d}天{:d}时{:d}分{:d}秒前更新。\n".format(time.strftime("%Y-%m-%d %H:%M:%S",time.gmtime(data_time)),d_tm, h_tm, m_tm, s_tm))
        if diff_time > 86400: 
            uc = input("距离上次更新已超过一天，是否更新？(y/n)\n")
            if uc.lower() == 'n': pass
            else: raise Exception("数据需更新")
    else: print("\n上次于UTC {}，\n{:d}天{:d}时{:d}分{:d}秒前更新。\n\n".format(time.strftime("%Y-%m-%d %H:%M:%S",time.gmtime(data_time)),d_tm, h_tm, m_tm, s_tm))
    
def load_youthdata(s, account, password):
    try:
        with open(os.path.join(d,"youthdata.txt"), encoding="utf-8") as f:
            youthdata = json.loads(f.read())
            getmtime(True)
    except:
        youthdata = update_youthdata(s, account, password)
    return youthdata

def load_headers(s):
    try:
        with open(os.path.join(d,"cookies.txt"), encoding="utf-8") as f:
            header_ls = f.readlines()
            load_cookies = json.loads(header_ls[0].replace('\n',''))
            load_headers = json.loads(header_ls[1])
            f.close()
        s.cookies = requests.utils.cookiejar_from_dict(load_cookies)
        s.headers.update(load_headers)
        print("Cookies successfully loaded!")
    except:
        print("Failed to load cookies.")
        s.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36 Edg/94.0.992.47"})
        s.get("https://bghb.54heb.com")

def change_ldList(account, password):
    ldList = input("请输入各班团支书姓名(空格分隔)\n").split()
    with open(os.path.join(d,"profile.txt"), 'w', encoding="utf-8") as f:
        f.writelines([account+'\n', password+'\n', ' '.join(ldList)])
    print("团支书名单储存成功！")
    return ldList

def change_stopwords():
    return input("请输入忽略词(空格分隔)\n").split()
'''
def encode_str(str):
    return list(map(ord, str.encode('unicode-escape').decode('utf-8')))

def decode_str(ls):
    str = ''.join(list(map(chr, ls)))
    return str.encode().decode('unicode-escape')
'''
print('冀e青春青年大学习信息统计工具\n\nCreated by 马瑞 of NCEPU_SIE on 2021/10/18.\nCopyright 2021年 马瑞. All rights reserved.\n\n\n')
menu_des = ['输出未完成青年大学习人员名单','储存团员数据','重新加载团员数据','更新团员数据','查看更新数据时间','储存未完成名单至csv','更改团支书名单','更改忽略词','退出']
menu = ['show_dnStudy(youthdata)','save_youthdata(youthdata)','youthdata = load_youthdata(s, account, password)','youthdata = update_youthdata(s, account, password)','getmtime(False)','save_dnStudy(youthdata)','ldList = change_ldList(account, password)','stop_words = change_stopwords()','loop = False']
if len(menu_des) != len(menu): raise Exception("Menu length error")
s = requests.session()
try:
    with open(os.path.join(d,"profile.txt"), encoding="utf-8") as f:
        prof = f.readlines()
        account = prof[0].replace('\n','')
        password = prof[1].replace('\n','')
        ldList = prof[2].split()
        f.close()
    print("当前账户为{}".format(account))
    load_headers(s)
    youthdata = load_youthdata(s, account, password)
except:
    print("Failed to load profile.")
    while True:
        try:
            prof = input("请输入冀e青春账户密码(空格分隔)\n")
            account, password = prof.split()
            s.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36 Edg/94.0.992.47"})
            s.get("https://bghb.54heb.com")
            youthdata = update_youthdata(s, account, password)
            ldList = input("请输入各班团支书姓名(空格分隔)\n仅用于确认团支书完成情况，如无需要可不填\n").split()
            break
        except:
            continue
    with open(os.path.join(d,"profile.txt"), 'w', encoding="utf-8") as f:
        f.writelines([account+'\n', password+'\n', ' '.join(ldList)])
    print("Profile saved.")
stop_words = []
loop = True
while loop:
    print("\n\n选项菜单：\n")
    for i in range(len(menu_des)):
        print('{:d}:{}'.format(i, menu_des[i]))
    userInput = input('\n请输入选项序号\n')
    try:
        exec(menu[eval(userInput)])
    except:
        print("输入错误")
        pass
print("清理文件...")
youthdata.clear()
s.close()

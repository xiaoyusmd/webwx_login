# -*- coding:utf-8 -*-

import os
import re
import time
import sys
import subprocess
import requests
import xml.dom.minidom
import json


class WebwxLogin(object):
    def __init__(self):
        self.session = requests.session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 5.1; rv:33.0) Gecko/20100101 Firefox/33.0'}
        self.QRImgPath = os.path.split(os.path.realpath(__file__))[0] + os.sep + 'webWeixinQr.jpg'
        self.uuid = ''
        self.tip = 0
        self.base_uri = ''
        self.redirect_uri = ''
        self.skey = ''
        self.wxsid = ''
        self.wxuin = ''
        self.pass_ticket = ''
        self.deviceId = 'e000000000000000'
        self.BaseRequest = {}
        self.ContactList = []
        self.My = []
        self.SyncKey = ''

    def getUUID(self):

        url = 'https://login.weixin.qq.com/jslogin'
        params = {
            'appid': 'wx782c26e4c19acffb',
            'redirect_uri': 'https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxnewloginpage',
            'fun': 'new',
            'lang': 'zh_CN',
            '_': int(time.time() * 1000),  # 时间戳
        }

        response = self.session.get(url, params=params)
        target = response.content.decode('utf-8')

        pattern = r'window.QRLogin.code = (\d+); window.QRLogin.uuid = "(\S+?)"'
        ob = re.search(pattern, target)  # 正则提取uuid

        code = ob.group(1)
        self.uuid = ob.group(2)

        if code == '200':  # 判断请求是否成功
            return True

        return False

    def showQRImage(self):

        url = 'https://login.weixin.qq.com/qrcode/' + self.uuid
        response = self.session.get(url)

        self.tip = 1

        with open(self.QRImgPath, 'wb') as f:
            f.write(response.content)
            f.close()
        # 打开二维码
        if sys.platform.find('darwin') >= 0:
            subprocess.call(['open', self.QRImgPath])  # 苹果系统
        elif sys.platform.find('linux') >= 0:
            subprocess.call(['xdg-open', self.QRImgPath])  # linux系统
        else:
            os.startfile(self.QRImgPath)  # windows系统

        print('请使用微信扫描二维码登录')

    def checkLogin(self):

        url = 'https://login.weixin.qq.com/cgi-bin/mmwebwx-bin/login?tip=%s&uuid=%s&_=%s' % (
            self.tip, self.uuid, int(time.time()*1000))

        response = self.session.get(url)
        target = response.content.decode('utf-8')

        pattern = r'window.code=(\d+);'
        ob = re.search(pattern, target)
        code = ob.group(1)

        if code == '201':  # 已扫描
            print('成功扫描,请在手机上点击确认登录')
            self.tip = 0
        elif code == '200':  # 已登录
            print('正在登录中...')
            regx = r'window.redirect_uri="(\S+?)";'
            ob = re.search(regx, target)
            self.redirect_uri = ob.group(1) + '&fun=new'
            self.base_uri = self.redirect_uri[:self.redirect_uri.rfind('/')]
        elif code == '408':  # 超时
            pass

        return code

    def login(self):

        response = self.session.get(self.redirect_uri, verify=False)
        data = response.content.decode('utf-8')

        doc = xml.dom.minidom.parseString(data)
        root = doc.documentElement
        # 提取响应中的参数
        for node in root.childNodes:
            if node.nodeName == 'skey':
                self.skey = node.childNodes[0].data
            elif node.nodeName == 'wxsid':
                self.wxsid = node.childNodes[0].data
            elif node.nodeName == 'wxuin':
                self.wxuin = node.childNodes[0].data
            elif node.nodeName == 'pass_ticket':
                self.pass_ticket = node.childNodes[0].data

        if not all((self.skey, self.wxsid, self.wxuin, self.pass_ticket)):
            return False

        self.BaseRequest = {
            'Uin': int(self.wxuin),
            'Sid': self.wxsid,
            'Skey': self.skey,
            'DeviceID': self.deviceId,
        }

        return True

    def webwxinit(self):

        url = self.base_uri + \
              '/webwxinit?pass_ticket=%s&skey=%s&r=%s' % (
                  self.pass_ticket, self.skey, int(time.time()*1000))
        params = {
            'BaseRequest': self.BaseRequest
        }

        h = self.headers
        h['ContentType'] = 'application/json; charset=UTF-8'
        response = self.session.post(url, data=json.dumps(params), headers=h, verify=False)
        data = response.content.decode('utf-8')
        print(data)

        dic = json.loads(data)
        self.ContactList = dic['ContactList']
        self.My = dic['User']

        SyncKeyList = []
        for item in dic['SyncKey']['List']:
            SyncKeyList.append('%s_%s' % (item['Key'], item['Val']))
        self.SyncKey = '|'.join(SyncKeyList)

        ErrMsg = dic['BaseResponse']['ErrMsg']

        Ret = dic['BaseResponse']['Ret']
        if Ret != 0:
            return False

        return True

    def webwxgetcontact(self):

        url = self.base_uri + \
              '/webwxgetcontact?pass_ticket=%s&skey=%s&r=%s' % (
                  self.pass_ticket, self.skey, int(time.time()))

        h = self.headers
        h['ContentType'] = 'application/json; charset=UTF-8'
        response = self.session.get(url, headers=h, verify=False)
        data = response.content.decode('utf-8')
        # print(data)

        dic = json.loads(data)
        MemberList = dic['MemberList']

        # 倒序遍历,不然删除的时候出问题..
        SpecialUsers = ["newsapp", "fmessage", "filehelper", "weibo", "qqmail", "tmessage", "qmessage", "qqsync",
                        "floatbottle", "lbsapp", "shakeapp", "medianote", "qqfriend", "readerapp", "blogapp",
                        "facebookapp", "masssendapp",
                        "meishiapp", "feedsapp", "voip", "blogappweixin", "weixin", "brandsessionholder",
                        "weixinreminder", "wxid_novlwrv3lqwv11", "gh_22b87fa7cb3c", "officialaccounts",
                        "notification_messages", "wxitil", "userexperience_alarm"]
        for i in range(len(MemberList) - 1, -1, -1):
            Member = MemberList[i]
            if Member['VerifyFlag'] & 8 != 0:  # 公众号/服务号
                MemberList.remove(Member)
            elif Member['UserName'] in SpecialUsers:  # 特殊账号
                MemberList.remove(Member)
            elif Member['UserName'].find('@@') != -1:  # 群聊
                MemberList.remove(Member)
            elif Member['UserName'] == self.My['UserName']:  # 自己
                MemberList.remove(Member)

        return MemberList

    def main(self):

        if not self.getUUID():
            print('获取uuid失败')
            return

        self.showQRImage()
        time.sleep(1)

        while self.checkLogin() != '200':
            pass

        os.remove(self.QRImgPath)

        if not self.login():
            print('登录失败')
            return
        # 登录完成, 下面查询好友
        if not self.webwxinit():
            print('初始化失败')
            return

        MemberList = self.webwxgetcontact()

        print('通讯录共%s位好友' % len(MemberList))

        for x in MemberList:
            sex = '未知' if x['Sex'] == 0 else '男' if x['Sex'] == 1 else '女'
            print('昵称:%s, 性别:%s, 备注:%s, 签名:%s' % (x['NickName'], sex, x['RemarkName'], x['Signature']))


if __name__ == '__main__':
    print('开始')
    wx = WebwxLogin()
    wx.main()


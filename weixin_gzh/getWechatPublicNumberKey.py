# 获取微信公众号的后台唯一标识key
from weixin_gzh.setting import *
import pymysql
import random
import requests
from urllib.parse import urlencode
import time

class vxPublicSpider(object):

    def __init__(self):
        self.db = self.db = pymysql.connect(host, user, password, DB, post)
        self.cursor = self.db.cursor()

    def startSpider(self,vxNumber):
        if not vxNumber:
            self.logMsg("请输入微信公众号")
            return
        if self.fakeidRequest(vxNumber):
            self.logMsg("获取成功，请到数据库查看")
        else:
            self.logMsg("获取失败，请查看日志")

    def fakeidRequest(self, weChatNumber, exact=True):

        # 通过网络请求获取fakeid
        headers = {

            'accept': 'application/json, text/javascript, */*; q=0.01',
            'accept-encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'Connection': 'keep-alive',
            'Host': 'mp.weixin.qq.com',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36',
            'X-Requested-With': 'XMLHttpRequest',
            'cookie': fakeidCooke

        }
        parameters = {
            'action': 'search_biz',
            'token': token,  # 微信公众平台页面获取
            'lang': 'zh_CN',
            'f': 'json',
            'ajax': '1',
            'random': random.random(),
            'query': weChatNumber,
            'begin': 0,  # 下一页计算记录开始行,返回列表里面有total：表示总共搜索到的记录
            'count': 5,
        }
        url = 'https://mp.weixin.qq.com/cgi-bin/searchbiz?'
        startUrl = url + urlencode(parameters)
        try:
            responce = requests.get(startUrl, headers=headers, verify=False)
        except Exception as e:
            self.logMsg(err="抓取后台唯一标识ID失败：" + str(e))
            return None

        if responce.status_code == 200:
            resData = responce.json()
            if resData.get('list'):
                total = resData.get('total')
                # 精确获取
                if exact:
                    for data in resData.get('list'):
                        # 查询该公众号是否存在
                        fakeid = data.get("fakeid")
                        nickname = data.get("nickname")
                        alias = data.get("alias")
                        service_type = data.get("service_type")
                        sql = "SELECT * FROM accountnews  WHERE fakeid = '%s'" % (fakeid)
                        self.cursor.execute(sql)
                        results = self.cursor.fetchall()
                        if results:
                            self.logMsg(info=nickname + " 数据库中已存在")
                            continue
                        else:
                            sql = "INSERT INTO accountnews (fakeid,nickname,alias,service_type) VALUES ('%s','%s','%s','%s')" % (
                                fakeid, nickname, alias, service_type)
                            try:
                                self.cursor.execute(sql)
                                self.db.commit()
                                self.logMsg(info=fakeid + " , " + nickname + " 数据库备份成功")
                            except Exception as e:
                                self.db.rollback()
                                self.logMsg(err=fakeid + " , " + nickname + " 数据库备份失败。数据库操作异常，错误详情：" + str(e))
                                return None
                    return resData.get('list')
                else:
                    return None
            else:
                self.logMsg(err="数据获取失败，status_codes:" + str(responce.status_code) + " 请检查是否cooke等相关信息过期")
                return None

    def logMsg(self,err='',info=''):
        if not err and not info:
            return
        now = int(time.time())
        timeArray = time.localtime(now)
        otherStyleTime = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
        if err:
            print(otherStyleTime+":[ERRORLOF]"+err)
        else:
            print(otherStyleTime + ":" + info)

if __name__=="__main__":

    spider=vxPublicSpider()

    spider.startSpider('test347857')
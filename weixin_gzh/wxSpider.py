# 爬取微信公众号文章，阅读量，点赞数，评论量，前100评论，及评论点赞数
from weixin_gzh.setting import *
import pymysql
import random
import requests
import time
import re
import datetime
import json
from urllib.parse import urlencode
class wxSpider(object):

    # 参数初始化
    def __init__(self):
        self.db=self.db = pymysql.connect(host, user, password, DB, post)
        self.cursor = self.db.cursor()

    # 爬虫开始
    def startSpider(self,weChatNumber):
        if not weChatNumber:
            self.logMsg( err = "请输入需要爬取的公众号ID")
            return

        # 获取公众号后台唯一标识的id
        fakeId = self.getWechatIdByNumber(weChatNumber)

        if not fakeId:
            self.logMsg( err = "公众号 "+weChatNumber+" 无法识别，请确认")
            return

        # 获取标识性变量
        appmsg_token = self.argumentGet(fakeId)

        if not appmsg_token:
            return

        # 获取文章
        self.articleAppSpider(fakeId,appmsg_token)

    # 参数变量获取(appmsg_token,key)
    def argumentGet(self,fakeId):
        url = 'https://mp.weixin.qq.com/mp/profile_ext?'

        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,image/wxpic,image/sharpp,image/apng,image/tpg,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,en-US;q=0.9',
            'User-Agent': userAgent,
            'Cookie': appCookies,
            'Host': 'mp.weixin.qq.com',
            'Connection': 'keep-alive',
        }

        paramaters = {
            '__biz': fakeId,
            'a8scene': '3',
            'action': 'home',
            'bizpsid': '0',
            'devicetype': 'android-27',
            'lang': 'zh_CN',
            'nettype': 'WIFI',
            'pass_ticket': passTicket,
            'scene': '126',
            'version': '2700043c',
        }
        startUrl = url + urlencode(paramaters)
        try:
            responce = requests.get(startUrl, headers=headers, verify=False)

            if responce.status_code == 200:
                responcetEXT = responce.text
                data={}
                pattern1 = re.compile('window.appmsg_token = "(.*)";')  # 截取<td>与</td>之间第一个数为数字的内容
                results = re.findall(pattern1, responcetEXT)
                if results:
                    appmsg_token = results[0]
                    return appmsg_token
                else:
                    self.logMsg(err="appmsg_token参数获取失败" )
                    return None
            else:
                self.logMsg(err="appmsg_token参数请求返回信息异常,status_code:" + str(responce.status_code))
                return None

        except Exception as e:
            self.logMsg(err="appmsg_token 参数请求访问异常，异常详情："+str(e))
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

    # 微信号下的文章爬取(根据app爬取)
    def articleAppSpider(self,fakeId,appmsg_token,totalNum = 1):
        headers = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,en-US;q=0.9',
            'User-Agent': userAgent,
            'X-Requested-With': 'XMLHttpRequest',
            'Connection': 'keep-alive',
            'Host': 'mp.weixin.qq.com',
            'cookie': appCookies
        }
        parameters = {
            'action': 'getmsg',
            '__biz': fakeId,
            'f': 'json',
            'offset': 0,
            'count': 10,
            'is_ok': 1,
            'scene': 126,
            'uin': '777',
            'key': '777',
            'pass_ticket': passTicket,
            'wxtoken': '',
            'appmsg_token': appmsg_token,
            'x5': 1,
            'f': 'json',
        }

        loopNum = 0

        while True:
            if loopNum >= totalNum:
                break

            time.sleep(random.randrange(5,10))
            loopNum = loopNum * 10
            parameters['offset'] = loopNum
            url = 'https://mp.weixin.qq.com/mp/profile_ext?'
            startUrl = url + urlencode(parameters)

            loopNum+=1
            try:
                responce = requests.get(startUrl, headers=headers,proxies = self.ipProxiesGet(), verify=False)

                if responce.status_code == 200:
                    responceData = responce.json()
                    if responceData.get("general_msg_list"):

                        dictinfo = json.loads( responceData.get("general_msg_list") )
                        # 文章发布时间
                        for da in dictinfo.get("list"):
                            update_time = self.dateChange(da.get('comm_msg_info').get("datetime"))
                            news = da.get('app_msg_ext_info')

                            title = news.get('title')
                            digest = news.get('digest')
                            link = news.get('content_url')
                            appmsgid = ''
                            pattern1 = re.compile('mid=(.*?)&')  # 截取<td>与</td>之间第一个数为数字的内容
                            results = re.findall(pattern1, link)
                            if results:
                                appmsgid = results[0]

                            itemidx = ''
                            pattern1 = re.compile('idx=(.*?)&')  # 截取<td>与</td>之间第一个数为数字的内容
                            results = re.findall(pattern1, link)
                            if results:
                                itemidx = results[0]
                            aid = str(appmsgid)+'_'+str(itemidx)
                            # 内容保存
                            sql = "SELECT * FROM articlenews  WHERE aid = '%s'" % (aid)
                            self.cursor.execute(sql)
                            results = self.cursor.fetchall()
                            if not results:

                                # 文章不存在需要保存到数据库
                                sql = "INSERT INTO articlenews (fakeid,appmsgid,aid,itemidx,title,digest,update_time,link) VALUES " \
                                      "('%s','%s','%s','%s','%s','%s','%s','%s')" \
                                      % (fakeId, appmsgid, aid, itemidx, title, digest, update_time, link)

                                try:
                                    self.cursor.execute(sql)
                                    self.db.commit()
                                    self.logMsg(info="文章：" + title + " 保存成功")
                                except Exception as e:
                                    self.db.rollback()
                                    self.logMsg(err="文章保存失败：" + title + "。 数据库操作异常，错误详情：" + str(e))
                                    # 保存失败的文章不需要再去取阅读量等其它信息
                                    return None

                            # 获取所需的隐藏信息
                            hiddenData =  self.getHiddenVariable(link)

                            if not hiddenData:
                                return
                            # 流程正常的文章记录，获取阅读量信息
                            if hiddenData.get('req_id'):
                                self.getReadandLike(link,fakeId,hiddenData.get('req_id'),appmsg_token)

                            #流程正常的评论信息抓取
                            if hiddenData.get('comment_id') and not hiddenData.get('comment_id') == "0" :
                                self.getComment(fakeId,appmsgid,hiddenData.get('comment_id'),itemidx,appmsg_token)

                            # 检查是否有其它文章
                            if news.get('multi_app_msg_item_list'):
                                for itemData in news.get('multi_app_msg_item_list'):
                                    title = itemData.get('title')
                                    digest = itemData.get('digest')
                                    link = itemData.get('content_url')
                                    appmsgid = ''
                                    pattern1 = re.compile('mid=(.*?)&')  # 截取<td>与</td>之间第一个数为数字的内容
                                    results = re.findall(pattern1, link)
                                    if results:
                                        appmsgid = results[0]

                                    itemidx = ''
                                    pattern1 = re.compile('idx=(.*?)&')  # 截取<td>与</td>之间第一个数为数字的内容
                                    results = re.findall(pattern1, link)
                                    if results:
                                        itemidx = results[0]
                                    aid = str(appmsgid) + '_' + str(itemidx)
                                    # 内容保存
                                    sql = "SELECT * FROM articlenews  WHERE aid = '%s'" % (aid)
                                    self.cursor.execute(sql)
                                    results = self.cursor.fetchall()
                                    if not results:

                                        # 文章不存在需要保存到数据库
                                        sql = "INSERT INTO articlenews (fakeid,appmsgid,aid,itemidx,title,digest,update_time,link) VALUES " \
                                              "('%s','%s','%s','%s','%s','%s','%s','%s')" \
                                              % (fakeId, appmsgid, aid, itemidx, title, digest, update_time, link)

                                        try:
                                            self.cursor.execute(sql)
                                            self.db.commit()
                                            self.logMsg(info="文章：" + title + " 保存成功")
                                        except Exception as e:
                                            self.db.rollback()
                                            self.logMsg(err="文章保存失败：" + title + "。 数据库操作异常，错误详情：" + str(e))
                                            # 保存失败的文章不需要再去取阅读量等其它信息
                                            return None

                                    # 获取所需的隐藏信息
                                    hiddenData = self.getHiddenVariable(link)

                                    if not hiddenData:
                                        return
                                    # 流程正常的文章记录，获取阅读量信息
                                    if hiddenData.get('req_id'):
                                        self.getReadandLike(link, fakeId, hiddenData.get('req_id'), appmsg_token)

                                    # 流程正常的评论信息抓取
                                    if hiddenData.get('comment_id'):
                                        self.getComment(fakeId, appmsgid, hiddenData.get('comment_id'), itemidx,appmsg_token)


                    else:
                        self.logMsg(err="文章获取失败" )
                        return None
                else:
                    self.logMsg(err="文章请求返回信息异常，：status_code" + str(responce.status_code))
                    return None

            except Exception as e:
                self.logMsg(err="文章请求访问异常，异常详情："+str(e))
                return None

    # 微信号下的文章爬取(根据微信公众平台爬取)
    def articleSpider(self,fakeId,totalNum = 1):

        headers = {
            'accept': 'application/json, text/javascript, */*; q=0.01',
            'accept-encoding': 'gzip, deflate, br',
            'accept-language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
            'Connection': 'keep-alive',
            'x-requested-with': 'XMLHttpRequest',
            'Host': 'mp.weixin.qq.com',
            'user-agent': userAgent,
            'cookie': fakeidCooke
        }
        parameters = {
            'token': token,
            'lang': 'zh_CN',
            'f': 'json',
            'ajax': '1',
            'random':random.random(),
            'action': 'list_ex',
            'begin': 0,
            'count': 5,
            'query': '',
            'fakeid': fakeId,
            'type': 9,
        }
        loopNum = 0
        articleNum = 0

        while True:
            if loopNum >= ( totalNum ):
                break
            time.sleep(random.randrange(5,10))

            parameters['begin'] = loopNum * 5

            loopNum+=1

            url = "https://mp.weixin.qq.com/cgi-bin/appmsg?"
            startUrl = url + urlencode(parameters)
            try:
                responce = requests.get(startUrl, headers=headers,proxies = self.ipProxiesGet(), verify=False)

                if responce.status_code == 200:
                    resData = responce.json()
                    totalArticle = resData.get("app_msg_cnt")

                    for data in resData.get('app_msg_list'):
                        #记录爬取的数量，与总数量对比，超过则跳出循环
                        articleNum+=1
                        aid = data.get("aid")     #文章详细ID
                        title = data.get("title") #文章标题
                        link = data.get("link")   #文章链接
                        appmsgid = data.get("appmsgid") #文章ID
                        itemidx = data.get("itemidx")   #文章明细ID
                        update_time = self.dateChange(data.get("update_time")) #文章创建时间
                        digest = data.get("digest")    #二级标题

                        sql = "SELECT * FROM articlenews  WHERE aid = '%s'" % (aid)
                        self.cursor.execute(sql)
                        results = self.cursor.fetchall()

                        if not results:

                            # 文章不存在需要保存到数据库
                            sql = "INSERT INTO articlenews (fakeid,appmsgid,aid,itemidx,title,digest,update_time,link) VALUES " \
                                  "('%s','%s','%s','%s','%s','%s','%s','%s')" \
                                  % (fakeId, appmsgid, aid, itemidx, title, digest, update_time,link)

                            try:
                                self.cursor.execute(sql)
                                self.db.commit()
                                self.logMsg( info = "文章：" + title + " 保存成功")
                            except Exception as e:
                                self.db.rollback()
                                self.logMsg(err = "文章保存失败："+title+"。 数据库操作异常，错误详情：" + str(e))
                                # 保存失败的文章不需要再去取阅读量等其它信息
                                continue

                        # 获取所需的隐藏信息
                        hiddenData =  self.getHiddenVariable(link)

                        if not hiddenData:
                            return
                        # 流程正常的文章记录，获取阅读量信息
                        if hiddenData.get('req_id'):
                            self.getReadandLike(link,fakeId,hiddenData.get('req_id'))

                        #流程正常的评论信息抓取
                        if hiddenData.get('comment_id'):
                            self.getComment(fakeId,appmsgid,hiddenData.get('comment_id'),itemidx)

                    if articleNum >= totalArticle:
                        break
                else:
                    self.logMsg(err="文章信息抓取失败，status_code："+str(responce.status_code)+"请检查cookie信息是过期")
                    return None

            except Exception as e:
                self.logMsg(err="文章信息抓取请求异常：" + str(e))
                return None

    def getHiddenVariable(self,link):
        time.sleep(random.randrange(5, 10))
        headers = {
            'User-Agent': userAgent
        }
        returnData={}
        try:
            responce = requests.get(link, headers=headers,proxies = self.ipProxiesGet(),verify=False)
            if responce.status_code == 200:
                allText = responce.text
                pattern1 = re.compile("req_id = '(.*?)';")  # 截取<td>与</td>之间第一个数为数字的内容
                results = re.findall(pattern1, responce.text)
                if results:
                    returnData["req_id"] = results[0]
                pattern1 = re.compile('comment_id = "(.*?)" \|\|')  # 截取<td>与</td>之间第一个数为数字的内容
                results = re.findall(pattern1, responce.text)
                if results:
                    returnData["comment_id"] = results[0]

                return returnData
            else:
                self.logMsg(err="文章隐藏信息抓取,返回状态码不对，status_code" + str(responce.status_code))
                return None
        except Exception as e:
            self.logMsg(err="文章隐藏信息抓取异常，异常信息："+str(e))
            return None

    # 时间格式转换
    def dateChange(self,dateTime=int(time.time())):

        timeArray = time.localtime(int(dateTime))
        otherStyleTime = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
        return str(otherStyleTime)

    #文章的阅读量抓取
    def getReadandLike(self,link,fakeId,req_id,appmsg_token = ''):

        if not req_id:
            return
        time.sleep(random.randrange(5, 10))
        # 获得mid,_biz,idx,sn 这几个在link中的信息
        pattern1 = re.compile("mid=(.*?)&")  # 截取<td>与</td>之间第一个数为数字的内容
        results = re.findall(pattern1, link)
        mid = ''
        if results:
            mid = results[0]  #文章id

        pattern1 = re.compile("idx=(.*?)&")  # 截取<td>与</td>之间第一个数为数字的内容
        results = re.findall(pattern1, link)
        idx = ''
        if results:
            idx = results[0]  # 文章明细id

        pattern1 = re.compile("sn=(.*?)&")  # 截取<td>与</td>之间第一个数为数字的内容
        results = re.findall(pattern1, link)
        sn = ''
        if results:
            sn = results[0]  #

        _biz = fakeId  #公众号id

        # fillder 中取得一些不变得信息
        pass_ticket = passTicket

        # 添加Cookie避免登陆操作，这里的"User-Agent"最好为手机浏览器的标识
        headers = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.8,en-us;q=0.6,en;q=0.5;q=0.4',
            'X-Requested-With': 'XMLHttpRequest',
            "User-Agent": userAgent,
            "Cookie": appCookies,
        }

        data = {
            "__biz": _biz,
            "appmsg_type": 9,
            "mid": mid,
            "sn": sn,
            "idx": idx,
            "scene": 38,
            "devicetype": 'Windows 10',
            "is_need_ticket": "1",
            "msg_daily_idx": "1",
            "is_only_read": "1",
            "req_id": req_id,
            "pass_ticket": pass_ticket,
            "is_temp_url": "0",
            "tmp_version": 1,
            "appmsg_like_type": 2,
        }
        paramKey = '777'
        uIn = '777'
        params = {
            'f': 'json',
            "uin": uIn,
            "key": paramKey,
            "pass_ticket": pass_ticket,
            "wxtoken": "777",
            "clientversion": "62060739",
            "appmsg_token": appmsg_token,
            "x5": 0,
        }

        # 目标url
        url = "http://mp.weixin.qq.com/mp/getappmsgext"
        # 使用post方法进行提交
        try:
            responce = requests.post(url, headers=headers, data=data,proxies = self.ipProxiesGet(), params=params)
        except Exception as e:
            self.logMsg( err="抓取阅读量的请求访问异常：" + str(e))
            return None

        if responce.status_code == 200:
            content = responce.json()
            if content.get("appmsgstat"):
                if content["appmsgstat"].get("read_num"):
                    readNum = int(content["appmsgstat"]["read_num"])
                else:
                    readNum = 0
                if content["appmsgstat"].get("like_num"):
                    likeNum = int(content["appmsgstat"]["like_num"])
                else:
                    likeNum = 0
                if content.get('comment_count'):
                    comment_num = int(content['comment_count'])
                else:
                    comment_num = 0

                read_add_num = 0
                like_add_num = 0
                comment_add_num = 0
                currentupdate= self.dateChange()
                berforeupdate= self.dateChange()

                aid = mid+'_'+idx
                # 保存阅读量和喜欢量
                sql = "SELECT read_num,like_num,comment_num,currentupdate FROM articlenews  WHERE aid = '%s'" % (aid)
                self.cursor.execute(sql)
                results = self.cursor.fetchall()
                for res in results:
                    if res[0]:
                        read_add_num = readNum - int(res[0])
                    else:
                        read_add_num = readNum - 0
                    if res[1]:
                        like_add_num = likeNum - int(res[1])
                    else:
                        ike_add_num = likeNum - 0
                    if res[2]:
                        comment_add_num = comment_num - int(res[2])
                    else:
                        comment_add_num = comment_num - 0
                    if res[3]:
                        berforeupdate = res[3]

                    break

                try:

                    sql = "UPDATE articlenews SET read_num = %d,read_add_num = %d,like_num = %d , like_add_num = %d,  comment_num = %d ,comment_add_num = %d, currentupdate = '%s', berforeupdate = '%s' WHERE aid = '%s' " % \
                          (readNum,read_add_num, likeNum,like_add_num,comment_num,comment_add_num, currentupdate,berforeupdate,aid)
                    self.cursor.execute(sql)
                    self.db.commit()
                    self.logMsg( info = mid + " 阅读信息保存成功")
                except Exception as e:
                    self.db.rollback()
                    self.logMsg( err = "阅读信息保存失败，数据库操作异常，详细信息：" + str(e))
                    return None
            else:
                self.logMsg( err ="阅读信息抓取失败:" +str(content))
                return  None
        else:
            self.logMsg( err ="抓取阅读信息状态码不对：" + str(responce.status_code))
            return None

    def getComment(self,fakeId,appmsgid,commentId,idx,appmsg_token=''):

        if not commentId:
            return
        time.sleep(random.randrange(5,10))
        headers = {
            'Host': 'mp.weixin.qq.com',
            'Connection': 'keep-alive',
            'Accept': '*/*',
            'CSP': 'active',
            'X-Requested-With': 'XMLHttpRequest',
            'Accept-Language': 'Accept-Language: zh-CN,zh;q=0.8,en-us;q=0.6,en;q=0.5;q=0.4',
            'accept-encoding': 'gzip, deflate',
            'User-Agent': userAgent,
            'cookie': appCookies
        }
        parameters = {
            'action': 'getcomment',
            'scene': 0,
            '__biz': fakeId,
            'appmsgid': appmsgid,
            'comment_id': commentId,
            'idx': idx,
            'offset': 0,
            'limit': 100,
            'uin':'777',
            'key':'777',
            'pass_ticket': passTicket,
            'wxtoken': '777',
            "devicetype": 'Windows 10',
            "clientversion": '62060739',
            'appmsg_token': appmsg_token,
            'x5': 0,
            'f': 'json',
        }

        url = 'https://mp.weixin.qq.com/mp/appmsg_comment?'
        startUrl = url + urlencode(parameters)
        try:
            responce = requests.get(startUrl, headers=headers,proxies = self.ipProxiesGet(), verify=False)

        except Exception as e:
            self.logMsg(err = "评论信息抓取异常，异常详情:" + str(e))
            return None

        if responce.status_code == 200:
            resData = responce.json()
            if resData.get('elected_comment'):
                for data in resData.get('elected_comment'):
                    content_id = data.get('content_id')  #评论ID
                    create_time = self.dateChange(int(data.get('create_time')))  #评论创建时间
                    nick_name = data.get('nick_name')
                    content = data.get('content')
                    if data.get('like_num'):
                        like_num = int(data.get('like_num'))
                    else:
                        like_num = 0
                    sql = "SELECT * FROM comment  WHERE appmsgid = '%s' and idx = '%s'and content_id = '%s'" % (
                        appmsgid, idx, content_id)
                    self.cursor.execute(sql)
                    results = self.cursor.fetchall()
                    if results:
                        #已存在更新点赞数
                        sql = "UPDATE comment SET like_num = %d WHERE appmsgid = '%s' and idx = '%s'and content_id = '%s'" % (like_num,appmsgid,idx,content_id)
                    else:
                        sql = "INSERT INTO comment (appmsgid,idx,nick_name,content_id,content,like_num) VALUES ('%s','%s','%s','%s','%s',%d)" % \
                              (appmsgid, idx, nick_name, content_id, content, like_num)
                    try:
                        self.cursor.execute(sql)
                        self.db.commit()
                        self.logMsg( info= content_id + " 评论信息存储成功")
                    except Exception as e:
                        self.db.rollback()
                        self.logMsg( err="评论信息存储失败，数据库操作异常，异常详情：" + str(e))
                        return None
            else:
                self.logMsg( err="评论信息抓取失败，返回信息："+str(resData))
                return None
        else:
            self.logMsg(err="评论信息抓取请求状态码不对，请检查cooke等信息，status_code：" + str(responce.status_code))
            return None

    def ipProxiesGet(self):

        try:
            return {}
        except Exception as e:

            return {}

    def getWechatIdByNumber(self,weChatNumber):

        # 第一去数据库查询是否有该微信号的记录
        sql = "SELECT fakeid FROM accountnews WHERE alias = '%s'" %(weChatNumber)
        self.cursor.execute(sql)
        result = self.cursor.fetchall()
        if result:
            # 取得成功,返回微信后台唯一标识ID
            mid = ''
            for res in result:
                mid = res[0]
                break
            if mid:
                return mid
            else:
                self.logMsg(err='公众号的唯一key标识不存在')
                return None
        else:
            self.logMsg(err='公众号信息不存在')

if __name__=="__main__":
    spider = wxSpider()
    spider.startSpider("wow36kr")
import base64
import time

import pymysql
import requests
import scrapy

import re

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

from zpepdi.items import ZpepdiItem, VolumeItem, VolumeIdItem, CheckerItem

chorme_options = Options()
chorme_options.add_argument("--headless")
chorme_options.add_argument("--disable-gpu")


class ProjectlistSpider(scrapy.Spider):
    proList = ''
    # 所有卷册列表
    volList = ''
    # 除尚未开展和正在设计状态外的所有卷册
    vol1List = ''
    # 用于页面中翻页
    volIndex = 1
    # 用于proList取值
    proIndex = 0
    # 用于volList取值
    vol = 0
    vol1 = 0
    name = 'projectList'
    allowed_domains = ['zmis.zepdi.com.cn']
    start_urls = ['http://zmis.zepdi.com.cn/Portal/EPMS/List/ProjectDesign/ProjectStartList.aspx?secid=87ddc819-a9a7'
                  '-4b2a-8c45-2dcfc2019342']

    def __init__(self):
        self.connect = pymysql.connect(host='localhost', user='root', passwd='7499', db='appraise', port=3306,
                                       charset='utf8', autocommit=True)
        self.cursor = self.connect.cursor()
        self.cursor.execute("SELECT * FROM project where spider=0")
        self.proList = self.cursor.fetchall()
        self.connect.commit()
        self.browser = webdriver.Chrome(chrome_options=chorme_options)
        self.browser.wait = WebDriverWait(self.browser, 5)  # wartet bis zu 5 sekunden
        super().__init__()

    # 整个爬虫结束后关闭浏览器
    def close(self, spider):
        self.browser.quit()

    def start_requests(self):
        # self.cursor.execute("SELECT * FROM volume")
        # self.volList = self.cursor.fetchall()
        # self.connect.commit()
        # yield scrapy.Request(
        #     url='http://zmis.zepdi.com.cn/Portal/EPMS/List/RollInfo/ContentMange.aspx?actionType'
        #         '=1&RollID=' + self.volList[self.vol][4],
        #     callback=self.parse)
        print("proList", self.proList)
        if self.proList[0][3]:
            yield scrapy.Request(url='http://zmis.zepdi.com.cn/Portal/EPMS/List/RollInfo/RollEntityBill.aspx?'
                                     'OrganizationId=' + self.proList[int(self.proIndex)][3] +
                                     '&secid=00000000-0000-0000-0000-000000000000&IsPortal=True',
                                 meta={'number': self.proList[0][1], "volIndex": self.volIndex}, dont_filter=True,
                                 callback=self.parse)
        else:
            url = 'http://zmis.zepdi.com.cn/Portal/EPMS/List/ProjectDesign/ProjectStartList.aspx?secid=87ddc819-a9a7' \
                  '-4b2a-8c45-2dcfc2019342'
            response = scrapy.Request(url,
                                      meta={'number': self.proList[int(self.proIndex)][1], "volIndex": self.volIndex},
                                      dont_filter=True, callback=self.parse)
            yield response

    def parse(self, response):
        projectID = ''
        filename = "zpepdi.html"
        open(filename, 'wb').write(response.body)
        print("*" * 80)
        print("url,url :")
        # open(filename, 'w').write(response.xpath("//*[@id='ctl00_listGrid_gridList']/tbody/tr"))
        # print("response text: %s" % response.text)
        # print("response headers: %s" % response.status)
        # print("response headers: %s" % response.cookies)
        # if response.cookies:
        #     self.myCookie = response.cookies
        # print("response meta: %s" % response.meta)
        # print("request headers: %s" % response.request.headers)
        if 'ProjectStartList' in response.url:
            item = ZpepdiItem()
            for box in response.xpath("//*[@id='ctl00_listGrid_gridList']/tbody/tr"):
                item['projectPhaseID'] = eval(re.findall(r'[(](.*?)[)]',
                                                         box.xpath('.//td[1]/a/img/@onclick').extract()[0].strip())[0])
                projectID = item['projectPhaseID']
                item['number'] = box.xpath('.//td[2]/text()').extract()[0].strip()
                item['name'] = box.xpath('.//td[3]/a/text()').extract()[0].strip()
                item['stage'] = box.xpath('.//td[4]/text()').extract()[0].strip()
                item['director'] = box.xpath('.//td[5]/text()').extract()[0].strip()
                item['type'] = box.xpath('.//td[8]/text()').extract()[0].strip()
                item['general'] = box.xpath('.//td[9]/text()').extract()[0].strip()
                item['date'] = box.xpath('.//td[10]/text()').extract()[0].strip()
                item['state'] = box.xpath('.//td[14]/text()').extract()[0].strip()
                yield item
                time.sleep(1)
                yield scrapy.Request(url='http://zmis.zepdi.com.cn/Portal/EPMS/List/RollInfo/RollEntityBill.aspx'
                                         '?OrganizationId=' + projectID + '&secid=00000000-0000-0000-0000-000000000000'
                                                                          '&IsPortal=True',
                                     meta={"volIndex": self.volIndex},
                                     dont_filter=True,
                                     callback=self.parse)
        elif 'RollEntityBill' in response.url:
            index = response.xpath('//*[@id="ctl00_listGrid_pdgRollList"]/tfoot/tr/td/text()[2]').extract()[0].strip()
            self.volIndex = index[index.rfind('第') + 1:index.rfind('/')]
            indexSum = index[index.rfind('/') + 1:index.rfind('页')]
            print("index:", index)
            print("index:", self.volIndex)
            print("index", indexSum)
            item = VolumeIdItem()
            for box in response.xpath("//*[@id='ctl00_listGrid_pdgRollList']/tbody/tr"):
                item['proID'] = self.proList[int(self.proIndex)][0]
                item['rollID'] = eval(re.findall(r'[(](.*?)[)]',
                                                 box.xpath('.//td[1]/a/@onclick').extract()[0].strip())[0])[1]
                item['number'] = box.xpath('.//td[3]/text()').extract()[0].strip()
                yield item
            print("self.volIndex < indexSum:", int(self.volIndex) < int(indexSum))
            if int(self.volIndex) < int(indexSum):
                self.volIndex = int(self.volIndex) + int(1)
                yield scrapy.Request(url=response.url,
                                     meta={"volIndex": self.volIndex},
                                     dont_filter=True,
                                     callback=self.parse)
            else:
                if self.proIndex < len(self.proList) - 1:
                    self.volIndex = 0
                    self.proIndex = int(self.proIndex) + int(1)
                    if self.proList[int(self.proIndex)][3]:
                        yield scrapy.Request(url='http://zmis.zepdi.com.cn/Portal/EPMS/List/RollInfo/RollEntityBill'
                                                 '.aspx?OrganizationId=' + self.proList[int(self.proIndex)][3] +
                                                 '&secid=00000000-0000-0000-0000-000000000000&IsPortal=True',
                                             meta={"volIndex": self.volIndex},
                                             dont_filter=True,
                                             callback=self.parse)
                    else:
                        url = 'http://zmis.zepdi.com.cn/Portal/EPMS/List/ProjectDesign/ProjectStartList.aspx?secid' \
                              '=87ddc819-a9a7-4b2a-8c45-2dcfc2019342'
                        response = scrapy.Request(url, meta={'number': self.proList[int(self.proIndex)][1],
                                                             "volIndex": self.volIndex}, dont_filter=True,
                                                  callback=self.parse)
                        yield response
                else:
                    if len(self.volList) == 0:
                        self.cursor.execute("SELECT * FROM volume v,project p where p.id = v.project_id and p.spider = 0")
                        self.volList = self.cursor.fetchall()
                        self.connect.commit()
                        print(self.volList)
                    yield scrapy.Request(
                        url='http://zmis.zepdi.com.cn/Portal/EPMS/List/RollInfo/ContentMange.aspx?actionType'
                            '=1&RollID=' + self.volList[int(self.vol)][4],
                        callback=self.parse)
        elif 'ContentMange' in response.url:
            item = VolumeItem()
            item['number'] = response.xpath('//*[@id="ctl00_BusinessObjectHolder_tbRollCode"]/@value').extract()[
                0].strip()
            item['name'] = response.xpath('//*[@id="ctl00_BusinessObjectHolder_tbRollName"]/@value').extract()[
                0].strip()
            item['tec'] = response.xpath('//*[@id="ctl00_BusinessObjectHolder_tbSpecialtyName"]/@value').extract()[
                0].strip()
            item['dep'] = response.xpath('//*[@id="ctl00_BusinessObjectHolder_tbBelongDeptName"]/@value').extract()[
                0].strip()
            item['state'] = response.xpath('//*[@id="ctl00_BusinessObjectHolder_tbRollStateName"]/@value').extract()[
                0].strip()
            item['principal'] = \
                response.xpath('//*[@id="ctl00_BusinessObjectHolder_tbMasterDesigner"]/@value').extract()[
                    0].strip()
            item['chief'] = response.xpath('//*[@id="ctl00_BusinessObjectHolder_tbMasterEngineer"]/@value').extract()[
                0].strip()
            item['designer'] = response.xpath('//*[@id="ctl00_BusinessObjectHolder_tbRollOwner"]/@value').extract()[
                0].strip()
            item['planned_start_date'] = \
                response.xpath('//*[@id="ctl00_BusinessObjectHolder_tbPlanStartDate"]/@value').extract()[
                    0].strip()
            item['start_date'] = \
                response.xpath('//*[@id="ctl00_BusinessObjectHolder_tbFactStartDate"]/@value').extract()[
                    0].strip()
            item['planned_shot_date'] = \
                response.xpath('//*[@id="ctl00_BusinessObjectHolder_tbPlanDesignedDate"]/@value').extract()[
                    0].strip()
            item['shot_date'] = \
                response.xpath('//*[@id="ctl00_BusinessObjectHolder_tbFactDesignedDate"]/@value').extract()[
                    0].strip()
            item['proofreading_date'] = \
                response.xpath('//*[@id="ctl00_BusinessObjectHolder_tbVerifyEndDate"]/@value').extract()[
                    0].strip()
            item['planned_publication_date'] = response.xpath(
                '//*[@id="ctl00_BusinessObjectHolder_tbPlanToPublishDate"]/@value').extract()[0].strip()
            item['publication_date'] = \
                response.xpath('//*[@id="ctl00_BusinessObjectHolder_tbToPublishDate"]/@value').extract()[
                    0].strip()
            item['complete_time'] = \
                response.xpath('//*[@id="ctl00_BusinessObjectHolder_tbFactOutOfCollege"]/@value').extract()[
                    0].strip()
            item['formId'] = eval(re.findall(r'[(](.*?)[)]', response.xpath(
                '//*[@id="ctl00_BusinessObjectHolder_lbtnVerifyInfo"]/@onclick').extract()[0].
                                             strip())[0])[0]
            item['wfInstId'] = eval(re.findall(r'[(](.*?)[)]', response.xpath(
                '//*[@id="ctl00_BusinessObjectHolder_lbtnVerifyInfo"]/@onclick').extract()[0].
                                               strip())[0])[1]
            yield item
            if int(self.vol) < len(self.volList) - 1:
                self.vol = int(self.vol) + 1
                yield scrapy.Request(
                    url='http://zmis.zepdi.com.cn/Portal/EPMS/List/RollInfo/ContentMange.aspx?actionType'
                        '=1&RollID=' + self.volList[self.vol][4],
                    callback=self.parse)
            else:
                if len(self.vol1List) == 0:
                    self.cursor.execute("SELECT * FROM volume where `state` not in ('尚未开展', '正在设计') and `wfInstId` != ''")
                    self.vol1List = self.cursor.fetchall()
                    self.connect.commit()
                yield scrapy.Request(
                    url='http://zmis.zepdi.com.cn/Portal/Sys/Workflow/FormDetail.aspx?'
                        'actionType=1&formId=' + self.vol1List[int(self.vol1)][22] +
                        '&wfInstId=' + self.vol1List[int(self.vol1)][23],
                    callback=self.parse)
        elif 'FormDetail' in response.url:
            item = CheckerItem()
            item['number'] = response.xpath('//*[@id="ctl06_tbRollCode"]/@value').extract()[0].strip()
            item['checker'] = response.xpath('//*[@id="ctl06_tbRollCheckUserName"]/@value').extract()[0].strip()
            yield item
            if int(self.vol1) < len(self.vol1List) - 1:
                self.vol1 = int(self.vol1) + 1
                yield scrapy.Request(
                    url='http://zmis.zepdi.com.cn/Portal/Sys/Workflow/FormDetail.aspx?'
                        'actionType=1&formId=' + self.vol1List[int(self.vol1)][22] +
                        '&wfInstId=' + self.vol1List[int(self.vol1)][23],
                    callback=self.parse)

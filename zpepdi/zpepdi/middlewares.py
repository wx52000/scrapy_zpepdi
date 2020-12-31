# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html
import base64
import time

import requests
from requests_ntlm import HttpNtlmAuth
from scrapy import signals

# useful for handling different item types with a single interface
from itemadapter import is_item, ItemAdapter
from scrapy.http import HtmlResponse, Response, TextResponse
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.select import Select


class ZpepdiSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class ZpepdiDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass


class NTLM_Middleware(object):
    html_set_cookie = ''

    def process_request(self, request, spider):
        url = request.url
        pwd = getattr(spider, 'ntlm_pass', '')
        usr = getattr(spider, 'ntlm_user', '')
        print("*" * 60)
        print("url", request.cookies)
        if request.cookies:
            # 如果Spider中没有设置ntlm_user属性，就是普通的网站不在这里处理了。
            return
        ss = usr + ':' + pwd
        base64string = base64.b64encode(ss.encode()).decode('ascii')
        # request.headers["Authorization"] = "Basic %s" % base64string
        s = requests.session()
        response = s.get(url, auth=HttpNtlmAuth(usr, pwd))
        self.html_set_cookie = requests.utils.dict_from_cookiejar(response.cookies)
        print("html_set_cookie", self.html_set_cookie)
        request.cookies = self.html_set_cookie
        return TextResponse(url, response.status_code, {}, response.content)

    def process_response(self, request, response, spider):
        # 对response的status进行改写
        # 最终在spiders文件上的parse函数显示的response.status 显示为201
        response.cookies = self.html_set_cookie
        return response


class TimeoutException(object):
    pass


class WangyiproDownloaderMiddleware(object):

    # 可以拦截到request请求
    def process_request(self, request, spider):
        # 在进行url访问之前可以进行的操作, 更换UA请求头, 使用其他代理等
        pass

    # 可以拦截到response响应对象(拦截下载器传递给Spider的响应对象)
    def process_response(self, request, response, spider):
        """
        三个参数:
        # request: 响应对象所对应的请求对象
        # response: 拦截到的响应对象
        # spider: 爬虫文件中对应的爬虫类 WangyiSpider 的实例对象, 可以通过这个参数拿到 WangyiSpider 中的一些属性或方法
        """

        #  对页面响应体数据的篡改, 如果是每个模块的 url 请求, 则处理完数据并进行封装
        # if request.url in ["http://news.163.com/domestic/", "http://war.163.com/", "http://news.163.com/world/",
        #                    "http://news.163.com/air/"]:
        print("WangyiproDownloaderMiddlewareUrl:" + request.url)
        spider.browser.get(url=request.url)
        if 'ProjectStartList' in request.url:
            # more_btn = spider.browser.find_element_by_class_name("post_addmore")     # 更多按钮
            # print(more_btn)
            # js = "window.scrollTo(0,document.body.scrollHeight)"
            # spider.browser.execute_script(js)
            # if more_btn and request.url == "http://news.163.com/domestic/":
            #     more_btn.click()
            number = request.meta.get("number").strip()
            try:
                print("request.meta:if ", number)
                # spider.browser.find_element_by_xpath('//*[@id="ctl00_listGrid_gridList"]/tfoot/tr/td/input[5]').click
                spider.browser.find_element_by_xpath('//*[@id="ctl00_listGrid_tbProjectInfo"]').send_keys(number)
                spider.browser.find_element_by_xpath('//*[@id="ctl00_listGrid_btnQuery"]/span').click()
            except TimeoutException:
                spider.browser.close()
                print(" block-content NOT FOUND IN TECHCRUNCH !!!")
            time.sleep(3)  # 等待加载,  可以用显示等待来优化.
            row_response = spider.browser.page_source
            return HtmlResponse(url=spider.browser.current_url, body=row_response, encoding="utf8",
                                request=request)  # 参数url指当前浏览器访问的url(通过current_url方法获取), 在这里参数url也可以用request.url
            # 参数body指要封装成符合HTTP协议的源数据, 后两个参数可有可无
        elif 'RollEntityBill' in request.url:
            volIndex = request.meta.get('volIndex')
            print("request.meta:else", volIndex)
            pro = spider.browser.find_element_by_xpath('//*[@id="ctl00_listGrid_pdgRollList"]/tfoot/tr/td').text.strip()
            proSum = pro[pro.rfind('总数') + 2:pro.rfind('第') - 1]
            print("prosum", proSum)
            if 15 < int(proSum) <= 100:
                try:
                    s1 = Select(
                        spider.browser.find_element_by_xpath(
                            '//*[@id="ctl00_listGrid_pdgRollList"]/tfoot/tr/td/select'))
                    s1.select_by_index(3)
                except TimeoutException:
                    spider.browser.close()
                    print(" block-content NOT FOUND IN TECHCRUNCH !!!")
            else:
                if int(volIndex) > 1:
                    try:
                        input_goNum = spider.browser.find_element_by_xpath(
                            '/html/body/form/table/tbody/tr[2]/td/div/table/tfoot/tr/td/input[7]')
                        input_goNum.clear()
                        input_goNum.send_keys(volIndex)
                        btnGo = spider.browser.find_element_by_xpath('//*[@id="ctl00_listGrid_pdgRollList"]/tfoot/tr/td'
                                                                     '/input[8]').click()
                    except TimeoutException:
                        spider.browser.close()
                        print(" block-content NOT FOUND IN TECHCRUNCH !!!")
            time.sleep(3)
            volume_response = spider.browser.page_source
            return HtmlResponse(url=spider.browser.current_url, body=volume_response, encoding="utf8",
                                request=request)  # 是原来的主页的响应对象
        else:
            volume_response = spider.browser.page_source
            return HtmlResponse(url=spider.browser.current_url, body=volume_response, encoding="utf8",
                                request=request)

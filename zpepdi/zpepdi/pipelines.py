# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import json

import pymysql
from itemadapter import ItemAdapter

from zpepdi.items import ZpepdiItem, VolumeItem, VolumeIdItem


class ZpepdiPipeline:
    def __init__(self):
        # 打开文件
        self.connect = pymysql.connect(host='localhost', user='root', passwd='7499', db='appraise', port=3306,
                                       charset='utf8', autocommit=True)
        self.cursor = self.connect.cursor()
        self.file = open('data.json', 'w', encoding='utf-8')

    # 该方法用于处理数据
    def process_item(self, item, spider):
        if isinstance(item, ZpepdiItem):
            self.cursor.execute(
                "update project set `name`=%s, `state`=%s, `projectPhaseID`=%s, `director`=%s,"
                "`general`=%s, create_time=%s where `number` = %s",
                (
                    item['name'], item['state'], item['projectPhaseID'], item['director'], item['general'],
                    item['date'],
                    item['number']))
            self.connect.commit()
        # 读取item中的数据
        elif isinstance(item, VolumeIdItem):
            self.cursor.execute(
                "insert ignore into volume(`project_id`,`number`,`rollId`) values (%s,%s,%s)",
                (item['proID'], item['number'], item['rollID']))
            self.connect.commit()
        elif isinstance(item, VolumeItem):
            self.cursor.execute("update volume set `name`=%s,`tec` = %s, `dep` = %s,`state`=%s, `principal` = %s,"
                                "`chief` = %s,`designer` = %s,`planned_start_date` = %s,`start_date` = %s,"
                                "`planned_shot_date` = %s,`shot_date` = %s,"
                                "`proofreading_date` = %s,`planned_publication_date` = %s,`actual_publication_date` = %s,"
                                "`complete_time` = %s, `formId` = %s, `wfInstId` = %s where `number` = %s",
                                (
                                    item['name'], item['tec'], item['dep'], item['state'], item['principal'],
                                    item['chief'], item['designer'], item['planned_start_date'], item['start_date'],
                                    item['planned_shot_date'], item['shot_date'], item['proofreading_date'],
                                    item['planned_publication_date'], item['publication_date'], item['complete_time'],
                                    item['formId'], item['wfInstId'], item['number']))
            self.connect.commit()
        else:
            self.cursor.execute(
                "update volume set `checker`=%s where `number` = %s",
                (
                    item['checker'], item['number']))
            self.connect.commit()
        # 返回item
        return item

    # 该方法在spider被开启时被调用。
    def open_spider(self, spider):
        pass

    # 该方法在spider被关闭时被调用。
    def close_spider(self, spider):
        pass

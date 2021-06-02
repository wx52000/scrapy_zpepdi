# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class ZpepdiItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    # 项目链接Id
    projectPhaseID = scrapy.Field()
    # 项目编号
    number = scrapy.Field()
    # 项目名称
    name = scrapy.Field()
    # 项目阶段
    stage = scrapy.Field()
    # 项目主管
    director = scrapy.Field()
    # 项目类别
    type = scrapy.Field()
    # 设总
    general = scrapy.Field()
    # 下达日期
    date = scrapy.Field()
    # 状态
    state = scrapy.Field()


class VolumeIdItem(scrapy.Item):
    proID = scrapy.Field()
    # 卷册链接
    rollID = scrapy.Field()
    # 卷册编号
    number = scrapy.Field()


class VolumeItem(scrapy.Item):
    # 卷册编号
    number = scrapy.Field()
    # 卷册名称
    name = scrapy.Field()
    # 卷册专业
    tec = scrapy.Field()
    # 卷册部门
    dep = scrapy.Field()
    # 卷册状态
    state = scrapy.Field()
    # 工日
    workDay = scrapy.Field()
    # 主设人
    principal = scrapy.Field()
    # 主任工程师
    chief = scrapy.Field()
    # 卷册负责人
    designer = scrapy.Field()
    # 计划开始日期
    planned_start_date = scrapy.Field()
    # 开始日期
    start_date = scrapy.Field()
    # 计划出手日期
    planned_shot_date = scrapy.Field()
    # 实际出手日期
    shot_date = scrapy.Field()
    # 校审完成日期
    proofreading_date = scrapy.Field()
    # 计划出版日期
    planned_publication_date = scrapy.Field()
    # 实际出版时间
    publication_date = scrapy.Field()
    # 完成日期
    complete_time = scrapy.Field()
    # 卷册URL formId
    formId = scrapy.Field()
    # 卷册Url wfInstId
    wfInstId = scrapy.Field()


class CheckerItem(scrapy.Item):
    # 卷册编号
    number = scrapy.Field()
    # 互校人姓名
    checker = scrapy.Field()
    # 实际主设人
    actual_principal = scrapy.Field()

# -*- coding: utf-8 -*-

import requests
from lxml import html
import ast
from tqdm import tqdm
import pandas as pd
import asyncio
import aiohttp

class LinkedHome(object):

    """链家二手房在线数据
    
    requirements
    ==========
    Python3.5
    requests
    lxml
    tqdm
    pandas
    asyncio
    aiohttp

    parameters
    ==========
    field : dict
        可选区域：东城, 西城, 朝阳, 海淀, 丰台, 石景山, 
        通州, 昌平, 大兴, 亦庄开发区, 顺义, 房山, 门头沟, 
        平谷, 怀柔, 密云, 延庆, 燕郊
    field_name : str
        区域名称，显示在输出文件名
    header : str
        区域url链接
    page_all : int
        全部页数
    page_info : list
        需要的信息列表，输出文件后，替换为最终Dataframe
    sem : asyncio.Semaphore
        协程锁
    headers : dict
        Http get请求头
    columns : list
        pandas Dataframe字段名称
    new_columns : list
        输出excel文件字段名称    
    """

    def __init__(self, field:str):
        self.field = {'dongcheng': '东城',
                      'xicheng': '西城',
                      'chaoyang': '朝阳',
                      'haidian': '海淀',
                      'fengtai': '丰台',
                      'shijingshan': '石景山',
                      'tongzhou': '通州',
                      'changping': '昌平',
                      'daxing': '大兴',
                      'yizhuangkaifaqu': '亦庄开发区',
                      'shunyi': '顺义',
                      'fangshan': '房山',
                      'mentougou': '门头沟',
                      'pinggu': '平谷',
                      'huairou': '怀柔',
                      'miyun': '密云',
                      'yanqing': '延庆',
                      'yanjiao': '燕郊'}

        self.field_name = self.field.get(field, '')
        self.header = 'http://bj.lianjia.com/ershoufang/{}'.format(field)
        self.first_url = self.header + '/pg1' + 'sf1co21tf1lc1lc2l2p4p5'
        self.page_all = int
        self.page_info = list
        self.sem = asyncio.Semaphore(10)
        self.headers = {"User-Agent": ("Mozilla/5.0 (Windows NT 10.0; WOW64)"
                                       "AppleWebKit 537.36 (KHTML, like Gecko) Chrome"),
                        "Accept": ("text/html,application/xhtml+xml,application/xml;"
                                   "q=0.9,image/webp,*/*;q=0.8")}
        self.columns = ['url', '名称', '小区', '房型', '面积',
                        '朝向', '装修', '有无电梯', '楼层', '楼龄', '区域',
                        '关注', '带看', '首发', '评价', '价格', '单位', '均价']
        self.new_columns = ['区域', 'url', '小区', '房型', '面积', '价格', '均价',
                            '状态', '朝向', '装修', '楼层', '有无电梯', '楼龄',
                            '类型', '关注', '带看', '首发', '名称', '评价']
        self.file_name = '链家{}二手房信息{}.xlsx'.format(
            self.field_name, pd.Timestamp.today().date())
        self.get_first()

    def get_first(self):
        '''
        通过首页内容，获取总页数和首页字段数据

        returns
        ==========
        tree : str
            lxml parse the first page dom tree
        '''
        page = requests.get(self.first_url, headers=self.headers)
        tree = html.fromstring(page.content.decode('utf8'))
        # 从首页获取总页数
        path = '//div[@class="page-box house-lst-page-box"]'
        self.page_all = ast.literal_eval(
            tree.xpath(path)[0].attrib['page-data'])['totalPage']
        # 从首页获取字段数据
        self.page_info = self.get_info(tree)

    def get_info(self, tree):
        '''
        解析页面，获取需要的数据

        parameters
        ==========
        tree : lxml
            lxml tree structure
        '''
        cnt = []
        for foo in tree.xpath('//li[@class="clear"]'):
            url = foo.xpath('a/@href')
            pp = foo.xpath('div[@class="info clear"]')[0]
            t = ('title', 'address', 'flood', 'followInfo', 'tag', 'priceInfo')
            v = [pp.xpath('div[@class="%s"]//text()' % c) for c in t]
            v[1] = [v[1][0]] + v[1][1].split(' | ')[1:]
            v[2] = v[2][0].split('  ')[:-2] + [v[2][1]]
            v[3] = v[3][0].split(' / ')
            v[4] = [', '.join(v[4])]
            cnt.append((url + [y for x in v for y in x]))
        return cnt

    async def wait_with_progress(self, tasks):
        '''
        利用tqdm显示进度条

        parameters
        ==========
        task : int
            task running in the asyncio event loop
        '''
        for f in tqdm(asyncio.as_completed(tasks), total=len(tasks)):
            await f

    async def get_async(self, p):
        '''
        通过GET请求获取页面内容

        parameters
        ==========
        p : int
            page number
        '''
        with (await self.sem):
            url = self.header + '/pg{}sf1co21tf1lc1lc2l2p4p5'.format(p)
            response = await aiohttp.request('GET', url, headers=self.headers, compress=True)
            page = await response.text(encoding='utf-8')
            tree = html.fromstring(page)
        self.page_info.extend(self.get_info(tree))

    def get_all(self):
        '''先从首页获取页数和字段，然后运行asyncio loop获取所有数据'''
        loop = asyncio.get_event_loop()
        f = [self.get_async(d) for d in range(2, self.page_all+1)]
        loop.run_until_complete(self.wait_with_progress(f))

    def clean_data(self):
        '''
        过滤数据：
        - 去掉新上/房主自荐
        - 特定区域
        - 满五年唯一

        删除：
        - 楼龄早于1990
        - 地下室
        - 不限购
        - 一个月以上无带看
        '''
        data = [[x for x in p if x != '新上' and x != '房主自荐']
                for p in self.page_info]
        df = pd.DataFrame(data=data, columns=self.columns)
        for v in ('价格', '均价', '带看', '关注'):
            df[v] = df[v].str.extract('(\d+)', expand=False).apply(int)
        df.面积 = df.面积.str.replace('平米', '').apply(float)
        df.首发 = df.首发.str.replace('[以发布]+', '')
        df['状态'] = df.评价.str.extract('(满\w+)', expand=False)
        df[['楼龄', '类型']] = df.楼龄.str.extract('(\d{4})年建(\w+)', expand=True)
        df.楼龄 = df.楼龄.fillna(0).apply(int)
        df = df[(~df.楼层.str.match('地下室')) & (~df.名称.str.match('.+限购')) &
                ~((df.首发.str.match('.+月')) & (df.带看 == 0))]
        df = df.loc[:, self.new_columns]
        df.to_excel(self.file_name, index=False)
        self.page_info = df


if __name__ == "__main__":
    home = LinkedHome('haidian')
    home.get_all()
    home.clean_data()

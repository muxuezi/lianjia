# -*- coding: utf-8 -*-

import requests
from lxml import html
from tqdm import tqdm
import pandas as pd
import asyncio
import aiohttp

headers = {"User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5)"
                          "AppleWebKit 537.36 (KHTML, like Gecko) Chrome"),
           "Accept": ("text/html,application/xhtml+xml,application/xml;"
                      "q=0.9,image/webp,*/*;q=0.8")}
head = 'http://210.75.213.188/shh/portal/bjjs/audit_house_list.aspx'


def get_page(p):
    url = head + '?pagenumber={}&pagesize=20'.format(p)
    try:
        page = requests.get(url, headers=headers)
    except:
        return
    else:
        return html.fromstring(page.content.decode('utf8'))


def get_tbody(page):
    tbody = []
    table = page.find_class('houseList')[0]
    for x in table.xpath('./tbody/tr'):
        row = x.xpath('.//text()')[1:-1][::2]
        url = x.xpath('./td[9]')[0].find('a').attrib['href'].split('?')[1]
        row.append(url)
        tbody.append(row)
    return tbody

pp = get_page(1)
page_num = int(
    pp.xpath('//*[contains(text(),"页次")]')[0].text.split('/')[-1][:-1])
table = pp.find_class('houseList')[0]
thead = table.xpath('./thead//text()')[2:-2][::2]
records = get_tbody(pp)
allpages = range(2, page_num)

async def get(*args, **kwargs):
    response = await aiohttp.request('GET', *args, **kwargs)
    return await response.text(encoding='utf-8')

async def wait_with_progress(tasks):
    for f in tqdm(asyncio.as_completed(tasks), total=len(tasks)):
        await f

async def get_all(p):
    with (await sem):
        page = await get(head + '?pagenumber={}&pagesize=20'.format(p),
                         headers=headers, compress=True)
    page = html.fromstring(page)
    records.extend(get_tbody(page))


sem = asyncio.Semaphore(5)
loop = asyncio.get_event_loop()
f = [get_all(d) for d in allpages]
loop.run_until_complete(wait_with_progress(f))

df = pd.DataFrame(data=records, columns=thead)
df.发布机构 = df.发布机构.str.strip()
df.面积 = df.面积.apply(float)
df.拟售价格 = df.拟售价格.apply(lambda x: float(x.replace('万元', '')))
df['年份'] = df['月份'] = None
df.loc[:, ['年份', '月份']] = df.时间.str.extract(
    '^(\d{4})-(\d{2})', expand=False).applymap(int).values
df.详细 = head.replace('_list', '_detail') + '?' + df.详细

df.to_excel('存量房交易服务平台{}.xlsx'.format(
    pd.Timestamp.today().date()), index=False)

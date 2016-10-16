# 北京二手房在线数据采集

使用 Python 3.5 的 [asyncio](https://docs.python.org/3/library/asyncio.html) + [aiohttp](http://aiohttp.readthedocs.io/en/stable/)

- [链家二手房在线数据](http://bj.lianjia.com/ershoufang/)

```
    requirements
    使用Python 3.5及以上版本，建议安装以下依赖包
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
```

```python
from linkedhome import LinkedHome
home = LinkedHome('haidian') # 初始化区域
home.get_all() # 获取数据
home.clean_data() # 清洗数据
```

- [存量房交易服务平台数据](http://210.75.213.188/shh/portal/bjjs/audit_house_list.aspx)

```bash
python data存量房交易服务平台.py
```

<a rel="license" href="http://creativecommons.org/licenses/by-nc-sa/3.0/cn/"><img alt="知识共享许可协议" style="border-width:0" src="https://i.creativecommons.org/l/by-nc-sa/3.0/cn/88x31.png" /></a><br />本作品采用<a rel="license" href="http://creativecommons.org/licenses/by-nc-sa/3.0/cn/">知识共享署名-非商业性使用-相同方式共享 3.0 中国大陆许可协议</a>进行许可。

import os
import queue
import requests
from lxml import etree

down_load_records = {
    1: 0.2,
    2: 1,
    3: 0.5
}

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
}

url = 'https://www.bilibili.com/video/av35928275/?p=1' #输入要播放的视频
response = requests.get(url, headers=headers)
print(response.text)
html = etree.HTML(response.text)
print(html.xpath('//span[@class="tit"]/text()')[0])

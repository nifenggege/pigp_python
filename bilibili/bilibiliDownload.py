
import requests
import re
import urllib.request
import time
import sys
import threading
from queue import Queue
import socket
import os
from lxml import etree

'''
使用方式：
1. 在浏览器中打开要下载的视频, 将播放视频页面的url替换到main函数中的url中
2. headers中的Cookie参数可以配置，也可以不配置，如何获取Cookie见《注意事项》
    （1）配置Cookie的话，会根据Cookie用户的身份信息进行下载最高清晰度的视频， 默认是720,1080， 再高的需要用户身份是会员
    （2）不配置Cookie的话，相当于用户没有登录，只能下载360清晰度的视频

注意事项：
1. 如何获取cookie
在浏览器登录bilibili账号，F12打开开发者面板，访问url: https://api.bilibili.com/x/web-interface/view?aid=
查找Network-->All->找到该url请求，点击查找Headers-->Request--->Headers-->Cookie
将Cookie中的SESSDATA项拷贝出来即可
2. 该脚本默认下载该系列视频全局，可以通过构造Producer的时候传入[start_p, end_p]开始集数-终止集数，进行选集下载
    eg: product_download_info(video_id, has_done_list, start_p=29, end_p=29)
3. 该脚本默认开启了9个消费者进行下载，如果自己的电脑性能搞，可以适当调整消费者的个数，在main函数的for循环中的range进行调整
    eg: for x in range(20):
'''


down_load_records = {}
lock = threading.Lock()
socket.setdefaulttimeout(5)

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
    'Host': 'api.bilibili.com',
    'Cookie': 'SESSDATA=c0c48f36%2C1573134751%2Ce21a47a1' #不添加该cookie只能下载顺畅视频
}


def product_download_info(aid, has_done_list, start_p=None, end_p=None):
    videos = query_vedio_info(aid)
    video_infos = []
    for video in videos:
        if start_p is not None and start_p > video['num']:
            continue
        if end_p is not None and end_p < video['num']:
            break

        if has_done_list is not None and str(video['num']) in has_done_list:
            continue

        video_infos.append({
            'title': build_order_pre(video['num']) + '_' + video['title'],
            'ref': 'https://api.bilibili.com/x/web-interface/view?aid=%s/?p=%s' % (aid, video['num']),
            'url': query_download_url(aid, video['cid']),
            'aid': aid,
            'num': video['num']
        })
        time.sleep(1)
    return video_infos


def build_order_pre(num):
    return '00' + str(num) \
        if num < 10 else '0' + str(num) \
        if num < 100 else str(num)


def query_vedio_info(aid):
    query_info_url = 'https://api.bilibili.com/x/web-interface/view?aid=%s' % aid
    resp = requests.get(query_info_url, headers=headers).json()
    pages = resp['data']['pages']
    page_infos = []
    for page in pages:
        page_infos.append(
            {
                'cid': page['cid'],
                'title': re.sub(r'[\?\-（）\s？]', '', page['part']),
                'num': page['page']
            }
        )
    return page_infos


def query_download_url(aid, cid):
    download_info_url = 'https://api.bilibili.com/x/player/playurl?avid=%s&cid=%s&qn=116' % (aid, cid)
    resp = requests.get(download_info_url, headers=headers).json()
    if len(resp['data']['durl']) > 1:
        print('error download %s-%s' % (aid, cid))
    return resp['data']['durl'][0]['url']


def download_bilibili(url, title, start_url, tag):

    save_path = os.path.join(base_path, r'{}.flv'.format(title))
    header = [
        ('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:56.0) Gecko/20100101 Firefox/56.0'),
        ('Accept', '*/*'),
        ('Accept-Language', 'en-US,en;q=0.5'),
        ('Accept-Encoding', 'gzip, deflate, br'),
        ('Range', 'bytes=0-'),  # Range 的值要为 bytes=0- 才能下载完整视频
        ('Referer', start_url),  # 注意修改referer,必须要加的!
        ('Origin', 'https://www.bilibili.com'),
        ('Connection', 'keep-alive')
    ]
    DownloadTool(url, save_path, header, tag).down_video()


def check_path_exist(save_path):
    paths = os.path.split(save_path)
    dir_path = paths[0]
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)


class DownloadTool(object):
    #  下载视频
    def __init__(self, down_load_url, save_path, header, tag):
        self.down_load_url = down_load_url
        self.save_path = save_path
        self.header = header
        self.tag = tag

    def down_video(self):
        opener = urllib.request.build_opener()
        opener.addheaders = self.header
        urllib.request.install_opener(opener)
        check_path_exist(self.save_path)
        urllib.request.urlretrieve(url=self.down_load_url, filename=self.save_path,
                                   reporthook=self.report_process)

    def report_process(self, blocknum, blocksize, totalsize):
        percent = (blocknum * blocksize) / totalsize
        #这里应该更新到一个全局变量中
        down_load_records[self.tag] = percent


class Consumer(threading.Thread):

    def run(self):
        while True:
            record = None
            try:
                record = queue.get(False)
            except Exception:
                record = None

            if record is None:
                print('consumer-%s, finish' % threading.current_thread().name)
                break

            try:
                print('[consumer-%s，start download] P-%s' % (threading.current_thread().name, record['title']))
                download_bilibili(record['url'], record['title'], record['ref'], record['num'])
                print('[consumer-%s，finish download] P-%s' % (threading.current_thread().name, record['title']))
            except:
                if record is not None:
                    queue.put(record)
                print('consumer-%s error' % threading.current_thread().name)


def show_process():

    fd = open(os.path.join(base_path, record_file), 'a+', encoding='utf-8')
    done_count = 0
    while True:
        time.sleep(60)
        sum = 0
        for key in down_load_records:
            sum += down_load_records[key]
        percent = (sum+done_count)/(len(down_load_records)+done_count)
        print("has done %s/%s, task download %.2f%%" % (done_count, (len(down_load_records)+done_count), (percent*100)))

        finish = list(map(lambda x: str(x), filter(lambda key: down_load_records[key] >= 1, down_load_records)))
        if finish is not None and len(finish) > 0:
            fd.write(",".join(finish))
            fd.write(",")
            fd.flush()
            for x in finish:
                down_load_records.pop(int(x))

        if finish is not None:
            done_count += len(finish)
        if down_load_records is None or len(down_load_records) == 0:
            print('====tash has done!!!====')
            break
        if percent > 0.7:
            print('un finish : %s' % down_load_records.keys())
    fd.close()


def query_has_done():

    file_path = os.path.join(base_path, record_file)
    if not os.path.exists(file_path):
        return None

    with open(file_path, 'r', encoding='utf-8') as fp:
        has_done = fp.readline().split(",")
        return list(filter(lambda key: key is not None and key.strip() != '', has_done))


def query_video_name(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
    }
    response = requests.get(url, headers=headers)
    html = etree.HTML(response.text)
    return html.xpath('//span[@class="tit"]/text()')[0]


if __name__ == '__main__':

    url = 'https://www.bilibili.com/video/av57591340?from=search&seid=10477641346968902964' #输入要播放的视频
    video_name = query_video_name(url)
    video_id = re.search(r'av(.*?)\D', url).group(1)
    vide_name = video_id if video_name is None else video_name
    print('start parse url , veido name is %s' % video_name)
    base_path = os.path.join(sys.path[0], 'bilibili_video', video_name)
    record_file = 'record'
    check_path_exist(os.path.join(base_path, record_file))
    print('start parse donwload url')
    has_done_list = query_has_done()

    download_infos = product_download_info(video_id, has_done_list)
    #print('donwload url is %s' % download_infos)

    totals = len(download_infos)
    queue = Queue(totals)
    for info in download_infos:
        down_load_records[info['num']] = 0
        queue.put(info)
    print('queue info is %s' % queue.qsize())

    #启动消费者进行消费
    for x in range(5):
        Consumer(name='consumer_'+str(x)).start()

    show_process()

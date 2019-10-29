
import requests
import re
import urllib.request
import time
import os
import sys
import threading
from queue import Queue

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
    eg: Product(video_id, name='product', start_p=29, end_p=29).start()
3. 该脚本默认开启了9个消费者进行下载，如果自己的电脑性能搞，可以适当调整消费者的个数，在main函数的for循环中的range进行调整
    eg: for x in range(20):
'''


queue = Queue(100)
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
    'Host': 'api.bilibili.com',
    'Cookie': 'SESSDATA=c0c48f36%2C1573134751%2Ce21a47a1' #不添加该cookie只能下载顺畅视频
}


class Product(threading.Thread):

    def __init__(self, aid, start_p=None, end_p=None, *args, **kwargs):
        super(Product, self).__init__(*args, **kwargs)
        self.aid = aid
        self.start_p = start_p
        self.end_p = end_p

    def run(self):
        videos = self.query_vedio_info(self.aid)
        for video in videos:
            #首先判断video是否在判断
            if self.start_p is not None and self.start_p > video['num']:
                continue
            if self.end_p is not None and self.end_p < video['num']:
                break

            download_url = self.query_download_url(self.aid, video['cid'])
            pre_title = '00' + str(video['num']) \
                if video['num'] < 10 else '0' + str(video['num']) \
                if video['num'] < 100 else str(video['num'])
            start_url = 'https://api.bilibili.com/x/web-interface/view?aid=%s/?p=%s' % (self.aid, video['num'])
            print('生产者：%s, 开始生产: %s' % (threading.current_thread(), video['num']))
            queue.put({
                'title': pre_title+'_'+video['title'],
                'ref': start_url,
                'url': download_url,
                'aid': self.aid
            })
            time.sleep(1)

    def query_vedio_info(self, aid):
        url = 'https://api.bilibili.com/x/web-interface/view?aid=%s' % aid
        resp = requests.get(url, headers=headers).json()
        pages = resp['data']['pages']
        result = []
        for page in pages:
            result.append(
                {
                    'cid': page['cid'],
                    'title': re.sub(r'[\?\-（）\s？]', '', page['part']),
                    'num': page['page']
                }
            )
        return result

    def query_download_url(self, aid, cid):
        url = 'https://api.bilibili.com/x/player/playurl?avid=%s&cid=%s&qn=116' % (aid, cid)
        resp = requests.get(url, headers=headers).json()
        if len(resp['data']['durl']) > 1:
            print('error download %s-%s' % (aid, cid))
        return resp['data']['durl'][0]['url']


class Consumer(threading.Thread):

    start_time = time.time()

    def run(self):
        while True:
            try:
                record = None
                try:
                    record = queue.get(timeout=20)
                except Exception:
                    record = None

                if record is None:
                    print('消费者%s, 消费完成' % threading.current_thread())
                    break
                self.start_time = time.time()
                self.down_video(record['url'], record['title'], record['ref'], record['aid'])
                print('消费者%s，下载视频P%s完成' % (threading.current_thread(), record['title']))
            except:
                print('counser %s error' % threading.current_thread())

    def schedule_cmd(self, blocknum, blocksize, totalsize):
        speed = (blocknum * blocksize) / (time.time() - self.start_time)
        # speed_str = " Speed: %.2f" % speed
        speed_str = " Speed: %s" % self.format_size(speed)
        recv_size = blocknum * blocksize

        # 设置下载进度条
        f = sys.stdout
        pervent = recv_size / totalsize
        percent_str = "%.2f%%" % (pervent * 100)
        n = round(pervent * 50)
        s = ('#' * n).ljust(50, '-')
        f.write(percent_str.ljust(8, ' ') + '[' + s + ']' + speed_str)
        f.flush()
        f.write('\r')

    # 字节bytes转化K\M\G
    def format_size(self, bytes):
        try:
            bytes = float(bytes)
            kb = bytes / 1024
        except:
            print("传入的字节格式不对")
            return "Error"
        if kb >= 1024:
            M = kb / 1024
            if M >= 1024:
                G = M / 1024
                return "%.3fG" % (G)
            else:
                return "%.3fM" % (M)
        else:
            return "%.3fK" % (kb)

    #  下载视频
    def down_video(self, video_url, title, start_url, aid):
        print('[消费者%s, 正在下载%s段视频,请稍等...]:' % (threading.current_thread(), title))
        currentVideoPath = os.path.join(sys.path[0], 'bilibili_video', str(aid))  # 当前目录作为下载目录

        opener = urllib.request.build_opener()
        # 请求头
        opener.addheaders = [
            # ('Host', 'upos-hz-mirrorks3.acgvideo.com'),  #注意修改host,不用也行
            ('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:56.0) Gecko/20100101 Firefox/56.0'),
            ('Accept', '*/*'),
            ('Accept-Language', 'en-US,en;q=0.5'),
            ('Accept-Encoding', 'gzip, deflate, br'),
            ('Range', 'bytes=0-'),  # Range 的值要为 bytes=0- 才能下载完整视频
            ('Referer', start_url),  # 注意修改referer,必须要加的!
            ('Origin', 'https://www.bilibili.com'),
            ('Connection', 'keep-alive')
        ]
        urllib.request.install_opener(opener)
        # 创建文件夹存放下载的视频
        if not os.path.exists(currentVideoPath):
            os.makedirs(currentVideoPath)
        urllib.request.urlretrieve(url=video_url, filename=os.path.join(currentVideoPath, r'{}.flv'.format(title)),
                                   reporthook=self.schedule_cmd)  # 写成mp4也行  title + '-' + num + '.flv'


if __name__ == '__main__':

    url = 'https://www.bilibili.com/video/av39126512?from=search&seid=15034860517630283296' #输入要播放的视频
    video_id = re.search(r'av(.*?)\D', url).group(1)
    Product(video_id, name='product', start_p=17, end_p=17).start()
    for x in range(10):
        Consumer(name='consumer_'+str(x)).start()

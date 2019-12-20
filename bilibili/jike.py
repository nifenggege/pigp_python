import requests
import json
import sys
import os
import re
from urllib import request
import socket

url = 'https://time.geekbang.org/serv/v1/article'
comment_url = 'https://time.geekbang.org/serv/v1/comments'
articles_url = 'https://time.geekbang.org/serv/v1/column/articles'
socket.setdefaulttimeout(5)

header = {
    'Cookie':'GCID=17debbd-86a2973-7c67621-8124436;\
    GCESS=BAwBAQkBAQIEgtn8XQoEAAAAAAYEwSFDRgEEBoYRAAcE9ftUJQMEgtn8XQQEAC8NAAsCBAAIAQMFBAAAAAA-;',
    #'GCID': '17debbd-86a2973-7c67621-8124436',
    #'GRID': '17debbd-86a2973-7c67621-8124436',
    #'SERVERID': '1fa1f330efedec1559b3abbcb6e30f50|1576827408|1576826896',
    #'Referer': 'https://time.geekbang.org/column/article/149941',
    'Origin': 'https://time.geekbang.org',
    'Content-Type': 'application/json',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.79 Safari/537.36'
}

params = {
    #'id': '149941',
    'include_neighbors': 'true',
    'is_freelyread': 'true'
}


def parse_article(aid):
    header['Referer'] = 'https://time.geekbang.org/column/article/' + str(aid['aid'])
    params['id'] = aid['aid']
    response = requests.post(url=url, data=json.dumps(params), headers=header)
    result = response.json()
    return re.sub(r'<p><img src=[^>]*?></p>$', '',result['data']['article_content'])

def parse_comment(aid):
    header['Referer'] = 'https://time.geekbang.org/column/article/' + str(aid['aid'])
    comment_param = {
        'aid': aid['aid'],
        'prev': 0
    }
    response = requests.post(url=comment_url, data=json.dumps(comment_param), headers=header)
    comment_list = response.json()['data']['list']
    comment_result = '\n###精选评论'
    for comment in comment_list:
        reply_list = []
        if 'replies' in comment:
            replies = comment['replies']
            for reply in replies:
                reply_list.append(reply['content'])
        temp = ''
        if len(reply_list) > 0:
            temp = '\n\n    - 回复：' + '\n\n    - 回复：'.join(reply_list)
        comment_result +=  ('\n\n----\n- ' + comment['comment_content'] + temp)

    return comment_result

def parse_column(cid):
    header['Referer'] = 'https://time.geekbang.org/column/article/149941'  #cid: 238, size: 100, prev: 0, order: "earliest", sample: false
    articles_param = {
        'cid': cid,
        'size': 100,
        'prev': 0,
        'order': 'earliest',
        'sample': 'false'
    }

    articles = []
    response = requests.post(url=articles_url, data=json.dumps(articles_param), headers=header)
    print(response.text)
    print('==='*30)
    print(response.json())
    article_list = response.json()['data']['list']
    print('===' * 30)
    print(article_list)
    for article in article_list:
        articles.append({
            'aid': article['id'],
            'mp3': article['audio_download_url'] if 'audio_download_url' in article else None,
            'title': article['article_title']
        })
    return articles

def check_path_exist(save_path):
    paths = os.path.split(save_path)
    dir_path = paths[0]
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)


if __name__ == '__main__':
    cid = '180'
    start_index = 0
    end_index = 100000
    base_path = os.path.join(sys.path[0], 'bilibili_video', cid)
    check_path_exist(os.path.join(base_path, cid))
    articles = parse_column(cid)
    print('==='*30)
    print('处理文章', len(articles), articles)

    for index, article in enumerate(articles):
        if index < start_index:
            continue

        if index > end_index:
            break;
        print('开始处理：', str(index), "/", str(len(articles)), article['title'])
        content = parse_article(article)
        pre = str(index) if index>=100 else '0'+str(index) if index>=10 else '00'+str(index)
        fp = open(os.path.join(base_path, pre+'_'+re.sub(r'[|:><\s，：?/]+', '_',article['title'])+'.md'), 'w', encoding='utf-8')

        fp.write(content)
        comments = parse_comment(article)
        fp.write(comments)
        fp.close()
        if 'mp3' in article and article['mp3'] is not None:
            while True:
                try:
                    request.urlretrieve(article['mp3'], os.path.join(base_path, pre+'_'+re.sub(r'[|:><\s，?：/]+', '_',article['title'])+'.mp3'))
                    break
                except:
                    print('超时。。。。。')
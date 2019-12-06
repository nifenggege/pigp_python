import requests
from lxml import etree
import json
import csv

proxy = {
    'http': '127.0.0.1:10809'
}

header = {
    'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36"
}
event_list = [""]


def parse_day(url, time):

    response = requests.get(url + time, headers=header)
    html = etree.HTML(response.content.decode(encoding='utf-8'))
    content_div = html.xpath('//div[@class="mw-parser-output"]/h2|//div[@class="mw-parser-output"]/ul')
    count = 0
    for element in content_div:
        #h2标签
        span = element.xpath('./span[@class="mw-headline"]')
        if span is not None and len(span) > 0:
            event_name = span[0].xpath('./text()')[0]
            count += 1
            if count > 4:
                break
            continue
        parse_ul(element, event_name, time, count)


def parse_ul(element, event_name, time, count):
    # ul 标签构造数据
    li_list = element.xpath('./li')
    for li in li_list:
        parse_li(li, event_name, time, count)


def parse_li(li, event_name, time, count):
    #第1个a是时间， 后面的a都需要大请求获取数据
    #判断li下面有没有ul标签，如果有逻辑就不一样了
    li_ul_li_list = li.xpath('./ul/li')
    if li_ul_li_list is not None and len(li_ul_li_list) > 0:
        event_time = li.xpath('./a/text()')
        if len(event_time) <= 0:
            return
        for li_ul_li in li_ul_li_list:
            parse_li_ul_li(li_ul_li, event_name, time, event_time[0])
    else:
        text = li.xpath('.//text()')
        if len(text) <= 0:
            return
        event_time = None
        if count != 4:
            event_time = text[0]
            content = ''.join(text[1:]).strip('：')
        else:
            content = ''.join(text).strip('：')
        detail_info = parse_detail(li)
        date = {
            'time': time,
            'type': event_name,
            'event_time': event_time,
            'content': content,
            'detail': detail_info
        }
        save_file(date)


def parse_li_ul_li(li, event_name, time, event_time):
    text = li.xpath('.//text()')
    content = ''.join(text).strip('：')
    detail_info = parse_detail(li)
    date = {
        'time': time,
        'type': event_name,
        'event_time': event_time,
        'content': content,
        'detail': detail_info
    }
    save_file(date)


def save_file(date):
    writer.writerow(date)


def parse_detail(li):
    a_list = li.xpath('.//a')
    detail_list = []
    if a_list is None or len(a_list) <= 0:
        return detail_list
    for a in a_list[1:]:
        text_list = a.xpath('./text()')
        if len(text_list) <= 0:
            continue

        text = text_list[0]
        url = 'https://zh.wikipedia.org/api/rest_v1/page/summary/' + str(text)
        try:
            response = requests.get(url, headers=header)
            #解析结果
            res_dic = json.loads(response.content.decode(encoding='utf-8'))
            extract = None
            if 'extract' in res_dic:
                extract = res_dic['extract']
            image = None
            if 'originalimage' in res_dic:
                image_dic = res_dic['originalimage']
                if image_dic is not None and 'source' in image_dic:
                    image = image_dic['source']
            detail_list.append(
                {
                    'keyword': text,
                    'image': image,
                    'extract': extract
                }
            )
        except:
            print("error")
    return detail_list


if __name__ == '__main__':
    token = ['time', 'type', 'event_time', 'content', 'detail']
    fp = open('event.csv', 'w', encoding='utf-8', newline='')
    writer = csv.DictWriter(fp, token)
    writer.writeheader()
    date_num_dict = {1:31, 2:29, 3:31, 4:30, 5:31, 6:30, 7:31, 8:31, 9:30, 10:30, 11:30, 12:31}
    for i in range(5, 6):
        for j in range(19, date_num_dict[i]+1):
            parse_day('https://zh.wikipedia.org/wiki/', '%s月%s日' % (str(i), str(j)))
    fp.close()
import os
import sys
import requests
import datetime
from Crypto.Cipher import AES
from binascii import b2a_hex, a2b_hex

#reload(sys)
#sys.setdefaultencoding('utf-8')


header = {
    'User-Agent': '[{"key":"User-Agent","value":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36\
     (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36","enabled":true}]',
    'Referer': 'https://time.geekbang.org/course/detail/265-179503',
    'Origin': 'https://time.geekbang.org'
}


def download(content):
    if "#EXTM3U" not in content:
        raise BaseException("非M3U8的链接")

    file_line = content.split("\n")

    unknow = True
    key = ""
    for index, line in enumerate(file_line):  # 第二层
        if "#EXT-X-KEY" in line:  # 找解密Key
            method_pos = line.find("MEATHOD")
            comma_pos = line.find(",")
            method = line[method_pos:comma_pos].split('=')[1]
            print('decode Method', method)

            uri_pos = line.find("URI")
            quotation_mark_pos = line.rfind('"')
            key_path = line[uri_pos:quotation_mark_pos].split('"')[1]

            key_url = 'https://media001.geekbang.org/2aa5c0ceb85840279fb376a0a029cee4/' + key_path  # 拼出key解密密钥URL
            res = requests.get(key_url, headers=header)
            key = ''
            print('key:', res.content)

        if "ts" in line:  # 找ts地址并下载

            pd_url = 'https://media001.geekbang.org/2aa5c0ceb85840279fb376a0a029cee4/' + line  # 拼出ts片段的URL
            # print pd_url

            res = requests.get(pd_url, headers=header)
            file_block_name = line.split('-')[-1]
            if len(key):  # AES 解密
                cryptor = AES.new(key, AES.MODE_CBC, key)
                with open(os.path.join(base_path, file_block_name), 'ab') as f:
                    f.write(cryptor.decrypt(res.content))
            else:
                with open(os.path.join(base_path, file_block_name), 'ab') as f:
                    f.write(res.content)
                    f.flush()
    merge_file(base_path)


def merge_file(path):
    os.chdir(path)
    cmd = "copy /b * new.tmp"
    os.system(cmd)
    os.system('del /Q *.ts')
    os.system('del /Q *.mp4')
    os.rename("new.tmp", "new.mp4")


def check_path_exist(save_path):
    paths = os.path.split(save_path)
    dir_path = paths[0]
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)


def parse_m3u8(url):
    response = requests.get(url=url, headers=header)
    return response.text


if __name__ == '__main__':
    base_path = os.path.join(sys.path[0], 'bilibili_video', '110')
    check_path_exist(os.path.join(base_path, '110'))
    url = "https://media001.geekbang.org/2aa5c0ceb85840279fb376a0a029cee4/1e1b128b8740401f94efbc90855a0610-8eedcc25f4bb8e2ff99abb795fc50d99-ld-encrypt-stream.m3u8"
    #content = parse_m3u8(url)
    cmd = 'ffmpeg -y -i %s %s' % (url, os.path.join(base_path, "110"))
    os.system(cmd)
    #download(content)
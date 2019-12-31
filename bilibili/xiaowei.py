import xlrd
import xlwt
import os
import sys


def get_files():
    path = os.path.join(sys.path[0], "xiaowei")
    files = os.listdir(path)
    file_paths = []
    for f in files:
        if f.endswith("xlsx"):
            file_paths.append(path + '\\' + str(f))
    return file_paths


def process_file(f):
    data = xlrd.open_workbook(f)
    table = data.sheets()[0]
    rows = table.nrows

    items = table.row_values(0)
    peoples = {}
    for row in range(rows):
        if row < 1:
            continue
        people = {}
        for index, item in enumerate(items):
            people[item] = table.cell(row, index).value

        id_card = people['身份证号']
        if id_card in peoples:
            temp = peoples[id_card]
            for token in people.keys():
                if type(temp[token]) == float:
                    temp[token] = temp[token] + people[token]
        else:
            peoples[people['身份证号']] = people

    return peoples


def sort_key(elem):
    return elem['工资\n月份']


def build_all_info(data):
    f = xlwt.Workbook()
    sheet1 = f.add_sheet('sheet1', cell_overwrite_ok=True)
    index = 0

    total_info = []
    for item in data.keys():
        people_info = data[item]
        if people_info is None or len(people_info) < 1:
            continue

        temp = {}
        people_info.sort(key=sort_key)
        for people in people_info:
            temp['name'] = people['姓名']
            temp['id_card'] = people['身份证号']
            temp[people['工资\n月份']] = people['应发合计']
        total_value = 0
        for token in temp.keys():
            if token == 'name' or token == 'id_card':
                continue
            total_value += temp[token]
        temp['total'] = total_value
        total_info.append(temp)

    keys = build_all_keys(total_info)
    for key_index, key in enumerate(keys):
        sheet1.write(index, key_index, key, set_style('Times New Roman', 220, True))
    index += 1

    for info in total_info:
        for key_index, key in enumerate(keys):
            if key in info:
                sheet1.write(index, key_index, info[key], set_style('Times New Roman', 220, False))
        index += 1

    f.save('total.xls')


def set_style(name, height, bold=False):
    style = xlwt.XFStyle()
    font = xlwt.Font()
    font.name = name
    font.bold = bold
    font.color_index = 4
    font.height = height
    style.font = font
    return style


def build_all_keys(people_info):
    keys = []
    for people in people_info:
        temp = people.keys()
        for temp_token in temp:
            if temp_token not in keys:
                keys.append(temp_token)
    return keys


def query_people_by_name(query_name, data):
    f = xlwt.Workbook()
    sheet1 = f.add_sheet('sheet1', cell_overwrite_ok=True)
    index = 0
    for item in data.keys():
        people_info = data[item]
        if people_info is None or len(people_info) < 1:
            continue
        people = people_info[0]
        if people is None or '姓名' not in people:
            continue

        name = people['姓名']
        if name != query_name:
            continue

        #收集所有的key
        keys = build_all_keys(people_info)

        for key_index, key in enumerate(keys):
            sheet1.write(index, key_index, key, set_style('Times New Roman', 220, True))
        index += 1

        people_info.sort(key=sort_key)
        for people in people_info:
            for key_index, key in enumerate(keys):
                if key in people:
                    sheet1.write(index, key_index, people[key], set_style('Times New Roman', 220, False))
            index += 1

        index += 2
    f.save(query_name+'.xls')


def query_people_by_id_card(id_card, data):

    if id_card not in data:
        print('***不存在该用户***', id_card)
        return

    f = xlwt.Workbook()
    sheet1 = f.add_sheet('sheet1', cell_overwrite_ok=True)
    index = 0
    people_info = data[id_card]

    # 收集所有的key
    keys = build_all_keys(people_info)

    for key_index, key in enumerate(keys):
        sheet1.write(index, key_index, key, set_style('Times New Roman', 220, True))
    index += 1

    people_info.sort(key=sort_key)
    for people in people_info:
        for key_index, key in enumerate(keys):
            if key in people:
                sheet1.write(index, key_index, people[key], set_style('Times New Roman', 220, False))
        index += 1

    index += 2
    f.save(id_card + '.xls')


if __name__ == '__main__':
    data = {}
    files = get_files()
    for f in files:
        values = process_file(f)
        for token in values.keys():
            if token in data.keys():
                temp = data[token]
                temp.append(values[token])
            else:
                temp = []
                temp.append(values[token])
                data[token] = temp

    print('===='*40)
    print('1:输出总体员工情况')
    print('2:根据姓名查询员工情况')
    print('3:根据身份证号查询员工情况')
    print('====' * 40)
    while True:
        event_type = input('请选择您的操作：输入1/2/3进行选择：')
        if event_type == '1':
            build_all_info(data)
            print('员工总体情况表格生成')
            continue
        if event_type == '2':
            query_name = input('请输入员工姓名：')
            query_people_by_name(query_name, data)
            print('员工信息表格生成', query_name)
            continue
        if event_type == '3':
            id_card = input('请输入员工身份证号：')
            query_people_by_id_card(id_card, data)
            print('员工信息表格生成', id_card)
            continue

        print('您输入的操作不支持，请重新选择')
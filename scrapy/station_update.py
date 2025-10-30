# 爬取全国火车站点并存储到PG数据库

import requests
import psycopg2
import re
from functools import reduce


def insert_into_db(sql_vals_str):
    conn = psycopg2.connect(dbname="db_name", user="db_user",
                            password="db_password", host="db_host", port="db_port")

    full_sql = "INSERT INTO station(id, name, code, pinyin, abbr, version) VALUES {};".format(sql_vals_str)
    print(full_sql)

    cursor = conn.cursor()
    cursor.execute(full_sql)
    conn.commit()


def txt_to_data(txt, version="1.9109"):
    data_list = []
    for i in re.finditer(
            "@[a-z]+\|(?P<name>[\u4e00-\u9fa5]+)\|(?P<code>[A-Z]+)\|(?P<pinyin>[a-z]+)\|(?P<abbr>[a-z]+)\|(?P<id>\\d+)",
            txt):
        d = i.groupdict()
        d["version"] = version
        data_list.append(d)

    return data_list


if __name__ == '__main__':
    station_version = "1.9109"
    url = "https://kyfw.12306.cn/otn/resources/js/framework/station_name.js?station_version=" + station_version
    res = requests.get(url=url)

    data_list = txt_to_data(
        res.text
    )

    sql_txt = reduce(
        lambda p, n: p + "({},'{}','{}','{}','{}','{}'),".format(n['id'], n['name'], n['code'], n['pinyin'], n['abbr'],
                                                                 n['version']),
        [i for i in data_list], '')

    insert_into_db(sql_txt[:-1])

#! python3
# -*- coding:utf-8 -*-

"""
按年份爬取全国行政区划及邮编
"""

import requests
import grequests
import psycopg2
import bs4
import re
from functools import reduce

host = "http://www.mca.gov.cn"
home_page = host + "/article/sj/xzqh/1980/?"
pages = ['3', '2', '']
start_year = 1980  # include
end_year = 2019  # exclude

code_area_map = {}


def insert_into_db():
    print(code_area_map)

    sql_txt = reduce(lambda p, n: "{} ('{}','{}',{},{},{}),".format(p, n[0], n[1], n[2], n[3], n[4]),
                     code_area_map.values(), '')

    conn = psycopg2.connect(dbname="db_name", user="db_user",
                            password="db_password", host="db_host", port="db_port")
    sql = "INSERT INTO area_code_t(area_id, area_name, area_level, start_year, end_year) VALUES {};" \
        .format(sql_txt[:-1])

    cursor = conn.cursor()
    cursor.execute(sql, list(code_area_map.values()))
    conn.commit()


def filter_reqs_from_p1(p1_html):
    soup = bs4.BeautifulSoup(p1_html, 'lxml')
    year_page_reqs = []
    lines = soup.find_all(name="tr")
    for line in lines:
        cells = line.find_all(name="td")
        for cell in cells:
            cell_cnt = cell.find(name="a")

            if cell_cnt and re.match("\\d+年中华人民共和国行政区划代码.+", cell_cnt.text):
                req = grequests.request(method='GET', url=host + cell_cnt.attrs["href"])
                year_page_reqs.append(req)
    return year_page_reqs


def filter_req_from_p2(p2_res):
    p2_html = p2_res.text
    soup = bs4.BeautifulSoup(p2_html, 'lxml')
    rurl = redirect_url(soup)
    if rurl:
        return grequests.request(method='GET', url=rurl), None

    cnt_div_list = soup.select("div[class=content]")
    if len(cnt_div_list) == 0:
        return None, p2_html
    lines = cnt_div_list[0].find_all(name="a")
    for line in lines:
        if line.string.__contains__("县以上"):
            return grequests.request(method='GET', url=line.attrs['href']), None


def redirect_url(soup):
    srp_list = soup.select('script')
    for srp in srp_list:
        m = re.match('\s+window\.location\.href="(?P<url>.+)";\s*', srp.text)
        if m:
            return m.group('url')
    return None


def filter_data_from_p3(p3_html):
    soup = bs4.BeautifulSoup(p3_html, 'lxml')
    lines = soup.select("table")

    datas = []
    year = None
    d = None
    for line in lines:
        cells = line.find_all(name="td")
        sta = 0
        for cell in cells:
            if cell.text:
                if sta == 0:
                    if not year:
                        title_matcher = re.match("(?P<year>\\d{4})年(12月)?中华人民共和国(县以上)?行政区划代码", cell.text)
                        if title_matcher:
                            year = title_matcher.group('year')
                            continue
                    code_matcher = re.match("^(?P<code>\\d{6})\s*$", cell.text)
                    if code_matcher:
                        d = {}
                        d['code'] = code_matcher.group('code')
                        sta = 1
                elif sta == 1:
                    d['name'] = str.strip(cell.text)
                    datas.append(d)
                    sta = 0
    return year, datas


def data_aggregate(year, year_area_data):
    for area_data in year_area_data:
        code = area_data['code']
        name = area_data['name']
        area_in_map = code_area_map.get(code)
        year = int(year)
        c_year = year + 1
        if not area_in_map:
            code_area_map[code] = [int(code), name, level_of_area(code), year, 9999 if c_year == end_year else c_year]
        else:
            area_in_map[3] = year if year < area_in_map[3] else area_in_map[3]

            area_in_map[4] = 9999 if c_year == end_year else c_year if c_year > area_in_map[4] else area_in_map[4]


def level_of_area(area_code):
    m = re.search("(?P<z>0*)$", area_code)
    return 3 - int(len(m.group('z')) / 2)


if __name__ == '__main__':
    # res = requests.get("http://www.mca.gov.cn/article/sj/tjbz/a/1980-2000/201707141125.html")
    # year, d = filter_data_from_p3(res.text)
    # data_aggregate(year, d)
    # print(code_area_map)

    try:
        for p in pages:
            p1_html = requests.get(url=home_page + p).text
            p2_reqs = filter_reqs_from_p1(p1_html)

            p2_res = grequests.map(requests=p2_reqs, size=5)
            p3_reqs = []
            p3_htmls = []
            for p2 in p2_res:
                res = filter_req_from_p2(p2)
                req_for_p3, p3_html = res
                if req_for_p3:
                    p3_reqs.append(req_for_p3)
                else:
                    p3_htmls.append(p3_html)

            p3_res = grequests.map(requests=p3_reqs, size=5)
            for p3 in p3_res:
                year, data = filter_data_from_p3(p3.text)
                print("%s: %s" % (year, data))
                data_aggregate(year, data)
            for p3_html in p3_htmls:
                year, data = filter_data_from_p3(p3_html)
                print("%s: %s" % (year, data))
                data_aggregate(year, data)
    except Exception as e:
        print(e)
    insert_into_db()

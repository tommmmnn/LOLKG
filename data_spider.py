#  -*- encoding:utf-8 -*-
# Author: tommmmnn
# email: hwhuang00@163.com
# Date: 2022-06-08



from urllib import request
from bs4 import BeautifulSoup
import pymongo


class LOLSpider:
    def __init__(self):
        # 使用mongo数据库存储数据
        self.conn = pymongo.MongoClient()
        self.db = self.conn['hero']
        self.col = self.db['data']
        self.col2 = self.db['rune']

    # 获取网页html文件
    def get_html(self, url):
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0'}
        req = request.Request(url = url, headers = headers)
        res = request.urlopen(req)
        html = res.read().decode('utf-8')
        return html

    def get_position_info(self, url, hero_name):
        position = []
        # 解析html文本
        hero_url = url + "/" + hero_name
        html = self.get_html(hero_url)
        soup = BeautifulSoup(html, 'lxml')

        # 英雄位置
        container = soup.find("div", id="content-header")
        for url in container.find_all("a"):
            #提取href中以"/"开头的元素（即各个英雄网页对应的网址）
            if url.get("href").startswith("/champions/" + hero_name + '/') and url.get("href").endswith('/build'):
                tmp = url.get("href")
                index = tmp.index("/champions/"+hero_name) + len("/champions/"+hero_name)
                position_tmp = (tmp[index+1:]).replace('/build', '')
                if position_tmp not in position:
                    position.append(position_tmp)

        return position


    def get_counters(self, url, hero_name, hero_position):
        weak_counter_data = []
        strong_couter_data = []
        for hero_pos in hero_position:
            counters_url = url + "/" +  hero_name + "/" + hero_pos + "/counters"
            html = self.get_html(counters_url)
            soup = BeautifulSoup(html, 'lxml')

            counters_container = soup.find_all("tr", class_="css-1opotah eocu2m74")
            for ct in counters_container:
                hero_name = (ct.find("div", class_="css-aj4kza eocu2m71")).get_text()
                hero_win_rate = float((ct.find("span", class_="css-ekbdas eocu2m73")
                                       .get_text().replace('<!-- -->%','')).replace('%',''))
                if 53 > hero_win_rate > 50:
                    weak_counter_data.append(hero_name.lower())
                elif hero_win_rate > 53:
                    strong_couter_data.append(hero_name.lower())

            break           # 暂时只考虑一个位置的counter

        return weak_counter_data, strong_couter_data

    def get_runes(self, hero_url):
        html = self.get_html(hero_url)
        soup = BeautifulSoup(html, 'lxml')

        runes = []
        runes_container = soup.find("li", class_="css-luxpgs e80y3m2")
        for img in runes_container.find_all("img"):
            runes.append(img.get("alt"))
        return runes

    # 解析op.gg页面获得每个英雄的网页
    def get_basic_data(self, url):
        # 获取html
        html = self.get_html(url)
        hero_links = []
        hero_names = []

        #print(html)
        # 通过BeautifulSoup对html进行解析
        soup = BeautifulSoup(html, "lxml")
        # 获取div中 id为content-container 的部分
        container = soup.find("div", id="content-container")

        # # 获取上面的所有的<a>
        # for url in container.find_all("a"):
        #     #提取href中以"/"开头的元素（即各个英雄网页对应的网址）
        #     if url.get("href").startswith("/champions"):
        #         hero_info_link = "https://op.gg" + url.get("href")
        #         hero_infos.append(hero_info_link)

        # 获取上面的所有的<img>并获取其中的"alt"内容
        for img in container.find_all("img"):
            hero_name = img.get("alt")
            if hero_name.lower() not in hero_names:
                hero_names.append(hero_name)
                hero_info_link = "https://op.gg" + '/champions/' + hero_name
                hero_links.append(hero_info_link)
        url_base = 'https://op.gg/champions'
        added_runes = []
        for i in range(len(hero_links)):
            if hero_names[i] == '' or hero_names[i] == 'skarner':
                continue
            if hero_names[i] == 'Wukong':
                break
            basic_data = {}
            rune_data = {}
            basic_data['hero_url'] = hero_links[i]
            basic_data['hero_name'] = hero_names[i]
            runes = self.get_runes(hero_links[i])
            basic_data['primary_rune'] = runes[1]
            basic_data['secondary_rune'] = runes[2]
            rune_data['second_level'] = runes[1]
            rune_data['first_level'] = runes[0]
            if runes[1] not in added_runes:
                added_runes.append(runes[1])
                print(added_runes)
                self.col2.insert_one(rune_data)

            basic_data['hero_position'] = self.get_position_info(url_base, hero_names[i])
            basic_data['hero_weak_counter'], basic_data['hero_strong_counter'] = self.get_counters(
                url_base, hero_names[i], basic_data['hero_position'])
            # print('hero:  ' + hero_names[i] + '\t hero_link   ' + hero_links[i])
            self.col.insert_one(basic_data)
            print('hero:  '+ hero_names[i] + '\t hero_link   ' + hero_links[i] + '\tposition: {}\tstrong_couters_num:{}'
                  .format( basic_data['hero_position'], len(basic_data['hero_strong_counter'])))
        print("collect basic data:hero_name and hero_url")




# 主程序入口
if __name__ == '__main__':
    lol = LOLSpider()
    url = "https://www.op.gg/champions"
    lol.get_basic_data(url)

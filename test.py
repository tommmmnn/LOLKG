from urllib import request
from bs4 import BeautifulSoup


def get_html(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:6.0) Gecko/20100101 Firefox/6.0'}
    req = request.Request(url=url, headers=headers)
    res = request.urlopen(req)
    html = res.read().decode('utf-8')
    return html

def get_data(url):
    html = get_html(url)
    soup = BeautifulSoup(html, 'lxml')


    msg_lsit = []
    container = soup.find("div", class_ = "carrer")
    message = container.find_all("div", class_ = "text")

    for msg in message:
        m = msg.text.split(":")[1]
        msg_lsit.append(m)


def get_url(url):
    html = get_html(url)
    soup = BeautifulSoup(html, 'lxml')


    url_list = []
    container = soup.find("ul", class_ = "xx_zm_nr")
    urls = container.find_all("a")
    for url in urls:
        tmp = url.get("href")
        url_list.append(tmp)

    print(url_list)

def get_list_txt(url):
    html = get_html(url)
    hero_names = []

    soup = BeautifulSoup(html, "lxml")
    container = soup.find("div", id="content-container")
    with open("hero.txt", "w") as f:
        for img in container.find_all("img"):
            hero_name = img.get("alt")
            if hero_name == "Wukong":
                break
            if hero_name.lower() not in hero_names:
                hero_names.append(hero_name)
                print(hero_name)
                f.write(hero_name+"\n")



if __name__ == '__main__':
    get_list_txt("https://op.gg/champions")
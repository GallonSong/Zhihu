# coding:utf8
import json
import requests
from bs4 import BeautifulSoup as bs

session = requests.session()

HOST = 'www.zhihu.com'
HEADER = {
    'Cookie': '',
    'Accept': "*/*",
    'Content-Type': "application/x-www-form-urlencoded; charset=UTF-8",
    'Connection': 'keep-alive',
    'Host': HOST,
    'Origin': 'https://www.zhihu.com',
    'Referer': 'https://www.zhihu.com/topic/19551915/organize/entire',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36',
    'X-Requested-With': 'XMLHttpRequest'
}
TOPIC_CODE = ''
XSRF = ''


def set_cookie():
    with open('/Users/inad/Documents/scripts/zhihu/cookie.txt', 'r') as f:
        cookie = f.read()
    if not cookie:
        return False
    HEADER['Cookie'] = cookie
    return True


def set_topic_address():
    topic_code = raw_input("请输入话题编号: ")  # 19551915 汽车
    if not topic_code:
        return False
    return topic_code, 'https://www.zhihu.com/topic/' + topic_code + '/organize/entire'


def get_xsrf():
    session.get('http://www.zhihu.com', headers=HEADER)
    xsrf = bs(
        session.get('http://www.zhihu.com', headers=HEADER).content, 'html.parser'
    ).find('input', attrs={'name': '_xsrf'})['value']
    return xsrf


def get_data(topic_code):
    hot_page = 'https://www.zhihu.com/topic/' + topic_code + '/hot'
    data_response = session.get(hot_page, headers=HEADER)

    if data_response.status_code == 200:
        page_html = bs(data_response.text, 'html.parser')
        key_word = page_html.find("div", class_="topic-name").find("h1").string.encode('utf8')
        question_count = page_html.find("meta", itemprop="questionCount")["content"].encode('utf8')
        top_answer_count = page_html.find("meta", itemprop="topAnswerCount")["content"].encode('utf8')
        follower_count = page_html.find("div", class_="zm-topic-side-followers-info").find("strong").string.encode('utf8')
        print ','.join(map(str, [code, key_word, question_count, top_answer_count, follower_count]))
    else:
        print data_response.status_code, data_response.text


def get_topics(topic_tree):
    for topic_tuple in topic_tree:
        if 'topic' in topic_tuple:  # ('topic', 'name', 'code') | ('load', '', '', 'code')
            topics[topic_tuple[2]] = topic_tuple[1]
        elif 'load' in topic_tuple:
            child_code = None
            if u'显示子话题' in topic_tuple:
                child_code = topic_tuple[3]
                if child_code not in listed_topic:
                    # print '显示', child_code
                    listed_topic.append(child_code)
                    child_topic_page = 'https://www.zhihu.com/topic/' + code + '/organize/entire?child=&parent=' + child_code
                else:
                    continue
            elif u'加载更多' in topic_tuple:
                child_code = topic_tuple[2]
                if child_code not in loaded_topic:
                    # print '加载', child_code
                    loaded_topic.append(child_code)
                    child_topic_page = 'https://www.zhihu.com/topic/' + code + '/organize/entire?child=' + child_code +'&parent=' + code
                else:
                    return

            if child_code:
                child_response = requests.post(child_topic_page, data={'_xsrf': XSRF}, headers=HEADER)
                if child_response.status_code == 200:
                    get_topics(json.loads(child_response.content)['msg'])
        elif not topic_tuple:
            pass
        else:
            get_topics(topic_tuple)


if __name__ == "__main__":
    if not set_cookie():
        print("请先登录知乎, 并将cookie粘贴在Cookie.txt文件中.")
        raise Exception

    code, topic_page = set_topic_address()
    if not code:
        print("请输入有效的话题编号.")
        raise Exception

    topics = dict()
    listed_topic, loaded_topic = list(), list()
    XSRF = get_xsrf()
    response = requests.post(topic_page, data={'_xsrf': XSRF}, headers=HEADER)

    if response.status_code == 200:
        get_topics(json.loads(response.content)['msg'])
    else:
        print response.status_code, response.text

    for code in topics.keys():
        try:
            get_data(code)
        except Exception as e:
            print e
            continue

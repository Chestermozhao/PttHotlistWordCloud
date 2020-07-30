import re
import os
import time
import arrow
import asyncio
import requests
import matplotlib.pyplot as plt

from pyhanlp import *
from imageio import imread
from bs4 import BeautifulSoup as bs
from requests.adapters import HTTPAdapter
from concurrent.futures import ThreadPoolExecutor
from wordcloud import WordCloud

words_count_dict = {}

# font type
base_path = os.getcwd()
font_path = base_path + '/fonts/SourceHanSerif/SourceHanSerifK-Light.otf'

# backgroud image
image_path = base_path + '/bck_img/img_bck.png'
back_coloring = imread(image_path)

# skip_word_pat
skip_word_pat = re.compile("文章|https|http|html|JPTT|bbs|標題|ptt|女孩|八卦|版|WomenTalk|批踢踢")


def paint_word_cloud():
    wordcloud = WordCloud(
        font_path=font_path,
        background_color="black",
        max_words=2000,
        mask=back_coloring,
        max_font_size=100,
        random_state=42,
        width=1000,
        height=860,
        margin=2
    ).generate_from_frequencies(words_count_dict)
    plt.figure()
    plt.imshow(wordcloud, interpolation="bilinear")
    plt.axis("off")
    filename = "wordcloud_imgs/{date}_word_cloud.jpg".format(date=arrow.now().format("YYYY-MM-DD"))
    plt.savefig(filename)

def _segment(source):
    for term in HanLP.segment(source):
        pos = term.nature.__str__()
        word = term.word
        if pos.startswith("n"):
            if skip_word_pat.search(word):
                continue
            if word in words_count_dict:
                words_count_dict[word] += 1
            else:
                words_count_dict[word] = 1


def fetch(session, url):
    with session.get(url) as response:
        src_html = response.text
        soup = bs(src_html, "html.parser")
        main_content = soup.select("#main-content")
        for d in main_content:
            main_c = d.get_text()
            _segment(main_c)


async def get_data_asynchronous(urls):
    with ThreadPoolExecutor(max_workers=20) as executor:
        with requests.Session() as session:
            # Set any session parameters here before calling `fetch`
            session.mount('http://', HTTPAdapter(max_retries=3))
            session.mount('https://', HTTPAdapter(max_retries=3))
            loop = asyncio.get_event_loop()
            tasks = [
                loop.run_in_executor(
                    executor,
                    fetch,
                    *(session, url)
                )
                for url in urls
            ]
            for response in await asyncio.gather(*tasks):
                pass


async def gen_today_freq_dict():
    hotlist_url = "https://moptt.azurewebsites.net/api/v2/hotpost?b=Gossiping&b=Boy-Girl&b=Beauty&b=marvel&b=WomenTalk&b=movie&page=%257B%2522skip%2522%253A0%257D"
    headers = {"cookie": "over18=1;", "Authorization": "cMIS1Icr95gnR2U19hxO2K7r6mYQ96vp"}
    resp = requests.get(hotlist_url, headers=headers)
    res_json = resp.json()["posts"]
    article_urls = [r["url"] for r in res_json]
    await get_data_asynchronous(article_urls)
    #article_titles = [r["title"] for r in res_json]
    #for title in article_titles:
    #    _segment(title)


loop = asyncio.get_event_loop()
loop.run_until_complete(gen_today_freq_dict())
paint_word_cloud()

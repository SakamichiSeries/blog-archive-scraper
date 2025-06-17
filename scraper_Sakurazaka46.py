from bs4 import BeautifulSoup
import requests
import time
import random
import json
import urllib.parse
from utils import add_host, download_image_return_path


def get_profile(member_id: str):
    if str(member_id).startswith("2001"):
        return {
            "member_name_kanji": "四期生",
            "member_name_kana": "",
            "member_name_romaji": "sakurazaka46-yonkisei",
            "repo_name": "sakurazaka46-yonkisei-blog-archive",
            "SNS": {},
            "生年月日": "",
            "血液型": "",
            "星座": "",
            "身長": "",
            "profile_pic": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7a/Sakurazaka46_logo.svg/386px-Sakurazaka46_logo.svg.png",
        }
    result = {}
    profile_url = f"https://sakurazaka46.com/s/s46/artist/{member_id}"
    soup = BeautifulSoup(requests.get(profile_url).content, "lxml")
    result["member_name_kanji"] = soup.find_all("p", class_="name")[0].get_text()
    result["member_name_kana"] = soup.find_all("p", class_="kana")[0].get_text()
    with open("members.json") as members_json:
        members = json.load(members_json)
        for member in members["S"]:
            if member[0] == result["member_name_kanji"]:
                result["member_name_romaji"] = member[1]
                break
    result["repo_name"] = (
        result["member_name_romaji"].lower().replace(" ", "-") + "-blog-archive"
    )

    dltb = soup.find_all("dl", class_="dltb")[0]
    for i in range(5):  # 生年月日 星座 身長 出身地 血液型
        key = dltb.find_all("dt")[i].get_text()
        result[key] = dltb.find_all("dd")[i].get_text()

    result["SNS"] = {}
    if soup.find_all("dl", class_="prof-elem-sns"):
        for a in soup.find_all("dl", class_="prof-elem-sns")[0].find_all("a"):
            # a.parent.get("class") insta
            if a.parent.get("class")[0] == "insta":
                result["SNS"]["Instagram"] = a.get("href")
            else:
                raise Exception

    print(result)
    result["profile_pic"] = download_image_return_path(
        soup.find_all("p", class_="ph")[0].find_all("img")[0].get("src"),
        result["repo_name"],
        "S",
    )

    print(result)
    return result


def get_blog_url_list(member_id: str, previous_blog_url_list: list):
    current_page = 1
    current_url = f"https://sakurazaka46.com/s/s46/diary/blog/list?ct={member_id}"
    articles_url_list = []

    while True:
        soup = BeautifulSoup(requests.get(current_url).content, "lxml")
        # print(soup.prettify())
        a_list = soup.find_all("ul", class_="com-blog-part box3 fxpc")[0].find_all("a")
        for a in a_list:
            url_with_param = add_host(a.get("href"), "S")
            # Parse the URL
            parsed_url = urllib.parse.urlparse(url_with_param)
            # Reconstruct the URL without the query parameters
            url_without_params = urllib.parse.urlunparse(
                (parsed_url.scheme, parsed_url.netloc, parsed_url.path, "", "", "")
            )
            # Previously crawled
            if url_without_params in previous_blog_url_list:
                return articles_url_list
            articles_url_list.append(url_without_params)
        print(f"{len(a_list)} results on page {current_page}. ({current_url})")

        next_li_div = soup.find_all("div", class_="com-pager")
        if "→" in next_li_div[-1].get_text():
            current_url = f"https://sakurazaka46.com/s/s46/diary/blog/list?ct={member_id}&page={current_page}"
            current_page += 1
            # print(articles_url_list)
            # print(current_url)

            # when testing, uncomment below line to only get page 1
            # break
            time.sleep(random.randint(1, 3))
        else:
            break

    return articles_url_list


def get_blog_content(url: str, repo_name: str):
    while True:
        try:
            data = {}
            soup = BeautifulSoup(requests.get(url).content, "lxml")

            # https://sakurazaka46.com/s/s46/diary/detail/57724
            data["title"] = (
                soup.find_all("div", class_="inner title-wrap")[0].get_text().strip()
            )

            if data["title"] == "":
                data["title"] = "(無題)"

            data["time"] = (
                soup.find_all("article")[0]
                .find_all("p", class_="date wf-a")[-1]
                .get_text()
                .strip()
            )

            data["url"] = url

            content = soup.find_all("div", class_="box-article")[0]
            img_list = content.find_all("img")
            for img in img_list:
                # Check if the img has a src attribute
                if img.get("src"):
                    img["src"] = download_image_return_path(
                        img.get("src"), repo_name, "S"
                    )

            data["content"] = str(content)

            return data
        except Exception as e:
            print(e)
            time.sleep(random.randint(30, 60))
            pass

from bs4 import BeautifulSoup
import requests
import time
import random
import json
import urllib.parse
from utils import add_host, download_image_return_path


def get_profile(member_id: str):
    if str(member_id).startswith("40003"):
        return {
            "member_name_kanji": "運営スタッフ",
            "member_name_kana": "",
            "member_name_romaji": "staff",
            "repo_name": "staff-blog-archive",
            "SNS": {},
            "生年月日": "",
            "血液型": "",
            "星座": "",
            "身長": "",
            "profile_pic": "https://upload.wikimedia.org/wikipedia/commons/9/92/Nogizaka46_logo.png",
        }
    if str(member_id).startswith("40004"):
        return {
            "member_name_kanji": "3期生",
            "member_name_kana": "",
            "member_name_romaji": "sankisei",
            "repo_name": "sankisei-blog-archive",
            "SNS": {},
            "生年月日": "",
            "血液型": "",
            "星座": "",
            "身長": "",
            "profile_pic": "https://upload.wikimedia.org/wikipedia/commons/9/92/Nogizaka46_logo.png",
        }
    if str(member_id).startswith("40005"):
        return {
            "member_name_kanji": "4期生",
            "member_name_kana": "",
            "member_name_romaji": "yonkisei",
            "repo_name": "yonkisei-blog-archive",
            "SNS": {},
            "生年月日": "",
            "血液型": "",
            "星座": "",
            "身長": "",
            "profile_pic": "https://upload.wikimedia.org/wikipedia/commons/9/92/Nogizaka46_logo.png",
        }
    if str(member_id).startswith("40001"):
        return {
            "member_name_kanji": "新4期生",
            "member_name_kana": "",
            "member_name_romaji": "shinyonkisei",
            "repo_name": "shinyonkisei-blog-archive",
            "SNS": {},
            "生年月日": "",
            "血液型": "",
            "星座": "",
            "身長": "",
            "profile_pic": "https://upload.wikimedia.org/wikipedia/commons/9/92/Nogizaka46_logo.png",
        }
    if str(member_id).startswith("40007"):
        return {
            "member_name_kanji": "5期生",
            "member_name_kana": "",
            "member_name_romaji": "gokisei",
            "repo_name": "gokisei-blog-archive",
            "SNS": {},
            "生年月日": "",
            "血液型": "",
            "星座": "",
            "身長": "",
            "profile_pic": "https://upload.wikimedia.org/wikipedia/commons/9/92/Nogizaka46_logo.png",
        }
    if str(member_id).startswith("40008"):
        return {
            "member_name_kanji": "6期生",
            "member_name_kana": "",
            "member_name_romaji": "rokisei",
            "repo_name": "rokisei-blog-archive",
            "SNS": {},
            "生年月日": "",
            "血液型": "",
            "星座": "",
            "身長": "",
            "profile_pic": "https://upload.wikimedia.org/wikipedia/commons/9/92/Nogizaka46_logo.png",
        }
    result = {}
    profile_url = f"https://www.nogizaka46.com/s/n46/artist/{member_id}"
    soup = BeautifulSoup(requests.get(profile_url).content, "lxml")
    result["member_name_kanji"] = soup.find_all(
        "h1", class_="md--hd__ttl f--head a--tx js-tdi js-membername"
    )[0].get_text()
    result["member_name_kana"] = soup.find_all(
        "p", class_="md--hd__j f--head a--tx js-tdi"
    )[0].get_text()
    # result["member_name_romaji"] = soup.find_all(
    #     "p", class_="md--hd__e f--head a--tx js-tdi"
    # )[0].get_text()
    with open("members.json") as members_json:
        members = json.load(members_json)
        for member in members["N"]:
            if member[0] == result["member_name_kanji"]:
                result["member_name_romaji"] = member[1]
                break

    result["repo_name"] = (
        result["member_name_romaji"].lower().replace(" ", "-") + "-blog-archive"
    )

    dl_list = soup.find_all("dl", class_="md--hd__data a--tx js-tdi")
    for dl in dl_list:
        key = dl.find_all("dt")[0].get_text()
        result["SNS"] = {}
        if key != "SNS":
            result[key] = dl.find_all("dd")[0].get_text()
        else:
            for a in dl.find_all("dd")[0].children:
                result["SNS"][a.get_text()] = a.get("href")
    print(result)
    result["profile_pic"] = download_image_return_path(
        soup.find_all("div", class_="md--hd__fig a--img js-pos m--fig")[0]
        .find_all("div")[0]
        .get("data-src"),
        result["repo_name"],
        "N",
    )

    print(result)
    return result


def get_blog_url_list(member_id: str, previous_blog_url_list: list):
    current_page = 1
    current_url = (
        f"https://www.nogizaka46.com/s/n46/diary/MEMBER/list?page=0&ct={member_id}"
    )
    articles_url_list = []

    while True:
        soup = BeautifulSoup(requests.get(current_url).content, "lxml")
        # print(soup.prettify())
        a_list = soup.find_all("a", class_="bl--card js-pos a--op hv--thumb")
        for a in a_list:
            url_with_param = add_host(a.get("href"), "N")
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

        next_li = soup.find_all("li", class_="next")
        if next_li:
            for a in next_li[0]:
                current_url = add_host(a.get("href"), "N")
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
            data["title"] = (
                soup.find_all("h1", class_="bd--hd__ttl f--head a--tx js-tdi")[0]
                .get_text()
                .strip()
            )
            if data["title"] == "":
                data["title"] = "(無題)"

            data["time"] = (
                soup.find_all("p", class_="bd--hd__date a--tx js-tdi")[0]
                .get_text()
                .strip()
            )

            data["url"] = url

            content = soup.find_all("div", class_="bd--edit")[0]
            img_list = content.find_all("img")
            for img in img_list:
                # Check if the img has a src attribute
                if img.get("src"):
                    img["src"] = download_image_return_path(
                        img.get("src"), repo_name, "N"
                    )

            data["content"] = str(content)

            return data
        except Exception as e:
            print(e)
            time.sleep(random.randint(30, 60))
            pass

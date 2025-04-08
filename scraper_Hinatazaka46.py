from bs4 import BeautifulSoup
import requests
import time
import random
import json
import urllib.parse
from utils import add_host, download_image_return_path


def get_profile(member_id: str):
    if str(member_id).startswith("000"):
        return {
            "member_name_kanji": "ポカ",
            "member_name_kana": "ポカ",
            "member_name_romaji": "poka",
            "repo_name": "poka-blog-archive",
            "SNS": {},
            "生年月日": "",
            "血液型": "",
            "星座": "",
            "身長": "",
            "profile_pic": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d4/Hinatazaka46_logomark_2021.svg/386px-Hinatazaka46_logomark_2021.svg.png",
        }
    if str(member_id).startswith("3000"):
        return {
            "member_name_kanji": "五期生",
            "member_name_kana": "",
            "member_name_romaji": "hinatazaka46-gokisei",
            "repo_name": "hinatazaka46-gokisei-blog-archive",
            "SNS": {},
            "生年月日": "",
            "血液型": "",
            "星座": "",
            "身長": "",
            "profile_pic": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d4/Hinatazaka46_logomark_2021.svg/386px-Hinatazaka46_logomark_2021.svg.png",
        }
    result = {}

    profile_url = f"https://www.hinatazaka46.com/s/official/artist/{member_id}"
    soup = BeautifulSoup(requests.get(profile_url).content, "lxml")

    temp_en = soup.find_all("span", class_="name_en")[0].get_text()
    result["member_name_kanji"] = (
        soup.find_all("div", class_="c-member__name--info")[0]
        .get_text()
        .replace(temp_en, "")
        .strip()
    )
    result["member_name_kana"] = (
        soup.find_all("div", class_="c-member__kana")[0].get_text().strip()
    )

    with open("members.json") as members_json:
        members = json.load(members_json)
        for member in members["H"]:
            if member[0] == result["member_name_kanji"]:
                result["member_name_romaji"] = member[1]
                break

    result["repo_name"] = (
        result["member_name_romaji"].lower().replace(" ", "-") + "-blog-archive"
    )

    info_table = soup.find_all("table", class_="p-member__info-table")[0]
    for i in range(5):  # 生年月日 星座 身長 出身地 血液型
        key = info_table.find_all("td")[i * 2].get_text().strip()
        result[key] = info_table.find_all("td")[i * 2 + 1].get_text().strip()

    result["SNS"] = {}
    temp_td__text_list = soup.find_all("td", class_="c-member__info-td__text")
    if len(temp_td__text_list) > 5:
        for a in temp_td__text_list[5].find_all("a"):
            if "instagram" in a.get("href"):
                result["SNS"]["Instagram"] = a.get("href")
            else:
                raise Exception

    print(result)
    result["profile_pic"] = download_image_return_path(
        soup.find_all("div", class_="c-member__thumb c-member__thumb__large")[0]
        .find_all("img")[0]
        .get("src"),
        result["repo_name"],
        "H",
    )

    print(result)
    return result


def get_blog_url_list(member_id: str, previous_blog_url_list: list):
    current_page = 0
    articles_url_list = []

    while True:
        current_url = f"https://www.hinatazaka46.com/s/official/diary/member/list?page={current_page}&ct={member_id}"
        soup = BeautifulSoup(requests.get(current_url).content, "lxml")
        # print(soup.prettify())
        a_list = soup.find_all("a", string="個別ページ")
        for a in a_list:
            url_with_param = add_host(a.get("href"), "H")
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

        next_page = soup.find_all(
            "li", class_="c-pager__item--count c-pager__item--next"
        )
        if next_page:
            current_page += 1

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
                soup.find_all("div", class_="c-blog-article__title")[0]
                .get_text()
                .strip()
            )
            if data["title"] == "":
                data["title"] = "(無題)"

            data["time"] = (
                soup.find_all("div", class_="c-blog-article__date")[0]
                .get_text()
                .strip()
            )

            data["url"] = url

            content = soup.find_all("div", class_="c-blog-article__text")[0]
            img_list = content.find_all("img")
            for img in img_list:
                # Check if the img has a src attribute
                if img.get("src"):
                    img["src"] = download_image_return_path(
                        img.get("src"), repo_name, "H"
                    )

            data["content"] = str(content)

            return data
        except Exception as e:
            print(e)
            time.sleep(random.randint(30, 60))
            pass

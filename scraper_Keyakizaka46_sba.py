from bs4 import BeautifulSoup
import requests
import time
import random
import json
import urllib.parse
from utils import add_host, download_image_return_path


def get_profile(member_id: str):
    result = {}
    profile_url = f"https://archive.sakamichi.co/keyaki/members/{member_id}/"
    soup = BeautifulSoup(requests.get(profile_url).content, "lxml")
    result["member_name_kanji"] = soup.find_all(
        "a", class_="blogs-view__breadcrumbs__link"
    )[1].get_text()
    # result["member_name_kana"] = soup.find_all("p", class_="kana")[0].get_text()
    print(result["member_name_kanji"])
    with open("members.json") as members_json:
        members = json.load(members_json)
        for member in members["SG"]:
            if member[0] == result["member_name_kanji"]:
                result["member_name_romaji"] = member[1]
                break
    result["repo_name"] = (
        result["member_name_romaji"].lower().replace(" ", "-") + "-blog-archive"
    )

    # dltb = soup.find_all("dl", class_="dltb")[0]
    # for i in range(5):  # 生年月日 星座 身長 出身地 血液型
    #     key = dltb.find_all("dt")[i].get_text()
    #     result[key] = dltb.find_all("dd")[i].get_text()

    # result["SNS"] = {}
    # if soup.find_all("dl", class_="prof-elem-sns"):
    #     for a in soup.find_all("dl", class_="prof-elem-sns")[0].find_all("a"):
    #         # a.parent.get("class") insta
    #         if a.parent.get("class")[0] == "insta":
    #             result["SNS"]["Instagram"] = a.get("href")
    #         else:
    #             raise Exception

    print(result)
    # result["profile_pic"] = download_image_return_path(
    #     soup.find_all("p", class_="ph")[0].find_all("img")[0].get("src"),
    #     result["repo_name"],
    #     "S",
    # )

    print(result)
    return result


def get_blog_url_list(member_id: str, previous_blog_url_list: list):
    current_page = 1
    current_url = f"https://archive.sakamichi.co/keyaki/members/{member_id}"
    articles_url_list = []

    while True:
        soup = BeautifulSoup(requests.get(current_url).content, "lxml")
        # print(soup.prettify())
        a_list = soup.find_all(
            "div", class_="blog-list blogs-view__blogs blogs-view__blogs--margin-side"
        )[0].find_all("a")
        for a in a_list:
            url_with_param = a.get("href").replace(
                "/keyaki/blogs/",
                "https://www.keyakizaka46.com/s/k46o/diary/detail/",
            )
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

        next_a_div = soup.find_all("a", class_="pagination__item__link right")
        if next_a_div:
            current_page += 1
            current_url = f"https://archive.sakamichi.co/keyaki/members/{member_id}/p{current_page}"
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
            sba_url = url.replace(
                "https://www.keyakizaka46.com/s/k46o/diary/detail/",
                "https://archive.sakamichi.co/keyaki/blogs/",
            )
            soup = BeautifulSoup(requests.get(sba_url).content, "lxml")

            # https://archive.sakamichi.co/keyaki/blogs/35793
            data["title"] = (
                soup.find_all("h1", class_="blog-view__blog__title")[0]
                .get_text()
                .strip()
            )

            if data["title"] == "":
                data["title"] = "(無題)"

            data["time"] = soup.find_all("time")[0].get_text().strip()

            data["url"] = url

            content = soup.find_all(
                "section", class_="content blog-view__blog__content markdown-body"
            )[0]
            img_list = content.find_all("img")
            for img in img_list:
                # Check if the img has a src attribute
                if img.get("src"):
                    img["src"] = download_image_return_path(
                        img.get("src"), repo_name, "K_sba"
                    )

            data["content"] = str(content)

            return data
        except Exception as e:
            print(e)
            time.sleep(random.randint(30, 60))
            pass

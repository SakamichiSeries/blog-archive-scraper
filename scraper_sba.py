import requests
import json
import os
import subprocess
import sys
from github import Github

from scraper_Keyakizaka46_sba import (
    get_profile as get_profile_K_sba,
    get_blog_url_list as get_blog_url_list_K_sba,
    get_blog_content as get_blog_content_K_sba,
)

from scraper_Hinatazaka46_sba import (
    get_profile as get_profile_H_sba,
    get_blog_url_list as get_blog_url_list_H_sba,
    get_blog_content as get_blog_content_H_sba,
)

from scraper_Sakurazaka46_sba import (
    get_profile as get_profile_S_sba,
    get_blog_url_list as get_blog_url_list_S_sba,
    get_blog_content as get_blog_content_S_sba,
)

# from scraper_Sakurazaka46 import (
#     get_profile as get_profile_S,
#     get_blog_url_list as get_blog_url_list_S,
#     get_blog_content as get_blog_content_S,
# )
# from scraper_Hinatazaka46 import (
#     get_profile as get_profile_H,
#     get_blog_url_list as get_blog_url_list_H,
#     get_blog_content as get_blog_content_H,
# )


# pip install lxml
# https://www.crummy.com/software/BeautifulSoup/bs4/doc/#the-keyword-arguments:~:text=External%20Python%20dependency-,If%20you%20can%2C%20I%20recommend%20you%20install%20and%20use%20lxml%20for%20speed.,-Note%20that%20if


def get_profile(member_id: str, group: str):
    if group == "K_sba":
        return get_profile_K_sba(member_id)
    elif group == "H_sba":
        return get_profile_H_sba(member_id)
    elif group == "S_sba":
        return get_profile_S_sba(member_id)
    # elif group == "H":
    #     return get_profile_H(member_id)
    # elif group == "S":
    #     return get_profile_S(member_id)
    else:
        raise Exception


def get_blog_url_list(member_id: str, previous_blog_url_list: list, group: str):
    if group == "K_sba":
        return get_blog_url_list_K_sba(member_id, previous_blog_url_list)
    elif group == "H_sba":
        return get_blog_url_list_H_sba(member_id, previous_blog_url_list)
    elif group == "S_sba":
        return get_blog_url_list_S_sba(member_id, previous_blog_url_list)
    # elif group == "H":
    #     return get_blog_url_list_H(member_id, previous_blog_url_list)
    # elif group == "S":
    #     return get_blog_url_list_S(member_id, previous_blog_url_list)
    else:
        raise Exception


def get_blog_content(url: str, repo_name: str, group: str):
    if group == "K_sba":
        return get_blog_content_K_sba(url, repo_name)
    elif group == "H_sba":
        return get_blog_content_H_sba(url, repo_name)
    elif group == "S_sba":
        return get_blog_content_S_sba(url, repo_name)
    # elif group == "H":
    #     return get_blog_content_H(url, repo_name)
    # elif group == "S":
    #     return get_blog_content_S(url, repo_name)
    else:
        raise Exception


def scrape_repo(member_id: str, group: str, du_results: list):
    # fix https://www.nogizaka46.com/s/n46/diary/detail/56176
    sys.setrecursionlimit(4646)

    update_repo = not not os.getenv("RUNNING_GITHUB_ACTIONS")

    result = get_profile(member_id, group)
    repo_name = result["repo_name"]
    # Fix profile_pic already exists leading to clone failing
    subprocess.run(["rm", "-rf", repo_name])

    if update_repo:
        # Replace with your GitHub token and organization name
        token = os.getenv("TOKEN_GITHUB")
        organization_name = "SakamichiSeries"

        g = Github(token)
        org = g.get_organization(organization_name)
        try:
            repo = org.get_repo(repo_name)
            print(f"Repository '{repo_name}' already exists.")
        except:
            # Create a new repository
            repo = org.create_repo(name=repo_name)
            print(f"Creating repository '{repo_name}'.")
        # clone_url = repo.clone_url
        clone_url = f"https://{token}@github.com/SakamichiSeries/{repo_name}.git"
        subprocess.run(["date"])
        subprocess.run(["git", "clone", clone_url])
        subprocess.run(["date"])
    else:
        os.makedirs(repo_name, exist_ok=True)

    result = get_profile(member_id, group)

    clean_repo = False
    if clean_repo:
        # clean repo to crawl again
        subprocess.run(["rm", "-rf", repo_name + "/.github"])
        subprocess.run(["rm", "-rf", repo_name + "/files"])
        subprocess.run(["rm", "-rf", repo_name + "/images"])
        subprocess.run(["rm", "-rf", repo_name + "/result.json"])

    previous_blog_url_list = []
    if os.path.exists(repo_name + "/result.json"):
        with open(repo_name + "/result.json") as previous_json:
            previous_result = json.load(previous_json)
            for blog_entry in previous_result["blog"]:
                previous_blog_url_list.append(blog_entry["url"])
                # print("Previous blog url: " + blog_entry["url"])
    blogs_url_list = get_blog_url_list(member_id, previous_blog_url_list, group)
    result["blog"] = []

    for i in range(len(blogs_url_list)):
        print(f"downloading {i+1}/{len(blogs_url_list)}: {blogs_url_list[i]}")
        blog = get_blog_content(blogs_url_list[i], result["repo_name"], group)
        result["blog"].append(blog)
        # time.sleep(random.randint(1, 3))

    # Add back previous results:
    if os.path.exists(repo_name + "/result.json"):
        with open(repo_name + "/result.json") as previous_json:
            for blog_entry in previous_result["blog"]:
                tmp = blog_entry
                if tmp["title"] == "":
                    tmp["title"] = "(無題)"
                result["blog"].append(tmp)

    with open(f"{result['repo_name']}/result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    if update_repo:
        subprocess.run(["cp", "../.nojekyll", "."], cwd=repo_name)
        subprocess.run(
            ["git", "config", "--local", "user.name", "GitHub Action"],
            check=True,
            cwd=repo_name,
        )
        subprocess.run(
            ["git", "config", "--local", "user.email", "action@github.com"],
            check=True,
            cwd=repo_name,
        )

        # Add all changes
        subprocess.run(["git", "add", "-A"], check=True, cwd=repo_name)

        url = f"https://api.github.com/repos/SakamichiSeries/{repo_name}/pages"
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        data = {"source": {"branch": "main", "path": "/"}}

        response = requests.post(url, headers=headers, json=data)

        try:
            # Commit the changes
            subprocess.run(
                ["git", "commit", "-m", "Automated commit by GitHub Action"],
                check=True,
                cwd=repo_name,
            )

            # Push the changes
            subprocess.run(["git", "push"], check=True, cwd=repo_name)
        except:
            pass

        subprocess.run(["date"])
        du_result = subprocess.run(["du", "-sm", repo_name], capture_output=True)
        du_results.append(du_result.stdout.decode("unicode_escape"))
        subprocess.run(["rm", "-rf", repo_name])


code_Nogizaka46 = [
    "36749",  # 伊藤 理々杏
    "36750",  # 岩本 蓮加
    "36751",  # 梅澤 美波
    "36753",  # 久保 史緒里
    "36755",  # 佐藤 楓
    "36756",  # 中村 麗乃
    # "36757",  # 向井 葉月
    "36759",  # 吉田 綾乃クリスティー
    # "36760",  # 与田 祐希
    "48006",  # 遠藤 さくら
    "48008",  # 賀喜 遥香
    "48010",  # 金川 紗耶
    "48013",  # 柴田 柚菜
    "48015",  # 田村 真佑
    "48017",  # 筒井 あやめ
    "48019",  # 矢久保 美緒
    "55383",  # 黒見 明香
    "55384",  # 佐藤 璃果
    "55385",  # 林 瑠奈
    "55386",  # 松尾 美佑
    "55387",  # 弓木 奈於
    "55389",  # 井上 和
    "55390",  # 一ノ瀬 美空
    "55391",  # 菅原 咲月
    "55392",  # 小川 彩
    "55393",  # 冨里 奈央
    "55394",  # 奥田 いろは
    "55395",  # 中西 アルノ
    "55396",  # 五百城 茉央
    "55397",  # 池田 瑛紗
    "55400",  # 川﨑 桜
    "55401",  # 岡本 姫奈
    "40008",  # 六期生
]
code_Sakurazaka46 = [
    #  "03",  # "上村 莉菜"],
    "06",  # "小池 美波"],
    # "08",  # "齋藤 冬優花"],
    "43",  # "井上 梨名"],
    "53",  # "遠藤 光莉"],
    "54",  # "大園 玲"],
    "55",  # "大沼 晶保"],
    "56",  # "幸阪 茉里乃"],
    "45",  # "武元 唯衣"],
    "46",  # "田村 保乃"],
    "47",  # "藤吉 夏鈴"],
    "57",  # "増本 綺良"],
    "48",  # "松田 里奈"],
    "50",  # "森田 ひかる"],
    "58",  # "守屋 麗奈"],
    "51",  # "山﨑 天"],
    "59",  # "石森 璃花"],
    "60",  # "遠藤 理子"],
    "61",  # "小田倉 麗奈"],
    "62",  # "小島 凪紗"],
    "63",  # "谷口 愛季"],
    "64",  # "中嶋 優月"],
    "65",  # "的野 美青"],
    "66",  # "向井 純葉"],
    "67",  # "村井 優"],
    "68",  # "村山 美羽"],
    "69",  # "山下 瞳月"],
]
code_Hinatazaka46 = [
    # "5",  #  "加藤 史帆"],
    "7",  #  "佐々木 久美"],
    "8",  #  "佐々木 美玲"],
    "9",  #  "高瀬 愛奈"],
    # "11",  # "東村 芽依"],
    "12",  # "金村 美玖"],
    "13",  # "河田 陽菜"],
    "14",  # "小坂 菜緒"],
    "15",  # "富田 鈴花"],
    # "16",  # "丹生 明里"],
    # "17",  # "濱岸 ひより"],
    "18",  # "松田 好花"],
    "21",  # "上村 ひなの"],
    "22",  # "髙橋 未来虹"],
    "23",  # "森本 茉莉"],
    "24",  # "山口 陽世"],
    "25",  # "石塚 瑶季"],
    "27",  # "小西 夏菜実"],
    "28",  # "清水 理央"],
    "29",  # "正源司 陽子"],
    "30",  # "竹内 希来里"],
    "31",  # "平尾 帆夏"],
    "32",  # "平岡 海月"],
    "33",  # "藤嶌 果歩"],
    "34",  # "宮地 すみれ"],
    "35",  # "山下 葉留花"],
    "36",  # "渡辺 莉奈"],
    "000",  # ポカ
    "3000",  # 五期生
]

du_results = []
# for member in code_Nogizaka46:
#     scrape_repo(member, "N", du_results)
# for member in code_Sakurazaka46:
#     scrape_repo(member, "S", du_results)
# for member in code_Hinatazaka46:
#     scrape_repo(member, "H", du_results)

# scrape_repo("01", "K_sba", du_results)
# scrape_repo("02", "K_sba", du_results)
# scrape_repo("05", "K_sba", du_results)
# scrape_repo("09", "K_sba", du_results)
# scrape_repo("10", "K_sba", du_results)
# scrape_repo("12", "K_sba", du_results)
# scrape_repo("13", "K_sba", du_results)
# scrape_repo("17", "K_sba", du_results)
# scrape_repo("19", "K_sba", du_results)
# scrape_repo("22", "K_sba", du_results)

# scrape_repo("1", "H_sba", du_results)
# scrape_repo("2", "H_sba", du_results)
# scrape_repo("3", "H_sba", du_results)
# scrape_repo("4", "H_sba", du_results)
scrape_repo("6", "H_sba", du_results)
# scrape_repo("10", "H_sba", du_results)
# scrape_repo("19", "H_sba", du_results)
# scrape_repo("20", "H_sba", du_results)
# scrape_repo("26", "H_sba", du_results)

# scrape_repo("04", "S_sba", du_results)
# scrape_repo("07", "S_sba", du_results)
# scrape_repo("11", "S_sba", du_results)
# scrape_repo("14", "S_sba", du_results)
# scrape_repo("15", "S_sba", du_results)
# scrape_repo("18", "S_sba", du_results)
# scrape_repo("20", "S_sba", du_results)
# scrape_repo("21", "S_sba", du_results)
# scrape_repo("44", "S_sba", du_results)
# scrape_repo("49", "S_sba", du_results)

print(du_results)
print("".join(du_results))

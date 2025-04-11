import requests
import json
import os
import subprocess
import sys
from github import Github
from bs4 import BeautifulSoup
import urllib
import time
import random

# pip install lxml
# https://www.crummy.com/software/BeautifulSoup/bs4/doc/#the-keyword-arguments:~:text=External%20Python%20dependency-,If%20you%20can%2C%20I%20recommend%20you%20install%20and%20use%20lxml%20for%20speed.,-Note%20that%20if


def add_host(img_src_url: str, member_id: str) -> str:
    return urllib.parse.urljoin(
        f"https://janelin612.github.io/n46-crawler/mb/{member_id}/", img_src_url
    )


def download_image_return_path(img_src_url: str, repo_name: str, member_id: str) -> str:
    if img_src_url.startswith("blob"):
        return img_src_url
    if img_src_url.startswith("cid"):
        return img_src_url
    img_full_url = add_host(img_src_url, member_id)
    img_relative_path = (
        f"{repo_name}/{urllib.parse.urlparse(img_full_url).path[1:]}".replace(
            f"/n46-crawler/mb/{member_id}/img", ""
        )
    )
    if os.path.exists(img_relative_path):
        print(f"File exists: {img_relative_path}")
        return "/" + img_relative_path
    print(f"Downloading {img_full_url} to {img_relative_path}")
    os.makedirs(os.path.dirname(img_relative_path), exist_ok=True)
    fail_count = 0
    while True:
        try:
            if fail_count > 3:
                return "/" + img_relative_path
            response = requests.get(img_full_url)
            with open(img_relative_path, "wb") as f:
                f.write(response.content)
            print(f"File saved: {img_relative_path}")
            return "/" + img_relative_path
        except Exception as e:
            fail_count += 1
            print(e)
            time.sleep(random.randint(30, 60))
            pass


def scrape_repo(member_id: str, du_results: list):
    # fix https://www.nogizaka46.com/s/n46/diary/detail/56176
    sys.setrecursionlimit(4646)

    update_repo = not not os.getenv("RUNNING_GITHUB_ACTIONS")

    result = {}
    profile_url = f"https://janelin612.github.io/n46-crawler/mb/{member_id}/member.json"
    profile_json = requests.get(profile_url).json()
    result["member_name_kanji"] = profile_json["name"]
    result["member_name_kana"] = profile_json["name_hiragana"]
    with open("members.json") as members_json:
        members = json.load(members_json)
        for member in members["NG"]:
            if member[0] == result["member_name_kanji"]:
                result["member_name_romaji"] = member[1]
                break

    result["repo_name"] = (
        result["member_name_romaji"].lower().replace(" ", "-") + "-blog-archive"
    )

    result["SNS"] = {}
    SNS_url = f"https://janelin612.github.io/n46-crawler/mb/{member_id}/link.json"
    try:
        SNS_json = requests.get(SNS_url).json()
        for entry in SNS_json:
            result["SNS"][entry["type"]] = entry["link"]
    except:
        pass

    for entry in profile_json["intro"]:
        result[entry["key"]] = entry["value"]

    result["profile_pic"] = download_image_return_path(
        profile_json["image"],
        result["repo_name"],
        member_id,
    )

    print(result)

    repo_name = result["repo_name"]

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

    clean_repo = False
    if clean_repo:
        # clean repo to crawl again
        subprocess.run(["rm", "-rf", repo_name + "/.github"])
        subprocess.run(["rm", "-rf", repo_name + "/files"])
        subprocess.run(["rm", "-rf", repo_name + "/images"])
        subprocess.run(["rm", "-rf", repo_name + "/result.json"])

    archive_url = f"https://janelin612.github.io/n46-crawler/mb/{member_id}/result.json"
    archive_json = requests.get(archive_url).json()
    result["blog"] = []

    for entry in archive_json:
        tmp = {}
        tmp["title"] = entry["title"]
        tmp["time"] = entry["datetime"]
        tmp["url"] = entry["url"]
        tmp["content"] = entry["content"]
        soup = BeautifulSoup(tmp["content"], "html.parser")
        img_list = soup.find_all("img")
        for img in img_list:
            # Check if the img has a src attribute
            if img.get("src"):
                img["src"] = download_image_return_path(
                    img.get("src"),
                    result["repo_name"],
                    member_id,
                )

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


du_results = []

scrape_repo("manatsu.akimoto", du_results)

print(du_results)
print("".join(du_results))

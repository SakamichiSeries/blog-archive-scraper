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

# pip install lxml
# https://www.crummy.com/software/BeautifulSoup/bs4/doc/#the-keyword-arguments:~:text=External%20Python%20dependency-,If%20you%20can%2C%20I%20recommend%20you%20install%20and%20use%20lxml%20for%20speed.,-Note%20that%20if


def get_profile(member_id: str, group: str):
    if group == "K_sba":
        return get_profile_K_sba(member_id)
    elif group == "H_sba":
        return get_profile_H_sba(member_id)
    elif group == "S_sba":
        return get_profile_S_sba(member_id)
    else:
        raise Exception


def get_blog_url_list(member_id: str, previous_blog_url_list: list, group: str):
    if group == "K_sba":
        return get_blog_url_list_K_sba(member_id, previous_blog_url_list)
    elif group == "H_sba":
        return get_blog_url_list_H_sba(member_id, previous_blog_url_list)
    elif group == "S_sba":
        return get_blog_url_list_S_sba(member_id, previous_blog_url_list)
    else:
        raise Exception


def get_blog_content(url: str, repo_name: str, group: str):
    if group == "K_sba":
        return get_blog_content_K_sba(url, repo_name)
    elif group == "H_sba":
        return get_blog_content_H_sba(url, repo_name)
    elif group == "S_sba":
        return get_blog_content_S_sba(url, repo_name)
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


du_results = []

scrape_repo("01", "K_sba", du_results)
scrape_repo("02", "K_sba", du_results)
scrape_repo("05", "K_sba", du_results)
scrape_repo("09", "K_sba", du_results)
scrape_repo("10", "K_sba", du_results)
scrape_repo("12", "K_sba", du_results)
scrape_repo("13", "K_sba", du_results)
scrape_repo("17", "K_sba", du_results)
scrape_repo("19", "K_sba", du_results)
scrape_repo("22", "K_sba", du_results)

scrape_repo("1", "H_sba", du_results)
scrape_repo("2", "H_sba", du_results)
scrape_repo("3", "H_sba", du_results)
scrape_repo("4", "H_sba", du_results)
scrape_repo("6", "H_sba", du_results)
scrape_repo("10", "H_sba", du_results)
scrape_repo("19", "H_sba", du_results)
scrape_repo("20", "H_sba", du_results)
scrape_repo("26", "H_sba", du_results)

scrape_repo("04", "S_sba", du_results)
scrape_repo("07", "S_sba", du_results)
scrape_repo("11", "S_sba", du_results)
scrape_repo("14", "S_sba", du_results)
scrape_repo("15", "S_sba", du_results)
scrape_repo("18", "S_sba", du_results)
scrape_repo("20", "S_sba", du_results)
scrape_repo("21", "S_sba", du_results)
scrape_repo("44", "S_sba", du_results)
scrape_repo("49", "S_sba", du_results)

print(du_results)
print("".join(du_results))

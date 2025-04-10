import urllib.parse
import time
import random
import os
import requests


def add_host(img_src_url: str, group: str) -> str:
    if group == "N":
        return urllib.parse.urljoin("https://www.nogizaka46.com/", img_src_url)
    elif group == "K":
        return urllib.parse.urljoin("https://www.keyakizaka46.com/", img_src_url)
    elif group == "H":
        return urllib.parse.urljoin("https://www.hinatazaka46.com/", img_src_url)
    elif group == "S":
        return urllib.parse.urljoin("https://www.sakurazaka46.com/", img_src_url)
    elif group == "K_sba":
        return urllib.parse.urljoin("https://images.sakamichi.co/", img_src_url)
    elif group == "H_sba":
        return urllib.parse.urljoin("https://images.sakamichi.co/", img_src_url)
    else:
        print("Exception:add_host", img_src_url, group)
        raise Exception


def download_image_return_path(img_src_url: str, repo_name: str, group: str) -> str:
    if img_src_url.startswith("blob"):
        return img_src_url
    if img_src_url.startswith("cid"):
        return img_src_url
    img_full_url = add_host(img_src_url, group)
    img_relative_path = f"{repo_name}/{urllib.parse.urlparse(img_full_url).path[1:]}"
    # if os.path.exists(img_relative_path):
    #     print(f"File exists: {img_relative_path}")
    #     return "/" + img_relative_path
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

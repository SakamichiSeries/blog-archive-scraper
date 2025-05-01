def has_br_around(a_tag):
    prev = a_tag.find_previous_sibling()
    next = a_tag.find_next_sibling()
    return (prev and prev.name == 'br') or (next and next.name == 'br')

with open("members.json", "r") as f:
    import json
    import requests
    import bs4
    members = json.load(f)
    l=[]
    for entry in members:
        for entry2 in members["N"]:
            try:
                
                a=(("-".join(entry2[1].split(" "))).lower())
                link=f"https://sakamichiseries.github.io/{a}-blog-archive/result.json"
                print(link)
                # response = requests.get(link)
                # with open(f"{a}.json", "w") as f:
                #     f.write(response.text)
                with open(f"{a}.json", "r") as f2:
                    data=json.load(f2)
                    for blog in data["blog"]:
                        soup=bs4.BeautifulSoup(blog["content"], "html.parser")
                        for a in soup.find_all("a"):
                            if not has_br_around(a):
                                #print(a.get("href"))
                                if a.get("href").startswith("http") and  not a.get_text().startswith("http") and a.get_text().strip()!="":
                                    print(a.get_text())
                                    print(blog["url"])
            except:
                pass
from treat_comments import treat_comments
import re, os, json

pattern = re.compile(r'r\/([a-zA-Z_0-9]+)')

if __name__ == "__main__":
    max_sub_id = 0
    subs_ids = dict()
    relations = list()

def get_sub_id(subreddit):
    global max_sub_id, subs_ids
    
    if subreddit not in subs_ids.keys():
        subs_ids[subreddit] = max_sub_id + 1
        max_sub_id += 1
    
    return subs_ids[subreddit]

def treat_comment_regex(comment):
    global subs, authors

    sub_id = get_sub_id(comment["subreddit"])
    results = re.findall(pattern, comment["body"])

    for result in set(results):
        relations.append( (sub_id, get_sub_id(result)) )
        
if __name__ == "__main__":
    file_name = "RC_2019-12.zst"
    try:
        treat_comments(treat_comment_regex, file_name)
    except KeyboardInterrupt:
        print("Arrêt...")

    os.makedirs("output", exist_ok=True)

    with open("output/relations.json","w") as f:
        json.dump(relations, f)

    with open("output/subreddits_ids.json","w") as f:
        json.dump(subs_ids, f)
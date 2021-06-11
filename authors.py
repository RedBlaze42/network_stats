from treat_comments import treat_comments
import json, os

if __name__ == "__main__":

    max_sub_id = 0
    subs_ids = dict()
    subs = dict()
    authors = dict()

def treat_comment(comment):
    global max_sub_id, subs_ids, subs, authors
    if comment["subreddit"] not in subs_ids.keys():
        subs_ids[comment["subreddit"]] = max_sub_id + 1
        max_sub_id += 1

    sub_id = subs_ids[comment["subreddit"]]
    if sub_id not in subs.keys(): subs[sub_id] = 1
    subs[sub_id] += 1
    
    if comment["author"] not in authors.keys(): authors[comment["author"]] = dict()
    if sub_id not in authors[comment["author"]].keys(): authors[comment["author"]][sub_id] = 0
    authors[comment["author"]][sub_id]+=1

if __name__ == "__main__":
    
    file_name = "RC_2019-12.zst"
    try:
        treat_comments(treat_comment, file_name)
    except KeyboardInterrupt:
        print("Arrêt...")

    os.makedirs("output", exist_ok=True)
    with open("output/authors.json","w") as f:
        json.dump(authors, f)

    with open("output/subreddits.json","w") as f:
        json.dump(subs, f)

    with open("output/subreddits_ids.json","w") as f:
        json.dump(subs_ids, f)
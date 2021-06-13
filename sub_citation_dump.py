from treat_dump_file import treat_file
import re, os, json, ndjson

pattern = re.compile(r'r\/([a-zA-Z_0-9]+)')

if __name__ == "__main__":
    max_sub_id = 0
    subs_ids = dict()
    subs = dict()
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

    if sub_id not in subs.keys(): subs[sub_id] = 1

    for result in set(results):
        subs[sub_id] += 1
        relations.append( (sub_id, get_sub_id(result)) )
        
if __name__ == "__main__":
    file_name = "RC_2019-12.zst"
    try:
        treat_file(treat_comment_regex, file_name)
    except KeyboardInterrupt:
        print("Arrêt...")

    os.makedirs("output", exist_ok=True)

    with open("output/relations.ndjson","w") as f:
        writer = ndjson.writer(f, ensure_ascii=False)
        for from_sub, to_sub in relations.items():
            writer.writerow({from_sub: to_sub})

    with open("output/subreddits.json","w") as f:
        json.dump(subs, f)

    with open("output/subreddits_ids.json","w") as f:
        json.dump(subs_ids, f)

    with open("output/dump_infos.json","w") as f:
        json.dump({"element_number": len(relations)}, f)
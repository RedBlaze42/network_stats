from treat_dump_file import treat_file, treat_files
import json, ndjson, os

if __name__ == "__main__":

    max_sub_id = 0
    subs_ids = dict()
    subs = dict()
    authors = dict()

def treat_submission(submission):
    global max_sub_id, subs_ids, subs, authors
    if submission["subreddit"] not in subs_ids.keys():
        subs_ids[submission["subreddit"]] = max_sub_id + 1
        max_sub_id += 1

    sub_id = subs_ids[submission["subreddit"]]
    if sub_id not in subs.keys(): subs[sub_id] = 1
    subs[sub_id] += 1
    
    if submission["author"] not in authors.keys(): authors[submission["author"]] = dict()
    if sub_id not in authors[submission["author"]].keys(): authors[submission["author"]][sub_id] = 0
    authors[submission["author"]][sub_id]+=1

if __name__ == "__main__":
    
    file_name = "reddit_data/RS*.zst"
    try:
        treat_files(treat_submission, file_name)
    except KeyboardInterrupt:
        print("Arrêt...")

    os.makedirs("output", exist_ok=True)
    with open("output/authors.ndjson","w") as f:
        writer = ndjson.writer(f, ensure_ascii=False)
        for author_name, author_data in authors.items():
            writer.writerow({author_name: author_data})

    with open("output/subreddits.json","w") as f:
        json.dump(subs, f)

    with open("output/subreddits_ids.json","w") as f:
        json.dump(subs_ids, f)
        
    with open("output/dump_infos.json","w") as f:
        json.dump({"element_number": len(authors)}, f)
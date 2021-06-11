import json
from re import I
from pyvis.network import Network
from tqdm import tqdm
from math import log
import pickle, os
from os.path import join

path = "output_authors_december"
relation_type = "authors" #authors, citations

sub_number = 1000
connections_number = 4

blacklist = ["AskReddit"]

with open(join(path, "subreddits.json"), "r") as f:
    subs = json.load(f)

with open(join(path, "subreddits_ids.json"), "r") as f:
    sub_ids = json.load(f)
    sub_ids = {str(sub_id): sub for sub, sub_id in sub_ids.items()}

#Sub filter
subs_sorted = sorted(subs.keys(), key=lambda x: subs.get(x), reverse=True)
sub_number = min(len(subs_sorted),sub_number+1)
top = {sub_ids[sub_id] : subs[sub_id] for sub_id in subs_sorted[:sub_number] if sub_ids[sub_id]}

del subs

top_subs_name = sorted(top.keys())

#Relations
if not os.path.exists(join(path, "relations.pickle")):
    relations = { (sub_1, sub_2) : 0 for sub_1 in top_subs_name for sub_2 in top_subs_name if sub_1 < sub_2}
    
    if relation_type == "authors":

        with open(join(path, "authors.json"), "r") as f:
            authors = json.load(f)

        print("Total messages to analyze: {:,}".format(sum([len(author) for author in authors])))

        for author_name, author_data in tqdm(authors.items()):
            if author_name == "AutoModerator": continue
            author_data = {sub_ids[sub_id]:value for sub_id, value in author_data.items() if sub_ids[sub_id] in top_subs_name}

            author_coms = sum(author_data.values())
            author_subs_name = sorted(author_data.keys())
            
            for sub_1 in author_subs_name:
                for sub_2 in author_subs_name:
                    if sub_1 >= sub_2: continue
                    
                    #(min(author_data[sub_1],author_data[sub_2])/max(author_data[sub_1],author_data[sub_2]))*(author_data[sub_1]+author_data[sub_2])
                    #(author_data[sub_1]+author_data[sub_2])/author_coms
                    relations[(sub_1, sub_2)] += (author_data[sub_1]/author_coms)*(author_data[sub_2]/author_coms) # Formule de relation
    elif relation_type == "citations":
        
        with open(join(path, "relations.json"), "r") as f:
            citations = json.load(f)

        print("Total citations to analyze: {:,}".format(len(citations)))

        for from_sub, to_sub in tqdm(citations):
            if from_sub == to_sub: continue
            from_sub, to_sub = sub_ids[from_sub], sub_ids[to_sub]
            
            sub_1, sub_2 = min(from_sub, to_sub), max(from_sub, to_sub)

            relations[ (sub_1, sub_2) ] += 1
    
    with open(join(path, "relations.pickle"), "wb") as f:
        pickle.dump(relations, f)
else:
    with open(join(path, "relations.pickle"), "rb") as f:
        relations = pickle.load(f)

#Banning
relations = {key: value for key, value in relations.items() if key[0] not in blacklist and key[1] not in blacklist}
top_subs_name = [sub_name for sub_name in top_subs_name if sub_name not in blacklist]
top = {key: value for key, value in top.items() if key not in blacklist}


#Edge filtering
top_edges = dict()
node_relations = dict()
for sub_1 in top_subs_name:
    node_relations[sub_1]=dict()
    for sub_2 in top_subs_name:
        if sub_1 == sub_2: continue
        node_relations[sub_1][sub_2] = relations[min(sub_1, sub_2), max(sub_1, sub_2)]
    
    top_node_relation = sorted(node_relations[sub_1].keys(), key = lambda x: node_relations[sub_1][x], reverse = True)[:connections_number]
    
    for sub_2 in top_node_relation:
        top_edges[(min(sub_1, sub_2), max(sub_1, sub_2))] = relations[(min(sub_1, sub_2), max(sub_1, sub_2))]

#Final network
net = Network('920px', '1900px')
net.add_nodes(list(top.keys()), value = list(top.values()))
max_weight = max([weight for sub, weight in relations.items()])
edges = [(sub[0], sub[1], (weight/max_weight)*20) for sub, weight in top_edges.items() if weight > 0]
net.add_edges(edges)

del relations

#Options

#net.show_buttons(filter_=['physics',"nodes", "edges"])

net.options["physics"].use_barnes_hut({
            "gravity": -31000,
            "central_gravity": 1,
            "spring_length": 300,
            "spring_strength": 0.04,
            "damping": 0.2,
            "overlap": 0.1,
        })

net.options.__dict__["nodes"] = {
    "borderWidthSelected": 5,
    "color": {
        "highlight": {
            "border": "rgba(255,0,0,1)"
        }
    },
    "font": {
        "strokeWidth": 5,
        "strokeColor": "rgba(255,255,255,0.9)"
    }
}

net.show(join(path, "output.html"))
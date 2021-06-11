import json
from re import I
from pyvis.network import Network
from tqdm import tqdm
from math import log
import pickle, os
from os.path import join

path = "output_citations_december"
relation_type = "citations" #authors, citations

sub_number = 1000
connections_number = 4
primary_colors = True
secondary_colors = True

blacklist = ["AskReddit"]

#Import
print("Import...")
with open(join(path, "subreddits_ids.json"), "r") as f:
    ids_sub = json.load(f)
    sub_ids = dict()
    for sub, sub_id in ids_sub.items():
        sub_ids[str(sub_id)] = sub+"_" if sub.isdigit() else str(sub)

with open(join(path, "subreddits.json"), "r") as f:
    subs = json.load(f)
    subs = {sub_id: value for sub_id, value in subs.items() if sub_ids[sub_id] not in blacklist}

#Sub filter
print("Filtering...")
subs_sorted = sorted(subs.keys(), key=lambda x: subs.get(x), reverse=True)
sub_number = min(len(subs_sorted),sub_number+1)
top = {sub_ids[sub_id] : subs[sub_id] for sub_id in subs_sorted[:sub_number]}

del subs

top_subs_name = sorted(top.keys())

#Relations
print("Relations...")
if not os.path.exists(join(path, "relations.pickle")):
    relations = dict()#{ (sub_1, sub_2) : 0 for sub_1 in top_subs_name for sub_2 in top_subs_name if sub_1 < sub_2}
    
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
                    if not (sub_1, sub_2) in relations.keys(): relations[ (sub_1, sub_2) ] = 0
                    
                    #(min(author_data[sub_1],author_data[sub_2])/max(author_data[sub_1],author_data[sub_2]))*(author_data[sub_1]+author_data[sub_2])
                    #(author_data[sub_1]+author_data[sub_2])/author_coms
                    relations[(sub_1, sub_2)] += (author_data[sub_1]/author_coms)*(author_data[sub_2]/author_coms) # Formule de relation
    elif relation_type == "citations":
        
        with open(join(path, "relations.json"), "r") as f:
            citations = json.load(f)

        print("Total citations to analyze: {:,}".format(len(citations)))

        for from_sub, to_sub in tqdm(citations):
            if from_sub == to_sub: continue
            from_sub, to_sub = str(from_sub), str(to_sub)
            
            from_sub, to_sub = sub_ids[from_sub], sub_ids[to_sub]

            if from_sub not in top_subs_name or to_sub not in top_subs_name: continue

            sub_1, sub_2 = min(from_sub, to_sub), max(from_sub, to_sub)

            if not (sub_1, sub_2) in relations.keys(): relations[sub_1, sub_2] = 0
            relations[ (sub_1, sub_2) ] += 1
    
    with open(join(path, "relations.pickle"), "wb") as f:
        pickle.dump(relations, f)
else:
    with open(join(path, "relations.pickle"), "rb") as f:
        relations = pickle.load(f)

#Edge filtering
print("Edge filtering...")
top_edges = dict()
node_relations = dict()
for sub_1 in top_subs_name:
    node_relations[sub_1]=dict()
    for sub_2 in top_subs_name:
        if sub_1 == sub_2: continue
        if (min(sub_1, sub_2), max(sub_1, sub_2)) not in relations.keys(): continue
        node_relations[sub_1][sub_2] = relations[min(sub_1, sub_2), max(sub_1, sub_2)]
    
    top_node_relation = sorted(node_relations[sub_1].keys(), key = lambda x: node_relations[sub_1][x], reverse = True)[:connections_number]
    
    for sub_2 in top_node_relation:
        top_edges[(min(sub_1, sub_2), max(sub_1, sub_2))] = relations[(min(sub_1, sub_2), max(sub_1, sub_2))]

#Final network
net = Network('920px', '1900px', bgcolor="#000000", font_color="#ffffff")
net.add_nodes(list(top.keys()), value = list(top.values()), color = ["#ffffff" for i in range(len(top))])#default color 97c2fc
max_weight = max([weight for sub, weight in relations.items()])
edges = [(sub[0], sub[1], (weight/max_weight)*20) for sub, weight in top_edges.items() if weight > 0]
net.add_edges(edges)


#Options

#net.show_buttons(filter_=True)

net.options["physics"].use_barnes_hut({
            "gravity": -31000,
            "central_gravity": 1,
            "spring_length": 300,
            "spring_strength": 0.04,
            "damping": 0.2,
            "overlap": 0.1,
        })

net.options.__dict__["nodes"] = {
    "borderWidth": 3,
    "borderWidthSelected": 5,
    "color": {
        "highlight": {
            "border": "rgba(255,0,0,1)"
        }
    },
    "font": {
        "strokeWidth": 5,
        "strokeColor": "rgba(0,0,0,0.7)"
    }
}

#Colors
def get_connected_nodes(node, edge_list):
    connected_nodes = list()
    for sub, weight in edge_list.items():
        if node in sub:
            if sub[0] == node:
                connected_nodes.append(sub[1])
            else:
                connected_nodes.append(sub[0])
    
    return connected_nodes

def mix_colors(d):
    d_items = sorted(d.items())
    tot_weight = sum(d.values())
    red = int(sum([int(k[:2], 16)*v for k, v in d_items])/tot_weight)
    green = int(sum([int(k[2:4], 16)*v for k, v in d_items])/tot_weight)
    blue = int(sum([int(k[4:6], 16)*v for k, v in d_items])/tot_weight)
    zpad = lambda x: x if len(x)==2 else '0' + x
    return zpad(hex(red)[2:]) + zpad(hex(green)[2:]) + zpad(hex(blue)[2:])

if primary_colors:
    print("Primary colors...")
    #Top nodes colors
    top_connected_nodes = {sub: 0 for sub in top_subs_name}

    for sub in top_subs_name:
        for edge_sub, weight in top_edges.items():
            if sub in edge_sub and edge_sub in relations.keys():
                top_connected_nodes[sub] += relations[edge_sub]

    top_connected_nodes = sorted(top_connected_nodes.items(), key = lambda x: x[1], reverse = True)

    top_colors = ["2fcc27", "d97614", "f2d40f", "0ff2ea", "eb09e7"]

    selected_nodes = list()
    for node, links in top_connected_nodes:
        if len(selected_nodes) == len(top_colors): break

        connected_to_top_node = False
        connected_nodes = get_connected_nodes(node, top_edges)
        for node_edges in connected_nodes:
            if node_edges in selected_nodes:
                connected_to_top_node = True
                break
        
        if not connected_to_top_node: selected_nodes.append(node)

    for i, selected_node in enumerate(selected_nodes):
        net.get_node(selected_node)["color"] = "#{}".format(top_colors[i])
        for edge in net.edges:
            if edge['from'] == selected_node or edge['to'] == selected_node:
                edge["color"] = "#{}".format(top_colors[i])

    #Secondary colors
    if secondary_colors:
        print("Secondary colors...")
        for node in top_subs_name:
            if node in selected_nodes: continue
            connected_nodes = get_connected_nodes(node, top_edges)
            
            node_colors = dict()
            for connected_node in connected_nodes:
                if connected_node in selected_nodes and (min(node, connected_node), max(node, connected_node)) in relations.keys():
                    color = top_colors[selected_nodes.index(connected_node)]
                    node_colors[color] = relations[min(node, connected_node), max(node, connected_node)]

            node_colors["ffffff"] = max(node_colors.values()) if len(node_colors) > 0 else 1
            net.get_node(node)["color"] = "#{}".format(mix_colors(node_colors))

print("Output...")
net.show(join(path, "output.html"))
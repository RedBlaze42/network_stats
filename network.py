import json
from re import I
from pyvis.network import Network
from tqdm import tqdm
from math import log, exp
import pickle, os
from os.path import join
from save_pos import save_pos

path = "output_comments_december"
relation_type = "authors" #authors, citations

sub_number = 2000
connections_number = 3
primary_colors = True
secondary_colors = True
filter_explicit = False 
customized_node_colors = {"memes": "71eb34", "guns": "ffa200", "politics": "ffea00", "AmItheAsshole": "00fff7", "gonewild": "ff00d0", "pokemon": "9000ff", "nfl": "002fff", "Drugs": "5eff00", "unitedkingdom": "00a2ff", "canada": "ff0055"}

blacklist = ["AskReddit"]

top_colors = ["2fcc27", "d97614", "f2d40f", "0ff2ea", "eb09e7"]

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

    if filter_explicit:
        with open("explicit_subs.json", "r") as f:
            explicit_subs = json.load(f)

        subs = {sub_id: value for sub_id, value in subs.items() if sub_ids[sub_id] not in explicit_subs}

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

def get_connected_nodes(node, edge_list):
    connected_nodes = list()
    for sub, weight in edge_list.items():
        if node in sub:
            if sub[0] == node:
                connected_nodes.append(sub[1])
            else:
                connected_nodes.append(sub[0])
    
    return connected_nodes

#Final network
print("Network...")
net = Network('1080px', '1920px', bgcolor="#000000", font_color="#ffffff")
net.path = "template.html"
max_weight = max([weight for sub, weight in relations.items()])
edges = [(sub[0], sub[1], (weight/max_weight)*20) for sub, weight in top_edges.items() if weight > 0]

default_color = "#ffffff" if primary_colors else "97c2fc"
max_comments = max(top.values())
for node, value in top.items():
    net.add_node(node, size = (exp(value/max_comments)-1)*100, color = default_color, mass = len(get_connected_nodes(node, top_edges)))

net.add_edges(edges)

#Options

#net.show_buttons(filter_=True)

net.options["physics"].use_barnes_hut({
        "gravity": -31000,
        "central_gravity": 0.1,
        "spring_length": 200,
        "spring_strength": 0.04,
        "damping": 0.2,
        "overlap": 0.1,
    })

net.options.__dict__["layout"] = {"improvedLayout": False}
net.options.__dict__["physics"].__dict__["stabilization"] = {
        "enabled": True,
        "fit": True,
        "iterations": 3000,
        "onlyDynamicEdges": False,
        "updateInterval": 50
    }

net.options.__dict__["nodes"] = {
    "borderWidth": 3,
    "borderWidthSelected": 5,
    "color": {
        "highlight": {
            "border": "rgba(255,0,0,1)"
        }
    },
    "font": {
        "size" : 32,
        "strokeWidth": 5,
        "strokeColor": "rgba(0,0,0,0.7)"
    }
}

#Colors
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

    primary_nodes = dict()
    #Top nodes colors
    if len(customized_node_colors) == 0:
        top_connected_nodes = {sub: 0 for sub in top_subs_name}

        for sub in top_subs_name:
            for edge_sub, weight in top_edges.items():
                if sub in edge_sub and edge_sub in relations.keys():
                    top_connected_nodes[sub] += relations[edge_sub]

        top_connected_nodes = sorted(top_connected_nodes.items(), key = lambda x: x[1], reverse = True)

        for node, links in top_connected_nodes:
            if len(primary_nodes) == len(top_colors): break

            connected_to_top_node = False
            connected_nodes = get_connected_nodes(node, top_edges)
            for node_edges in connected_nodes:
                if node_edges in primary_nodes.keys():
                    connected_to_top_node = True
                    break
            
            if not connected_to_top_node: primary_nodes[node] = top_colors[len(primary_nodes)]

    primary_nodes = customized_node_colors

    #Color nodes and edges
    for selected_node, color in primary_nodes.items():
        net.get_node(selected_node)["color"] = "#{}".format(color)
        for edge in net.edges:
            if edge['from'] == selected_node or edge['to'] == selected_node:
                edge["color"] = "#{}".format(color)

    #Secondary colors
    if secondary_colors:
        print("Secondary colors...")
        for node in top_subs_name:
            if node in primary_nodes.keys(): continue
            connected_nodes = get_connected_nodes(node, top_edges)
            
            node_colors = dict()
            for connected_node in connected_nodes:
                if connected_node in primary_nodes.keys() and (min(node, connected_node), max(node, connected_node)) in relations.keys():
                    color = primary_nodes[connected_node]
                    node_colors[color] = relations[min(node, connected_node), max(node, connected_node)]

            node_colors["ffffff"] = max(node_colors.values()) if len(node_colors) > 0 else 1
            net.get_node(node)["color"] = "#{}".format(mix_colors(node_colors))

net.get_node(node)

print("Output...")
html_path = join(path, "output.html")
net.save_graph(html_path)

save_pos(html_path)
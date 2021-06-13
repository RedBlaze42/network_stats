import json, ndjson
from re import I
from pyvis.network import Network
from tqdm import tqdm
from math import log, exp
import pickle, os
from os.path import join
from save_pos import save_pos
from hashlib import md5

def mix_colors(d):
    d_items = sorted(d.items())
    tot_weight = sum(d.values())
    red = int(sum([int(k[:2], 16)*v for k, v in d_items])/tot_weight)
    green = int(sum([int(k[2:4], 16)*v for k, v in d_items])/tot_weight)
    blue = int(sum([int(k[4:6], 16)*v for k, v in d_items])/tot_weight)
    zpad = lambda x: x if len(x)==2 else '0' + x
    return zpad(hex(red)[2:]) + zpad(hex(green)[2:]) + zpad(hex(blue)[2:])

class RedditNetwork():
    
    #Filter specific parameters
    blacklisted_subs = ["AskReddit", "TalkativePeople", "reddit_feed_bot"]
    blacklisted_authors = ["AutoNewsAdmin","AutoModerator", "[deleted]"]
    sub_number = 1000
    filter_explicit = False
    inverse_explicit_filter = False

    #Default values
    connections_number = 4
    primary_colors = True
    secondary_colors = True
    top_colors = ["2fcc27", "d97614", "f2d40f", "0ff2ea", "eb09e7"]
    customized_node_colors = {}

    net_data = None
    top_edges_data = None
    relations_data = None    
    
    def __init__(self, input_path, config_path):
        self.input_path = input_path

        with open(config_path, "r") as f:
            self.config = json.load(f)
        
        if "blacklisted_subs" in self.config.keys(): self.blacklisted_subs = self.config["blacklisted_subs"]
        if "blacklisted_authors" in self.config.keys(): self.blacklisted_authors = self.config["blacklisted_authors"]
        if "top_colors" in self.config.keys(): self.top_colors = self.config["top_colors"]
        if "customized_node_colors" in self.config.keys(): self.customized_node_colors = self.config["customized_node_colors"]
        if "sub_number" in self.config.keys(): self.sub_number = self.config["sub_number"]
        if "primary_colors" in self.config.keys(): self.primary_colors = self.config["primary_colors"]
        if "filter_explicit" in self.config.keys(): self.filter_explicit = self.config["filter_explicit"]
        if "inverse_explicit_filter" in self.config.keys(): self.inverse_explicit_filter = self.config["inverse_explicit_filter"]
        if "secondary_colors" in self.config.keys(): self.secondary_colors = self.config["secondary_colors"]
        
        self.filter_config_hash = md5(json.dumps([self.sub_number, self.filter_explicit, self.inverse_explicit_filter, self.blacklisted_authors, self.blacklisted_subs]).encode('utf-8')).hexdigest()[:5]
        print("Import...")
        #Import sub ids
        with open(join(input_path, "subreddits_ids.json"), "r") as f:
            ids_sub = json.load(f)
            self.sub_ids = dict()
            for sub, sub_id in ids_sub.items():
                self.sub_ids[str(sub_id)] = sub+"_" if sub.isdigit() else str(sub)

        #Import sub values
        with open(join(input_path, "subreddits.json"), "r") as f:
            subs = json.load(f)
            subs = {sub_id: value for sub_id, value in subs.items() if self.sub_ids[sub_id] not in self.blacklisted_subs and not self.sub_ids[sub_id].startswith("u_")}

            if self.filter_explicit:
                with open("explicit_subs.json", "r") as f:
                    explicit_subs = json.load(f)

                if not self.inverse_explicit_filter:
                    subs = {sub_id: value for sub_id, value in subs.items() if self.sub_ids[sub_id] not in explicit_subs}
                else:
                    subs = {sub_id: value for sub_id, value in subs.items() if self.sub_ids[sub_id] in explicit_subs}

        #Sub filter
        print("Filtering...")
        subs_sorted = sorted(subs.keys(), key=lambda x: subs.get(x), reverse=True)
        sub_number = min(len(subs_sorted),self.sub_number+1)
        self.top_subs = {self.sub_ids[sub_id] : subs[sub_id] for sub_id in subs_sorted[:sub_number]}
        self.top_subs_name = sorted(self.top_subs.keys())

    def get_connected_nodes(self, node, edge_list):
        connected_nodes = list()
        for sub, weight in edge_list.items():
            if node in sub:
                if sub[0] == node:
                    connected_nodes.append(sub[1])
                else:
                    connected_nodes.append(sub[0])
        
        return connected_nodes

    @property
    def relations(self):
        if self.relations_data is not None: return self.relations_data

        print("Relations...")
        relation_path = join(self.input_path, "relations_{}.pickle".format(self.filter_config_hash))
        if os.path.exists(relation_path): #If a relation map is found with the same settings, load it
            with open(relation_path, "rb") as f:
                self.relations_data = pickle.load(f)
        else:
            if self.config["type"] == "posts":
                self.relations_data = self.compute_relations_post()
            elif self.config["type"] == "citations":
                self.relations_data = self.compute_relations_citations()
            
            with open(relation_path, "wb") as f:
                pickle.dump(self.relations_data, f)
        
        return self.relations_data

    def compute_relations_post(self):
        relations = dict()
        with open(join(self.input_path, "authors.ndjson"), "r") as f:
            authors = ndjson.reader(f)

            total_posts = 0

            for author in authors:
                author_name, author_data = list(author.items())[0]
                if author_name == "AutoModerator": continue
                author_data = {self.sub_ids[sub_id]:value for sub_id, value in author_data.items() if self.sub_ids[sub_id] in self.top_subs_name}

                author_coms = sum(author_data.values())
                author_subs_name = sorted(author_data.keys())
                total_posts += author_coms

                for sub_1 in author_subs_name:
                    for sub_2 in author_subs_name:
                        if sub_1 >= sub_2: continue
                        if not (sub_1, sub_2) in relations.keys(): relations[ (sub_1, sub_2) ] = 0
                        
                        #(min(author_data[sub_1],author_data[sub_2])/max(author_data[sub_1],author_data[sub_2]))*(author_data[sub_1]+author_data[sub_2])
                        #(author_data[sub_1]+author_data[sub_2])/author_coms
                        relations[(sub_1, sub_2)] += (author_data[sub_1]/author_coms)*(author_data[sub_2]/author_coms) # Formule de relation
                        
            print("Total posts to analyzed: {:,}".format(total_posts))

        return relations

    def compute_relations_citations(self):
        relations = dict()
        with open(join(self.input_path, "relations.ndjson"), "r") as f:
            citations = ndjson.reader(f)

            total_citations = 0

            for sub in citations:
                from_sub, to_sub = list(sub.items())[0]
                if from_sub == to_sub: continue
                from_sub, to_sub = str(from_sub), str(to_sub)
                
                from_sub, to_sub = self.sub_ids[from_sub], self.sub_ids[to_sub]

                if from_sub not in self.top_subs_name or to_sub not in self.top_subs_name: continue

                sub_1, sub_2 = min(from_sub, to_sub), max(from_sub, to_sub)

                if not (sub_1, sub_2) in relations.keys(): relations[sub_1, sub_2] = 0
                relations[ (sub_1, sub_2) ] += 1
                total_citations += 1

            print("Total citations to analyze: {:,}".format(total_citations))

            return relations

    @property
    def top_edges(self):
        if self.top_edges_data is not None: return self.top_edges_data

        print("Edge filtering...")
        self.top_edges_data = dict()
        node_relations = dict()
        for sub_1 in self.top_subs_name:
            node_relations[sub_1]=dict()
            for sub_2 in self.top_subs_name:
                if sub_1 == sub_2: continue
                if (min(sub_1, sub_2), max(sub_1, sub_2)) not in self.relations.keys(): continue
                node_relations[sub_1][sub_2] = self.relations[min(sub_1, sub_2), max(sub_1, sub_2)]
            
            top_node_relation = sorted(node_relations[sub_1].keys(), key = lambda x: node_relations[sub_1][x], reverse = True)[:self.connections_number]
            
            for sub_2 in top_node_relation:
                self.top_edges_data[(min(sub_1, sub_2), max(sub_1, sub_2))] = self.relations[(min(sub_1, sub_2), max(sub_1, sub_2))]
        
        return self.top_edges_data

    @property
    def net(self):
        if self.net_data is not None: return self.net_data
        print("Network...")
        
        self.net_data = Network('1080px', '1920px', bgcolor="#000000", font_color="#ffffff")
        self.net_data.path = "template.html"
        max_weight = max([weight for sub, weight in self.relations.items()])
        edges = [(sub[0], sub[1], (weight/max_weight)*20) for sub, weight in self.top_edges_data.items() if weight > 0]

        default_color = "#ffffff" if self.primary_colors else "97c2fc"
        max_comments = max(self.top_subs.values())
        for node, value in self.top_subs.items():
            self.net_data.add_node(node, size = (exp(value/max_comments)-1)*100, color = default_color, mass = len(self.get_connected_nodes(node, self.top_edges_data)))

        self.net_data.add_edges(edges)

        self.net_data.options["physics"].use_barnes_hut({
                "gravity": -31000,
                "central_gravity": 0.1,
                "spring_length": 200,
                "spring_strength": 0.04,
                "damping": 0.2,
                "overlap": 0.1,
            })

        self.net_data.options.__dict__["layout"] = {"improvedLayout": False}
        self.net_data.options.__dict__["physics"].__dict__["stabilization"] = {
                "enabled": True,
                "fit": True,
                "iterations": 3000,
                "onlyDynamicEdges": False,
                "updateInterval": 50
            }

        self.net_data.options.__dict__["nodes"] = {
            "borderWidth": 3,
            "borderWidthSelected": 10,
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

        if "show_buttons" in self.config.keys() and self.config["show_buttons"]: self.net_data.show_buttons(filter_=True)

        return self.net_data

    def set_primary_colors(self):
        print("Primary colors...")
        self.primary_nodes = dict()
        if len(self.customized_node_colors) == 0:
            top_connected_nodes = {sub: 0 for sub in self.top_subs_name}

            for sub in self.top_subs_name:
                for edge_sub, weight in self.top_edges_data.items():
                    if sub in edge_sub and edge_sub in self.relations.keys():
                        top_connected_nodes[sub] += self.relations[edge_sub]

            top_connected_nodes = sorted(top_connected_nodes.items(), key = lambda x: x[1], reverse = True)

            for node, links in top_connected_nodes:
                if len(self.primary_nodes) == len(self.top_colors): break

                connected_to_top_node = False
                connected_nodes = self.get_connected_nodes(node, self.top_edges_data)
                for node_edges in connected_nodes:
                    if node_edges in self.primary_nodes.keys():
                        connected_to_top_node = True
                        break
                
                if not connected_to_top_node: self.primary_nodes[node] = self.top_colors[len(self.primary_nodes)]
        else:
            self.primary_nodes = self.customized_node_colors

        #Color nodes and edges
        for selected_node, color in self.primary_nodes.items():
            if selected_node not in self.net_data.node_ids: continue
            self.net_data.get_node(selected_node)["color"] = "#{}".format(color)
            for edge in self.net_data.edges:
                if edge['from'] == selected_node or edge['to'] == selected_node:
                    edge["color"] = "#{}".format(color)
    
    def set_secondary_color(self):
        print("Secondary colors...")
        for node in self.top_subs_name:
            if node in self.primary_nodes.keys(): continue
            connected_nodes = self.get_connected_nodes(node, self.top_edges_data)
            
            node_colors = dict()
            for connected_node in connected_nodes:
                if connected_node in self.primary_nodes.keys() and (min(node, connected_node), max(node, connected_node)) in self.relations.keys():
                    color = self.primary_nodes[connected_node]
                    node_colors[color] = self.relations[min(node, connected_node), max(node, connected_node)]

            node_colors["ffffff"] = max(node_colors.values()) if len(node_colors) > 0 else 1
            self.net_data.get_node(node)["color"] = "#{}".format(mix_colors(node_colors))

    def export_network(self, output_path):
        self.relations
        self.top_edges
        self.net

        if self.primary_colors:
            self.set_primary_colors()
            
            if self.secondary_colors:
                self.set_secondary_color()

        self.net.save_graph(output_path)


if __name__ == "__main__":
    from save_pos import save_pos
    net = RedditNetwork("output_comments_jan-nov", "config.json")
    net.export_network("output_comments_jan-nov/output.html")
    save_pos("output_comments_jan-nov/output.html")
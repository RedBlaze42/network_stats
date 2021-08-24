import network, ndjson, json
from os.path import join
from tqdm import tqdm

from guppy import hpy; h=hpy()

class NodeRedditNetwork(network.RedditNetwork):

    def __init__(self, config_file):
        super().__init__(config_file)
        self.start_node = "starcitizen"
        self.levels = [{self.ids_sub[self.start_node]:list()}]
        self.primary_colors = False
        self.level_number = 3
        

    def get_related_subs(self, sub_ids, top_relations_number = 6):
        other_subs = [sub for sub_level in self.levels for sub in sub_level]
        if type(sub_ids) != list: sub_ids = [sub_ids]
        blacklisted_subs = [self.ids_sub[sub] for sub in self.blacklisted_subs if sub in self.ids_sub.keys()]
        sub_ids = [str(sub) for sub in sub_ids]
        concerned_authors = list()
        with open(join(self.input_path, "dump_infos.json"), "r") as f:
            element_number = json.load(f)["element_number"]
        
        with open(join(self.input_path, "authors.ndjson"), "r") as f:
            authors = ndjson.reader(f)

            progress_bar = tqdm(total = element_number, mininterval = 0.5, unit_scale = True)
            for author in authors:
                progress_bar.update(1)
                author_name, author_data = list(author.items())[0]
                if author_name in self.blacklisted_authors: continue

                for sub_1 in sub_ids:
                    if sub_1 in author_data.keys():
                        concerned_authors.append(author)
                        break
            progress_bar.close()

        top_sub_relations = dict()
        for sub_1 in sub_ids:
            sub_relations = dict()
            for author in concerned_authors:
                author_name, author_data = list(author.items())[0]
                if sub_1 not in author_data.keys(): continue
                author_coms = sum(author_data.values())
                author_subs_name = sorted(author_data.keys())

                for sub_2 in author_subs_name:
                    if sub_2 in other_subs: continue
                    if sub_1 >= sub_2: continue
                    if sub_2 in blacklisted_subs or sub_2 not in self.subs.keys(): continue
                    
                    try:
                        sub_relations[sub_2] += (author_data[sub_1]/author_coms)*(author_data[sub_2]/author_coms) # Formule de relation
                    except KeyError:
                        sub_relations[sub_2] = (author_data[sub_1]/author_coms)*(author_data[sub_2]/author_coms)
            top_sub_relations[sub_1] = sorted(sub_relations.items(), key=lambda x: x[1], reverse = True)[:top_relations_number]
            top_sub_relations[sub_1] = {sub: value for sub, value in top_sub_relations[sub_1]}
        return top_sub_relations

    @property
    def relations(self):
        if self._relations is not None: return self._relations
        self._relations = dict()
        for i in range(self.level_number):
            level = self.get_related_subs(list(self.levels[-1].keys()))
            self.levels[-1] = level
            if len(self.levels) < self.level_number:
                self.levels.append({down_sub:dict() for top_sub in level.values() for down_sub in top_sub.keys()})

            print(h.heap(), "\n\n\n", h.iso(self.levels))
            input("Appuyez sur une touche pour continuer...")

        self.top_subs_ids = set()
        for level in self.levels:
            for sub_1, sub_relations in level.items():
                self.top_subs_ids.add(sub_1)
                for sub_2, value in sub_relations.items():
                    self._relations[(sub_1, sub_2)] = value
                    self.top_subs_ids.add(sub_2)
        
        self.top_subs = {str(sub_id): self.subs[str(sub_id)] for sub_id in self.top_subs_ids}

        return self._relations

    @property
    def top_edges(self):
        return {(self.sub_ids[subs[0]], self.sub_ids[subs[1]]):value for subs, value in self.relations.items()}

    def export_network(self, output_path):
        self.filter_explicit_subs()

        self.relations

        self.net

        self.net.get_node(self.start_node)["mass"] = 100

        if self.primary_colors:
            self.set_primary_colors()

        self.net.save_graph(output_path)


if __name__ == "__main__":
    node_net = NodeRedditNetwork("config_test.json")
    node_net.export_network("test2.html")
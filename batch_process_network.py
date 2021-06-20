from network import RedditNetwork
from save_pos import save_pos
from glob import glob
import json, os, gc

configs = glob("configs/*.json")
configs.sort()

for config in configs:
    with open(config, "r") as f: output_path = json.load(f)["output_path"]
    if os.path.exists(output_path): continue
    
    print("Config file: {}".format(config))
    net = RedditNetwork(config)

    net.export_network(output_path)
    del net
    gc.collect()
    save_pos(output_path)
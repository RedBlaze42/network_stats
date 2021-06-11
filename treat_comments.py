import json
import zstandard as zstd
from tqdm import tqdm
import os, glob

def treat_files(comment_method, slug):
    for file_path in glob.glob(slug):
        treat_comments(comment_method, file_path)

def treat_comments(comment_method, file_name):
    last_update = 0
    comment_nb = 0
    with open(file_name, 'rb') as fh:
        dctx = zstd.ZstdDecompressor()
        with dctx.stream_reader(fh) as reader:
            previous_line = ""
            with tqdm(total = os.path.getsize(file_name), unit='B', unit_scale=True, unit_divisor=1024) as pbar:
                while True:
                    chunk = reader.read(2**24)

                    update = int(fh.tell())
                    pbar.update(update - last_update)
                    last_update = update
                    
                    if not chunk:
                        break

                    string_data = chunk.decode('utf-8')
                    lines = string_data.split("\n")
                    for i, line in enumerate(lines[:-1]):
                        if i == 0:
                            line = previous_line + line

                        comment = json.loads(line)
                        
                        comment_method(comment)
                        comment_nb += 1
                    previous_line = lines[-1]
import json
import zstandard as zstd
from tqdm import tqdm
import os, glob

def treat_files(comment_method, slug):
    for file_path in glob.glob(slug):
        print(file_path)
        treat_file(comment_method, file_path)

def human_size(bytes, units=[' bytes','KB','MB','GB','TB', 'PB', 'EB']):
    return str(bytes) + units[0] if bytes < 1024 else human_size(bytes>>10, units[1:])

def treat_file(comment_method, file_name):
    last_update = 0
    chunk_nb = 0
    with open(file_name, 'rb') as fh:
        dctx = zstd.ZstdDecompressor()
        with dctx.stream_reader(fh) as reader:
            previous_line = ""
            with tqdm(total = os.path.getsize(file_name), mininterval = 0.5, unit='B', unit_scale=True, unit_divisor=1024) as pbar:
                while True:
                    chunk = reader.read(2**24)
                    chunk_nb += 1

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
                        
                    previous_line = lines[-1]
    print("Finished treating {}".format(human_size(chunk_nb*(2**24))))
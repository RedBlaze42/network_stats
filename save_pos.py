from selenium import webdriver
import os, re
from time import sleep

iterations = 5000
regex_progress_bar = re.compile(r"\/\/PROGRESS BAR FROM(?:.|\n)+\/\/PROGRESS BAR TO")
regex_physics = re.compile(r'(,\n *"enabled": )true(,\n *"stabilization")')

def get_pos(file_path):
    with open(file_path, "r") as f:
        html = f.read()

    if "//POSITION_STORED" in html: return None

    previous_iterations = html.split('"iterations": ')[1].split("\n")[0].replace(",","")
    html = html.replace('"iterations": {}'.format(previous_iterations), '"iterations": {}'.format(iterations))

    with open(file_path, "w") as f:
        f.write(html)

    save_script = """var node_positions = {};
    nodes.forEach(function(item){
    var positions = network.getPositions(item.id);
    node_positions[item.id] = positions[item.id]
    });
    network.fit();
    node_positions["VIEWPORT_VISJS"] = {"x": network.getViewPosition()["x"],"y": network.getViewPosition()["y"],"scale": network.getScale()}
    return JSON.stringify(node_positions)
    """

    driver = webdriver.Chrome()
    driver.get("file://" + os.path.abspath(file_path))
    driver.set_script_timeout(300)

    if "#loadingBar" in html:
        while driver.find_element_by_xpath('//*[@id="loadingBar"]').get_attribute("style") == "":
            sleep(0.5)
    else:
        sleep(5)


    return_value = driver.execute_script(save_script)
    driver.quit()
    return return_value

def set_pos(file_path, positions):

    load_script = """//POSITION_STORED
    var positions = JSON.parse('DATA_HERE');
    nodes.forEach(function(item){
        network.moveNode(item.id, positions[item.id]["x"], positions[item.id]["y"])
    });
    network.moveTo({position: positions["VIEWPORT_VISJS"], scale: positions["VIEWPORT_VISJS"]["scale"]})"""

    with open(file_path, "r") as f:
        html = f.read()
    html = html.replace("//LOADING_SCRIPT", load_script.replace("DATA_HERE", positions))
    html = re.sub(regex_progress_bar, "", html)
    html = re.sub(regex_physics, r"\1false\2", html)

    html = html.replace('"iterations": {}'.format(iterations), '"iterations": 0')


    html = html.replace("""<div id="loadingBar">
    <div class="outerBorder">
      <div id="text">
        0%
      </div>
      <div id="border">
        <div id="bar"></div>
      </div>
    </div>
  </div>""", "")

    with open(file_path, "w") as f:
        f.write(html)

def save_pos(file_path):
    positions = get_pos(file_path)
    set_pos(file_path, positions)

if __name__ == "__main__":
    file_path = "output_comments_december/output.html"
    save_pos(file_path)
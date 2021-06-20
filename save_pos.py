from selenium import webdriver
import os
from time import sleep

iterations = 5000

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
    return JSON.stringify(node_positions)
    """

    driver = webdriver.Chrome()
    driver.get("file://" + os.path.abspath(file_path))
    driver.set_script_timeout(300)

    while driver.find_element_by_xpath('//*[@id="loadingBar"]').get_attribute("style") == "":
        sleep(1)


    return_value = driver.execute_script(save_script)
    driver.quit()
    return return_value

def set_pos(file_path, positions):

    load_script = """//POSITION_STORED
    var positions = JSON.parse('DATA_HERE');
    nodes.forEach(function(item){
        network.moveNode(item.id, positions[item.id]["x"], positions[item.id]["y"])
    });"""

    with open(file_path, "r") as f:
        html = f.read()
    html = html.replace("//LOADING_SCRIPT", load_script.replace("DATA_HERE", positions))
    html = html.replace("""network.on("stabilizationProgress", function(params) {
                    document.getElementById('loadingBar').removeAttribute("style");
                    var maxWidth = 496;
                    var minWidth = 20;
                    var widthFactor = params.iterations/params.total;
                    var width = Math.max(minWidth,maxWidth * widthFactor);

                    document.getElementById('bar').style.width = width + 'px';
                    document.getElementById('text').innerHTML = Math.round(widthFactor*100) + '%';
                });
                network.once("stabilizationIterationsDone", function() {
                    document.getElementById('text').innerHTML = '100%';
                    document.getElementById('bar').style.width = '496px';
                    document.getElementById('loadingBar').style.opacity = 0;
                    // really clean the dom element
                    setTimeout(function () {document.getElementById('loadingBar').style.display = 'none';}, 500);
                });
    """, "")
    #html = html.replace(""""stabilization": {
    #            "enabled": true""",""""stabilization": {
    #            "enabled": false""")

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
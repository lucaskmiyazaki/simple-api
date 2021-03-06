from flask import Flask
from flask import request, jsonify
import numpy as np
from numpy import linalg as la
from random import randint
import json

# Elastic Beanstalk looks for an 'application' that is callable by default
app = Flask(__name__)

# Health Check 
@app.route('/healthcheck')
def hello_world():
    return 'Your Server is working!'

# REST API
@app.route('/api/get_ref', methods=['GET', 'POST'])
def get_ref():
    content = request.json
    img = json.loads(content)
    L = 100
    img = np.array(img)
    d1, d2, d3 = img.shape
    img = img.reshape((d1*d2, d3))
    for pixel in img:
        pixel[0] = int(L*pixel[0]/la.norm(pixel))
        pixel[1] = int(L*pixel[1]/la.norm(pixel))
        pixel[2] = int(L*pixel[2]/la.norm(pixel))
    mean = np.mean(img, axis=0)
    std = np.std(img, axis=0)
    hashtable = {"mean": mean.tolist(), "std": std.tolist()}
    content = json.dumps(hashtable)
    return content

def color_norm(img):
    L = 100
    for line in img:
        for pixel in line:
            pixel[0] = int(L*pixel[0]/la.norm(pixel))
            pixel[1] = int(L*pixel[1]/la.norm(pixel))
            pixel[2] = int(L*pixel[2]/la.norm(pixel))
    return img

@app.route('/api/segmentation', methods=['GET', 'POST'])
def segmentation():
    content = request.json
    hashtable = json.loads(content) #content.json()
    img = hashtable["img"]
    import numpy as np
    img = np.array(img)
    mean = hashtable["mean"]
    std = hashtable["std"]
    img_map = []
    img_size = len(img)*len(img[0])
    img_dim = [len(img), len(img[0])]
    count = 0

    # normalize ilunmination
    img = color_norm(img)
    std = std*6

    # color filter
    for line in img:
        temp = []
        for pixel in line:
            dev = abs(pixel - mean)
            if dev[0] < std[0] and dev[1] < std[1] and dev[2] < std[2]:
                temp.append(-1)
                count += 1
            else: temp.append(0)
        img_map.append(temp)

    # region growing
    group = 1
    border_gp = []
    while count < img_size:
        # find an unclassified pixel
        while True:
            l = randint(0, img_dim[0]-1)
            w = randint(0, img_dim[1]-1)
            if img_map[l][w] == 0: break
        # check recursively neighbors
        stack = []
        stack.append((l, w))
        img_map[l][w] = group
        while len(stack) > 0:
            l, w = stack.pop()
            count += 1
            try:
                if img_map[l-1][w] == 0:
                    stack.append((l-1, w))
                    img_map[l-1][w] = group
                if img_map[l+1][w] == 0:
                    stack.append((l+1, w))
                    img_map[l+1][w] = group
                if img_map[l][w+1] == 0:
                    stack.append((l, w+1))
                    img_map[l][w+1] = group
                if img_map[l][w-1] == 0:
                    stack.append((l, w-1))
                    img_map[l][w-1] = group

                if img_map[l-1][w-1] == 0:
                    stack.append((l-1, w-1))
                    img_map[l-1][w-1] = group
                if img_map[l+1][w-1] == 0:
                    stack.append((l+1, w-1))
                    img_map[l+1][w-1] = group
                if img_map[l-1][w+1] == 0:
                    stack.append((l-1, w+1))
                    img_map[l-1][w+1] = group
                if img_map[l+1][w+1] == 0:
                    stack.append((l+1, w+1))
                    img_map[l+1][w+1] = group
            except:
                if len(border_gp) == 0 or border_gp[-1] != group: border_gp.append(group)
        group += 1

    # temp modify img and identify groups
    objs = []
    groups = []
    for i in range(img_dim[0]):
        for j in range(img_dim[1]):
            gp = img_map[i][j]
            if gp > 0 and gp not in border_gp:
                if gp in groups:
                    objs[groups.index(gp)].append((i, j))
                else:
                    groups.append(gp)
                    objs.append([(i, j)])

    # create rectangle
    max_value = 0
    for obj in objs:
        min_x = img_dim[1]
        min_y = img_dim[0]
        max_x = 0
        max_y = 0
        np    = 0
        for i, j in obj:
            np += 1
            if j > max_x: max_x = j
            if j < min_x: min_x = j
            if i > max_y: max_y = i
            if i < min_y: min_y = i
        if np > max_value:
            w = max_x - min_x
            h = max_y - min_y
            x = float(min_x + w/2)/img_dim[1]
            y = float(min_y + h/2)/img_dim[0]
            w = float(w)/img_dim[1]
            h = float(h)/img_dim[0]
            max_value = np
            box = (x, y, w, h)

    x, y, w, h = box
    hashtable = {'x': x, 'y': y, 'w': w, 'h': h}
    content = json.dumps(hashtable)
    return content

@app.route('/api/add_message/<uuid>', methods=['GET', 'POST'])
def add_message(uuid):
    content = request.json
    frame = json.loads(content)
    n = len(frame)
    hashtable = {"size": n, "data": frame}
    content = json.dumps(hashtable)
    return content

@app.route('/api/create_file', methods=['GET', 'POST'])
def create_file():
    f = open("hello.txt", "w")
    f.write("helloooo")
    content = json.dumps("criou arquivo")
    return content

@app.route('/api/read_file', methods=['GET', 'POST'])
def read_file():
    try:
        f = open("hello.txt", "r")
        content = json.dumps(f.read())
    except:
        content = json.dumps("erro ao ler o arquivo")
    return content

# Run the application
if __name__ == "__main__":
    # Setting debug to True enables debug output. This line should be
    # removed before deploying a production application.
    app.debug = True
    app.run(host="0.0.0.0")

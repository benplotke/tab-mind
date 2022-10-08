from __future__ import annotations

import json
from uuid import uuid4 as newUuid
from typing import Union

URLS = "urls"
TOPICS = "topics"
EDGES = "edges"
ID = "id"
URL = "url"
TOPIC = "topic"
DATA_PATH = "tabs.json"

topics: dict[str, Topic] = {}
urls: dict[str, Url] = {}
idToNode: dict[str, Node] = {}
edges: set[frozenset[str]] = set()


class Url:
    def __init__(self, uuid: str, name: str, neighbors: set[Node]):
        self.id = uuid
        self.name = name
        self.neighbors = neighbors
        self.visited = False

    def __str__(self):
        return f"url:{self.name} id:{self.id}"

    def __lt__(self, other):
        return self.name < other.name

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)

    @classmethod
    def newUrl(cls, url: str):
        return cls(str(newUuid()), url, set())


class Topic:
    def __init__(self, uuid: str, name: str, neighbors: set[Node]):
        self.id = uuid
        self.name = name
        self.neighbors = neighbors
        self.visited = False

    def __str__(self):
        return f"topic:{self.name} id:{self.id}"

    def __lt__(self, other):
        return self.name < other.name

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)

    @classmethod
    def newTopic(cls, topic: str):
        return cls(str(newUuid()), topic, set())


Node = Union[Url, Topic]


def getNode(identifier: str):
    if identifier in idToNode:
        return idToNode[identifier]
    if identifier in topics:
        return topics[identifier]
    return urls[identifier]


def validate(filePath: str):
    with open(filePath, "r") as f:
        data = json.loads(f.read())
        if not isinstance(data, dict):
            raise Exception("Outermost json is not object")
        if URLS not in data:
            raise Exception("urls not found in json")
        if not isinstance(data[URLS], list):
            raise Exception(URLS + " is not a list")
        for url in data[URLS]:
            if not isinstance(url, dict):
                raise Exception("url is not a json object: " + str(url))
            if ID not in url:
                raise Exception(ID + " is not in url: " + str(url))
            if URL not in url:
                raise Exception(URL + " is not in url: " + str(url))
        if TOPICS not in data:
            raise Exception(TOPICS + " not found in json")
        if not isinstance(data[TOPICS], list):
            raise Exception(TOPICS + " is not a list")
        for topic in data[TOPICS]:
            if not isinstance(topic, dict):
                raise Exception("topic is not a json object: " + str(topic))
            if ID not in topic:
                raise Exception(ID + " is not in topic: " + str(topic))
            if TOPIC not in topic:
                raise Exception(TOPIC + " is not in topic: " + str(topic))
        if EDGES not in data:
            raise Exception(EDGES + " not found in json")
        if not isinstance(data[EDGES], list):
            raise Exception(EDGES + " is not a list")


def load():
    with open(DATA_PATH, "r") as f:
        data = json.load(f)
    for rawUrl in data[URLS]:
        uuid = rawUrl[ID]
        urlStr = rawUrl[URL]
        url = Url(uuid, urlStr, set())
        urls[urlStr] = url
        idToNode[uuid] = url
    for rawTopic in data[TOPICS]:
        uuid = rawTopic[ID]
        topicStr = rawTopic[TOPIC]
        topic = Topic(uuid, topicStr, set())
        topics[topicStr] = topic
        idToNode[uuid] = topic
    for rawEdge in data[EDGES]:
        try:
            node1 = idToNode[rawEdge[0]]
            node2 = idToNode[rawEdge[1]]
            node1.neighbors.add(node2)
            node2.neighbors.add(node1)
            edges.add(frozenset((rawEdge[0], rawEdge[1])))
        except Exception as e:
            print(e)


def save():
    data = {URLS: [], TOPICS: [], EDGES: []}
    for url in urls.values():
        data[URLS].append({ID: url.id, URL: url.name})
    for topic in topics.values():
        data[TOPICS].append({ID: topic.id, TOPIC: topic.name})
    for edge in edges:
        data[EDGES].append(list(edge))
    with open(DATA_PATH, "w") as f:
        json.dump(data, f)


def printUrls():
    for url in sorted(urls.values()):
        print(url)


def printTopics():
    for topic in sorted(topics.values()):
        print(topic)


def printNodes(nodeId: str, distance: int):
    node = getNode(nodeId)
    if not node:
        print("Node " + nodeId + " not found")
        return
    for url in urls.values():
        url.visited = False
    for topic in topics.values():
        topic.visited = False
    printNodesR(node, distance, 0)


def printNodesR(node: Node, maxDistance: int, currentDistance: int):
    if maxDistance < currentDistance:
        return
    if node.visited:
        return
    print(currentDistance * "  " + str(node))
    node.visited = True
    for neighbor in sorted(node.neighbors):
        printNodesR(neighbor, maxDistance, currentDistance + 1)


def addUrl(urlStr: str):
    if urlStr in urls:
        print(urlStr + " already exists")
        urlId = urls[urlStr].id
        printNodes(urlId, 1)
        return
    url = Url.newUrl(urlStr)
    urls[urlStr] = url
    idToNode[url.id] = url
    save()
    print("Added " + str(url))


def removeUrl(urlId: str):
    url = getNode(urlId)
    if not url:
        print("No url " + urlId + " found. Nothing to remove")
        return
    for neighbor in url.neighbors:
        neighbor.neighbors.remove(url)
    del urls[url.name]
    del idToNode[url.id]
    save()
    print("Removed " + str(url))


def addTopic(topicStr: str):
    if topicStr in topics:
        print(topicStr + " already exists")
        topicId = topics[topicStr].id
        printNodes(topicId, 1)
        return
    topic = Topic.newTopic(topicStr)
    topics[topicStr] = topic
    idToNode[topic.id] = topic
    save()
    print("Added " + str(topic))


def removeTopic(topicId: str):
    topic = getNode(topicId)
    if not topic:
        print("No topic " + topicId + " found. Nothing to remove")
        return
    for neighbor in topic.neighbors:
        neighbor.neighbors.remove(topic)
    del topics[topic.name]
    del idToNode[topic.id]
    save()
    print("Removed " + str(topic))


def addEdge(id1: str, id2: str):
    node1 = getNode(id1)
    if not node1:
        print("Node " + id1 + " not found")
        return
    node2 = getNode(id2)
    if not node2:
        print("Node " + id2 + " not found")
        return
    edge = frozenset((node1.id, node2.id))
    if edge in edges:
        print("edge " + str(edge) + " already exists")
        return
    node1.neighbors.add(node2)
    node2.neighbors.add(node1)
    edges.add(edge)
    save()
    print("Added edge between " + str(node1) + " and " + str(node2))


def removeEdge(id1: str, id2: str):
    node1 = getNode(id1)
    if not node1:
        print("Node " + id1 + " not found")
        return
    node2 = getNode(id2)
    if not node2:
        print("Node " + id2 + " not found")
        return
    edge = frozenset((node1.id, node2.id))
    if edge not in edges:
        print("edge " + str(edge) + " not found. Doing nothing")
        return
    node1.neighbors.remove(node2)
    node2.neighbors.remove(node1)
    edges.remove(edge)
    save()
    print("Removed edge between " + str(node1) + " and " + str(node2))


def printOptions():
    print("? - print available commands")
    print("pu - print urls")
    print("pt - print topics")
    print("pn node n - print nodes >= n distance from specified node")
    print("au url - add url")
    print("at topic - add topic")
    print("ae node1 node2 - add edge between two nodes")
    print("ru - remove url")
    print("rt - remove topic")
    print("re - remove edge between two nodes")


def repl():
    while True:
        try:
            cmd = input("enter command (? for options):")
            args = cmd.split()
            if args[0] == "?":
                printOptions()
            elif args[0] == "pu":
                printUrls()
            elif args[0] == "pt":
                printTopics()
            elif args[0] == "pn":
                if len(args) != 3:
                    print("Wrong number of arguments for command " + args[0])
                else:
                    printNodes(args[1], int(args[2]))
            elif args[0] == "au":
                if len(args) != 2:
                    print("Wrong number of arguments for command " + args[0])
                else:
                    addUrl(args[1])
            elif args[0] == "at":
                if len(args) != 2:
                    print("Wrong number of arguments for command " + args[0])
                else:
                    addTopic(args[1])
            elif args[0] == "ae":
                if len(args) != 3:
                    print("Wrong number of arguments for command " + args[0])
                else:
                    addEdge(args[1], args[2])
            elif args[0] == "ru":
                if len(args) != 2:
                    print("Wrong number of arguments for command " + args[0])
                else:
                    removeUrl(args[1])
            elif args[0] == "rt":
                if len(args) != 2:
                    print("Wrong number of arguments for command " + args[0])
                else:
                    removeTopic(args[1])
            elif args[0] == "re":
                if len(args) != 3:
                    print("Wrong number of arguments for command " + args[0])
                else:
                    removeEdge(args[1], args[2])
        except Exception as e:
            print("Command failed")
            print(e)


validate(DATA_PATH)
load()
repl()

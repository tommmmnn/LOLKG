import json
import os
from py2neo import Graph,Node, GraphService

class LOLGraph:
    def  __init__(self):
        cur_dir = '/'.join(os.path.abspath(__file__).split('/')[:-1])
        self.data_path = os.path.join(cur_dir, 'data.json')
        self.graph = Graph("http://localhost:7474/browser/", name='kgcourse', auth=("neo4j", "12345678"))


    def read_nodes(self):
        heroinfos = []
        rune_infos = []

        rels_weak_counters = []
        rels_strong_counters = []
        rels_primary_rune_is = []
        rels_secondary_rune_is = []
        rels_is_in = []
        count = 0
        for rune_data in open("./rune.json", encoding='utf-8'):
            data_in_json = json.loads(rune_data)
            rune2 = data_in_json["second_level"]
            rune1 = data_in_json["first_level"]
            rune_infos.append(rune2)
            if rune1 not in rune_infos:
                rune_infos.append(rune1)
            rels_is_in.append([rune2, rune1])

        for data in open('./new_data.json', encoding='utf-8'):

            # 获取实体信息
            hero_dict = {}
            data_json = json.loads(data)
            hero = data_json['hero_name']
            hero_dict["name"] = hero
            hero_dict["url"] = data_json["hero_url"]
            hero_dict["position"] = data_json["hero_position"]
            heroinfos.append(hero_dict)

            # 获取关系信息
            for w_counter in data_json["hero_weak_counter"]:
                rels_weak_counters.append([hero, w_counter])
            for s_counter in data_json["hero_strong_counter"]:
                rels_strong_counters.append([hero, s_counter])
            rels_primary_rune_is.append([hero, data_json["primary_rune"]])
            rels_secondary_rune_is.append([hero, data_json["secondary_rune"]])
            count += 1
            print("读取节点  {}  个".format(count))
        return heroinfos, rune_infos, rels_weak_counters, rels_strong_counters, rels_primary_rune_is, rels_secondary_rune_is, rels_is_in

    def create_nodes(self, label, nodes):
        count = 0
        for node_name in nodes:
            node = Node(label, name=node_name)
            self.graph.create(node)
            count += 1
            print("创建节点{}/{}".format(count, len(nodes)))

    def create_hero_nodes(self, hero_infos):
        count = 0
        for hero_info in hero_infos:
            node = Node("Hero", name=hero_info["name"], hero_url=hero_info["url"], position=hero_info["position"])
            self.graph.create(node)
            count += 1
            print("创建英雄节点{}/{}".format(count, len(hero_infos)))

    def create_rune_nodes(self, rune_infos):
        count = 0
        for rune_info in rune_infos:
            node = Node("Rune", name=rune_info)
            self.graph.create(node)
            count += 1
            print("创建符文节点{}/{}".format(count, len(rune_infos)))

    def create_graph_nodes(self):
        hero_infos, rune_infos, rels_weak_counters, rels_strong_counters, rels_primary_rune_is, rels_secondary_rune_is, rels_is_in = self.read_nodes()
        self.create_rune_nodes(rune_infos)
        self.create_hero_nodes(hero_infos)

    def create_graph_relationship(self):
        hero_infos, rune_infos, rels_weak_counters, rels_strong_counters, rels_primary_rune_is, rels_secondary_rune_is, rels_is_in = self.read_nodes()
        self.create_relationship("Hero", "Hero", rels_weak_counters, "weakly_counter", "弱克制")
        self.create_relationship("Hero", "Hero", rels_strong_counters, "strongly_counter", "强克制")
        self.create_relationship("Hero", "Rune", rels_primary_rune_is, "primary_rune_should_be", "主系符文应该带")
        self.create_relationship("Hero", "Rune", rels_secondary_rune_is, "secondary_rune_should_be", "副系符文应该带")
        self.create_relationship("Rune", "Rune", rels_is_in, "is_in", "包含于")

    def create_relationship(self, start_node, end_node, edges, rel_type, rel_name):
        count = 0
        # 去重处理
        set_edges = []
        for edge in edges:
            set_edges.append('###'.join(edge))
        all = len(set(set_edges))
        for edge in set(set_edges):
            edge = edge.split('###')
            p = edge[0]
            q = edge[1]
            query = "match(p:%s),(q:%s) where p.name='%s'and q.name='%s' create (p)-[rel:%s{name:'%s'}]->(q)" % (
                start_node, end_node, p, q, rel_type, rel_name)
            try:
                self.graph.run(query)
                count += 1
                print(rel_type, count, all)
            except Exception as e:
                print(e)




if __name__ == "__main__":
    handler = LOLGraph()
    print("开始导入节点")
    handler.create_graph_nodes()
    print("开始导入边")
    handler.create_graph_relationship()


import ahocorasick
import os
from py2neo import Graph,Node, GraphService

class QASystem:
    def __init__(self):
        cur_dir = '/'.join(os.path.abspath(__file__).split('/')[:-1])
        self.hero_path = os.path.join(cur_dir, 'hero.txt')
        self.hero_wds = [i.strip() for i in open(self.hero_path) if i.strip()]
        self.couter_qwds = ["克制", "好打", "强"]
        self.be_countered_qwds = ["被", "被克制"]
        self.primary_rune_qwds = ["主系符文", "主系天赋", "主系"]
        self.secondary_rune_qwds = ["副系符文", "副系天赋", "副系"]
        self.position_qwds = ["上单", "打野", "中单", "下路", "辅助"]

        self.graph = Graph("http://localhost:7474/browser/", name='kgcourse', auth=("neo4j", "12345678"))


    def make_AC(self, AC, word_set):
        for word in word_set:
            AC.add_word(word,word)
        return AC

    def test_ahocorasick(self, question):
        '''
        ahocosick：自动机的意思
        可实现自动批量匹配字符串的作用，即可一次返回该条字符串中命中的所有关键词
        '''
        AC_KEY = ahocorasick.Automaton()
        AC_KEY = self.make_AC(AC_KEY, set(self.hero_wds+self.couter_qwds+self.primary_rune_qwds+
                                          self.secondary_rune_qwds+self.position_qwds+self.be_countered_qwds))
        AC_KEY.make_automaton()
        name_list = set()
        question = [question]
        for content in question:
            for item in AC_KEY.iter(content):#将AC_KEY中的每一项与content内容作对比，若匹配则返回
                name_list.add(item[1])
            name_list = list(name_list)
        # if len(name_list) > 0:
        #     print(question, "--->命中的关键词有：", "\t".join(name_list))
        return name_list

    def check_dict(self, question):
        question_dict = {}
        question_dict["prune"] = False
        question_dict["srune"] = False
        question_dict["be_countered"] = False
        question_dict["select_position"] = False
        kw_list = self.test_ahocorasick(question)
        for kw in kw_list:
            if kw in self.position_qwds:
                question_dict["select_position"] = True
                if kw == "上单":
                    question_dict["position"] = "top"
                elif kw == "打野":
                    question_dict["position"] = "jungle"
                elif kw == "中单":
                    question_dict["position"] = "mid"
                elif kw == "下路":
                    question_dict["position"] = "adc"
                elif kw == "辅助":
                    question_dict["position"] = "support"
            if kw in self.hero_wds:
                question_dict["hero"] = kw
            if kw in self.primary_rune_qwds:
                question_dict["prune"] = True
            if kw in self.secondary_rune_qwds:
                question_dict["srune"] = True
            if kw in self.couter_qwds:
                question_dict["counter"] = kw
            if kw in self.be_countered_qwds:
                question_dict["be_countered"] = True

        return question_dict

    def question_parser(self, question):
        question_dict = self.check_dict(question)
        query  = ""
        if question_dict["prune"]:
            query = 'MATCH p=(n:Hero)-[:primary_rune_should_be]->(m:Rune) WHERE n.name="{}" RETURN m.name'.format(question_dict["hero"])
            return query
        if question_dict["srune"]:
            query = 'MATCH p=(n:Hero)-[:secondary_rune_should_be]->(m:Rune) WHERE n.name="{}" RETURN m.name'.format(
                    question_dict["hero"])
            return query
        try:
            hero_idx = question.find(question_dict["hero"])
            counter_idx = question.find(question_dict["counter"])
        except KeyError as e:
            return query

        if hero_idx < counter_idx:
            # print("英雄名称在前")
            if question_dict["be_countered"]:
                # xx 被谁克制
                # print("包含被字")
                if hero_idx < question.find("被"):
                    # print("被克制")
                    if question_dict["select_position"]:
                        query = 'MATCH p=(n:Hero)-[:strongly_counter | :weakly_counter]->(m:Hero) WHERE m.name="{}" AND "{}" IN n.position RETURN n.name'.format(
                            question_dict["hero"], question_dict["position"]
                        )
                    else:
                        query = 'MATCH p=(n:Hero)-[:strongly_counter | :weakly_counter]->(m:Hero) WHERE m.name="{}" RETURN n.name'.format(question_dict["hero"])
                    return query
                # 谁被 xx 克制
                else:
                    if question_dict["select_position"]:
                        query = 'MATCH p=(n:Hero)-[:strongly_counter | :weakly_counter]->(m:Hero) WHERE n.name="{}" AND "{}" IN m.position RETURN m.name'.format(
                            question_dict["hero"], question_dict["position"]
                        )
                    else:
                        query = 'MATCH p=(n:Hero)-[:strongly_counter | :weakly_counter]->(m:Hero) WHERE n.name="{}" RETURN m.name'.format(
                            question_dict["hero"])
                    return query
            # xx能克制谁
            else:
                if question_dict["select_position"]:
                    query = 'MATCH p=(n:Hero)-[:strongly_counter | :weakly_counter]->(m:Hero) WHERE n.name="{}" AND "{}" IN m.position RETURN m.name'.format(
                        question_dict["hero"], question_dict["position"]
                    )
                else:
                    query = 'MATCH p=(n:Hero)-[:strongly_counter | :weakly_counter]->(m:Hero) WHERE n.name="{}" RETURN m.name'.format(question_dict["hero"])
                return query
        else:
            # print("英雄名称在后")
            # 谁能克制xx
            if question_dict["select_position"]:
                query = 'MATCH p=(n:Hero)-[:strongly_counter | :weakly_counter]->(m:Hero) WHERE m.name="{}" AND "{}" IN n.position RETURN n.name'.format(
                    question_dict["hero"], question_dict["position"]
                )
            else:
                query = 'MATCH p=(n:Hero)-[:strongly_counter | :weakly_counter]->(m:Hero) WHERE m.name="{}" RETURN n.name'.format(
                    question_dict["hero"])
            return query


    def search(self, query):
        res = []
        result = self.graph.run(query).data()
        count = 0
        for item in result:
            count += 1
            if "m.name" in item.keys():
                res.append(item["m.name"])
            else:
                res.append(item["n.name"])
            if count%10 == 0:
                res.append("\n")
        return "，".join(res)


    def answer_system(self, question):
        answer = "该问题暂时无法回答，请登陆op.gg/champions网站自行查找"
        if not self.question_parser(question):
            return answer
        else:
            query = self.question_parser(question)
        # print(query)
        answer = self.search(query)
        return answer
if __name__ == "__main__":
    my_QASystem = QASystem()
    print("欢迎使用英雄联盟问答助手，小助手竭力为您服务！！！\n")
    while 1:
        question = input("用户：")
        answer = my_QASystem.answer_system(question)
        print("英雄联盟问答助手：", answer)

# coding=utf-8
import json

def readdata(fpath):
    f = open(fpath, 'r')
    # 将json数据转换成python数据
    data = json.load(f)
    # 不太好使用map将unicode转换成string，因为不同文件的数据结构格式不确定
    # data.encode('utf8')
    f.close()
    return data

class ReadNodes(object):
    def __init__(self, fpathnodes):
        self.data = readdata(fpathnodes)
        self.node_types = []
        self.node_ids = []

    def output(self):
        for i in range(0, len(self.data)):
            self.node_ids.append(self.data[i]['id'])
            self.node_types.append(self.data[i].keys()[0])
            if self.node_types[i] == 'xyz':
                # 第一项开头或者不同种类开头需要加COOR_3D或者COOR_2D
                if i == 0 or self.node_types[i-1] != 'xyz':
                    yield 'COOR_3D'

                yield '%s %f %f %f' % (self.node_ids[i], float(self.data[i]['xyz'][0]),
                                       float(self.data[i]['xyz'][1]), float(self.data[i]['xyz'][2]))
                if i == len(self.data)-1:
                    yield 'FINSF'
                # elif self.node_types[i+1] != 'xyz':
                #     yield 'FINSF'

class ReadElements(object):
    def __init__(self, fpathelements):
        self.data = readdata(fpathelements)
        self.element_types = []
        self.element_ids = []
        self.element_part = []
        self.element_nodes = []

    def output(self):
        for i in range(0, len(self.data)):
            self.element_ids.append(self.data[i]['id'])
            self.element_types.append(self.data[i]['type'])
            self.element_part.append(self.data[i]['part'])
            self.element_nodes.append(self.data[i]['nodes'])
            # 对使用的单元种类进行判定
            if self.element_types[i] == 'TETRA4':
                if i == 0 or self.element_types[i-1] != 'TETRA4':
                    yield 'TETRA4'
                yield '%s %s %s %s %s' % (self.element_ids[i], self.data[i]['nodes'][0], self.data[i]['nodes'][1],
                                          self.data[i]['nodes'][2], self.data[i]['nodes'][3])
                if i == len(self.data)-1:
                    yield 'FINSF'
                # elif self.element_types[i+1] != 'TETRA4':
                #     yield 'FINSF'


class CreateCommand(object):
    def __init__(self):
        self.list_BulkCards = []

    def add_BulkCard(self, card):
        self.list_BulkCards.append(card)

    def output(self):
        for card in self.list_BulkCards:
            for line in card.output():
                yield line

    def add_readnodes(self, fpathnodes):
        self.add_BulkCard(ReadNodes(fpathnodes))

    def add_readelements(self, fpathelements):
        self.add_BulkCard(ReadElements(fpathelements))

    def write(self, fpath):
        with open(fpath, 'w') as fp:
            fp.write('TITRE NOM=MYSELF' + '\n')
            fp.write('FINSF' + '\n')
            for line in self.output():
                fp.write(line + '\n')
            fp.write('\n' + 'FIN')


def addcommand():
    commandmodel = CreateCommand()
    commandmodel.add_readnodes('/home/ygfrancois/simright_dev/model_inp_vs_json/json/nodes.json')
    commandmodel.add_readelements('/home/ygfrancois/simright_dev/model_inp_vs_json/json/elements.json')
    return commandmodel

model = addcommand()
model.write('/home/ygfrancois/simright_dev/jsontocomm/test.simmesh')
# coding=utf-8
import json


class BulkCard(object):
    def __init__(self, cardname):
        self.cardname = cardname


def readdata(fpath):
    f = open(fpath, 'r')
    data = json.load(f)
    f.close()
    return data


class DefineMaterial(BulkCard):
    def __init__(self, fpath):
        super(DefineMaterial, self).__init__('DEFINE_MATERIAL')
        self.data = readdata(fpath)
        self.typemat = []
        self.keywordfactorline = []

    def output(self):
        for i in range(0, len(self.data)):
            if self.data[i]['attributes'].keys() == ["ELASTIC_MODULUS", "POISSON_RATIO"]:
                self.typemat.append("ELAS")
                yield 'DEFI_MATERIAU(%s=_F(E=%f,NU=%f,),);' % \
                      (self.typemat[i], self.data[i]['attributes'].values()[0],
                       self.data[i]['attributes'].values()[1])


class AssignMaterial(BulkCard):
    def __init__(self, fpath):
        super(AssignMaterial, self).__init__('ASSIGN_MATERIAL')
        self.data = readdata(fpath)
        self.typemat = []
        self.keywordfactorline = []

    def output(self):
        for i in range(0, len(self.data)):
            if self.data[i]['attributes'].keys() == ["ELASTIC_MODULUS", "POISSON_RATIO"]:
                self.typemat.append("ELAS")
                yield 'DEFI_MATERIAU(%s=_F(E=%f,NU=%f,),);' % \
                      (self.typemat[i], self.data[i]['attributes'].values()[0],
                       self.data[i]['attributes'].values()[1])


class CreateCommand(object):
    def __init__(self):
        self.list_BulkCards = []

    def add_BulkCard(self, card):
        self.list_BulkCards.append(card)

    def output(self):
        for card in self.list_BulkCards:
            for line in card.output():
                yield line

    def add_material(self, fpath):
        self.add_BulkCard(DefineMaterial(fpath))

    def write(self, fpath):
        with open(fpath, 'w') as fp:
            fp.write('DEBUT' + '\n')
            fp.write('\n' + 'meshname' + '=LIRE_MAILLAGE();' + '\n\n')
            for line in self.output():
                fp.write('materialname=' + line + '\n')
            fp.write('\n' + 'FIN')


def addcommand():
    commandmodel = CreateCommand()
    commandmodel.add_material('/home/ygfrancois/simright_dev/model_inp_vs_json/json/materials.json')
    return commandmodel


model = addcommand()
model.write('/home/ygfrancois/simright_dev/jsontocomm/test.scmd')

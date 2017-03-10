# coding=utf-8
import json


class DefineMaterial(object):
    def __init__(self):
        f = open('/home/ygfrancois/simright_dev/model_inp_vs_json/json/materials.json', 'r')
        self.datamat = json.load(f)
        f.close()
        self.typemat = []
        self.keywordfactorline = []

    def output(self):
        for i in range(0, len(self.datamat)):
            if self.datamat[i]['attributes'].keys() == ["ELASTIC_MODULUS", "POISSON_RATIO"]:
                self.typemat.append("ELAS")
                yield 'DEFI_MATERIAU(%s=_F(E=%f,NU=%f,),);' % \
                                            (self.typemat[i], self.datamat[i]['attributes'].values()[0], \
                                            self.datamat[i]['attributes'].values()[1])




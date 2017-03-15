# coding=utf-8
import json
MeshName = []
AssignMaterialName =[]
ModelName = []
BoundaryConditionsName = []
# 两个字典各自的对应关系对于一个模型是不变的，所以可以设为全局变量，方便调用
dictpart_property = {}
dictproperty_type = {}

def readdata(fpath):
    f = open(fpath, 'r')
    # 将json数据转换成python数据
    data = json.load(f)
    # 不太好使用map将unicode转换成string，因为不同文件的数据结构格式不确定
    # data.encode('utf8')
    f.close()
    return data


# 阅读mesh文件命令，如果想阅读med格式的mesh文件，需要添加相关选项，此处默认为文本格式
class ReadMesh(object):
    def __init__(self, meshname):
        MeshName.append(meshname)

    def output(self):
        yield '%s=LIRE_MAILLAGE()' % MeshName[0]


# 定义材料性质，如E，NU等。对应aster关键词为DEFI_MATERIAU，关键词里的关键词因子根据材料性质改变
# 之后需要加更多的判断语句来增加其他种类的材料。如果涉及到热膨胀等其他参数，也需要修改样本代码。
class DefineMaterial(object):
    def __init__(self, fpathmaterials):
        self.data = readdata(fpathmaterials)
        self.typemat = []
        self.material_id = []
        self.materialname = []

    def output(self):
        for i in range(0, len(self.data)):
            # 把材料的名称读进materialname，此处还有材料id没用上，后面索引可能会用
            # self.materialname.append(self.data[i]['name'])
            # 注：material.json里的材料名称不一定能被python接受，所以需要用id
            self.material_id.append(self.data[i]['id'])
            if self.data[i]['attributes'].keys() == ["ELASTIC_MODULUS", "POISSON_RATIO"]:
                self.typemat.append("ELAS")
            yield '%s=DEFI_MATERIAU(%s=_F(E=%f,NU=%f,),);' % \
                (self.material_id[i], self.typemat[i], self.data[i]['attributes'].values()[0],
                    self.data[i]['attributes'].values()[1])


# 将定义的材料施加到对应的mesh上，对应aster关键词为AFFE_MATERIAU。
# 对应的.json数据为parts.json里的"material"和"id"。
###############################
# 此处将材料加到mesh的定义，会用在后面单元特征添加和最后计算的地方（AFFE_CARA_ELEM，MECA_STATIQUE）
class AssignMaterial(object):
    def __init__(self, fpathparts, assignmaterialname):
        # 将readmesh里设置的meshname引入
        self.data = readdata(fpathparts)
        self.property_id = []
        self.material_id = []
        self.part_id = []
        AssignMaterialName.append(assignmaterialname)

    def output(self):
        string_F = ''
        for i in range(0, len(self.data)):
            self.property_id.append(str(self.data[i]['property']))
            self.material_id.append(str(self.data[i]['material']))
            self.part_id.append(str(self.data[i]['id']))
            # 将part的id和property的id用字典写入，方便在assignmodel里面使用
            dictpart_property[self.part_id[i]] = self.property_id[i]
            # 可以使用材料的id，因为materials.json和parts.json里面都有对应的material 的id
            # 可能对多个part添加同一种材料，所以使用GROUP_MA,格式为：GROUP_MA = ('EAU',  'COUPLEAU',),(GROUP_MA是parts的id)
            ###############################
            # 但是对于json文件里的数据，即使有上述情况，也会分开写，此处需要考虑合并材料相同的part
            string_F += '_F(GROUP_MA=\'%s\',MATER=\'%s\',' % (self.part_id[i], self.material_id[i])
        yield '%s=AFFE_MATERIAL(MAILLAGE=%s,AFFE=(%s),);' % \
              (AssignMaterialName[0], MeshName[0], string_F)

# 加入模型property，对应aster关键词为AFFE_MODELE。
# 模型可能有多个，例如3D固体连续不可以和Shell写在同一个模型里，因为后面对shell加入厚度时，需要调用这里创建的model
class AssignProperty(object):
    # modelname输入参数应该是一个列表，因为可能定义多个模型种类
    def __init__(self, fpathproperties, modelname):
        self.data = readdata(fpathproperties)
        self.property_type = []
        self.property_id = []
        self.property_name = []
        ModelName.append(modelname)
        # 将用户创建的模型名称输入到全局变量ModelName里来，后面加载荷与边界条件/计算等都需要调用模型名称
        # 当PHENOMENON不是力学时在此处加上判断语句
        self.phenomenon = 'MECANIQUE'
        for i in range(0, len(self.data)):
            self.property_type.append(str(self.data[i]['attributes']['TYPE']))
            self.property_id.append(str(self.data[i]['id']))
            # 建立一个property_id和property_type之间的字典，part对应property，property再对应type
            # 为了后面不再进行遍历多次来判定属性种类，此处就进行划分，创建不同的模型对应的id的列表
            # 如Shell模型可能创建多次（因为可能定义不同的厚度）
            dictproperty_type[self.property_id[i]] = self.property_type[i]

    def output(self):
        string_F = ''
        for key, value in dictpart_property.items():
            if dictproperty_type[value] == 'SOLID':
                # 对于3D固体连续介质，除了关键词‘3D’，还有‘3D_SI’
                string_F += '_F(GROUP_MA=\'%s\',PHENOMENE=\'%s\',MODELISATION=\'3D\',' \
                            % (key, self.phenomenon)
            if dictproperty_type[value] == 'SHELL':
                # 在3D模型中（此处也称为2.5D模型），需要对相应模型施加厚度参数
                #             # 对于Shell模型，对应的关键词因子为‘COQUE_3D’；
                #             # 对于板模型，有DKT,DST,Q4G,DKTG,Q4GG五种;
                #             # 对于薄膜模型，对应为 ‘MEMBRANE’
                string_F += '_F(GROUP_MA=\'%s\',PHENOMENE=\'%s\',MODELISATION=\'COQUE_3D\',' \
                                 % (key, self.phenomenon)
        yield '%s=AFFE_MODELE(MAILLAGE=%s,AFFE=(%s),);' % (ModelName[0], MeshName[0], string_F)
    # 可能需要输出多个模型语句（创建了多个不同属性的模型），需要写不同的方法来定义不同种类模型


# 添加额外的property，例如Shell结构的厚度，aster将其分开到另外一个语句里了
class AssignPropertyAdditional(object):
    def __init__(self, fpathproperties):
        pass


# 添加边界条件
class AssignBoundaryConditions(object):
    def __init__(self, fpathboundaryConditions, boundaryconditionsname):
        BoundaryConditionsName.append(boundaryconditionsname)
        self.data = readdata(fpathboundaryConditions)
        self.bc_data = []
        self.bc_id = []
        self.bc_method = []

    def output(self):



class CreateCommand(object):
    def __init__(self):
        self.list_BulkCards = []

    def add_BulkCard(self, card):
        self.list_BulkCards.append(card)

    def output(self):
        for card in self.list_BulkCards:
            for line in card.output():
                yield line

    def add_readmesh(self, meshname):
        self.add_BulkCard(ReadMesh(meshname))

    def add_definematerial(self, fpathmaterials):
        self.add_BulkCard(DefineMaterial(fpathmaterials))

    def add_assignmaterial(self, fpathparts, assignmaterialname):
        self.add_BulkCard(AssignMaterial(fpathparts, assignmaterialname))

    def add_assignmodel(self, fpathproperties, modelname):
        self.add_BulkCard(AssignProperty(fpathproperties, modelname))

    def write(self, fpath):
        with open(fpath, 'w') as fp:
            fp.write('DEBUT' + '\n')
            for line in self.output():
                fp.write(line + '\n')
            fp.write('\n' + 'FIN')


def addcommand():
    commandmodel = CreateCommand()
    commandmodel.add_readmesh('mesh')
    commandmodel.add_definematerial('/home/ygfrancois/simright_dev/model_inp_vs_json/json/materials.json')
    commandmodel.add_assignmaterial('/home/ygfrancois/simright_dev/model_inp_vs_json/json/parts.json', 'assmat')
    commandmodel.add_assignmodel('/home/ygfrancois/simright_dev/model_inp_vs_json/json/properties.json',
                                 'model1')
    return commandmodel


model = addcommand()
model.write('/home/ygfrancois/simright_dev/jsontocomm/test.scmd')
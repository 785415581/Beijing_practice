#coding=utf-8

'''
01.坐标轴方向
02.相机
03.面数
04.freeze
05.Shape节点的历史
06.Instance复制
07.displayer和renderlayer
08.light
09.当前maya版本
10.无用面或者多边面
11.用点或者需要合并的点
12.Namespace
13.Shape节点带数字
14.nurbs格式(除毛发模型外)
15.Reference
16.重复命名
17.场景保存
18.场景单位
19.shape的名称和transform一致
20.swatchs render开关
21.贴图格式
22.Unkonwn节点
23.未使用的材质
24.无用插件
25.yetinode的display output关闭
'''
# ----------------01.坐标轴方向----------------
class AxisY(CheckingUnit):
            
    def cnLabel(self):
        '''Chinese label.'''
        return u'坐标轴方向'
    
    def run(self):
        '''Runs codes to start checking.'''
        import maya.cmds as cmds
        str = ''
        if cmds.upAxis(axis=True, q=True) != 'y':
            str = u'坐标轴与maya默认方向不一致'
            return str
        return str
    
# ----------------02.相机----------------
class Camera(CheckingUnit):
            
    def cnLabel(self):
        '''Chinese label.'''
        return u'资产多余的相机'
    
    def run(self):
        '''Runs codes to start checking.'''
        import maya.cmds as cmds
        self.result = cmds.listCameras()
        self.result.remove('front')
        self.result.remove('persp')
        self.result.remove('side')
        self.result.remove('top')

        return self.result
    
    def select(self,obj):
        import maya.cmds as cmds
        cmds.select(self.result)
# ----------------03.面数----------------
class FaceCount(CheckingUnit):
            
    def cnLabel(self):
        '''Chinese label.'''
        return u'面数'
    
    def run(self):
        '''Runs codes to start checking.'''
        import maya.cmds as cmds
        polys = cmds.ls(type='mesh')
        count = cmds.polyEvaluate(polys, face=True)
        if (count >=20000 and count<=50000):
            return u'面数 %s: 不达标' %count 
        return u'检查通过'
# ----------------04.freeze----------------
class Freeze(CheckingUnit):
            
    def cnLabel(self):
        '''Chinese label.'''
        return u'freeze'
    
    def run(self):
        '''Runs codes to start checking.'''
        import maya.cmds as cmds
        trans = cmds.ls(transforms=True)
        trans.remove('front')
        trans.remove('persp')
        trans.remove('side')
        trans.remove('top')
        self.result = []
        for tra in trans:
            tx = cmds.getAttr('%s.translateX'%tra)
            ty = cmds.getAttr('%s.translateY'%tra)
            tz = cmds.getAttr('%s.translateZ'%tra)
            rx = cmds.getAttr('%s.rotateX'%tra)
            ry = cmds.getAttr('%s.rotateY'%tra)
            rz = cmds.getAttr('%s.rotateZ'%tra)
            sx = cmds.getAttr('%s.scaleX'%tra)
            sy = cmds.getAttr('%s.scaleY'%tra)
            sz = cmds.getAttr('%s.scaleZ'%tra)
            if tx!=0.0 or ty !=0.0 or tz!=0.0 or rx!=0.0 or ry!=0.0 or rz!=0.0 or sx!=1.0 or sy!=1.0 or sz!=1.0:
                self.result.append(tra)
        
        
        return self.result
    
    def select(self, obj):
        import maya.cmds as cmds
        cmds.select(self.result)
    
    
        
# ----------------05.Shape节点的历史----------------
class History(CheckingUnit):
           
    def cnLabel(self):
        '''Chinese label.'''
        return u'Shape节点的历史'
        
    def run(self):
        '''Runs codes to start checking.'''
        import maya.cmds as cmds
        self.check_results = []
        nodes = cmds.ls(shapes=True)
        for node in nodes:
            if not node in ['frontShape', 'perspShape', 'sideShape', 'topShape']:
                history = cmds.listHistory(node)
                if len(history) > 1:
                    self.check_results.append(node)
        if self.check_results:
            return u'节点 %s: 存在历史' % self.check_results
        else:
            return self.check_results
    
# ----------------06.Instance复制----------------
class Instance(CheckingUnit):
    
        
    def cnLabel(self):
        '''Chinese label.'''
        return u'Instance复制'
        
    def run(self):
        '''Runs codes to start checking.'''
        import maya.cmds as cmds
        self.check_results = []
        nodes = cmds.ls(shapes=True)
        for node in nodes:
            if not node in ['frontShape', 'perspShape', 'sideShape', 'topShape']:
                parents = cmds.listRelatives(node, allParents=True)
                if len(parents) > 1:
                    self.check_results.append(node)
        if self.check_results:
            return u'节点 %s: 存在Instance复制' % self.check_results
        else:
            return self.check_results

# ----------------07.displayer和renderlayer----------------
class Layer(CheckingUnit):

    def cnLabel(self):
        '''Chinese label.'''
        return u'displayer和renderlayer'
        
    def run(self):
        '''Runs codes to start checking.'''
        self.check_results = []
        import maya.cmds as cmds
        display_lay = cmds.ls(type='displayLayer')
        try:
            display_lay.remove('defaultLayer')
        except:
            pass
        render_lay = cmds.ls(type='renderLayer')
        try:
            render_lay.remove('defaultRenderLayer')
        except:
            pass
        if display_lay or render_lay:
            return u'显示层或渲染层 %s,%s: 不应该在资产文件中' % (display_lay, render_lay)
        else:
            return ''
# ----------------08.light----------------
class Lighting(CheckingUnit):
            
    def cnLabel(self):
        '''Chinese label.'''
        return u'light'
    
    def run(self):
        '''Runs codes to start checking.'''
        import maya.cmds as cmds
        self.result = cmds.ls(lights=True)
        if self.result:
            return u'资产文件中包含light%s'%self.result 
        else:
            return self.result
        
    def fix(self):
        import maya.cmds as cmds
        cmds.delete(self.result)
# ----------------09.当前maya版本----------------
class MayaVersion(CheckingUnit):
            
    def cnLabel(self):
        '''Chinese label.'''
        return u'当前maya版本'
    
    def run(self):
        '''Runs codes to start checking.'''
        import maya.cmds as cmds
        version = cmds.about(q=True, v=True)
        if not version in ['2015', '2017']:
            return u'当前场景Maya版本为"%s"，不符合要求' %version
        else:
            return
# ----------------10.无用面或者多边面----------------
class MulFace(CheckingUnit):

    def cnLabel(self):
        '''Chinese label.'''
        return u'无用面或者多边面'
        
    def run(self):
        '''Runs codes to start checking.'''
        import maya.cmds as cmds
        import maya.OpenMaya as OpenMaya
        self.check_results = []
        sel = cmds.ls(type='mesh')
        if sel:
            for obj_name in sel:
                sel_list = OpenMaya.MSelectionList()
                obj = OpenMaya.MObject()
                sel_list.add(obj_name)
                sel_list.getDependNode(0, obj)
                mesh = OpenMaya.MItMeshPolygon(obj)
                
                while not mesh.isDone():

                    py_util = OpenMaya.MScriptUtil()
                    ptr = py_util.asDoublePtr()
                    mesh.getArea(ptr)
                    area = py_util.getDouble(ptr)
                    num = mesh.polygonVertexCount()
                    
                    face_name = '%s.f[%i]' %(obj_name, mesh.index())
                    
                    if num < 3 or area <= 0:
                        self.check_results.append(face_name)
                    if num > 4:
                        self.check_results.append(face_name)
                    mesh.next()
                    
        if self.check_results:
            
            return u'多边形面 %s: 是无用面或者多边面' % self.check_results
        return u'检查通'
    
    def select(self,obj):
        import maya.cmds as cmds
        cmds.select(self.check_results)
# ----------------11.用点或者需要合并的点----------------
class MulPoint(CheckingUnit):

    def cnLabel(self):
            '''Chinese label.'''
            return u'无用点或者需要合并的点'
        
    def run(self):
        '''Runs codes to start checking.'''
        import maya.cmds as cmds
        import maya.OpenMaya as OpenMaya
        self.check_results = {'delete': list(), 'merge': list()}
        sel = cmds.ls(type='mesh')
        if sel:
            for obj_name in sel:
                sel_list = OpenMaya.MSelectionList()
                obj = OpenMaya.MObject()
                sel_list.add(obj_name)
                sel_list.getDependNode(0, obj)
                mesh = OpenMaya.MItMeshVertex(obj)
                temp = dict()
                
                while not mesh.isDone():

                    faces = OpenMaya.MIntArray()
                    edges = OpenMaya.MIntArray()
                    mesh.getConnectedFaces(faces)
                    mesh.getConnectedEdges(edges)
                    
                    vertex_name = '%s.vtx[%i]' %(obj_name, mesh.index())
                    
                    if not faces.length() or not edges.length():
                        self.check_results['delete'].append(vertex_name)
                        
                    elif edges.length() > faces.length():
                        position = mesh.position()
                        
                        for v_name, pos in temp.items():
                            if (position-pos).length() <= self.parent().getToolWidget().stats_widget.value():
                                self.check_results['merge'].append((vertex_name, v_name))
                    mesh.next()
        del_point = None
        merge_point = None
        if self.check_results['delete']:
            del_point = u'多边形点 %s: 是无用点' % self.check_results['delete']
        if self.check_results['merge']:
            merge_point = u'多边形点 %s: 距离过于接近' % self.check_results['merge']
            if del_point + '\n' + merge_point != '\n':
                return del_point + '\n' + merge_point
        return ''
    
    def select(self,obj):
        import maya.cmds as cmds
        redult = []
        
        deleteVertex = self.check_results.get('delete',[])
        mergeVertex = self.check_results.get('merge',[])
        
        result = deleteVertex+mergeVertex
        if result:
            cmds.select(result)

#class Namespace(CheckingUnit):
#    def __init__(self):
#        self.check_results = list()
#        
#    def cnLabel(self):
#        '''Chinese label.'''
#        return u'Namespace'
#        
#    def run(self):
#        '''Runs codes to start checking.'''
#        import maya.cmds as cmds
#        nodes = cmds.ls(shapes=True)
#        for node in nodes:
#            if not node in ['frontShape', 'perspShape', 'sideShape', 'topShape']:
#                if ':' in node:
#                    self.check_results.append(node)
#        if self.check_results:
#            return u'节点 %s: 存在namespaces' % self.check_results
#        return u'检查通过'
# ----------------12.Namespace----------------
class Namespace(CheckingUnit):

    def cnLabel(self):
        '''Chinese label.'''
        return u'Namespace'
        
    def run(self):
        '''Runs codes to start checking.'''
        import maya.cmds as cmds
        self.check_results = cmds.namespaceInfo(listOnlyNamespaces=True,recurse=True)
        
        if self.check_results > 1:
            return u' 场景存在namespaces %s' % self.check_results
        else:
            return ''
# ----------------13.Shape节点带数字----------------
class NodeNum(CheckingUnit):

    def cnLabel(self):
        '''Chinese label.'''
        return u'Shape节点带数字'
        
    def run(self):
        '''Runs codes to start checking.'''
        import maya.cmds as cmds
        import re
        self.check_results = list()
        nodes = cmds.ls(shapes=True)
        for node in nodes:
            if not node in ['frontShape', 'perspShape', 'sideShape', 'topShape']:
                if re.match(r'.*\d+.*', node):
                    self.check_results.append(node)
                    
        return self.check_results
                    
        
# ----------------14.nurbs格式(除毛发模型外)----------------
class Nurbs(CheckingUnit):
            
    def cnLabel(self):
        '''Chinese label.'''
        return u'nurbs格式(除毛发模型外)'
    
    def run(self):
        '''Runs codes to start checking.'''
        import maya.cmds as cmds
        nodes = cmds.ls(type=['nurbsSurface', 'nurbsCurve'])
        self.result = list()
        if nodes:
            for node in nodes:
                self.result.append(node)
           
            return u'节点%s: 是nurbs格式'%self.result 
        return
    
# ----------------15.Reference----------------
class Reference(CheckingUnit):

    def cnLabel(self):
        '''Chinese label.'''
        return u'Reference'
        
    def run(self):
        '''Runs codes to start checking.'''
        import maya.cmds as cmds
        self.check_results = cmds.ls(referencedNodes=True)
        if self.check_results:
            return u'不能包含refenerce或者proxy'
        return 
# ----------------16.重复命名----------------
class RepetitionName(CheckingUnit):

    def cnLabel(self):
        '''Chinese label.'''
        return u'重复命名'
        
    def run(self):
        '''Runs codes to start checking.'''
        import maya.cmds as cmds
        self.check_results = list()
        nodes = cmds.ls(shapes=True)
        for node in nodes:
            if not node in ['frontShape', 'perspShape', 'sideShape', 'topShape']:
                if '|' in node:
                    self.check_results.append(node)
                    
        if self.check_results:
            return u'节点 %s: 命名不唯一' % self.check_results
            
        return
    
    def select(self,obj):
        import maya.cmds as cmds
        cmds.select(self.check_results)
    
# ----------------17.场景保存----------------
class SceneSave(CheckingUnit):
            
    def cnLabel(self):
        '''Chinese label.'''
        return u'场景保存'
    
    def run(self):
        '''Runs codes to start checking.'''
        import maya.cmds as cmds
        scene_path = cmds.file(q=True, sn=True)
        if not scene_path:
            return u'当前场景未保存'
        return 
# ----------------18.场景单位----------------
class SceneUnit(CheckingUnit):
    def cnLabel(self):
        '''Chinese label.'''
        return u'场景单位'
        
    def run(self):
        '''Runs codes to start checking.'''
        import maya.cmds as cmds
        linear = cmds.currentUnit(q=True, linear=True)
        if not linear in ['cm']:
            return u'当前场景Maya版本为"%s"，不符合要求' %linear
        return 
# ----------------19.shape的名称和transform一致----------------
class ShapeTransformSame(CheckingUnit):

    def cnLabel(self):
        '''Chinese label.'''
        return u'shape的名称和transform一致'
        
    def run(self):
        '''Runs codes to start checking.'''
        import maya.cmds as cmds
        self.check_results = list()
        nodes = cmds.ls(shapes=True)
        for node in nodes:
            if not node in ['frontShape', 'perspShape', 'sideShape', 'topShape']:
                parents = cmds.listRelatives(node, parent=True)
                if parents:
                    if node != '%sShape' % parents[0]:
                        self.check_results.append(node)
        if self.check_results:
            return u'节点 %s: 命名和transform不统一' % self.check_results
        return 'ok'
    
    def select(self, obj):
        import maya.cmds as cmds
        cmds.select(self.check_results)
    
# ----------------20.swatchs render开关----------------
class SwatchsRender(CheckingUnit):
            
    def cnLabel(self):
        '''Chinese label.'''
        return u'swatchs render开关'
    
    def run(self):
        '''Runs codes to start checking.'''
        import maya.cmds as cmds
        if cmds.optionVar(q='enableSwatchRendering'):
            return u'swatchs render没有关闭'
        return 
# ----------------21.贴图格式----------------
class Texture(CheckingUnit):
    def __init__(self):
        self.check_results = list()
        
    def cnLabel(self):
        '''Chinese label.'''
        return u'贴图格式'
        
    def run(self):
        '''Runs codes to start checking.'''
        import maya.cmds as cmds
        files = cmds.ls(textures=True)
        for file in files:
            try:
                path = cmds.getAttr('%s.fileTextureName'%file)
            except:
                pass
            if not path:
                continue
            if path.endswith('.jpg') or path.endswith('.gif'):
                self.check_results.append(path)
        if self.check_results:
            return u'%s : 存在高压缩格式的贴图'% self.check_results
        return
# ----------------22.Unkonwn节点----------------
class Unkonwn(CheckingUnit):
            
    def cnLabel(self):
        '''Chinese label.'''
        return u'Unkonwn节点'
    
    def run(self):
        '''Runs codes to start checking.'''
        import maya.cmds as cmds
        nodes = cmds.ls(exactType='unknown')
        result = list()
        if nodes:
            for node in nodes:
                result.append(node)
           
            return u'节点%s: 需要清理'%result 
        return
# ----------------23.未使用的材质----------------
class UnusedMaterials(CheckingUnit):
    def __init__(self):
        self.check_result = list()
            
    def cnLabel(self):
        '''Chinese label.'''
        return u'未使用的材质'
    
    def run(self):
        '''Runs codes to start checking.'''
        import maya.cmds as cmds
        shades = cmds.ls(type='shadingEngine')
        try:
            shades.remove('initialParticleSE')
        except:
           pass
        try:
            shades.remove('initialShadingGroup')
        except:
           pass
        
        self.result = []
        for s in shades:
            temp = cmds.listConnections(s, d=True, type='mesh')
            if not temp:
                self.result.append(s)
                return u'存在没有使用的材质球%s'%self.result
            
        return
    
    def select(self,obj):
        import maya.cmds as cmds
        cmds.select(self.result)
# ----------------24.无用插件----------------
class UnusedPlugin(CheckingUnit):
        
    def cnLabel(self):
        '''Chinese label.'''
        return u'无用插件'
        
    def run(self):
        '''Runs codes to start checking.'''
        import maya.cmds as cmds
        self.check_results = list()
        unused_plugins = ['Turtle', 'Mayatomr', 'mtoa', 'shaveNode', 'xgenMR', 'xgenToolkit',
                          'BifrostMain', 'bifrostshellnode', 'bifrostvisplugin',
                          'pgYetiMaya', 'pgYetiMaya']
        for plugin in unused_plugins:
            if cmds.pluginInfo(plugin, q=True, l=True):
                self.check_results.append(plugin)             
        if self.check_results:
            return u'插件 %s: 需要卸载' % self.check_results
        return 
# ----------------25.yetinode的display output关闭----------------
class Yetinode(CheckingUnit):

    def cnLabel(self):
        '''Chinese label.'''
        return u'yetinode的display output关闭'
        
    def run(self):
        '''Runs codes to start checking.'''
        import maya.cmds as cmds
        self.check_results = list()
        nodes = cmds.ls(type='pgYetiMaya')
        for node in nodes:
            if cmds.getAttr(u'%s.displayOutput'%node):
                self.check_results.append(node)
                
        if self.check_results:
            return u'节点 %s: 没有关闭display output' % self.check_results
        return
    

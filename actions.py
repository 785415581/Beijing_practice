# -*- coding: utf-8 -*-

'''
Engine Action Nodes

This module contains actions for the engine. 
'''

import sys
import os
import copy
import shutil
import glob
import json
import re
import time
import traceback
import pprint

import plcr
import rdlb
import filterFiles

#import apdr
Action = plcr.Action


def makeFolder(path):
    folder = os.path.dirname(path)
    if not os.path.isdir(folder):
        os.makedirs(folder)

def copyFile(src, dst):
    src = src.replace('\\', '/')
    dst = dst.replace('\\', '/')
    if os.path.exists(src) and src != dst:
        shutil.copyfile(src, dst)

class IsSceneUntitled(Action):
    
    def run(self):
        sw = self.software()
        if sw:
            if sw.isUntitled():
                text = 'Please save the sence first!'
                text = u'请先保存文件!'
                
                return text

class DoesVersionExisted(Action):
    
    _defaultParms = {
        'version': '{workfile_version}',
        'version_type': 'publish',
        'other_filters': []
    }
    
    def run(self):
        vn = self.parm('version')
        #print
        #print 'version:',vn
        
        versionType = self.parm('version_type')
        
        filters = [
            ['project', '=', self.project()],
            ['pipeline_type', '=', self.task().get('type')],
            ['type', '=', self.task().get('type')],
            ['sequence', '=', self.task().get('sequence')],
            ['shot', '=', self.task().get('shot')],
            ['asset_type', '=', self.task().get('asset_type')],
            ['asset', '=', self.task().get('asset')],
            ['task', '=', self.task().get('code')],
            ['version_type', '=', versionType],
            ['version', '=', vn]
        ]
        
        other = self.parm('other_filters')
        if not other:
            other = []
        filters += other
        
        #print
        #print 'filters:'
        #print filters
        
        r = self.database().doesVersionExist(self.project(), filters)
        
        if r:
            txt = u'版本 %s 已经提交过了，请升级版本再提交' % vn
            return txt

class DoesAnimationVersionExisted(Action):
    
    _defaultParms = {
        'version': '{workfile_version}',
        'version_type': 'publish', 
    }
    
    def run(self):
        vn = self.parm('version')
        versionType = self.parm('version_type')
        
        filters = [
            ['project', '=', self.project()],
            ['pipeline_type', '=', self.task().get('type')],
            ['type', '=', self.task().get('type')],
            ['sequence', '=', self.task().get('sequence')],
            ['shot', '=', self.task().get('shot')],
            #['asset_type', '=', self.task().get('asset_type')],
            ['task', '=', self.task().get('code')],
            ['version_type', '=', versionType],
            ['version', '=', vn]
        ]
        
        result = []
        for info in self.engine().getInputData():
            group = info['instance']
            
            theFilters = copy.deepcopy(filters)
            theFilters.append(['part', '=', group])
            theFilters.append(['asset', '=', info['asset']])
            
            #print 'filters:',theFilters
            
            r = self.database().doesVersionExist(self.project(), theFilters)
            
            if r:
                t = '    %s_%s' % (group, vn)
                if t not in result:
                    result.append(t)
        
        if result:
            txt = u'以下资产已经提交过了，请升级版本再提交:\n'
            txt += '\n'.join(result)
            return txt

class Condition(Action):
    
    def run(self):
        key = self.parm('key')
        condition = self.parm('condition')
        value = self.parm('value')
        
        if condition == 'in':
            return key in value

class CheckTaskStatus(Action):
    
    def run(self):
        kwargs = {
            'project': self.project(),
            'type': self.task().get('type'),
            'taskId': self.task().get('id')
        }
        status = self.database().getTaskStatus(**kwargs)
        value = self.parm('value')
        
        if not value:
            value = []
        
        if value:
            if status not in value:
                text = u'该任务状态为 %s , 不能提交任务\n' % status
                text += u'可以提交文件的任务状态为:\n'
                text += '\n'.join(value)
                
                return text

class Boolean(Action):
    
    _defaultParms = {
        'input': ''
    }
    
    def run(self):
        if self.parm('input'):
            return 1
        else:
            return 0

class WorkfileException(Exception):
    pass

def showWorkfileError(sw):
    try:
        msg = sys.exc_value.message
    except:
        msg = 'file error'
    raise WorkfileException(msg)

class NewScene(Action):
    
    progressText = 'Creating a new scene...'
    
    def run(self):
        sw = self.software()
        if sw:
            try:
                sw.new(force=True)
            except:
                showWorkfileError(sw)

class OpenScene(Action):
    
    progressText = 'Opening a scene...'
    
    def run(self):
        sw = self.software()
        if sw:
            path = self.parm('input')
            #print 'path:',path
            try:
                sw.open(path, force=True)
            except:
                showWorkfileError(sw)
            
            return path

class ImportScene(Action):
    
    def run(self):
        sw = self.software()
        if sw:
            path = self.parm('input')
            #print 'path:',path
            
            try:
                sw.import_(path, removeNamespace=True)
            except:
                showWorkfileError(sw)
            
            return path

def _reference(sw, info, createSets=True, configs={}, groupOption=None,
               displayMode=None, customAttributes=[]):
    #print
    #print 'info:',info
    
    if info:
        if type(info) == dict:
            path = info['path']
            
            if not os.path.isfile(path):
                return
            
            if info.get('part') == 'camera':
                res = info.get('resolution')
                ref = sw.referenceCamera(path, resolution=res)
            
            elif info.get('part') == 'material':
                ref = sw.importMaterials(path, configs=configs)
            
            else:
                if info['filetype'] == 'gpu':
                    ref = sw.importGpuCache(path)
                elif info['filetype'] == 'ass':
                    ref = sw.referenceAssembly(path)
                else:
                    ref = sw.reference(path, groupOption=groupOption,
                                       displayMode=displayMode,
                                       customAttributes=customAttributes)
            
            # Create sets for a model
            #print 'sets:',info.get('sets')
            if createSets:
                sw.createSets(info.get('sets'), namespace=ref['namespace'])
            
            return ref
        
        elif type(info) in (str, unicode):
            if not os.path.isfile(info):
                return
            
            ref = sw.reference(info)
            return ref

class ReferenceScene(Action):
    '''
    References the input file in the current scene.
    group_option is for the group info of Houdini alembic node.
        0: No Group
        1: Shape Node Full Path
        2: Transform Node Full Path
        3: Shape Node Name
        4: Transform Node Name
    
    display_mode is for display mode of Houdini alembic node:
        0: Full Geometry
        1: Point Cloud
        2: Bounding Box
        3: Centroid
        4: Hidden
    '''
    
    _defaultParms = {
        'input': '',
        'create_sets': False,
        'group_option': None,
        'display_mode': None,
        'custom_attributes': []
    }
    
    def run(self):
        sw = self.software()
        if sw:
            info = self.parm('input')
            key = self.parm('returned_key')
            res = self.parm('resolution')
            
            createSets = self.parm('create_sets')
            kwargs = {
                'sw': sw,
                'info': info,
                'createSets': createSets,
                'customAttributes': self.parm('custom_attributes')
            }
            groupOption = self.parm('group_option')
            if groupOption != None:
                kwargs['groupOption'] = groupOption
            
            displayMode = self.parm('display_mode')
            if displayMode != None:
                kwargs['displayMode'] = displayMode
            
            return _reference(**kwargs)

class RemoveReference(Action):
    
    _defaultParms = {
        'input': '',
    }
    
    def run(self):
        sw = self.software()
        if sw:
            refPath = self.parm('input')
            sw.removeReference(refPath)
            
            return refPath

class RemoveSceneObject(Action):
    
    _defaultParms = {
        'input': '',
    }
    
    def run(self):
        sw = self.software()
        if sw:
            obj = self.parm('input')
            sw.delete(obj)
            
            return obj

class AssignMaterials(Action):
    
    _defaultParms = {
        'input': '',
        'geo': '',
        'create_sets': False,
        'configs': {}
    }
    
    def run(self):
        sw = self.software()
        if sw:
            materials = self.parm('input')
            if type(materials) == dict and materials:
                # Reference materials
                #print 'materials:',materials
                geoNamespace = self.parm('geo').get('namespace')
                createSets = self.parm('create_sets')
                key = self.parm('returned_key')
                
                info = _reference(sw, materials, createSets=False,
                                  configs=self.parm('configs'))
                if info:
                    matNamespace = info['namespace']
                    #print 'matNamespace:',matNamespace
                    
                    # Assign materials
                    #print
                    #print 'Mapping:'
                    #print materials['mapping']
                    matNode = sw.assignMaterials(materials.get('mapping'),
                                                 geoNamespace=geoNamespace,
                                                 matNamespace=matNamespace)
                    info['material_node'] = matNode
                
                if createSets:
                    sw.createSets(materials.get('sets'), namespace=geoNamespace)
                
                return info

class AssignMaterials2(plcr.Action):
    
    _defaultParms = {
        'input': '',
        'geo': '',
        'create_sets': False,
        'configs': {}
    }
    
    def run(self):
        sw = self.software()
        if sw:
            materials = self.parm('input')
            if type(materials) == dict and materials:
                # Reference materials
                #print 'materials:',materials
                geoNamespace = self.parm('geo').get('namespace')
                createSets = self.parm('create_sets')
                key = self.parm('returned_key')
                
                info = _reference(sw, materials, createSets=False,
                                  configs=self.parm('configs'))
                if info:
                    matNamespace = info['namespace']
                    #print 'matNamespace:',matNamespace
                    
                    # Assign materials
                    #print
                    #print 'Mapping:'
                    #print "============================================"
                    #print materials['mapping']
                    
                    mappingName = "%s_%s_%s_mapping"%(materials.get('asset_type'),
                                                        materials.get('asset'),
                                                        materials.get('task'))
                    
                    #matNode = sw.assignMaterials(materials.get('mapping'),
                    #                             geoNamespace=geoNamespace,
                    #                             matNamespace=matNamespace)
                    matNode = sw.assignMaterials(materials.get(mappingName),
                                                 geoNamespace=geoNamespace,
                                                 matNamespace=matNamespace)
                    info['material_node'] = matNode
                
                if createSets:
                    sw.createSets(materials.get('sets'), namespace=geoNamespace)
                
                return info

class SetTransform(Action):
    
    _defaultParms = {
        'input': '',
        'transform': '',
        'subs': []
    }
    
    def run(self):
        sw = self.software()
        if sw:
            info = self.parm('input')
            transformInfo = self.parm('transform')
            
            #print
            #print 'input:',info
            #print 'transformInfo:',transformInfo 
            
            if info and transformInfo:
                topObjs = info.get('top_objects')
                if topObjs:
                    obj = topObjs[0]
                else:
                    obj = info['node']
                #print '%s: %s' % (obj, transformInfo)
                
                try:
                    sw.setTransform(obj, transformInfo)
                except:
                    pass
                
                subs = self.parm('subs')
                inputNode = self.parm('input_node')
                if type(subs) == list:
                    sw.setSubsTransform(obj, inputNode, subs)

class SetView(Action):
    '''Sets the view to the given camera or one of the scene cameras.'''
    
    _defaultParms = {
        'camera': '',
    }
    
    def run(self):
        sw = self.software()
        if sw:
            camera = self.parm('camera')
            if camera:
                sw.setView(camera)
            else:
                cams = sw.getCameras()
                if cams:
                    sw.setView(cams[0]['full_path'])

class CreateCamera(Action):
    '''Imports the camera from the template file or create a new one.'''
    
    _defaultParms = {
        'template': '',
        'camera_name': '',
    }
    
    progressText = 'Creating camera from template...'
    
    def run(self):
        sw = self.software()
        if sw:
            template = self.parm('template')
            cameraName = self.parm('camera_name')
            
            if os.path.isfile(template):
                sw.import_(template, removeNamespace=True)
                cams = sw.getCameras()
                if cams:
                    cam = cams[0]['full_path']
                    return sw.rename(cam, cameraName)
            
            else:
                return sw.createCamera(cameraName)[0]

class SaveScene(Action):
    
    progressText = 'Saving current scene...'
    
    def run(self):
        format_ = self.parm('format')
        sw = self.software()
        if sw:
            if not sw.isUntitled():
                if format_:
                    # If the format is different with current format
                    # Then save as to target format
                    currentPath = sw.filepath()
                    currentExt = os.path.splitext(currentPath)[1].replace('.','')
                    if currentExt.lower() == format_.lower():
                        try:
                            sw.save(force=True)
                        except:
                            showWorkfileError(sw)
                    
                    else:
                        currentBasename = os.path.splitext(currentPath)[0]
                        newPath = '%s.%s' % (currentBasename, format_)
                        try:
                            sw.saveAs(newPath, force=True)
                        except:
                            showWorkfileError(sw)
                
                else:
                    try:
                        sw.save(force=True)
                    except:
                        showWorkfileError(sw)
                
                return sw.filepath()

class SaveAsScene(Action):
    
    progressText = 'Saving the scene...'
    
    def run(self):
        sw = self.software()
        if sw:
            path = self.parm('input')
            makeFolder(path)
            
            try:
                sw.saveAs(path, force=True)
            except:
                showWorkfileError(sw)
            
            return path

class GetSceneReferences(Action):
    
    def run(self):
        sw = self.software()
        if sw:
            return sw.getReferenceObjects()
        
        else:
            return []

class FindSceneObjects(Action):
    
    _defaultParms = {
        'name': '',
        'namespace': '',
        'type': '',
        'attributes': {},
        'returned_index': None
    }
    
    def run(self):
        sw = self.software()
        if sw:
            name = self.parm('name')
            namespace = self.parm('namespace')
            type = self.parm('type')
            attris = self.parm('attributes')
            
            kwargs = {}
            if name:
                kwargs['name'] = name
            if namespace:
                kwargs['namespace'] = namespace
            if type:
                kwargs['type'] = type
            if attris:
                kwargs['attributes'] = attris
            
            result = sw.find(**kwargs)
        
        else:
            result = []
        
        returnedIndex = self.parm('returned_index')
        if returnedIndex == None:
            return result
        else:
            try:
                return result[returnedIndex]
            except:
                return

class HasWriteNode(Action):
    
    _defaultParms = {
        'name': '',
        'attributes': {},
    }
    
    def run(self):
        sw = self.software()
        if sw:
            name = self.parm('name')
            type = 'Write'
            attris = self.parm('attributes')
            
            kwargs = {'type': type}
            if name:
                kwargs['name'] = name
            if attris:
                kwargs['attributes'] = attris
            
            result = sw.find(**kwargs)
            
            if not result:
                return 'Can not find Write node!'

class RenameChildren(Action):
    
    _defaultParms = {       
        'input': '',
        'replace': '',
        'to': ''
    }
    
    def run(self):
        sw = self.software()
        if sw:
            path = self.parm('input')
            replace = self.parm('replace')
            replace = replace.replace('/', '\\')
            to = self.parm('to')
            sw.renameChildren(path, replace, to)

class GroupChildrenByNetworkBox(Action):
    '''
    Groups the node children into net work boxes.
    We get the group key by split the node name.
    '''
    
    _defaultParms = {       
        'input': '',
        'splitter': '_',
        'index': 0
    }
    
    def run(self):
        sw = self.software()
        if sw:
            path = self.parm('input')
            splitter = self.parm('splitter')
            index = self.parm('index')
            
            nodes = sw.getChildren(path)
            
            temp = {}
            for n in nodes:
                key = n.name().split(splitter)[index]
                if not temp.has_key(key):
                    temp[key] = []
                temp[key].append(n.path())
            
            for key in temp.keys():
                sw.createNetworkBox(path, name=key, items=temp[key])

class GetSceneObjectChildren(Action):
    
    _defaultParms = {
        'input': '',
        'type': '', 
        'all_subs': False
    }
    
    def run(self):
        sw = self.software()
        if sw:
            path = self.parm('input')
            typ = self.parm('type')
            allSubs = self.parm('all_subs')
            
            if path:
                if allSubs:
                    return sw.getAllSubChildren(path, type=typ)
                    
                else:
                    temp = sw.getChildren(path, type=typ)
                    
                    return [t.fullPath() for t in temp]
        
        return []

class CreateSceneHierachy(Action):
    
    progressText = 'Creating scene hierachy...'
    
    def run(self):
        sw = self.software()
        if sw:
            data = self.parm('hierachy')
            sw.createHierachy(data)
            return data

class SetSceneFrameRange(Action):
    
    _defaultParms = {
        'shot': {},
    }
    
    progressText = 'Setting scene frame range...'
    
    def run(self):
        sw = self.software()
        if sw:
            #print
            #print 'task:',
            #pprint.pprint(self.task())
            #print
            shot = self.parm('shot')
            if shot:
                shotId = shot.get('id')
            else:
                shotId = self.task().get('shot_id')
            
            kwargs = {
                'project': self.project(), 
                'shotId': shotId, 
            }
            
            firstFrame,lastFrame = self.database().getShotFrameRange(**kwargs)
            
            #print
            #print 'frame range: %s-%s' % (firstFrame, lastFrame)
            #print
            
            if firstFrame != None and lastFrame != None:
                sw.setFrameRange(firstFrame, lastFrame)

class SetPixelAspect(Action):
    _defaultParms = {
        'input': 1.0,
    }
    
    def run(self):
        import maya.cmds as cmds
        value = float(self.parm('input'))
        
        #cmds.setAttr('defaultResolution.pixelAspect',value)
        deviceAspectValue = value*2.33
        cmds.setAttr('defaultResolution.deviceAspectRatio',deviceAspectValue)
        #print 'value:',value
        
        

class GetSceneFrameRange(Action):
    _defaultParms = {
        'shot': {},
    }
    
    def run(self):
        shot = self.parm('shot')
        
        if shot:
            shotId = shot.get('id')
        else:
            shotId = self.task().get('shot_id')
        
        kwargs = {
            'project': self.project(), 
            'shotId': shotId, 
        }
        
        firstFrame,lastFrame = self.database().getShotFrameRange(**kwargs)
        
        
        return "%s-%s"%(firstFrame,lastFrame)


class GetSceneResolution(Action):
    
    def run(self):
        sw = self.software()
        if sw:
            return sw.resolution()
        else:
            return [None, None]

class SetSceneResolution(Action):
    
    _defaultParms = {
        'resolution': None,
    }
    
    progressText = 'Setting scene resolution...'
    
    def run(self):
        sw = self.software()
        if sw:
            res = self.parm('resolution')
            if not res:
                step = self.step()
                pro = self.project()
                res = plcr.getStepConfig(step, 'resolution', project=pro)
            
            if type(res) in (tuple, list):
                if len(res) == 2:
                    sw.setResolution(*res)

class GetFpsFromDatabase(Action):
    
    progressText = 'get fps from database ...'
    
    def run(self):
        import sys
        sys.path.append(r'C:\cgteamwork\bin\base')
        import cgtw
        reload(cgtw)
        
        pro = self.task().get('project')
        tw = cgtw.tw()
        t_info = tw.info_module('public', 'project')
        
        filters = [['project.code', '=', pro]]
        t_info.init_with_filter(filters)
        
        fields = ['project.frame_rate',
                  #'project.resolution',
                  ]
        
        get = t_info.get(fields)
        
        fps = int(get[0]['project.frame_rate'])
        
        return fps
    



class GetWidthFromDatabase(Action):
    
    progressText = 'get width of resolution from database ...'
    
    def run(self):
        import sys
        sys.path.append(r'C:\cgteamwork\bin\base')
        import cgtw
        reload(cgtw)
        
        pro = self.task().get('project')
        tw = cgtw.tw()
        t_info = tw.info_module('public', 'project')
        
        filters = [['project.code', '=', pro]]
        t_info.init_with_filter(filters)
        
        fields = [
                  'project.resolution',
                  ]
        get = t_info.get(fields)

        rs =  get[0]['project.resolution']
        rs = rs.encode('utf-8')
        #print "rs:",rs
        rsList =  rs.split('×')
        return int(rsList[0])


class GetHeightFromDatabase(Action):
    
    progressText = 'get height of resolution from database ...'
    def run(self):
        import sys
        sys.path.append(r'C:\cgteamwork\bin\base')
        import cgtw
        reload(cgtw)
        
        pro = self.task().get('project')
        tw = cgtw.tw()
        t_info = tw.info_module('public', 'project')
        
        filters = [['project.code', '=', pro]]
        t_info.init_with_filter(filters)
        
        fields = [
                  'project.resolution',
                  ]
        get = t_info.get(fields)

        rs =  get[0]['project.resolution']
        rs = rs.encode('utf-8')
        #print "rs:",rs
        rsList =  rs.split('×')
        return int(rsList[1])
    
class GetResolutionFromDatabase(Action):
    
    progressText = 'get width of resolution from database ...'
    
    def run(self):
        import sys
        sys.path.append(r'C:\cgteamwork\bin\base')
        import cgtw
        reload(cgtw)
        
        pro = self.task().get('project')
        tw = cgtw.tw()
        t_info = tw.info_module('public', 'project')
        
        filters = [['project.code', '=', pro]]
        t_info.init_with_filter(filters)
        
        fields = [
                  'project.resolution',
                  ]
        get = t_info.get(fields)

        rs =  get[0]['project.resolution']
        rs = rs.encode('utf-8')
        #print "rs:",rs
        rsList =  rs.split('×')
        return [int(rsList[0]),int(rsList[1])]

class SetSceneFps(Action):
    
    progressText = 'Setting scene fps...'
    _defaultParms = {
        'fps': None,
    }
    def run(self):
        sw = self.software()
        if sw:
            step = self.step()
            pro = self.project()
            fps = self.parm('fps')
            
            if not fps:
                fps = plcr.getStepConfig(step, 'fps', project=pro)
            if type(fps) in (int, float):
                sw.setFps(fps)


class CopyFile(Action):
    
    def run(self):
        sw = self.software()
        if sw:
            proFolder = self.parm('input')
            
            try:
                os.makedirs(proFolder)
            except OSError:
                if not os.path.isdir(proFolder):
                    raise
            
            sw.setProject(proFolder)
            
            return proFolder

class SetSceneHUDs(Action):
    
    def run(self):
        sw = self.software()
        if sw:
            data = self.parm('input')
            if data:
                sw.removeAllHUDs()
                
                # Parse the data
                info = self.task().copy()
                info['date'] = time.strftime('%Y-%m-%d')
                for d in data:
                    #print 'd:',d
                    key = 'label'
                    value = d.get(key)
                    d[key] = info.get(value, value)
                
                sw.setHUDs(data)
                
                return data

class RemoveAllHuds(Action):
    
    def run(self):
        sw = self.software()
        sw.removeAllHUDs()

class CheckGpuExists(Action):
    def run(self):
        import maya.cmds as cmds
        
        allGpu = cmds.ls(type='gpuCache')
        if len(allGpu)>0:
            return False
        else:
            return True

            
class SetSceneHUDs2(Action):
    
    def __init__(self, engine,parent=None):
        Action.__init__(self, engine)
        
        self.frameRange = self.getShotFrameRange()
    
    
    def getShotFrameRange(self):
        pro = self.task().get('project')
        shot = self.task().get('shot')
        shotId = self.task().get('shot_id')
        fRange = self.database().getShotFrameRange(pro, shotId)
        return fRange
    
    def focalLengthLabel(self):
        import maya.cmds as cmds
        shot = self.task().get('shot')
        fRange = self.frameRange
        currnetCameraView = '%s_Cam_F%s_%s'%(shot,fRange[0],fRange[1])
        
        focalLength = cmds.getAttr('%s.focalLength'%currnetCameraView)
        label = '%s/%s'%(currnetCameraView,focalLength)
        
        return label
    
    
    def frameLabel(self):
        import maya.cmds as cmds
        #maxPlaybackend = cmds.playbackOptions(q=True,max=True)
        currentTime = cmds.currentTime(query=True)
        startF = 101
        startFrame = startF
        frameRange = self.frameRange
        lastFrame = int(frameRange[-1])-int(frameRange[0])+101

        DValue = int(frameRange[0]) - startF
        
        
        fps = self.getFps()
        label = u'Frame:%s/%s %sfps' % (int(currentTime)-DValue,int(lastFrame),fps)
        return label
    
    def framesToTimecode(self,frames,framerate):
        frames = int(frames)
        framerate = int(framerate)
        #return '{0:02d}:{1:02d}:{2:02d}:{3:02d}'.format(frames / (3600*framerate),frames / (60*framerate) % 60,frames / framerate % 60,frames % framerate)
        return '{0:02d}:{1:02d}'.format(frames / framerate % 60,frames % framerate)
    
    
    def timeLabel(self,framerate):
        import maya.cmds as cmds
    
        currentTime = cmds.currentTime(query=True)
        startF = 101
        
        frame = currentTime - startF +1
        
        label = self.framesToTimecode(frame,framerate)
        return label
    
    def getFps(self):
        import maya.cmds as cmds
        sw = self.software()
        fps = sw.fps()
        return fps
    
    def run(self):
        import maya.cmds as cmds
        framerate = self.getFps()
        framerate = int(framerate)
        sw = self.software()
        if sw:
            data = self.parm('input')
            if data:
                sw.removeAllHUDs()
                
                # Parse the data
                info = self.task().copy()
                info['date'] = "Date:   %s"%(time.strftime('%Y/%m/%d'))
                
                newData = []
                for d in data:
                    #print 'd:',d
                    key = 'label'
                    value = d.get(key)
                    
                    if value == 'date':
                        d[key] = info.get('date','')
                        newData.append(d)
                        
                    elif value == 'project_shot':
                        if info.get('code') == 'Layout':
                            shortName = 'ly'
                        elif info.get('code') == 'Animation':
                            shortName = 'ani'
                            
                        psLabel = "%s_%s_%s"%(info.get('project',''),info.get('shot',''),shortName)
                        d[key] = psLabel
                        newData.append(d)
                        
                    elif value == 'artist':
                        userName = "USER:   %s"%(info.get('artist',''))
                        d[key] = userName
                        newData.append(d)
                        
                    elif value == 'time':
                        cmds.headsUpDisplay(d['name'], label='',section=d['section'], block=d['block'],
                                            blockSize='small',dfs='large',labelFontSize=d['labelFontSize'],
                                            labelWidth=1,command=lambda: self.timeLabel(framerate),atr=True)
                        
                        #data.remove(d)
                        
                    elif value == 'cam':
                        cmds.headsUpDisplay(d['name'], label='',section=d['section'], block=d['block'],
                                            blockSize='small',dfs='large',labelFontSize=d['labelFontSize'],
                                            labelWidth=1,command=self.focalLengthLabel,atr=True)
                        #data.remove(d)
                        
                    elif value == 'frame':
                        cmds.headsUpDisplay(d['name'], label='',section=d['section'], block=d['block'],
                                            blockSize='small',dfs='large',labelFontSize=d['labelFontSize'],
                                            labelWidth=1,command=self.frameLabel,atr=True)
                        #data.remove(d)
                    
                    
                    #elif value == 'fps':
                    #    
                    #    fps = "%sfps"%framerate
                    #    d[key] = fps
                    #    cmds.headsUpDisplay(d['name'], label=fps,section=d['section'], block=d['block'],
                    #                        blockSize='large',dfs='large',labelFontSize='large')
                        #newData.append(d)
                        
                
                sw.setHUDs(newData)
    
                
                return newData

class SetSceneActiveViewAttributes(Action):
    
    def run(self):
        sw = self.software()
        if sw:
            attribs = self.parm('input')
            if attribs:
                sw.setActiveCameraAttributes(**attribs)
                return attribs

class SetModelPanelDisplayAppearance(Action):
    
    _defaultParms = {"displayType":'smoothShaded'}
    
    def run(self):
        '''
        default displayAppearance "wireframe", "points",
        "boundingBox", "smoothShaded", "flatShaded"
        '''
        import maya.cmds as cmds
        displayType = self.parm('displayType')
        
        modelPanels = cmds.getPanel(type='modelPanel')
        for mp in modelPanels:
            modelEditor = cmds.modelPanel(mp,q=True,me=True)
            if modelEditor != "":
                print "displayType:",displayType
                cmds.modelEditor(mp, edit=True, displayAppearance=displayType)
        
        return displayType        


class MakeScenePlayblast(Action):
    
    _defaultParms = {
        'frame_range': '{scene_frame_range}',
        'resolution': [1920, 1080],
        'scale': 100,
        'quality': 100,
        'movie_codec': '',
        'playblackSpeed':24.0,
    }
    
    def run(self):
        sw = self.software()
        if sw:
            path = self.parm('output')
            frameRange = self.parm('frame_range')
            scale = self.parm('scale')
            quality = self.parm('quality')
            resolution = self.parm('resolution')
            camera = self.parm('camera')
            movieCodec = self.parm('movie_codec')
            
             # make playblack speed
            playblackSpeed = float(self.parm('playblackSpeed'))
            sw._cmds.playbackOptions(playbackSpeed=(playblackSpeed/24))#25.0/24  value is approximately 1.04166666667 
            # --------------------
            
            makeFolder(path)
            
            sw.playblast(path, scale, quality,
                         resolution=resolution,
                         override=True, camera=camera,
                         firstFrame=frameRange[0],
                         lastFrame=frameRange[-1],
                         movieCodec=movieCodec)
            
            return path

class MakeSceneTurntablePlayblast(Action):
    
    _defaultParms = {
        'frame_range': [1, 180],
        'resolution': [1920, 1080],
        'scale': 100,
        'quality': 100,
        'playblackSpeed':24.0,
        'movieCodec': '',
        
    }
    
    def run(self):
        sw = self.software()
        if sw:
            
            path = self.parm('output')
            scale = self.parm('scale')
            quality = self.parm('quality')
            frameRange = self.parm('frame_range')
            resolution = self.parm('resolution')
            #print "resolution:",resolution
            # set playblack speed
            playblackSpeed = float(self.parm('playblackSpeed'))
            #print "playblackSpeed:",playblackSpeed
            sw._cmds.playbackOptions(playbackSpeed=(playblackSpeed/24))#25.0/24  value is approximately 1.04166666667 
            # --------------------
            movieCodec = self.parm('movieCodec')
            
            
            
            tops = sw.getTopLevelObjectsOfMeshes()
            if tops:
                asset = tops[0]
            else:
                return
            
            # If user reference asset, then there's a namespace in the node name 
            objs = sw.findObjects(asset)
            if objs:
                asset = objs[0]
            
            makeFolder(path)
            
            try:
                firstFrame = frameRange[0]
                lastFrame = frameRange[1]
            except:
                firstFrame = None
                lastFrame = None
            
            if movieCodec:
                sw.makeTurntablePlayblast(path, asset,
                                          firstFrame=firstFrame,
                                          lastFrame=lastFrame,
                                          scale=scale,
                                          quality=quality,
                                          resolution=resolution,
                                          override=True,
                                          movieCodec=movieCodec
                                          )
            else:
                sw.makeTurntablePlayblast(path,asset,
                                          firstFrame=firstFrame,
                                          lastFrame=lastFrame,
                                          scale=scale,
                                          quality=quality,
                                          resolution=resolution,
                                          override=True,)

            
            
            return path

class MakeSceneTurntableRenderPreview(Action):
    
    _defaultParms = {
        'renderer': 'arnold',
        'template_path': '',
        'hdrPath': '',
        'frame_range': [1, 180],
        'frame_step': 1,
        'resolution': [1920, 1080],        
        'output': '',
    }
    
    def run(self):
        sw = self.software()
        if sw:
            path = self.parm('output')
            renderer = self.parm('renderer')
            frameRange = self.parm('frame_range')
            resolution = self.parm('resolution')
            hdrPath = self.parm('hdrPath')
            templatePath = self.parm('template_path')
            step = self.parm('frame_step')
            
            tops = sw.getTopLevelObjectsOfMeshes()
            if tops:
                asset = tops[0]
            else:
                return
            
            # If user reference asset, then there's a namespace in the node name 
            objs = sw.findObjects(asset)
            if objs:
                asset = objs[0]
            
            makeFolder(path)
            
            #print 'templatePath:',templatePath
            #print 'hdrPath:',hdrPath
            
            try:
                firstFrame = frameRange[0]
                lastFrame = frameRange[1]
            except:
                firstFrame = None
                lastFrame = None
            
            sw.makeTurntableRenderPreview(path, asset,
                                          renderer=renderer,
                                          firstFrame=firstFrame,
                                          lastFrame=lastFrame,
                                          resolution=resolution,
                                          hdrPath=hdrPath,
                                          templatePath=templatePath,
                                          frameStep=step)
            
            return path

class RenderScene(Action):
    
    _defaultParms = {
        'renderer': 'arnold',
        'frame_range': None,
        'frame_step': 1,
        'resolution': None, 
        'output': '',
        'enable_aovs': False,
        'camera': '',
        'aov_output_path': '<BeautyPath>/<RenderPass>/<BeautyFile>.<RenderPass>', 
        'render_settings': {},
        'return_one': False,
        'silence': False
    }
    
    def run(self):
        sw = self.software()
        if sw:
            path = self.parm('output')
            renderer = self.parm('renderer')
            frameRange = self.parm('frame_range')
            resolution = self.parm('resolution')
            step = self.parm('frame_step')
            enableAOVs = self.parm('enable_aovs')
            camera = self.parm('camera')
            
            if not camera:
                camera = sw.getCurrentView()
            
            #print
            #print 'frameRange:'
            #print frameRange
            
            if not frameRange:
                frameRange = sw.frameRange()
            
            #print
            #print 'frameRange1:'
            #print frameRange
            
            try:
                firstFrame = frameRange[0]
                lastFrame = frameRange[1]
            except:
                firstFrame = None
                lastFrame = None
            
            if path:
                makeFolder(path)
            
            #print 'templatePath:',templatePath
            #print 'hdrPath:',hdrPath
            
            kwargs = {
                'path': path,
                'renderer': renderer,
                'firstFrame': firstFrame,
                'lastFrame': lastFrame,
                'resolution': resolution,
                'camera': camera, 
                'enableAOVs': enableAOVs,
                'frameStep': step,
                'renderSettings': self.parm('render_settings'),
                'aovOutputPath': self.parm('aov_output_path'),
                'silence': self.parm('silence')
            }
            
            r = sw.render(**kwargs)
            
            if self.parm('return_one'):
                return r[0]
            else:
                return r

class CreateRenderNode(Action):
    '''
    Creates a render node in the scene. 
    
    Right now it supports software below:
    
    Nuke:
        It creates a Write node.
        custom_attributes is a list of dictionaries which has keys:
            type: type of Knob in Nuke
            name: parameter name of the attribute
            label: label of the parameter
            readonly: if it's true, set it to readonly status
    '''
    
    _defaultParms = {
        'renderer': 'arnold',
        'frame_range': None,
        'frame_step': 1,
        'resolution': None, 
        'output': '',
        'enable_aovs': False,
        'camera': '',
        'aov_output_path': '<BeautyPath>/<RenderPass>/<BeautyFile>.<RenderPass>', 
        'render_settings': {},
        'custom_attributes': []
    }
    
    def run(self):
        sw = self.software()
        if sw:
            path = self.parm('output')
            renderer = self.parm('renderer')
            frameRange = self.parm('frame_range')
            resolution = self.parm('resolution')
            step = self.parm('frame_step')
            enableAOVs = self.parm('enable_aovs')
            camera = self.parm('camera')
            
            if not camera:
                camera = sw.getCurrentView()
            
            #print
            #print 'frameRange:'
            #print frameRange
            
            if not frameRange:
                frameRange = sw.frameRange()
            
            #print
            #print 'frameRange1:'
            #print frameRange
            
            try:
                firstFrame = frameRange[0]
                lastFrame = frameRange[1]
            except:
                firstFrame = None
                lastFrame = None
            
            makeFolder(path)
            
            #print 'templatePath:',templatePath
            #print 'hdrPath:',hdrPath
            
            kwargs = {
                'path': path,
                'renderer': renderer,
                'firstFrame': firstFrame,
                'lastFrame': lastFrame,
                'resolution': resolution,
                'camera': camera, 
                'enableAOVs': enableAOVs,
                'frameStep': step,
                'renderSettings': self.parm('render_settings'),
                'aovOutputPath': self.parm('aov_output_path'),
                'customAttributes': self.parm('custom_attributes')
            }
            
            r = sw.createRenderNode(**kwargs)
            return r

class ReplaceReadNodesPaths(Action):
    
    _defaultParms = {
        'option': 'node_name',
        'input': ''
    }
    
    def run(self):
        sw = self.software()
        if sw:
            option = self.parm('option')
            
            if option == 'node_name':
                nodes = sw.find(type='Read')
                for name in nodes:
                    n = sw._nuke.toNode(name)
                    kwargs = {'pass': n.name()}
                    self.setFormatKeys(kwargs)
                    path = self.parm('input')

                    n['file'].setValue(path)
                    
class ReplaceReadNodesPaths2(Action):
    
    _defaultParms = {
        'option': 'node_name',
        'input': ''
    }
    
    def run(self):
        sw = self.software()

        first = self.task()['first_frame']
        last = self.task()['last_frame']
        if sw:
            option = self.parm('option')
            
            if option == 'node_name':
                nodes = sw.find(type='Read')
                for name in nodes:
                    n = sw._nuke.toNode(name)
                    n['first'].setValue(int(first))
                    n['last'].setValue(int(last))
                    passName = n['pass'].value()
                    kwargs = {'pass': passName}
                    self.setFormatKeys(kwargs)
                    path = self.parm('input')
                    #print "passName",passName
                    oldPath = n['file'].value()
                    if '/%s/'%passName in oldPath:
                        renderLayer = os.path.basename(oldPath.split('/%s/'%passName)[0])
                    else:
                        renderLayer = os.path.basename(os.path.dirname(oldPath))
                    #print n.name(),oldPath
                    if passName == 'Beauty':
                        #print path,renderLayer
                        path = path.replace('/Beauty','').replace('.Beauty','')
                        #print path,renderLayer
                    path = path.replace('{RenderLayer}',renderLayer)
                    n['file'].setValue(path)

class RunExpression(Action):
    
    _defaultParms = {
        'expression': '',
    }
    
    def run(self):
        ex = self.parm('expression')
        r = {}
        a = {}
        exec(ex, r, a)
        return a

class EvalString(Action):
    
    _defaultParms = {
        'input': '',
    }
    
    def run(self):
        ex = self.parm('input')
        ex = str(ex)
        return eval(ex)

class GetDictValue(Action):
    
    _defaultParms = {
        'input': '',
        'key': '',
    }
    
    def run(self):
        d = self.parm('input')
        key = self.parm('key')
        
        if type(d) == dict:
            return d.get(key)

class CheckFileExists(Action):
    
    def run(self):
        
        path = self.parm('input')
        #print 'path:',path
        if os.path.isfile(path):
            if os.path.exists(path):
                return True
            else:
                return False
        else:
            if os.path.exists(path):
                l = os.listdir(path)
                if len(l) > 0:
                    return True
                else:
                    return False
            else:
                return False

class GetListValue(Action):
    
    _defaultParms = {
        'input': '',
        'index': '',
    }
    
    def run(self):
        d = self.parm('input')
        i = self.parm('index')
        
        if type(d) in (list,tuple) and type(i) == int:
            if len(d) > i:
                return d[i]

class MakeMovie(Action):
    
    _defaultParms = {
        'input': '',         
        'output': '',
        'engine': 'rvio', 
        'fps': 24,
        'quality': 1,
        'first_frame': 0, 
    }
    
    def run(self):
        inputPath = self.parm('input')
        outputPath = self.parm('output')
        ext = os.path.splitext(inputPath)[-1].replace('.', '')
        
        kwargs = {
            'inputPath': inputPath,
            'outputPath': outputPath,
            'fps': self.parm('fps'),
            'quality': self.parm('quality')
        }
        
        first = self.parm('first_frame')
        if type(first) == int:
            kwargs['firstFrame'] = first
        
        engine = self.parm('engine').lower()
        if engine == 'rvio':
            if ext == 'exr':
                kwargs['outsrgb'] = True
            
            engine = rdlb.RVIO()
        
        elif engine == 'ffmpeg':
            engine = rdlb.FFmpeg()
        
        else:
            engine = None
        
        if engine:
            makeFolder(outputPath)
            engine.renderPhotoJPEGMov(**kwargs)
        
        return outputPath

class MakeThumbnail(Action):

    def run(self):
        inputPath = self.parm('input')
        outputPath = self.parm('output')
        
        makeFolder(inputPath)
        
        engine = rdlb.FFmpeg()
        engine.makeJPGSnapshot(inputPath, outputPath)
        
        return outputPath

class SetEnvContext(Action):
    '''Sets current context to system env.'''
    
    progressText = 'Setting working context...'
    
    def run(self):
        #print 'self._task:',self._task
        plcr.setEnv(self.task())

def _getFileOpenRecordFilename(currentFile):
    root = plcr._localSettingsPath()
    filename = os.path.basename(currentFile)
    path = '%s/file_open_%s.json' % (root,filename)
    return path

class MakeFileOpenRecord(Action):
    '''Makes a record after openning the file.'''
    
    _defaultParms = {       
        'input': '{current_file}',
    }
    
    progressText = 'Making file open record...'
    
    def run(self):
        currentFile = self.parm('input')
        currentFile = currentFile.replace('\\', '/')
        
        path = _getFileOpenRecordFilename(currentFile)
        
        info = {
            'file': currentFile,
            'task': self.task()
        }
        info = json.dumps(info, indent=4)
        
        f = open(path, 'w')
        f.write(info)
        f.close()
        
        return path

class CheckFileOpen(Action):
    '''Checks whether the user open the file through the tool.'''
    
    _defaultParms = {       
        'input': '{current_file}',
    }
    
    def run(self):
        result = False
        
        currentFile = self.parm('input')
        currentFile = currentFile.replace('\\', '/')
        
        path = _getFileOpenRecordFilename(currentFile)
        
        if os.path.isfile(path):
            f = open(path, 'r')
            t = f.read()
            f.close()
            
            info = json.loads(t)
            
            #print
            #print 'info:'
            #print info
            #
            #print
            #print 'task:',
            #print self.task()
            
            if type(info) == dict:
                task = info.get('task')
                if type(task) == dict:
                    openedTaskId = str(task.get('id'))
                    currentTaskId = str(self.task().get('id'))
                    if info.get('file') == currentFile and openedTaskId == currentTaskId:
                        result = True
        
        if result == False:
            txt = u'请使用Open工具打开文件!'
            return txt

class CGTeamworkTagException(Exception):
    pass

class GetPathFromTag(Action):
    
    progressText = 'Getting path from tag...'
    
    def run(self):
        tag = self.parm('input')
        task = self.task()
        
        kwargs = {}
        typ = task.get('type')
        kwargs['project'] = self.project()
        kwargs['type'] = typ
        kwargs['sequence'] = task.get('sequence')
        kwargs['shot'] = task.get('shot')
        kwargs['step'] = self.step()
        kwargs['tag'] = tag
        
        #print
        #print 'kwargs:'
        #print kwargs
        
        r = self.database().getPathFromTag(**kwargs)
        
        #print
        #print 'path:'
        #print r
        
        if r:
            return r
        else:
            msg = '%s' % tag
            raise CGTeamworkTagException(msg)

class GetFolder(Action):
    
    _defaultParms = {       
        'input': '',
    }
    
    def run(self):
        path = self.parm('input')
        return os.path.dirname(path)

class GetFilename(Action):
    
    _defaultParms = {       
        'input': '',
    }
    
    def run(self):
        path = self.parm('input')
        return os.path.basename(path)

class GetFileBaseName(Action):
    
    _defaultParms = {       
        'input': '',
    }
    
    def run(self):
        path = self.parm('input')
        temp = os.path.basename(path)
        return os.path.splitext(temp)[0]

class ReplaceString(Action):
    '''Replaces the string for the from and to values.'''
    
    _defaultParms = {       
        'input': '',
        'replace': '',
        'to': ''
    }
    
    def run(self):
        s = self.parm('input')
        fromS = self.parm('replace')
        fromS = fromS.replace('/', '\\')
        toS = self.parm('to')
        
        rePat = re.compile(fromS)
        return rePat.sub(toS, s)

_vnPattern = re.compile('([a-zA-Z]+)?(#+)')
def parseVersionPattern(s):
    result = _vnPattern.findall(s)
    if result:
        # s: tst_lgt_v###.ma
        # result: [('v', '###')]
        # prefix: v
        # padPat: ###
        # vnPat: v###
        # vnFormat: v%03d
        # rePat: tst_lgt_v(\d{3}).ma
        # formatS: tst_lgt_v%03d.ma
        prefix,padPat = result[-1]
        vnPat = prefix + padPat
        count = len(padPat)
        rePat = s.replace(padPat, '(\d{%s})' % count)
        rePat = re.compile(rePat)
        theF = '%0'+str(count)+'d'
        formatS = s.replace(padPat, theF)
        vnFormat = prefix + theF
        return rePat,formatS,vnPat,vnFormat
    else:
        return s,s,'',''

_digitsPattern = re.compile('([a-zA-Z]+)?(\d+)')
def toVersionPattern(string):
    '''
    Converts the string to a version pattern.
    
    Example:
        string: tst_lgt_v002.ma
        return: tst_lgt_v###.ma
    '''
    result = _digitsPattern.findall(string)
    if result:
        # s: tst_lgt_v002.ma
        # result: [('v', '002')]
        # prefix: v
        # digits: 002
        # digitsPat: v002
        # vnPat: v###
        # pattern: tst_lgt_v###.ma
        prefix,digits = result[-1]
        digitsPat = prefix + digits
        vnPat = prefix + len(digits)*'#'
        pattern = string.replace(digitsPat, vnPat)
        return pattern

def toVersionWildcard(string):
    '''
    Converts the string to a version wildcard pattern.
    
    Example:
        string: tst_lgt_v002.ma
        return: tst_lgt_*.ma
    '''
    result = _digitsPattern.findall(string)
    if result:
        # s: tst_lgt_v002.ma
        # result: [('v', '002')]
        # prefix: v
        # digits: 002
        # digitsPat: v002
        # vnPat: v???
        # pattern: tst_lgt_v###.ma
        prefix,digits = result[-1]
        digitsPat = prefix + digits
        vnPat = prefix + len(digits)*'?'
        pattern = string.replace(digitsPat, vnPat)
        return pattern

def getLatestVersion(files, filenamePattern):
    '''
    Gets latest version file of the files.
    files is a list of string of filenames,
    filenamePattern is a string for filtering the files.
    
    Example:
        files:
            tst_lgt_v001.ma
            tst_lgt_v002.ma
        filenamePattern:
            tst_lgt_v###.ma or tst_lgt_v001.ma
        return:
            {version_pattern: v###
             version_format: v%03d
             file_format: tst_lgt_v%03d.ma
             latest_version: v002
             latest_version_number: 2
             latest_file: tst_lgt_v002.ma
             current_version: v003
             current_version_number: 3
             current_file: tst_lgt_v003.ma
            }
    '''
    # Parse patterns
    # filenamePattern: tst_lgt_v###.ma
    # filenameRePattern: tst_lgt_v(\d{3}).ma
    # filenameFormat: tst_lgt_v%03d.ma
    # versionPattern: v###
    # versionRePattern: v(\d{3})
    # versionFormat: v%03d
    filenameRePattern,filenameFormat,versionPattern,versionFormat = parseVersionPattern(filenamePattern)
    #print 'filenameRePattern:',filenameRePattern
    #print 'filenameFormat:', filenameFormat
    #print 'versionPattern:',versionPattern
    #print 'versionFormat:', versionFormat
    
    if filenameRePattern == filenamePattern:
        # filenameRePattern: tst_lgt_v001.ma
        # filenameRePattern: tst_lgt_v###.ma
        filenamePattern = toVersionPattern(filenamePattern)
        if filenamePattern:
            filenameRePattern,filenameFormat,versionPattern,versionFormat = parseVersionPattern(filenamePattern)
        else:
            return
    
    # Filter the files
    okFiles = {}
    for f in files:
        r = filenameRePattern.findall(f)
        #print 'r:',r
        if r:
            vn = int(r[0])
            if not okFiles.has_key(vn):
                okFiles[vn] = []
            okFiles[vn].append(f)
    
    if okFiles:
        lastVersionNumber = sorted(okFiles.keys())[-1]
        latestVersion = versionFormat % lastVersionNumber
        latestFile = okFiles[lastVersionNumber][0]
    else:
        lastVersionNumber = 0
        latestVersion = ''
        latestFile = ''
    
    currentVersionNumber = lastVersionNumber + 1
    currentVersion = versionFormat % currentVersionNumber
    currentFile = filenameFormat % currentVersionNumber
    
    result = {
        'version_pattern': versionPattern, 
        'version_format': versionFormat, 
        'latest_version': latestVersion, 
        'latest_version_number': lastVersionNumber, 
        'latest_file': latestFile, 
        'current_version': currentVersion, 
        'current_version_number': currentVersionNumber, 
        'current_file': currentFile,
    }
    return result

class VersionUp(Action):
    '''
    Folder structure of the work files:
        001_01_model_v002.ma
        versions:
            001_01_model_v001.ma
            001_01_model_v002.ma
            001_01_model_v003.ma
    '''
    
    def run(self):
        sw = self.software()
        if sw:
            # filename: 
            path = self.parm('input')
            #print 'action:',self.name
            #print 'path:',[path]
            folder = os.path.dirname(path)
            filename = os.path.basename(path)
            filename = filename.replace('_______', '_')
            filename = filename.replace('______', '_')
            filename = filename.replace('_____', '_')
            filename = filename.replace('____', '_')
            filename = filename.replace('___', '_')
            filename = filename.replace('__', '_')
            
            if os.path.exists(folder):
                files = os.listdir(folder)
            else:
                files = []
            
            r = getLatestVersion(files, filename)
            result = '%s/%s' % (folder, r['current_file'])
            return result

class GetAutoVersion(Action):
    
    _defaultParms = {       
        'input': '',
        'pattern': 'v###', 
    }
    
    def run(self):
        folder = self.parm('input')
        pattern = self.parm('pattern')
        
        if os.path.exists(folder):
            files = os.listdir(folder)
        else:
            files = []
        
        r = getLatestVersion(files, pattern)
        
        return r['current_version']

class RenameFilePath(Action):
    _defaultParms = {
        'input': '',
        'output': '',
    }
    
    def run(self):
        oldPath = self.parm('input')
        newPath = self.parm('output')
        
        folderPath = os.path.dirname(oldPath)
        os.chdir(folderPath)
        
        if os.path.exists(oldPath):
            makeFolder(newPath)
            os.rename(oldPath,newPath)
            return newPath
    
class VersionUp2(Action):
    '''
    Gets latest version from database
    '''
    
    _defaultParms = {
        'input': '',
        'publish_type': '',
    }
    
    progressText = 'Getting latest filepath...'
    
    def run(self):
        path = self.parm('input')
        publishType = self.parm('publish_type')
        
        #print 'action:',self.name
        #print 'path:',[path]
        folder = os.path.dirname(path)
        filename = os.path.basename(path)
        filename = filename.replace('_______', '_')
        filename = filename.replace('______', '_')
        filename = filename.replace('_____', '_')
        filename = filename.replace('____', '_')
        filename = filename.replace('___', '_')
        filename = filename.replace('__', '_')
        ext = os.path.splitext(filename)[-1]
        
        kwargs = {
            'database': self.database(), 
            'project': self.project(),
            'type': self.task().get('type'),
            'sequence': self.task().get('sequence'),
            'shot': self.task().get('shot'),
            #'episode': '', 
            'steps': self.task().get('step'),
            'task': self.task().get('code'), 
            'latest': False,
            'enableCache': False,
            'publishType': publishType,
            'filetypes': ext.replace('.', '')
        }
        
        #print
        #print 'filters:'
        #print kwargs
        
        temp = plcr.getPublishedFiles(**kwargs)
        
        files = [i['name']+ext for i in temp]
        
        #print
        #print 'files:'
        #print files
        
        r = getLatestVersion(files, filename)
        result = '%s/%s' % (folder, r['current_file'])
        return result


class GetExrFileLastVersion(Action):
    
    def run(self):
        
        steps = self.parm('stepName')
        
        kwargs = {
            'database': self.database(), 
            'project': self.project(),
            'type': self.task().get('type'),
            'sequence': self.task().get('sequence'),
            'shot': self.task().get('shot'),
            #'episode': '', 
            #'task': self.task().get('code'), 
            'latest': True,
            'publishType': 'publish',
            'filetypes': 'exr'
        }
        
        if steps:
            kwargs['steps'] = steps
            kwargs['task'] = steps
        else:
            kwargs['steps'] = self.task().get('step')
            kwargs['task'] = self.task().get('code')
        
        #print kwargs
        temp = plcr.getPublishedFiles(**kwargs)
        #print temp
        if temp:
            return temp[0]['version']
        


class GetVersionNumber(Action):
    '''Gets version number in the string.'''
    
    _defaultParms = {       
        'input': '',
        'pattern': 'v###', 
    }
    
    progressText = 'Getting version number from input...'
    
    def run(self):
        s = self.parm('input')
        pat = self.parm('pattern')
        
        # Get re pattern
        result = _vnPattern.findall(pat)
        if result:
            # prefix: v
            # padPat: ###
            prefix,padPat = result[-1]
            count = len(padPat)
            rePat = pat.replace(padPat, '\d{%s}' % count)
            rePat = re.compile(rePat)
            
            token = rePat.findall(s)
            if token:
                return token[-1]
        
        return ''

class FindString(Action):
    
    _defaultParms = {       
        'input': '',
        'pattern': '',
        'returned_index': -1
    }
    
    def run(self):
        s = self.parm('input')
        pat = self.parm('pattern')
        pat = pat.replace('/', '\\')
        pat = re.compile(pat)
        temp = pat.findall(s)
        if temp:
            i = self.parm('returned_index')
            if type(i) == int:
                try:
                    r = temp[i]
                except:
                    r = temp[-1]
            else:
                r = temp[-1]
        
        else:
            r = ''
        
        return r

class CopyFile(Action):
    
    _defaultParms = {
        'input': '',
        'output': '',
        'force': True
    }
    
    def run(self):
        return True
        inputPath = self.parm('input')
        path = self.parm('output')
        #path = 'd:/project/BHYX/03_Asset/check/Texture/props/box/history/box_Texture_v001/props_box_Texture_check.ma'
        makeFolder(path)
        
        #print '%s -> %s' % (inputPath, path)
        if os.path.isfile(inputPath):
            if os.path.isdir(path):
                filename = os.path.basename(inputPath)
                path = '%s/%s' % (path, filename)
            
            copyFile(inputPath, path)
        
        elif os.path.isdir(inputPath):
            if os.path.exists(path):
                if self.parm('force'):
                    shutil.rmtree(path)
                else:
                    return path
            
            shutil.copytree(inputPath, path)
        
        return path

class RemoveFiles(Action):
    
    def run(self):
        path = self.parm('input')
        files = glob.glob(path)
        for f in files:
            if os.path.isfile(f):
                os.remove(f)
            elif os.path.isdir(f):
                shutil.rmtree(f)

class CombineData(Action):
    
    _defaultParms = {
        'inputs': [],
    }
    
    def run(self):
        inputs = self.parm('inputs')
        if not inputs:
            inputs = []
        
        result = []
        for i in inputs:
            result += i
        
        return result

'''
groupKey = 'namespace'
newKey, newKeySource = 'objects', 'full_path'

data = [{'asset': u'laserwave',
  'full_path': u'|laserwave:world_gp|laserwave:renderMesh_gp|laserwave:laserwave_GRP',
  'namespace': u'laserwave',
  'object': u'laserwave:laserwave_GRP'},
 {'asset': u'laserwave',
  'full_path': u'|laserwave:world_gp|laserwave:renderMesh_gp|mask',
  'namespace': u'laserwave',
  'object': u'mask'},
 {'asset': u'laserwave',
  'full_path': u'|laserwave1:world_gp|laserwave1:renderMesh_gp|laserwave1:laserwave_GRP',
  'namespace': u'laserwave1',
  'object': u'laserwave1:laserwave_GRP'},
 {'asset': u'laserwave',
  'full_path': u'|laserwave2:world_gp|laserwave2:renderMesh_gp|laserwave2:laserwave_GRP',
  'namespace': u'laserwave2',
  'object': u'laserwave2:laserwave_GRP'}]

run(groupKey, newKey, newKeySource, data)
'''

class GroupData(Action):
    
    _defaultParms = {
        'group_key': '',
        'collapse_key': '',
        'new_key': '',
        'data': []
    }
    
    def run(self):
        groupKey = self.parm('group_key')
        newKeySource = self.parm('collapse_key')
        newKey = self.parm('new_key')
        data = self.parm('data')
        
        groups = []
        temp = {}
        for d in data:
            group = d.get(groupKey)
            if not temp.has_key(group):
                temp[group] = []
                groups.append(d)
            temp[group].append(d)
        
        result = []
        for d in groups:
            group = d.get(groupKey)
            
            lst = []
            for info in temp[group]:
                lst.append(info.get(newKeySource))
            
            d[newKey] = lst
            del d[newKeySource]
            
            result.append(d)
        
        return result

class DataTable(Action):
    
    _defaultParms = {
        'input': [],
    }
    
    #def __init__(self, engine):
    #    Action.__init__(self, engine)
    #    
    #    self._items = []
    #
    #def addItem(self, item):
    #    self._items.append(item)
    
    def run(self):
        return self.parm('input')

class FilterDataTable(Action):
    '''
    '''
    
    _defaultParms = {       
        'input': '',
        'filters': {}
    }
    
    def run(self):
        result = []
        
        data = self.parm('input')
        filters = self.parm('filters')
        #print "filters:",filters
        for d in data:
            tem = []
            for f in filters.keys():
                if type(filters[f]) == list:
                    if d.get(f) in filters[f]:
                        tem.append(0)
                elif d.get(f) == filters[f]:
                    tem.append(0)
            
            if len(tem) == len(filters):
                result.append(d)
        return result

class AddData(Action):
    
    _defaultParms = {
        'input': [],
        #''
    }
    
    #def __init__(self, engine):
    #    Action.__init__(self, engine)
    #    
    #    self._items = []
    #
    #def addItem(self, item):
    #    self._items.append(item)
    
    def run(self):
        return self.parm('input')

class SetShotFrameRange(Action):
    
    _defaultParms = {
        'frame_range': '{scene_frame_range}',
    }
    
    def run(self):
        kwargs = {
            'project': self.project(),
            'shotId': self.task().get('shot_id'),
            'value': self.parm('frame_range')
        }
        self.database().updateShotFrameRange(**kwargs)

class GetCurrentRenderLayer(Action):
    
    def run(self):
        sw = self.software()
        return sw.getCurrentRenderLayer()
    


class SetShotLinkedAssets(Action):
    '''
    Sets linked assets of the shot on database based on
    assets in the scene.
    '''
    
    def run(self):
        sw = self.software()
        if sw:
            # Get referenced scene assets
            refs = sw.getReferenceObjects()
            refs += sw.getGpuCaches()
            refs += sw.getAssemblyReferences()
            
            paths = []
            for i in refs:
                path = i['path']
                if path not in paths:
                    paths.append(path)
            
            assetIds = []
            for path in paths:
                info = self.engine().getInfoFromPath(path, enableCache=True)
                
                if info:
                    kwargs = {
                        'project': info.get('project'),
                        'assetType': info.get('sequence'), 
                        'asset': info.get('shot')
                    }
                    id_ = self.database().getAssetId(**kwargs)
                    if id_:
                        assetIds.append(id_)
            
            if assetIds:
                project = self.project()
                shotId = self.task().get('shot_id')
                self.database().updateShotLinkedAssets(project, shotId, assetIds)

class SetShotLinkedAssets2(Action):
    '''
    Sets linked assets of the shot on database based on
    assets in the scene. We search the assets by the group name pattern.
    '''
    
    _defaultParms = {
        'type': 'transform', 
        'name_pattern': '',
        'index': 0,
    }
    
    def run(self):
        sw = self.software()
        if sw:
            typ = self.parm('type')
            pattern = self.parm('name_pattern')
            pat = re.compile(pattern)
            index = self.parm('index')
            
            assets = []
            temp = sw._cmds.ls(type=typ)
            #temp = sw.find(name=key, type=typ, fullPath=True)
            for t in temp:
                token = pat.findall(t)
                if token:
                    asset = token[0]
                    if asset not in assets:
                        assets.append(asset)
            
            assetIds = []
            for asset in assets:
                kwargs = {
                    'project': self.project(),
                    'asset': asset
                }
                id_ = self.database().getAssetId(**kwargs)
                if id_:
                    assetIds.append(id_)
            
            #print
            #print 'assetIds:'
            #print assetIds
            
            if assetIds:
                project = self.project()
                shotId = self.task().get('shot_id')
                self.database().updateShotLinkedAssets(project, shotId, assetIds)

class GetSceneCameras(Action):
    
    _defaultParms = {
        'name_pattern': '',
        'include_hidden': False
    }
    
    def run(self):
        result = []
        
        sw = self.software()
        if sw:
            camPattern = self.parm('name_pattern')
            includeHidden = self.parm('include_hidden')
            
            if camPattern:
                camPattern = camPattern.replace('/', '\\')
                camPattern = re.compile(camPattern)
            
            cams = sw.getCameras(includeHidden=includeHidden)
            
            #print
            #print 'cameras:'
            #pprint.pprint(cams)
            #print
            
            for c in cams:
                go = False
                if camPattern:
                    if camPattern.findall(c['full_path']):
                        go = True
                else:
                    go = True
                
                if go:
                    d = {}
                    #if c['namespace']:
                    #    d['namespace'] = c['namespace']
                    #else:
                        #d['namespace'] = 'camera'
                    
                    d['instance'] = 'camera'
                    d['namespace'] = 'camera'
                    d['asset'] = 'camera'
                    d['object'] = c['name']
                    d['full_path'] = c['full_path']
                    d['node_type'] = 'transform'
                    d['node'] = c['full_path']
                    
                    result.append(d)
        
        return result

def _addAssetInstance(data):
    '''
    Puts a new key called instance for the asset number
    where is more than one instance for the asset. 
    '''
    result = []
    
    for asset in data.keys():
        i = 0
        for d in data[asset]:
            if i:    
                d['instance'] = '%s%s' % (d['asset'], i)
            else:
                d['instance'] = d['asset']
            result.append(d)
            
            i += 1
    
    return result

class GetAnimationPublishedObjects(Action):
    
    _defaultParms = {
        'keyword': '',
    }
    
    def run(self):
        key = self.parm('keyword')
        
        alll = {}
        
        sw = self.software()
        if sw:
            refs = sw.getReferenceObjects()
            #temp = self._software.getReferences()
            for ref in refs:
                #print
                #print 'ref:',ref
                # ref: {name:'', code:'', full_name:'', namespace:'', path:''}
                
                info = self.engine().getInfoFromPath(ref['path'], enableCache=True)
                #print
                #print 'info:',info
                
                if not info:
                    continue
                
                if key:
                    kwargs = {
                        'name': key,
                        'namespace': ref['namespace'],
                    }
                    #print 'kwargs:',kwargs
                    objs = sw.find(**kwargs)
                    if objs:
                        obj = objs[0]
                        
                        #print 'obj:',obj
                        
                        for t in sw.getChildren(obj):
                            d = {}
                            d['namespace'] = ref['namespace']
                            d['asset_type'] = info.get('sequence')
                            d['asset'] = info['shot']
                            d['object'] = t.name()
                            d['full_path'] = t.fullPath()
                            d['ref_node'] = ref['ref_node']
                            d['ref_path'] = ref['ref_path']
                            
                            if not alll.has_key(info['shot']):
                                alll[info['shot']] = []
                            alll[info['shot']].append(d)
                
                else:
                    d = {}
                    d['namespace'] = ref['namespace']
                    d['asset_type'] = info.get('sequence')
                    d['asset'] = info['shot']
                    d['object'] = ref['full_name']
                    d['full_path'] = ref['full_name']
                    d['ref_node'] = ref['ref_node']
                    d['ref_path'] = ref['ref_path']
                    
                    if not alll.has_key(info['shot']):
                        alll[info['shot']] = []
                    alll[info['shot']].append(d)
        #print alll
        result = _addAssetInstance(alll)
        #print 'result:',result
        
        return result

class GetAnimationPublishedObjects2(Action):
    '''
    Gets object under the root group, then check which one match the
    name pattern.
    Example:
        aaa_rig:
            renderMesh
                dog_Model_GRP
                cat_Model_GRP
        
        keyword: renderMesh
        name_pattern: [a-zA-Z]_Model_GRP
        index: 0
        return:[
                {'asset':'dog', 'object':'',
                'full_path':'', 'instance':'dog'}
            ]
    '''
    
    _defaultParms = {
        'keyword': '',
        'type': 'transform', 
        'name_pattern': '',
        'index': 0,
    }
    
    def run(self):
        sw = self.software()
        if sw:
            alll = {}
            
            key = self.parm('keyword')
            typ = self.parm('type')
            pattern = self.parm('name_pattern')
            pat = re.compile(pattern)
            index = self.parm('index')
            newKey = 'asset'
            
            temp = sw.find(name=key, type=typ, fullPath=True)
            for t in temp:
                for c in sw.getChildren(t, type=typ):
                    token = pat.findall(c.name())
                    if token:
                        value = token[0]
                        
                        info = {
                            'namespace': c.namespace(),
                            'asset_type': '',
                            newKey: value,
                            'object': c.name(),
                            'full_path': c.fullPath(),
                            'ref_node': '', 
                            'ref_path': ''
                        }
                        
                        if not alll.has_key(value):
                            alll[value] = []
                        alll[value].append(info)
            
            result = _addAssetInstance(alll)
            
            return result
        
        return []

class GetAnimationPublishedObjects3(Action):
    
    '''
    export chars , props , cameras
    '''
    
    _defaultParms = {
        'keyword': '',
    }
    
    def run(self):
        key = self.parm('keyword')
        
        alll = {}
        
        sw = self.software()
        if sw:
            refs = sw.getReferenceObjects()
            #temp = self._software.getReferences()
            for ref in refs:
                #print
                #print 'ref:',ref
                # ref: {name:'', code:'', full_name:'', namespace:'', path:''}
                
                info = self.engine().getInfoFromPath(ref['path'], enableCache=True)
                #print
                #print 'info:',info
                
                if not info:
                    continue
                
                if key:
                    kwargs = {
                        'name': key,
                        'namespace': ref['namespace'],
                    }
                    #print 'kwargs:',kwargs
                    objs = sw.find(**kwargs)
                    if objs:
                        obj = objs[0]
                        
                        #print 'obj:',obj
                        
                        for t in sw.getChildren(obj):
                            d = {}
                            d['namespace'] = ref['namespace']
                            d['asset_type'] = info.get('sequence')
                            d['asset'] = info['shot']
                            d['object'] = t.name()
                            d['full_path'] = t.fullPath()
                            d['ref_node'] = ref['ref_node']
                            d['ref_path'] = ref['ref_path']
                            
                            if not alll.has_key(info['shot']):
                                alll[info['shot']] = []
                            alll[info['shot']].append(d)
                
                else:
                    d = {}
                    d['namespace'] = ref['namespace']
                    d['asset_type'] = info.get('sequence')
                    d['asset'] = info['shot']
                    d['object'] = ref['full_name']
                    d['full_path'] = ref['full_name']
                    d['ref_node'] = ref['ref_node']
                    d['ref_path'] = ref['ref_path']
                    
                    if not alll.has_key(info['shot']):
                        alll[info['shot']] = []
                    alll[info['shot']].append(d)
                    
                    
                    
                # ------------- add props --------------------
                #print 'info:',info
                
                if info.get('sequence') == 'props':
                    
                    kwargs2 = {
                        'name': "%s_Mod"%info['shot'],
                        'namespace': ref['namespace'],
                    }
                    #print 'kwargs:',kwargs
                    objs = sw.find(**kwargs2)
                    if objs:
                        obj = objs[0]
                    
                        
                        d = {}
                        d['namespace'] = ref['namespace']
                        d['asset_type'] = info.get('sequence')
                        d['asset'] = info['shot']
                        d['object'] = obj
                        d['full_path'] = sw._cmds.ls(obj,long=1)[0]
                        d['ref_node'] = ref['ref_node']
                        d['ref_path'] = ref['ref_path']
                        
                        if not alll.has_key(info['shot']):
                            alll[info['shot']] = []
                        alll[info['shot']].append(d)
                
        #print alll
        result = _addAssetInstance(alll)
        #print 'result:',result
        
        
        return result


class GetShotLinkedAssets(Action):
    
    _defaultParms = {
        'shot': ''
    }
    
    def run(self):
        shot = self.parm('shot')
        return self.database().getShotLinkedAssets(shot)

class GetPublishedFiles(Action):
    
    _defaultParms = {
        'project': '',
        'type': '',
        'sequence': '',
        'shot': '',
        #'episode': '', 
        'steps': [],
        'latest': False,
        'enableCache': False,
        'parts': [],
        'filetypes': []
    }
    
    def run(self):
        keys = self._parms.keys()
        kwargs = self.parms(keys)
        if not kwargs['project']:
            kwargs['project'] = self.project()
        kwargs['database'] = self.database()
        
        #print
        #print 'filters:'
        #print kwargs
        
        temp = plcr.getPublishedFiles(**kwargs)
        
        #print
        #print 'result:'
        #print temp
        
        return temp

class GetPublishedFiles(Action):
    
    _defaultParms = {
        'project': '',
        'type': '',
        'sequence': '',
        'shot': '',
        #'episode': '', 
        'steps': [],
        'latest': False,
        'enableCache': False,
        'parts': [],
        'filetypes': []
    }
    
    def run(self):
        keys = self._parms.keys()
        kwargs = self.parms(keys)
        if not kwargs['project']:
            kwargs['project'] = self.project()
        kwargs['database'] = self.database()
        
        #print
        #print 'filters:'
        #print kwargs
        
        temp = plcr.getPublishedFiles(**kwargs)
        
        #print
        #print 'result:'
        #print temp
        
        return temp

class GetWorkfileId(Action):
    
    _defaultParms = {
        'project': '',
        'name': ''
    }
    
    def run(self):
        project = self.parm('project')
        if not project:
            project = self.project()
        
        name = self.parm('name')
        entity = 'version'
        filters = [
            ['project', '=', project], 
            ['version.version_type', '=', 'workfile'],
            ['version.name', '=', name]
        ]
        fields = ['version.id']
        temp = self.database().find(entity, filters, fields)
        if temp:
            return temp[0]['version.id']

class GetAssemblyElements(Action):
    '''
    Finds the assembly elements for the shot.
    
    If layout is an empty list, get assets from shot links.
    
    Example of layout data:
    [
        {
            "name": "world_gp", 
            "namespace": "laserwave1", 
            "transform": {
                "translateX": 0.0, 
                "translateY": 0.0, 
                "translateZ": 0.0, 
                "scaleX": 1.0, 
                "scaleY": 1.0, 
                "scaleZ": 1.0, 
                "rotateX": 0.0, 
                "rotateY": 0.0, 
                "rotateZ": 0.0
            }, 
            "node_type": "transform", 
            "asset": "laserwave", 
            "full_name": "laserwave1:world_gp"
        }
    ]
    
    Returns a list of dictionaries:
    [
        {
            'asset': 'camera',
            'asset_type': '',
            'transform': {}, 
            'elements_order': ['shape'] 
            'elements': {
                'shape': [
                    {'name': 'shape', 'step':'animation', 'filetype':'abc', 'path': ''},
                    {'name': 'material', 'step':'', 'path': ''},
                    {'name': 'transform', 'step':'', 'path': ''}, 
                ]
            }
        },
        {
            'asset': 'buildingA',
            'asset_type': 'sets',
            'transform': {}, 
            'elements': {
                'shape': [
                    {'name': 'shape', 'step':'rig', 'filetype':'gpu', 'path': ''},
                    {'name': 'material', 'step':'', 'path': ''},
                    {'name': 'transform', 'step':'', 'path': ''}, 
                ]
            }
        }, 
        {
            'asset': 'dog',
            'asset_type': 'chr',
            'transform': {}, 
            'elements': {
                'shape': [
                    {'name': 'shape', 'step':'', 'path': ''},
                    {'name': 'material', 'step':'', 'path': ''},
                    {'name': 'transform', 'step':'', 'path': ''}, 
                ]
            }
        }
    ]
    '''
    
    _defaultParms = {
        'shot': '',
        'layout': [],
        'camera': {
            'shape': {
                'type': 'shot',
                'steps': 'ani',
                'parts': 'camera',
                'filetypes': 'abc'
            }
        },
        'elements_order': ['shape'],
        'default_asset_type': 'DEFAULT', 
        'elements': {
            'sets': {
                'shape': [
                    {
                        'type': 'asset', 
                        'steps': 'rig', 
                        'parts': 'model', 
                        'filetypes': 'gpu'
                    },
                    {
                        'type': 'asset', 
                        'steps': 'mod', 
                        'parts': 'model', 
                        'filetypes': 'gpu'
                    }
                ],
                'material': []
            }, 
            'chars': {
                'shape': [
                    {
                        'type': 'shot', 
                        'steps': 'animation', 
                        'filetypes': 'abc'
                    }
                ]
            }
        }
    }
    
    def run(self):
        plcr.clearConfigCache()
        
        #print
        result = []
        
        shot = self.parm('shot')
        elementsOrder = self.parm('elements_order')
        if not elementsOrder:
            elementsOrder = []
        elementsInfo = self.parm('elements')
        cameraInfo = self.parm('camera')
        layoutInfo = self.parm('layout')
        pro = shot.get('project')
        defaultAType = self.parm('default_asset_type')
        
        #print
        #print 'shot:',shot
        #print
        
        if type(layoutInfo) in (str, unicode):
            f = open(layoutInfo, 'r')
            t = f.read()
            f.close()
            layoutInfo = json.loads(t)
        
        # Get layout info
        if not layoutInfo:
            layoutInfo = []
            
            #print
            #print 'Getting shot assets'
            assets = self.database().getShotLinkedAssets(shot)
            #print 'Done'
            
            for asset in assets:
                #print
                #print 'asset:',asset
                
                info = {
                    "name": asset['code'], 
                    "namespace": '', 
                    "node_type": "transform", 
                    "asset": asset['code'],
                    'asset_type': asset['sequence'], 
                    "full_name": asset['code'],
                    'instance': asset['code']
                }
                layoutInfo.append(info)
        
        result = []
        
        # Get camera
        if not cameraInfo:
            cameraInfo = {}
        
        if cameraInfo:
            elements = {}
            for key in cameraInfo.keys():
                temp = []
                for unit in cameraInfo[key]:
                    kwargs = {
                        'database': self.database(),
                        'project': pro, 
                        'sequence': shot.get('sequence'),
                        'shot': shot.get('code'),
                        'latest': True,
                        'enableCache': True
                    }
                    kwargs.update(unit)
                    
                    #print
                    #print 'Getting published cameras'
                    temp1 = plcr.getPublishedFiles(**kwargs)
                    #print 'Done'
                    
                    temp += temp1
                
                if temp:
                    elements[key] = temp
            
            if elements:
                unit = {
                    'asset': 'camera',
                    'asset_type': '',
                    'elements_order': elementsOrder, 
                    'elements': elements
                }
                result.append(unit)
        
        # Get normal assets
        for lay in layoutInfo:
            #print
            #print 'lay:',lay
            
            asset = lay['asset']
            assetType = lay['asset_type']
            part = lay['instance']
            trans = lay.get('transform')
            if not trans:
                trans = {}
            #print 'part:',part
            
            subs = lay.get('subs')
            if not subs:
                subs = []
            
            setup = elementsInfo.get(assetType)
            if not setup:
                setup = elementsInfo.get(defaultAType)
            
            if setup:
                elements = {}
                
                for key in setup.keys():
                    temp = []
                    for unit in setup[key]:
                        typ = unit.get('type')
                        
                        if typ == 'shot':
                            kwargs = {
                                'database': self.database(),
                                'project': pro, 
                                'sequence': shot.get('sequence'),
                                'shot': shot.get('code'),
                                'latest': True,
                                'enableCache': True
                            }
                            kwargs['parts'] = [part]
                            kwargs.update(unit)
                        
                        else:
                            kwargs = {
                                'database': self.database(),
                                'project': pro, 
                                'sequence': assetType,
                                'shot': asset,
                                'latest': True,
                                'enableCache': True
                            }
                            kwargs.update(unit)
                        
                        #print
                        #print 'Getting published files...'
                        #print 'kwargs:',kwargs
                        
                        temp1 = plcr.getPublishedFiles(**kwargs)
                        #print temp1
                        #print 'Done'
                        
                        temp += temp1
                    
                    elements[key] = temp
                
                if elements:
                    unit = {
                        'asset': asset,
                        'asset_type': assetType,
                        'elements_order': elementsOrder, 
                        'elements': elements
                    }
                    
                    if trans:
                        unit['transform'] = trans
                    if subs:
                        unit['subs'] = subs
                    
                    result.append(unit)
        
        plcr.clearConfigCache()
        
        return result

class TranslateAssemblyElements(Action):
    '''
    Translates assembly elements data to a list of versions.
    input data is the result of GetAssemblyElements action.
    
    Example: 
    [
        {'shape': {}, 'material': {}},
        {},
    ]
    '''
    
    _defaultParms = {
        'input': '',
    }
    
    def run(self):
        data = self.parm('input')
        if not data:
            data = []
        
        result = []
        
        for d in data:
            info = {}
            trans = d.get('transform')
            if not trans:
                trans = {}
            if trans:
                info['transform'] = trans
            
            elements = d.get('elements')
            if not elements:
                elements = {}
            
            for key in elements.keys():
                if elements[key]:
                    info[key] = elements[key][0]
            
            if info:
                result.append(info)
        
        return result

class CreateVar(Action):
    
    _defaultParms = {
        'input': '',
    }
    
    def run(self):
        return self.parm('input')

class CreateDict(Action):
    
    _defaultParms = {}
    
    def run(self):
        result = {}
        for key in self._parms.keys():
            value = self.parm(key)
            result[key] = value
        
        return result

class SplitString(Action):
    
    _defaultParms = {
        'input': '',
        'splitter': '',
        'index': 0
    }
    
    def run(self):
        s = self.parm('input')
        splitter = self.parm('splitter')
        index = self.parm('index')
        return s.split(splitter)[index]

class If(Action):
    
    _defaultParms = {}
    
    def run(self):
        go = []
        keys = self._parms.keys()
        for key in keys:
            key1 = '{%s}' % key
            caseValue = self.parseValue(key1, extraArgs=self._formatKeys)
            value = self.parm(key)
            if type(value) in (tuple, list):
                if caseValue in value:
                    go.append(1)
            else:
                if caseValue == value:
                    go.append(1)
        
        if len(go) == len(keys):
            action = self._subs[0]
        else:
            action = self._subs[1]
        
        #print
        #print 'If.parms:',self._parms
        #print 'action:',action
        
        action.setFormatKeys(self._formatKeys)
        r = self.engine().runAction(action)
        
        return r

class ForLoop(Action):
    
    _defaultParms = {
        'input': '',
    }
    
    def count(self):
        '''Count of the sub items.'''
        n1 = len(self.parm('input'))
        n2 = len(self.subs())
        return n1*n2
    
    def run(self):
        result = []
        
        inputs = self.parm('input')
        for info in inputs:
            #print
            #print 'ForLoop.info:'
            #pprint.pprint(info)
            #print
            
            r = {}
            for sub in self._subs:
                #print
                #print 'sub:',sub
                #print
                sub.setFormatKeys(info)
                r = self.engine().runAction(sub)
            
            result.append(r)
        
        return result

class Boolean(Action):
    '''
    A boolean action.
    True to run sub node1, else to run sub node2.
    '''
    
    _defaultParms = {
        'input': '',
    }
    
    def run(self):
        node1,node2 = None,None
        n = len(self._subs)
        if n == 1:
            node1 = self._subs[0]
        elif n > 1:
            node1,node2 = self._subs[:2]
        
        r = self.parm('input')
        self.engine().setActionValue(self.name, r)
        
        #print 'result:',[r]
        
        if r:
            if node1:
                node1.run()
        else:
            if node2:
                node2.run()
        
        return r

class ExportScene(Action):
    
    _defaultParms = {
        'object': '', 
        'output': '',
    }
    
    progressText = 'Exporting scene objects...'
    
    def run(self):
        sw = self.software()
        if sw:
            obj = self.parm('object')
            path = self.parm('output')
            makeFolder(path)
            
            if obj:
                try:
                    sw.clearSelection()
                    sw.select(obj)
                    sw.exportSelected(path)
                except:
                    showWorkfileError(sw)
            
            else:
                try:
                    sw.exportAll(path)
                except:
                    showWorkfileError(sw)
            
            return path

class ExportAbc(Action):
    
    _defaultParms = {
        'input': '',
        'output': '',
        'single_frame': True,
        'options': [
            '-ro',
            '-stripNamespaces',
            '-uvWrite',
            '-writeVisibility',
            '-writeUVSets',
            '-worldSpace',
            '-dataFormat ogawa',
        ]
    }
    
    progressText = 'Exporting abc cache...'
    
    def run(self):
        sw = self.software()
        objs = self.parm('input')
        #print 'objs:',[objs]
        if sw and objs:
            if type(objs) != list:
                objs = [objs]
            
            #print 'objs1:',objs
            
            path = self.parm('output')
            options = self.parm('options')
            
            #print
            #print 'path:'
            #print [path]
            
            makeFolder(path)
            
            kwargs = {
                'path': path,
                'singleFrame': self.parm('single_frame'),
                'objects': objs
            }
            if options:
                kwargs['options'] = options
            
            sw.exportAbc(**kwargs)
            
            return path

class ExportAbc2(Action):
    
    _defaultParms = {
        'input': '',
        'output': '',
        'single_frame': True
    }
    
    def run(self):
        sw = self.software()
        tops = self.parm('input')
        if sw and tops:
            path = self.parm('output')
            sw.exportAbc(path, singleFrame=self.parm('single_frame'),
                         objects=tops)
            return path

class ExportGpu(Action):
    
    _defaultParms = {
        'input': '',
        'output': '',
        'single_frame': True
    }
    
    progressText = 'Exporting gpu cache...'
    
    def run(self):
        sw = self.software()
        tops = self.parm('input')
        if sw and tops:
            path = self.parm('output')
            makeFolder(path)
            sw.exportGpuCache(path, singleFrame=self.parm('single_frame'),
                              objects=tops)
            return path

class ExportRedshiftProxy(Action):
    
    _defaultParms = {
        'single_frame': True,
        'frame_range': None,
        'input': [],
        'output': '',
    }
    
    def run(self):
        sw = self.software()
        tops = self.parm('input')
        if sw and tops:
            singleFrame = self.parm('single_frame')
            frameRange = self.parm('frame_range')
            path = self.parm('output')
            makeFolder(path)
            sw.exportRedshiftProxy(path, singleFrame=singleFrame,
                                   frameRange=frameRange,
                                   objects=tops)
            return path

class ExportRedshiftProxyScene(Action):
    
    _defaultParms = {
        'single_frame': True,
        'frame_range': None,
        'input': [],
        'output': '',
    }
    
    progressText = 'Exporting Redshift proxy...'
    
    def run(self):
        sw = self.software()
        tops = self.parm('input')
        if sw and tops:
            singleFrame = self.parm('single_frame')
            frameRange = self.parm('frame_range')
            path = self.parm('output')
            makeFolder(path)
            sw.exportRedshiftProxyScene(path, singleFrame=singleFrame,
                                        frameRange=frameRange,
                                        objects=tops)
            return path

class ExportBoundingbox(Action):
    
    _defaultParms = {
        'input': '',
        'output': '',
    }
    
    progressText = 'Exporting bounding box...'
    
    def run(self):
        sw = self.software()
        tops = self.parm('input')
        if sw and tops:
            path = self.parm('output')
            makeFolder(path)
            sw.exportBoundingbox(path, tops[0])
            return path

class CreateAssemblyDefinitionScene(Action):
    
    _defaultParms = {
        'output': '',
        'name': '',
        'files': [],
        'actived': ''
    }
    
    progressText = 'Creating assembly scene...'
    
    def run(self):
        sw = self.software()
        files = self.parm('files')
        if sw and files:
            name = self.parm('name')
            path = self.parm('output')
            actived = self.parm('actived')
            sw.createAssemblyDefinitionScene(path, name=name,
                                             files=files,
                                             actived=actived)
            return path

class CreateAssemblyReferenceScene(Action):
    
    _defaultParms = {
        'input': '',
        'output': '',
        'name': '',
        'actived': ''
    }
    
    def run(self):
        sw = self.software()
        if sw:
            name = self.parm('name')
            adPath = self.parm('input')
            path = self.parm('output')
            actived = self.parm('actived')
            sw.createAssemblyReferenceScene(path, adPath=adPath,
                                            name=name,
                                            actived=actived)
            return path

class GetSceneMaterials(Action):
    
    _defaultParms = {
        'remove_namespace': False
    }
    
    def run(self):
        sw = self.software()
        if sw:
            removeNamespace = self.parm('remove_namespace')
            return sw.getMaterials(removeNamespace=removeNamespace)
        
        return {}

class ExportMaterials(Action):
    
    _defaultParms = {
        'export_textures': False,
        'textures_root': '',
        'output': '',
        'mapping_filename': 'mapping',
        'generate_mapping': True,
        'materials': {}
    }
    
    progressText = 'Exporting scene materials...'
    
    def run(self):
        sw = self.software()
        if sw:
            output = self.parm('output')
            makeFolder(output)
            mappingFilename = self.parm('mapping_filename')
            generateMapping = self.parm('generate_mapping')
            materials = self.parm('materials')
            
            sw.exportMaterials(output, generateMapping=generateMapping,
                               mappingFilename=mappingFilename, 
                               removeNamespace=True,
                               materials=materials)
            return output

class ExportMaterials2(Action):
    '''Exports all materials and objects materials mapping to a json file.'''
    
    _defaultParms = {
        'export_textures': False,
        'textures_root': '',
        'output': '',
        'configs': {},
        'objects': []
    }
    
    def run(self):
        sw = self.software()
        if sw:
            output = self.parm('output')
            configs = self.parm('configs')
            objs = self.parm('objects')
            makeFolder(output)
            
            #print
            #print 'output:',output
            
            sw.exportMaterials2(output, removeNamespace=True,
                                configs=configs, objects=objs)
            return output

def getFileMd5(path):
    import md5
    
    if os.path.isfile(path):
        f = open(path, 'rb')
        txt = f.read()
        f.close()
        
        result = md5.new(txt)
        return result.hexdigest()

class ExportTextures(Action):
    '''
    Copy textures to the target folder, version up each time copying the file.
    Check md5 of the latest version file to make sure only copy different files.
    
    Example:
        filepath:
            TST\assets\chr\dog\srf\work\textures\body_dif.1001.tif
        targetPath:
            TST\assets\chr\dog\srf\publish\textures
        files in targetPath:
            body_dif.1001
                body_dif.1001_v001.tif
                body_dif.1001_v002.tif
    '''
    
    _defaultParms = {
        'material_path': '',
        'output': '',
        'version_pattern': '_v###',
    }
    
    def run(self):
        sw = self.software()
        if sw:
            matPath = self.parm('material_path')
            output = self.parm('output')
            pattern = self.parm('version_pattern')
            
            textures = sw.getTexturePaths()
            
            pathInfo = {}
            for texPath in textures.values():
                if os.path.isfile(texPath):
                    
                    filename = os.path.basename(texPath)
                    baseName,ext = os.path.splitext(filename)
                    folder = '%s/%s' % (output, baseName)
                    if os.path.exists(folder):
                        files = os.listdir(folder)
                    else:
                        os.makedirs(folder)
                        files = []
                    
                    filePattern = '%s%s%s' % (baseName, pattern, ext)
                    r = getLatestVersion(files, filePattern)
                    
                    # Check md5
                    latestPath = '%s/%s' % (folder, r['latest_file'])
                    latestMd5 = getFileMd5(latestPath)
                    fileMd5 = getFileMd5(texPath)
                    #print '%s: %s' % (latestPath, latestMd5)
                    #print '%s: %s' % (texPath, fileMd5)
                    if fileMd5 == latestMd5:
                        targetPath = latestPath
                    else:
                        # Copy the target file to versions folder
                        targetPath = '%s/%s' % (folder, r['current_file'])
                        copyFile(texPath, targetPath)
                    
                    pathInfo[texPath] = targetPath
            
            if matPath:
                sw.replaceTexturePaths(matPath, pathInfo)

class ExportTextures2(Action):
    '''Copy textures to the target folder, override the existing files.'''
    
    _defaultParms = {
        'textures': [], 
        'material_path': '',
        'output': '',
    }
    
    def run(self):
        sw = self.software()
        if sw:
            matPath = self.parm('material_path')
            output = self.parm('output')
            textures = self.parm('textures')
            
            if not textures:
                textures = sw.getTexturePaths().values()
            
            pathInfo = {}
            for texPath in textures:
                if os.path.isfile(texPath):
                    filename = os.path.basename(texPath)
                    targetPath = '%s/%s' % (output, filename)
                    
                    # Check md5
                    texPathMd5 = getFileMd5(texPath)
                    targetPathMd5 = getFileMd5(targetPath)
                    #print '%s: %s' % (latestPath, latestMd5)
                    #print '%s: %s' % (texPath, fileMd5)
                    if texPathMd5 != targetPathMd5:
                        makeFolder(targetPath)
                        copyFile(texPath, targetPath)
                    
                    pathInfo[texPath] = targetPath
            
            if matPath:
                sw.replaceTexturePaths(matPath, pathInfo)
            

class ExportTextures3(Action):
    '''Copy textures to the target folder, override the existing files.'''
    
    _defaultParms = {
        'output': '',
        'replaceOutput':'',
        'rsNormalMap':False,
    }
    
    def run(self):
        sw = self.software()
        
        if sw:
            output = self.parm('output')
            replaceOutput =  self.parm('replaceOutput')
            rsNormalMap = self.parm('rsNormalMap')
            
            #print "rsNormalMap:",rsNormalMap
            textures = sw.getTexturePaths2(rsNormalMap = rsNormalMap)
            pathInfo = []
            # textures: {'file':{'fileNodes':[],}}
            
            for typ in textures.keys():
                texDic = textures[typ]
                for fn in texDic.keys():
                    texPathList = texDic[fn]
                    for texPath in texPathList:
    
                        if os.path.isfile(texPath):
                            texPath = texPath.replace('\\','/')
                            
                            filename = os.path.basename(texPath)
                            targetPath = '%s/%s' % (output, filename)
                            
                            # Check md5
                            texPathMd5 = getFileMd5(texPath)
                            targetPathMd5 = getFileMd5(targetPath)
                            #print '%s: %s' % (latestPath, latestMd5)
                            #print '%s: %s' % (texPath, fileMd5)
                            if texPathMd5 != targetPathMd5:
                                makeFolder(targetPath)
                                copyFile(texPath, targetPath)
                            
                            if replaceOutput:
                                targetPath = '%s/%s' % (replaceOutput, filename)
                            #      ['file','fileNodes','path1','path2']    
                            pathInfo.append([typ,fn,texPath,targetPath])
                        
            return pathInfo
        
class replaceTexturePath(Action):
    
    _defaultParms = {
        'input': [],
        'replaceTo':'',
    }
    
    def run(self):
        '''
        replaceTo is only "new" or "old"
        '''
        sw = self.software()
        if sw:
            pathInfo = self.parm('input')
            replaceTo = self.parm('replaceTo')
            
            sw.replaceTexturePaths2(pathInfo,replaceTo=replaceTo)
    

class ExportSets(Action):
    
    _defaultParms = {
        'set_types': [],
    }
    
    progressText = 'Exporting scene sets...'
    
    def run(self):
        sw = self.software()
        if sw:
            step = self.task().get('step')
            allTypes = plcr.getStepConfig(step, 'set_types')
            types = self.parm('set_types')
            
            if not types:
                types = []
            if not allTypes:
                allTypes = []
            
            parms = []
            for t in types:
                for t1 in allTypes:
                    name = t1.get('name')
                    if name and t == name:
                        ps = t1.get('parms')
                        if not ps:
                            ps = []
                        parms.extend(ps)
                        break
            
            #print 'set types:',types
            #print 'set parms:',parms
            
            info = sw.getSets(types=types, parms=parms)
            
            infoPath = self.parm('output')
            if info:
                makeFolder(infoPath)
                txt = json.dumps(info, indent=4)
                f = open(infoPath, 'w')
                f.write(txt)
                f.close()
            
            return infoPath

class ExportSceneLayout(Action):
    
    _defaultParms = {
        'asset_types': ['env'],
        'extra_group': '', 
        'extra_group_asset_type': 'other',
        'extra_group_asset': 'other', 
        'input': '{top_level_meshes}',
        'output': '{version_root}/layout.json',
        'all_subs_asset_types': [],
        'all_subs': False,
        'default_transform': {
            "translateX": 0.0, 
            "translateY": 0.0, 
            "translateZ": 0.0, 
            "scaleX": 1.0, 
            "scaleY": 1.0, 
            "scaleZ": 1.0, 
            "rotateX": 0.0, 
            "rotateY": 0.0, 
            "rotateZ": 0.0
        }, 
    }
    
    def getTransform(self, obj):
        sw = self.software()
        defaultTransform = self.parm('default_transform')
        r = sw.getTransform(obj)
        if defaultTransform:
            if r != defaultTransform:
                return r
        else:
            return r
        
        return {}
    
    def run(self):
        sw = self.software()
        if sw:
            assetTypes = self.parm('asset_types')
            allSubsATypes = self.parm('all_subs_asset_types')
            
            # Get scene output assets
            refs = sw.getReferenceObjects()
            refs += sw.getGpuCaches()
            refs += sw.getAssemblyReferences()
            
            alll = {}
            for i in refs:
                info = self.engine().getInfoFromPath(i['path'], enableCache=True)
                asset = info.get('shot')
                assetType = info.get('sequence')
                
                go = False
                if assetTypes:
                    if assetType in assetTypes:
                        go = True
                else:
                    go = True
                
                if go:
                    d = {
                        'asset': asset,
                        'asset_type': assetType, 
                        'name': i['name'],
                        'full_name': i['full_name'], 
                        'namespace': i['namespace'],
                        'node_type': i['node_type'], 
                        'transform': self.getTransform(i['transform_node'])
                    }
                    
                    # Get transform of all sub nodes
                    if assetType in allSubsATypes:
                        if self.parm('all_subs'):
                            subTransforms = []
                            subs = sw.getAllSubChildren(i['transform_node'], type='transform')
                            for sub in subs:
                                t = self.getTransform(sub)
                                if t:
                                    info = {
                                        'name': sub.split('|')[-1],
                                        'full_name': sub,
                                        'transform': t
                                    }
                                    subTransforms.append(info)
                            
                            d['subs'] = subTransforms
                    
                    if not alll.has_key(asset):
                        alll[asset] = []
                    alll[asset].append(d)
            
            result = _addAssetInstance(alll)
            
            extraGroup = self.parm('extra_group')
            if sw.exists(extraGroup):
                extraGroupAssetType = self.parm('extra_group_asset_type')
                extraGroupAsset = self.parm('extra_group_asset')
                info = {
                    'instance': extraGroupAsset,
                    'asset': extraGroupAsset,
                    'asset_type': extraGroupAssetType, 
                    'name': extraGroup,
                    'full_name': extraGroup, 
                    'namespace': '',
                    'node_type': 'transform', 
                    'transform': self.getTransform(extraGroup)
                }
                result.append(info)
            
            # Make the json file
            path = self.parm('output')
            makeFolder(path)
            txt = json.dumps(result, indent=4)
            f = open(path, 'w')
            f.write(txt)
            f.close()
            
            return path

class ExportCameras(Action):
    
    _defaultParms = {
        'input': '{current_file}',
        'output': '{version_root}/cameras.abc',
    }
    
    def run(self):

        sw = self.software()

        if sw:
            cams = sw.getCameras()
            cams = [c['full_path'] for c in cams]
            path = self.parm('output')
            makeFolder(path)
            sw.exportAbc(path, objects=cams)
            
            return path

class MakeSceneThumbnail(Action):
    
    _defaultParms = {
        'input': '{current_file}',
        'output': '{version_root}/thumbnail.jpg',
    }
    
    progressText = 'Making scene thumbnail...'
    
    def run(self):
        sw = self.software()
        if sw:
            path = self.parm('output')
            makeFolder(path)
            sw.makeSceneThumbnail(path)
            return path

class GetRenderFiles(Action):
    
    def run(self):
        files = self.parm('input')
        
        if not files:
            files = []
        
        for f in files:
            #f['path'] = f['full_path']
            f['part'] = f['pass']
        
        return files

class MakePublishInfoFile(Action):
    
    _defaultParms = {
        'input': '',
        'output': '{version_root}/info.json',
        'thumbnail': '{scene_thumbnail}',
        'version_type': 'publish',
        'part': '{step}',
        'level': '',
        'version': '{workfile_version}',
        'name': '{shot}_{step}_{workfile_version}',
        'description': '{engine_parm_description}',
        'entity_type': 'version',
        'asset': '',
        'files': [],
        'create_json_file': False,
        'only_include_existing_files': False
    }
    
    progressText = 'Creating a version to database...'
    
    def run(self):
        # Get parms
        name = self.parm('name')
        part = self.parm('part')
        thumbnail = self.parm('thumbnail')
        version = self.parm('version')
        infoPath = self.parm('output')
        folder = os.path.dirname(infoPath)
        files = self.parm('files')
        eType = self.parm('entity_type')
        comments = self.parm('description')
        versionType = self.parm('version_type')
        asset = self.parm('asset')
        level = self.parm('level')
        onlyIncludeExistingFiles = self.parm('only_include_existing_files')
        
        # Default parm value
        if not name:
            name = os.path.basename(folder)
        
        if not version:
            version = self.getVersion(folder)
        
        thumbnail = {
            'entity_type': 'image',
            'path': self.parsePath(thumbnail, root=folder),
        }
        
        #print 'files:',files
        
        files1 = []
        for f in files:
            if f:
                if type(f) == dict:
                    path = f.get('path')
                    
                    go = False
                    if onlyIncludeExistingFiles:
                        if os.path.exists(path):
                            go = True
                    else:
                        go = True
                    
                    if go:
                        f['path'] = self.parsePath(path, root=folder)
                        f['entity_type'] = 'published_file'
                        files1.append(f)
                
                elif type(f) in (str, unicode):
                    go = False
                    if onlyIncludeExistingFiles:
                        if os.path.exists(f):
                            go = True
                    else:
                        go = True
                    
                    if go:
                        ext = os.path.splitext(f)[-1]
                        ext = ext.replace('.', '')
                        d = {
                            'filetype': ext,
                            'path': self.parsePath(f, root=folder)
                        }
                        files1.append(d)
        
        # Get info
        info = plcr.getEnvContext(self.task())
        info = plcr.getTaskFromEnv(info)
        info['task'] = info.get('code')
        try:
            del info['code']
        except:
            pass
        
        info1 = {
            'entity_type': eType,
            'artist': self.user(),
            'description': comments,
            'files': files1,
            'version_type': versionType,
            'name': name,
            'part': part,
            'version': version,
            'thumbnail': thumbnail,
            'path': folder,
            'level': level
        }
        
        if asset:
            info1['asset'] = asset
        
        info.update(info1)
        
        # Make the json file
        if self.parm('create_json_file'):
            makeFolder(infoPath)
            txt = json.dumps(info, indent=4)
            f = open(infoPath, 'w')
            f.write(txt)
            f.close()
        
        # Create a version on CGTeamwork
        self.database().createVersion(self.project(), info)
        
        # Create a latest version
        if self.parm('create_latest_version'):
            latestInfo = info.copy()
            
            # Find existing version
            filterKeys = [
                'project', 'type', 'sequence', 'shot', 'asset_type',
                'asset', 'step', 'task', 'part', 'entity_type',
                'version_type', 'pipeline_type'
            ]
            filters = []
            for k in filterKeys:
                v = latestInfo.get(k)
                if v not in ('', None):
                    f = [k, '=', v]
                    filters.append(f)
            
            #print 'filters:'
            #print filters
            
            r = self.database().doesLatestVersionExist(self.project(), filters=filters)
            
            #print 'result:',r
            
            if r:
                # Update the version
                #print
                #print 'versionInfo:'
                #print latestInfo
                
                self.database().updateLatestVersionInfo(self.project(), r['id'], latestInfo)
            
            else:
                # Create a new one
                self.database().createLatestVersion(self.project(), latestInfo)
        
        # Make a version json file
        vnPath = ''
        
        return info

class CreateLatestVersion(Action):
    
    _defaultParms = {
        'path': '{version_root}',
        'thumbnail': '{scene_thumbnail}',
        'version_type': 'publish',
        'part': '{step}',
        'level': '',
        'version': 'latest',
        'name': '{shot}_{step}_{workfile_version}',
        'description': '{engine_parm_description}',
        'entity_type': 'version',
        'asset': '',
        'files': []
    }
    
    def run(self):
        # Get parms
        name = self.parm('name')
        part = self.parm('part')
        thumbnail = self.parm('thumbnail')
        version = self.parm('version')
        folder = self.parm('path')
        files = self.parm('files')
        eType = self.parm('entity_type')
        comments = self.parm('description')
        versionType = self.parm('version_type')
        asset = self.parm('asset')
        level = self.parm('level')
        
        #print
        #print 'entity_type:'
        #print eType
        
        # Default parm value
        if not name:
            name = os.path.basename(folder)
        
        if not version:
            version = 'latest'
        
        thumbnail = {
            'entity_type': 'image',
            'path': self.parsePath(thumbnail, root=folder),
        }
        
        #print 'files:',files
        
        files1 = []
        for f in files:
            if f:
                if type(f) == dict:
                    f['path'] = self.parsePath(f.get('path'), root=folder)
                    files1.append(f)
                
                elif type(f) in (str, unicode):
                    ext = os.path.splitext(f)[-1]
                    ext = ext.replace('.', '')
                    d = {
                        'filetype': ext,
                        'path': self.parsePath(f, root=folder)
                    }
                    files1.append(d)
        
        # Get info
        info = copy.deepcopy(self.task())
        info['task'] = info.get('code')
        try:
            del info['code']
        except:
            pass
        
        #print
        #print 'task:',
        #print info
        
        info1 = {
            'entity_type': eType,
            'artist': self.user(),
            'description': comments,
            'files': files1,
            'version_type': versionType,
            'name': name,
            'part': part,
            'version': version,
            'thumbnail': thumbnail,
            'path': folder,
            'level': level
        }
        
        if asset:
            info1['asset'] = asset
        
        #print
        #print 'version_info1:'
        #print info
        
        info.update(info1)
        
        #print
        #print 'version_info:'
        #print info
        
        # Find existing version
        filterKeys = [
            'project', 'type', 'sequence', 'shot', 'asset_type',
            'asset', 'step', 'task', 'part', #'entity_type',
            'version_type', 'pipeline_type', 'version'
        ]
        if level:
            filterKeys.append('level')
        
        filters = []
        for k in filterKeys:
            v = info.get(k)
            if v not in ('', None):
                f = [k, '=', v]
                filters.append(f)
        
        #print
        #print 'filters:'
        #print filters
        
        r = self.database().doesVersionExist(self.project(), filters=filters)
        
        #print 'result:',r
        
        if r:
            # Update the version
            #print
            #print 'versionInfo:'
            #print info
            
            self.database().updateVersionInfo(self.project(), r['id'], info)
        
        else:
            # Create a new one
            self.database().createVersion(self.project(), info)
        
        return info

class UpdateVersionInfo(Action):
    
    _defaultParms = {
        'project': '',
        'id': '',
        'data': {}
    }
    
    def run(self):
        project = self.parm('project')
        id_ = self.parm('id')
        data = self.parm('data')
        
        if not project:
            project = self.project()
        
        self.database().updateVersionInfo(project, id_, data)

class CreateVersionNote(Action):
    
    _defaultParms = {
        'input': {},
    }
    
    progressText = 'Creating a note to database...'
    
    def run(self):
        project = self.project()
        entity = self.task().get('type') + '_task'
        taskId = self.task().get('id')
        
        # Get note body
        info = self.parm('input')
        keys = [
            'type', 'sequence', 'shot', 'asset_type',
            'asset', 'step', 'task', 'part', 
            'version_type', 'version', 'description'
        ]
        
        text = u'%(artist)s 提交了一个新版本 %(version_type)s %(name)s'
        text += '<br>'
        text += u'%(description)s'
        text = text % info
        #lines = [title]
        #lines.append('')
        #for key in keys:
        #    v = info.get(key)
        #    if not v:
        #        v = ''
        #    line = '%s: %s' % (key, v)
        #    lines.append(line)
        
        #text = '<br>'.join(lines)
        
        self.database().createNote(project, entity, taskId, text)

class MakePreviewInfoFile(Action):
    
    _defaultParms = {
        'input': '',
        'output': '{version_root}/info.json',
        'thumbnail': '{scene_thumbnail}',
        'version_type': 'publish',
        'version': '{workfile_version}',
        'name': '{shot}_{step}_{workfile_version}',
        'description': '{engine_parm_description}',
        'entity_type': 'version',
        'asset': '',
        'file': []
    }
    
    def run(self):
        ''

class MakeWorkfileInfoFile(Action):
    
    _defaultParms = {
        'input': '{current_file}',
        'description': '{engine_parm_description}',
    }
    
    def run(self):
        # Get parms
        path = self.parm('input')
        
        infoPath = '%s.json' % path
        info = {
            'entity_type': 'workfile',
            'artist': self.user(),
            'description': self.parm('description'),
        }
        
        makeFolder(infoPath)
        txt = json.dumps(info, indent=4)
        f = open(infoPath, 'w')
        f.write(txt)
        f.close()
        
        return info

class SubmitToDatabase(Action):
    
    _defaultParms = {
        'input': '{VersionRoot}',
        'description': '{engine_parm_description}',
    }
    
    progressText = 'Submitting to database...'
    
    def run(self):
        path = self.parm('input')
        comments = self.parm('description')
        
        if type(path) == list:
            files = path
        else:
            files = [path]
        
        # Connect to CGTeamwork
        kwargs = {
            'project': self.task().get('project'),
            'type': self.task().get('type'),
            'taskId': self.task().get('id'),
            'files': files,
            'description': comments,
        }
        
        #print
        #print 'kwargs:'
        #print kwargs
        
        self.database().submit(**kwargs)

class GetUserTasks(Action):
    
    _defaultParms = {
        'user': '{artist}',
    }
    
    def run(self):
        user = self.parm('user')
        return self.database().getUserTasks(user)

class Print(Action):
    
    _defaultParms = {
        'input': '',
    }
    
    def run(self):
        i = self.parm('input')
        
        print 
        
        if type(i) in (tuple, list, dict):
            pprint.pprint(i)
        
        else:
            print i

class SaveToFile(Action):
    
    _defaultParms = {
        'input': '',
        'output': '',
    }
    
    def run(self):
        i = self.parm('input')
        t = pprint.pformat(i)
        path = self.parm('output')
        f = open(path, 'w')
        f.write(t)
        f.close()

############custom########################
class DelHistoryDirs(Action):
    
    _defaultParms = {
        "input": '',
        'output': '',
    }

    def run(self):
        directorPath = self.parm('input')
        if os.path.isdir(directorPath):
            creatTimeList = []
            baseName = []
            fileCounts = filterFiles.query(directorPath)
            if len(fileCounts) > 2:
                for ii in fileCounts:
                    creatTimeList.append(ii["created_times"][0])
                    baseName.append(ii["basename"])
            while len(creatTimeList) > 2:
                directorIndex = creatTimeList.index(min(creatTimeList))
                shutil.rmtree("%s/%s" %
                              (directorPath, baseName[directorIndex]))
                creatTimeList.remove(creatTimeList[directorIndex])
                baseName.remove(baseName[directorIndex])
            return True

class DelHistoryFiles(Action):
    
    _defaultParms = {
         "input": '',
         'output': '',
    }
    
    def run(self):
        filePath = self.parm('input')
        referenceLength = self.parm('output')
        if os.path.exists(filePath):
            if os.path.isdir(filePath):
                creatTimeList = []
                baseName = []
                fileCounts = filterFiles.query(filePath)
                if len(fileCounts) > 2:
                    for ii in fileCounts:
                        creatTimeList.append(ii["created_times"][0])
                        baseName.append(ii["filenames"][0])
                while len(creatTimeList) > 2*referenceLength:
                    directorIndex = creatTimeList.index(min(creatTimeList))
                    os.remove("%s/%s" % (filePath, baseName[directorIndex]))
                    creatTimeList.remove(creatTimeList[directorIndex])
                    baseName.remove(baseName[directorIndex])
                return True

class GetReferenceLength(Action):
    
    _defaultParms = {
         "input": '',
         'output': ''
    }
    
    def run(self):
        #'''2018.01.18 change '''
        result = []
        namespaceList = []
        referencePathList = []
        import maya.cmds as cmds
        allRN = cmds.ls(rf=True)

        if 'sharedReferenceNode' in allRN:
            allRN.remove('sharedReferenceNode')
        for rn in allRN:
            refPath = cmds.referenceQuery(rn, filename=True)
            namespace = cmds.referenceQuery(rn, namespace=True)
            if namespace[0] == ':':
                namespace = namespace[0:]
            info = {
                    'path': refPath
                    }
            result.append(info)
        for ii in result:
            referencePathList.append(result[0]["path"])
        return len(referencePathList)

class SelectExportObjects(Action):
    _defaultParms = {
        "input":'',
        "output":'',
    }
    def run(self):
        import maya.cmds as cmds
        allGpus = cmds.ls(type= "transform",long = True)
        newAllGups = []
        newAllGup_1 =[]
        for gup in  allGpus:
            if cmds.nodeType(gup)!='joint':
                gup = (gup.split('|'+gup.split('|')[-1]))[0].strip('|')

                newAllGups.append(gup)
        allGpusList = []
        for grp in newAllGups:
            if grp!='':
                grps = grp.split("|")
                for g in grps:
                    allGpusList.append(g)
            elif grp =="":
                pass
        for i in allGpusList: 
            if i not in newAllGup_1:
                newAllGup_1.append(i)
        objIteam = cmds.ls(dag = True,transforms = True,v = True)
        exportObject = [i for i in objIteam if i not in newAllGup_1]
        joint_obj = [
            i for i in exportObject if i is not cmds.nodeType(i) == 'joint']
        for i in joint_obj:
            for j in exportObject:
                if i == j:
                    exportObject.remove(j)
        return exportObject

class ExportAbc3(Action):
    
    _defaultParms = {
        "input": '',
        'single_frame': True,
        'start': 1,
        'end': 1,
    }
    def run(self):
        import maya.cmds as cmds
        import maya.mel as mel
        #start = self.parms('input')
        path = self.parms('output')
        
        TopLevelName = cmds.ls(assemblies=1) 
        Default = ['persp', 'top', 'front', 'side']
        StandTopLevelName = [i for i in TopLevelName if i not in Default]
        for i in StandTopLevelName:
            if cmds.nodeType(i) == 'joint':
                StandTopLevelName.remove(i)

        listLongName = []
        for i in StandTopLevelName:
            exportName = '-root ' + '|' + i
            listLongName.append(exportName)

        cmd = 'AbcExport -j "-frameRange %s %s -uvWrite -ro -writeFaceSets -writeVisibility -dataFormat ogawa' % (
            1, 10)
        for i in listLongName:
            cmd = cmd + " " + i
        print cmd
        cmd = cmd + ' -file %s";' % (path)
        print cmd
        #mel.eval(cmd)
class GetColorSpace(Action):
    _defaultParms = {
        "input":'',
        "output":'',
    }

    def run(self):
        import pymel.core as pm
        fileList = pm.ls(type = "file")
        colorSpaceList = []
        for ii in fileList:
            node = pm.PyNode(ii)
            colorSpaceList.append(node.getAttr("colorSpace"))
        return colorSpaceList

class SetColorSpace(Action):
    _defaultParms = {
        'input':'',
        'output': '',

    }
    def run(self):
        import pymel.core as pm
        fileList = pm.ls(type = "file")
        colorSpaceList = self.parm('input')
        for ii in xrange(len(fileList)):
            node = pm.PyNode(fileList[ii])
            node.setAttr("colorSpace",colorSpaceList[ii])

        return True

# class CreateHistoryDirs(Action):
#     _defaultParms = {
#         'input': '',
#         'output'： ''
#     }
#     def run(self):
#         path = self.parm('input')
#         if not os.path.exists(path):
#             os.makedirs(path)
#         return True


        
        

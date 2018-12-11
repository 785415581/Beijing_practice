#!/usr/bin/env python
# -*- coding:utf-8 -*-
import os,sys
import time
import shutil
# dirname, filename = os.path.split(os.path.abspath(sys.argv[0]))
# print "1", dirname#运行脚本目录
# print "2", filename#运行脚本文件名
# print "3",sys.path[0]#运行脚本目录
# print "4",sys.argv[0]#当前脚本目录
# print "5",os.getcwd()#运行脚本目录
# print "7",os.path.dirname(__file__)#当前脚本所在的目录
# print "6",__file__
# print "7",os.path.realpath(__file__) #Return the absolute version of a path.
# print "8",os.path.abspath(__file__)
# print "9",os.path.dirname(os.path.realpath(__file__))
# print "10",os.path.dirname(os.path.abspath(__file__))
# path = os.path.dirname(__file__)
# filePath = os.path.join(path,'123.py')
# print filePath.replace('/','\\')
# import subprocess
# child = subprocess.Popen(['ping','-c','4','asd'])
# child.wait()
# baseFileName = os.path.basename(__file__)
# print 'baseFileName:',baseFileName
# fileDirPath = os.path.dirname(__file__)
# print 'fileDirPath:',fileDirPath
# historyDir = os.path.join(fileDirPath, 'history')
# print 'historyDir:',historyDir
# fileNowTime = time.strftime("%Y-%m-%d-%H-%M-%S")
# print 'fileNowTime:',fileNowTime
# fileNowTimeDir = os.path.join(historyDir, fileNowTime)
# print 'fileNowTimeDir:',fileNowTimeDir
# os.makedirs(fileNowTimeDir)
# newFilePath = os.path.join(fileNowTimeDir, baseFileName)
# print "newFilePath:",newFilePath
# shutil.copy(__file__, newFilePath)#复制文件传入两个文件路径，第一个是原本的文件路径，第二个是要copy的路径

mtlFileDir = "G:/GODTV/Shot/Ep01/Debug/Sc_001/amiMtlFile"

os.makedirs(mtlFileDir)
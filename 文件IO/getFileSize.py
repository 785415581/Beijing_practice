#coding=utf-8
import os

def getImgSize(path):
    try:
        filePath = unicode(path, 'utf8')
        kb = float(os.path.getsize(filePath))/1024

        '''文件大小，不需要转换格式下面可以注释'''

        if kb >= 1024:
          M = kb / 1024
          if M >= 1024:
            G = M / 1024
            return "%fG" % (G)
          else:
            return "%fM" % (M)
        else:
          return "%fkb" % (kb)
    except:
        print u'传入格式有误！'

path = 'E:\\BaiduYunDownload\\爆炸2K高清实拍视频素材合辑\\10. Muzzle Flash\\muzzle_flash_front_04.png'
print getImgSize(path)

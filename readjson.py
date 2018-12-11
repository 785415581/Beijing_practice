import json
a = {'a':'b'}
json_filename = 'G:/Beijing/test.json'
txt = json.dumps(a)
f.open(json_filename,'w')
f.write(txt)
f.close()

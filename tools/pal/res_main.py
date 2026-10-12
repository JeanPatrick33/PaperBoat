import re,sys
p=sys.argv[1]; choices=eval(sys.argv[2])  # dict idx->'o'|'t'|str
L=open(p).read().split('\n')
out=[];i=0;n=0
while i<len(L):
    if L[i].startswith('<<<<<<<'):
        n+=1;o=[];b=[];t=[];i+=1
        while not L[i].startswith('|||||||'): o.append(L[i]);i+=1
        i+=1
        while not L[i].startswith('======='): b.append(L[i]);i+=1
        i+=1
        while not L[i].startswith('>>>>>>>'): t.append(L[i]);i+=1
        i+=1
        c=choices.get(n,'t')
        if c=='o': out+=o
        elif c=='t': out+=t
        elif c=='b': out+=b
        else: out+=c.split('\n')
    else: out.append(L[i]);i+=1
open(p,'w').write('\n'.join(out))
print(n,'hunks')

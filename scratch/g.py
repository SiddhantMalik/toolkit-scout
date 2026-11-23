import sys,re
i,pat=sys.argv[1],sys.argv[2]; w=int(sys.argv[3]) if len(sys.argv)>3 else 200; n=int(sys.argv[4]) if len(sys.argv)>4 else 6
import glob
fs=[f'/home/claude/toolkit-scout/data/evidence/{i}.txt']+sorted(glob.glob(f'/home/claude/toolkit-scout/data/evidence_extra/{i}_*.txt'))
c=0
for f in fs:
  t=open(f).read()
  for m in re.finditer(pat,t,re.I):
    print('['+f.split('/')[-1]+']','...'+t[max(0,m.start()-w):m.end()+w].replace('\n',' ')+'...\n'); c+=1
    if c>=n: sys.exit()

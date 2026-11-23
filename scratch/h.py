import sys,re,subprocess
u,out=sys.argv[1],sys.argv[2]
t=subprocess.run(['curl','-sL','-m','40','-A','Mozilla/5.0','--compressed',u],capture_output=True,).stdout.decode('utf-8','ignore')
t=re.sub(r'<script.*?</script>|<style.*?</style>|<nav.*?</nav>','',t,flags=re.S); t=re.sub(r'<[^>]+>',' ',t); t=re.sub(r'\s+',' ',t)
open(out,'w').write(t); print(len(t))

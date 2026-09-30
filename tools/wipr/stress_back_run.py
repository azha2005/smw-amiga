import subprocess,os,sys,re
def run(body, name='zz_t', root=os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')).replace(os.sep, '/')):
    p=root+'/tools/snesorc/%s.orc'%name
    open(p,'w').write(body)
    r=subprocess.run([root+'/work/snesorc.exe','--script',p,'--out',os.environ.get('TEMP', '/tmp')+'/stress_back_t.txt'],capture_output=True,text=True,cwd=root)
    err=[l for l in r.stderr.splitlines() if l.strip()]
    return r.returncode==0, err

# WIP (ola 1, R6): busqueda en profundidad del camino de vuelta a la izquierda
# para stress_back.orc. Uso: python tools/wipr/stress_back_dfs.py <prefijo.orc> <x inicial hex> <x final hex> <salida.orc>
# stress_back_parcial.orc es lo mejor que alcanzo (vuelta de $1240 a $0BC0). Necesita work/snesorc.exe
# y los .orc en LF (AGENTS P82).
import sys,os,time
from stress_back_run import run
CHK="assert $0071==00\nassert $0100==14\nassert $0019==00\n"
def step_opts(T,d,run_btn='LEFT+Y',jbtn='LEFT+Y+B',dirop='<='):
    # T = target after step (dirop <=) ; yields text blocks
    yield "until w$0094%s%04X max 150 %s\n%s"%(dirop,T,run_btn,CHK)
    sgn=-1 if dirop=='<=' else 1
    for o in (0,4,8,12):
        for n in (8,16,28):
            yield ("until w$0094%s%04X max 150 %s\n%d %s\nuntil w$0094%s%04X max 150 %s\n%s"
                   %(dirop,T-sgn*(d-o) if False else T+(d-o)*(1 if dirop=='<=' else -1),run_btn,n,jbtn,dirop,T,run_btn,CHK))
tries=0
def dfs(prefix,T,end,d,dirop,logf,depth_left):
    global tries
    if (T<=end if dirop=='<=' else T>=end): return prefix
    nxt=T-d if dirop=='<=' else T+d
    for blk in step_opts(nxt,d,dirop=dirop):
        tries+=1
        ok,err=run(prefix+blk,name='zz_s')
        if ok:
            print('ok',hex(nxt),tries,flush=True)
            open(logf,'w').write(prefix+blk)
            r=dfs(prefix+blk,nxt,end,d,dirop,logf,depth_left)
            if r: return r
            # else try next option
    return None
if __name__=='__main__':
    prefix=open(sys.argv[1]).read(); T=int(sys.argv[2],16); end=int(sys.argv[3],16)
    r=dfs(prefix,T,end,0x10,'<=',sys.argv[4],0)
    print('DONE' if r else 'FAIL',tries)

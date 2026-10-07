#!/usr/bin/env python3
"""Construye perfil privado, ejecuta WinUAE bajo candado y conserva evidencia D1.
Solo requiere builds ya hechos. Todas las salidas quedan en la carpeta work.
"""
import argparse,hashlib,json,subprocess,sys,time
from pathlib import Path
from d1_export import export
from d1_count_v2 import decode,metrics
ROOT=Path(__file__).resolve().parent.parent
LOCK=ROOT.parent/'winuae_lock.ps1'
WINUAE=Path('C:/Program Files/WinUAE/winuae64.exe')
ROM=Path('C:/Users/JC/Downloads/amivideo/kick12.rom')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('folder',type=Path);ap.add_argument('--ops',required=True,type=int);ap.add_argument('--oracle',required=True,type=Path);ap.add_argument('--replay',required=True,type=Path);ap.add_argument('--flags',required=True);ap.add_argument('--timeout',type=int,default=420);a=ap.parse_args()
    folder=a.folder.resolve()
    if not folder.is_relative_to(ROOT/'work'):raise ValueError('perfil y artefactos deben quedar en work')
    config=(ROOT/'a500.uae').read_text().replace('kickstart_rom_file=','kickstart_rom_file='+ROM.as_posix()).replace('floppy0=','floppy0='+(folder/'game.adf').as_posix())
    config+='\nuse_gui=no\ngfx_framerate=1\nwin32.active_not_captured_pause=false\nwin32.inactive_pause=false\nwin32.iconified_pause=false\n'
    (folder/'run.uae').write_text(config)
    for name in ('pid.txt','close.flag'):(folder/name).unlink(missing_ok=True)
    process=subprocess.Popen(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(LOCK),str(ROOT/'tools/d1_run.ps1'),'-Folder',str(folder),'-Limit',str(a.timeout)],cwd=ROOT,creationflags=subprocess.CREATE_NO_WINDOW)
    try:
        # Timeout empieza cuando el candado concede nuestro PID, no durante su cola.
        while not (folder/'pid.txt').exists():
            if process.poll() is not None:raise RuntimeError('launcher termino antes del PID')
            time.sleep(1)
        pid=int((folder/'pid.txt').read_text());deadline=time.monotonic()+a.timeout
        while True:
            try:blob,info=export(pid,folder/'game.bin',folder/'game.lst');break
            except ValueError:
                if time.monotonic()>deadline or process.poll() is not None:raise
                time.sleep(5)
        rows,events,metadata=decode(blob,a.ops)
        (folder/'raw.bin').write_bytes(blob);(folder/'raw.export.json').write_text(json.dumps(info,indent=2))
        subprocess.run([sys.executable,str(ROOT/'tools/d1_count_v2.py'),str(folder/'raw.bin'),'--expected-ops',str(a.ops),'--out',str(folder/'trace.json')],check=True)
        manifest=dict(commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),flags=a.flags,winuae_version=subprocess.check_output(['powershell.exe','-NoProfile','-Command','(Get-Item "'+str(WINUAE)+'").VersionInfo.FileVersion'],text=True).strip(),
                      hashes={str(p):sha(p) for p in [WINUAE,ROM,folder/'run.uae',folder/'game.bin',folder/'game.lst',folder/'game.adf',ROOT/'work/yi1_s.dat',a.oracle,a.replay,folder/'raw.bin']},metadata=metadata)
        (folder/'manifest.json').write_text(json.dumps(manifest,indent=2))
    finally:
        (folder/'close.flag').write_text('1')
        try:process.wait(timeout=12)
        except subprocess.TimeoutExpired:raise RuntimeError('launcher no cerro su WinUAE; inspeccionar PID propio')
if __name__=='__main__':main()

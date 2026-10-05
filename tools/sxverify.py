#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SX/SX2: ADF de ida/vuelta, capturas exactas y comparación antes/después.

    python tools/sxverify.py --build
    powershell -File work/sxverify/capture_baseline.ps1
    powershell -File work/sxverify/capture_current.ps1
    python tools/sxverify.py --compare

Las dos capturas pueden ejecutarse a la vez: cada una usa su copia privada
de shot.ps1 y el candado compartido de WinUAE (máximo dos instancias aquí).
Assets, binarios y capturas quedan en work/ (R9).
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "work" / "sxverify"
POSITIONS = (500, 1000, 1700, 2500, 3500, 4500)
RETURN = 4864
BASE = "68e2d1e"


def run(args):
    p = subprocess.run([str(a) for a in args], cwd=ROOT,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out = p.stdout.decode("utf-8", "replace")
    if p.returncode:
        raise RuntimeError("%s\n%s" % (" ".join(map(str, args)), out))
    return out


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def ps_quote(value):
    return "'" + str(value).replace("'", "''") + "'"


def build(a):
    OUT.mkdir(parents=True, exist_ok=True)
    vasm = a.vasm or shutil.which("vasmm68k_mot") or shutil.which("vasmm68k_mot.exe")
    if not vasm:
        vasm = r"C:\Users\JC\vbcc\bin\vasmm68k_mot.exe"
    source = OUT / "scroll-baseline.s"
    # Bytes originales del commit, sin pasar por la codificación de PowerShell.
    source.write_bytes(subprocess.check_output(["git", "show", BASE + ":player/scroll.s"], cwd=ROOT))
    boot = OUT / "boot.bin"
    run([vasm, "-quiet", "-Fbin", "-m68000", "-no-opt", "-I", "player",
         "-o", boot, "player/boot.s"])
    data = ROOT / "work" / "yi1_s.dat"
    render_data = ROOT / "work" / "yi1_d.dat"
    manifest = {"baseline": BASE, "current_commit": run(["git", "rev-parse", "HEAD"]).strip(),
                "current_scroll_sha256": sha(ROOT / "player" / "scroll.s"),
                "baseline_scroll_sha256": sha(source), "data_sha256": sha(data),
                "render_data_sha256": sha(render_data), "return": RETURN, "jobs": []}
    for direction in ("ida", "vuelta"):
        for x in POSITIONS:
            s0 = max(0, x - 512) if direction == "ida" else 0
            distance = x - s0 if direction == "ida" else 2 * RETURN - x
            # 50 Hz, 2 px/frame. Margen de arranque + carga host; última foto
            # 10 segundos después de la primera para comprobar STOPX estable.
            wait = int(math.ceil((70 + distance / 100) / 10) * 10)
            for variant in ("baseline", "current"):
                name = "%s_%s_%d" % (variant, direction, x)
                stage = OUT / (name + ".bin")
                adf = OUT / (name + ".adf")
                defs = ["-DSTOPX=%d" % x, "-DS0=%d" % s0, "-DSPEED=2"]
                if direction == "vuelta":
                    defs.append("-DRETURN=%d" % RETURN)
                src = source if variant == "baseline" else ROOT / "player" / "scroll.s"
                log = run([vasm, "-quiet", "-Fbin", "-m68000", "-no-opt", "-I", "player"]
                          + defs + ["-o", stage, src])
                log += run([sys.executable, "tools/mkadf.py", "--boot", boot, "--stage2", stage,
                            "--data", data, "--out", adf])
                (OUT / (name + "_build.log")).write_text(log, encoding="utf-8")
                manifest["jobs"].append({"name": name, "variant": variant, "direction": direction,
                                         "s": x, "s0": s0, "wait": wait, "defines": defs,
                                         "adf_sha256": sha(adf)})
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    generate_workers(manifest, a.lock)
    print("24 ADF construidos; capturas: work/sxverify/capture_{baseline,current}.ps1")


def generate_workers(manifest, lock):
    original = (ROOT / "tools" / "shot.ps1").read_text(encoding="utf-8-sig")
    hidden = "-ArgumentList @('-f', \"`\"$cfg`\"\") -PassThru"
    if hidden not in original:
        raise RuntimeError("shot.ps1 cambió: revisar el punto de lanzamiento")
    original = original.replace(hidden, hidden + " -WindowStyle Hidden")
    # Un proceso iniciado Hidden no da MainWindowHandle y PrintWindow de
    # una ventana sin dibujar devuelve negro. Encontrarla por PID y habilitar
    # su dibujo al fondo, sin activarla (validado con el banco G0).
    window_helpers = '''public static class A5Shot {
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int cmd);
    [DllImport("user32.dll")] public static extern bool SetWindowPos(IntPtr h, IntPtr after, int x, int y, int w, int ht, uint flags);
    [DllImport("user32.dll")] public static extern bool PostMessage(IntPtr h, uint msg, IntPtr w, IntPtr l);
    public delegate bool EnumProc(IntPtr h, IntPtr arg);
    [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc proc, IntPtr arg);
    [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
    public static IntPtr WindowFor(int wanted) {
        IntPtr found = IntPtr.Zero;
        EnumWindows((h, a) => { uint pid; GetWindowThreadProcessId(h, out pid); RECT r;
            GetWindowRect(h, out r);
            if (pid == wanted && r.R-r.L >= 640 && r.B-r.T >= 512) { found=h; return false; }
            return true; }, IntPtr.Zero);
        return found;
    }
'''
    original = original.replace("public static class A5Shot {", window_helpers)
    original = original.replace("$h = $Process.MainWindowHandle", "$h = [A5Shot]::WindowFor($Process.Id)")
    original = original.replace('Log "FALLO: WinUAE no tiene ventana"',
                                'Log "FALLO: WinUAE no tiene ventana PID=$($Process.Id) HasExited=$($Process.HasExited)"; if ($Process.HasExited) { Log "ExitCode=$($Process.ExitCode)" }')
    original = original.replace("    $bmp = New-Object System.Drawing.Bitmap $w, $ht",
                                '    Log "PrintWindow PID=$($Process.Id) HWND=$h"\n    $bmp = New-Object System.Drawing.Bitmap $w, $ht')
    original = original.replace('Log "pid $($proc.Id)"', '''Log "pid $($proc.Id)"
for ($wi = 0; $wi -lt 40; $wi++) {
    $renderHwnd = [A5Shot]::WindowFor($proc.Id)
    if ($renderHwnd -ne [IntPtr]::Zero) {
        [A5Shot]::ShowWindow($renderHwnd, 4) | Out-Null
        [A5Shot]::SetWindowPos($renderHwnd, [IntPtr]::new(1), 0, 0, 0, 0, 0x13) | Out-Null
        Log "Render PID=$($proc.Id) HWND=$renderHwnd"
        break
    }
    Start-Sleep -Milliseconds 250
}''')
    original = original.replace('    $proc.CloseMainWindow() | Out-Null', '''    $closeHwnd = [A5Shot]::WindowFor($proc.Id)
    Log "Cerrar PID=$($proc.Id) HWND=$closeHwnd"
    if ($closeHwnd -ne [IntPtr]::Zero) {
        [A5Shot]::PostMessage($closeHwnd, 0x10, [IntPtr]::Zero, [IntPtr]::Zero) | Out-Null
    }''')
    original = original.replace('Log "fin"', 'Log "fin PID=$($proc.Id) HasExited=$($proc.HasExited) ExitCode=$($proc.ExitCode)"')
    loop = "for ($t = $Every; $t -le $Wait; $t += $Every) {"
    if loop not in original:
        raise RuntimeError("shot.ps1 cambió: revisar el bucle de captura")
    # Dos capturas, con la misma instancia, a t=Wait-10 y t=Wait.
    original = original.replace(loop, "foreach ($t in @(($Wait - 10), $Wait)) {")
    for variant in ("baseline", "current"):
        slot = OUT / "slots" / variant
        (slot / "tools").mkdir(parents=True, exist_ok=True)
        (slot / "work").mkdir(exist_ok=True)
        shot = slot / "tools" / "shot.ps1"
        shot.write_text(original, encoding="utf-8-sig")
        script = ["$ErrorActionPreference = 'Stop'", "$ProgressPreference = 'SilentlyContinue'",
                  "$rootOut = " + ps_quote(OUT), "$shot = " + ps_quote(shot),
                  "$lock = " + ps_quote(lock), "$jobs = Get-Content -LiteralPath (Join-Path $rootOut 'manifest.json') -Raw | ConvertFrom-Json",
                  "foreach ($j in $jobs.jobs) {", "    if ($j.variant -ne " + ps_quote(variant) + ") { continue }",
                  "    $name = $j.name", "    $adf = Join-Path $rootOut ($name + '.adf')",
                  "    $out = Join-Path $rootOut ($name + '.png')",
                  "    $first = Join-Path $rootOut ('{0}_{1:d3}s.png' -f $name, ([int]$j.wait - 10))",
                  "    $last = Join-Path $rootOut ('{0}_{1:d3}s.png' -f $name, [int]$j.wait)",
                  "    $record = Join-Path $rootOut ($name + '_capture.json')",
                  "    if ((Test-Path -LiteralPath $record) -and (Test-Path -LiteralPath $out) -and (Test-Path -LiteralPath $first) -and (Test-Path -LiteralPath $last)) {",
                  "        $old = Get-Content -LiteralPath $record -Raw | ConvertFrom-Json",
                  "        if ($old.adf_sha256 -eq $j.adf_sha256 -and $old.wait -eq $j.wait) { Write-Host ('YA CAPTURADO ' + $name); continue }",
                  "    }",
                  "    foreach ($p in @($first, $last, $out)) { if (Test-Path -LiteralPath $p) { Remove-Item -LiteralPath $p -Force } }",
                  "    $start = Get-Date", "    Write-Host ('INICIO {0} {1:o} espera={2}s' -f $name, $start, $j.wait)",
                  "    & $lock $shot -Exact -Adf $adf -Out $out -Wait ([int]$j.wait) -Every 10",
                  "    if (-not (Test-Path -LiteralPath $first) -or -not (Test-Path -LiteralPath $last)) { throw ('faltan capturas: ' + $name) }",
                  "    Copy-Item -LiteralPath $last -Destination $out -Force",
                  "    $slotWork = Join-Path (Split-Path -Parent (Split-Path -Parent $shot)) 'work'",
                  "    Copy-Item -LiteralPath (Join-Path $slotWork 'shot.uae') -Destination (Join-Path $rootOut ($name + '.uae')) -Force",
                  "    Copy-Item -LiteralPath (Join-Path $slotWork 'shot.log') -Destination (Join-Path $rootOut ($name + '_shot.log')) -Force",
                  "    $pendingRecord = $record + '.tmp'",
                  "    @{name=$name; started=$start.ToString('o'); finished=(Get-Date).ToString('o'); wait=[int]$j.wait; adf_sha256=(Get-FileHash -LiteralPath $adf -Algorithm SHA256).Hash.ToLower()} | ConvertTo-Json | Set-Content -LiteralPath $pendingRecord -Encoding UTF8",
                  "    Move-Item -LiteralPath $pendingRecord -Destination $record -Force",
                  "    Write-Host ('FIN ' + $name)", "}"]
        (OUT / ("capture_" + variant + ".ps1")).write_text("\n".join(script) + "\n", encoding="utf-8-sig")


def compare(a):
    import numpy as np
    from PIL import Image
    import scroll_check
    import render_d

    manifest = json.loads((OUT / "manifest.json").read_text(encoding="utf-8"))
    if sha(ROOT / "work" / "yi1_d.dat") != manifest["render_data_sha256"]:
        raise RuntimeError("yi1_d.dat cambió desde el build")
    scroll_check.W = 256
    d = render_d.load(str(ROOT / "work" / "yi1_d.dat"))
    idx = render_d.l1_index(d)
    rows = []
    sampled = {}
    fail = False
    for job in manifest["jobs"]:
        name = job["name"]
        capture_record = OUT / (name + "_capture.json")
        deadline = time.monotonic() + a.wait
        while not capture_record.exists() and time.monotonic() < deadline:
            time.sleep(1)
        shot = OUT / (name + ".png")
        cfg = (OUT / (name + ".uae")).read_text(encoding="ascii")
        for setting in ("cpu_speed=real", "cycle_exact=true", "immediate_blits=false", "ntsc=false"):
            if setting not in cfg.splitlines():
                raise RuntimeError("%s: falta configuración %s" % (name, setting))
        metadata = json.loads(capture_record.read_text(encoding="utf-8-sig"))
        if metadata["adf_sha256"] != job["adf_sha256"]:
            raise RuntimeError(name + ": ADF distinto del manifest")
        log = run([sys.executable, "tools/scroll_check.py", "--shot", shot, "--s", job["s"],
                   "--sc", "2", "--mid", "--png", OUT / (name + "_pc.png")])
        (OUT / (name + "_pc.log")).write_text(log, encoding="utf-8")
        origin = re.search(r"origen de la captura \(([\d.]+), ([\d.]+)\)", log)
        bad = re.search(r"(\d+) px distintos de (\d+)", log)
        unexplained = re.search(r"fallos que no se explican por un vecino: (\d+)", log)
        if not (origin and bad and unexplained):
            raise RuntimeError(name + ": salida desconocida de scroll_check")
        x0, y0 = map(float, origin.groups())
        xs = (x0 + (np.arange(256) + .5) * 2).astype(int)
        ys = (y0 + (np.arange(224) + .5) * 2).astype(int)
        got = np.asarray(Image.open(shot).convert("RGB"))[ys][:, xs].astype(int)
        first = OUT / ("%s_%03ds.png" % (name, job["wait"] - 10))
        prior = np.asarray(Image.open(first).convert("RGB"))[ys][:, xs].astype(int)
        stable = int((np.abs(got - prior).max(axis=2) > 8).sum())
        expected = scroll_check.expect(d, idx, job["s"], True)
        # Se exige encuadre correcto y una cámara detenida. Comparar también
        # s±2 detecta el desfase de un frame sin aceptar un recorte desplazado.
        error = int((np.abs(got - expected).max(axis=2) > 8).sum())
        neighbors = {}
        for ds in (-16, -2, 2, 16):
            target = job["s"] + ds
            en = scroll_check.expect(d, idx, target, True)
            neighbors[str(ds)] = int((np.abs(got - en).max(axis=2) > 8).sum())
        position_ok = error < min(neighbors.values()) and error < 256 * 224 * .02
        if stable or not position_ok:
            fail = True
        row = {**job, "origin": [x0, y0], "bad": error,
               "unexplained": int(unexplained.group(1)), "stable_bad": stable,
               "position_ok": bool(position_ok), "neighbor_bad": neighbors}
        rows.append(row)
        sampled[(job["variant"], job["direction"], job["s"])] = got
        print("%s: PC=%d vecinos=%d estable=%d STOPX=%s" %
              (name, error, row["unexplained"], stable, position_ok), flush=True)
    pairs = []
    by_key = {(r["variant"], r["direction"], r["s"]): r for r in rows}
    fidelity_fail = False
    for direction in ("ida", "vuelta"):
        for x in POSITIONS:
            before = sampled[("baseline", direction, x)]
            after = sampled[("current", direction, x)]
            changed = (np.abs(after - before).max(axis=2) > 8)
            image = np.vstack([before, after, np.where(changed[..., None], [255, 0, 255], after // 2 + 64)])
            path = OUT / ("pair_%s_%d.png" % (direction, x))
            Image.fromarray(image.astype(np.uint8)).resize((768, 2016), Image.Resampling.NEAREST).save(path)
            old_errors = by_key[("baseline", direction, x)]["unexplained"]
            new_errors = by_key[("current", direction, x)]["unexplained"]
            regressed = new_errors > old_errors
            fidelity_fail |= regressed
            pairs.append({"direction": direction, "s": x, "different": int(changed.sum()),
                          "baseline_unexplained": old_errors, "current_unexplained": new_errors,
                          "regressed": regressed})
    report = {"manifest": manifest, "rows": rows, "pairs": pairs, "capture_gate_ok": not fail,
              "fidelity_gate_ok": not fidelity_fail}
    (OUT / "results.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("Puerta de captura (STOPX + estabilidad):", "FALLA" if fail else "OK")
    print("Puerta de fidelidad (sin más fallos no explicados):", "FALLA" if fidelity_fail else "OK")
    return 1 if fail or fidelity_fail else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--compare", action="store_true")
    ap.add_argument("--wait", type=int, default=0,
                    help="al comparar, esperar hasta N segundos cada captura que falta")
    ap.add_argument("--vasm", help="vasmm68k_mot.exe")
    ap.add_argument("--lock", default=str(ROOT.parent / "winuae_lock.ps1"))
    a = ap.parse_args()
    if not (a.build or a.compare):
        ap.error("elegir --build o --compare")
    if a.build:
        build(a)
    return compare(a) if a.compare else 0


if __name__ == "__main__":
    sys.exit(main())

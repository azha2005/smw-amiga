#!/usr/bin/env python3
"""D1 v2: VBL continuos y eventos de ticks completos, incluso varios por intervalo.
El CSV singular de d1_count.py conserva su rechazo de mas de un tick/VBL.
"""
import argparse,csv,json,struct
from pathlib import Path
from d1_count import timing
CAP=4600;ROW=20;EVENTS=32+CAP*ROW

def decode(blob,ops):
    if blob[:4]!=b'D1TR' or len(blob)<EVENTS:raise ValueError('D1TR v2 incompleto')
    ver,width,cap,n,done,overflow,tpf,ne=struct.unpack_from('>HHIIHHHH',blob,4)
    calibration=struct.unpack_from('>I',blob,24)[0]
    if (ver,width,cap,done,overflow)!=(2,20,CAP,1,0):raise ValueError('version/estado/overflow invalido')
    if len(blob)!=EVENTS+ne*12 or not 2<=n<=cap or ne!=ops-1:raise ValueError('longitud/eventos no coincide con replay')
    events=[]
    for i in range(ne):
        logical_id,duration,end=struct.unpack_from('>III',blob,EVENTS+i*12)
        if logical_id!=i+1:raise ValueError('ID evento discontinuo')
        if i and not 0<((events[-1]['end_cia_down']-end)&0xffffffff)<0x80000000:raise ValueError('reloj evento no monotono')
        if duration<calibration:raise ValueError('duracion evento menor que calibracion')
        events.append(dict(logical_id=logical_id,end_cia_down=end,duration_cia_ticks=duration-calibration))
    rows=[]
    for i in range(n):
        vbl,logic,shown,photo,tick,end=struct.unpack_from('>IHHIII',blob,32+i*ROW)
        if vbl!=i or shown>logic:raise ValueError('VBL/foto invalida')
        prev=rows[-1] if i else None; dl=logic-prev['logic_frame'] if i else 0;ds=shown-prev['shown_frame'] if i else 0
        if dl<0 or ds<0 or logic>ne:raise ValueError('retroceso de contador')
        ev=events[(prev['logic_frame'] if i else 0):logic]
        if len(ev)!=dl:raise ValueError('intervalo/eventos incompleto')
        if i:
            dt=(prev['capture_cia_down']-end)&0xffffffff
            if not 0<dt<2*tpf:raise ValueError('VBL omitido o reloj discontinuo')
            for e in ev:
                relative=(prev['capture_cia_down']-e['end_cia_down'])&0xffffffff
                if relative>dt:raise ValueError('evento fuera de su intervalo VBL')
        rows.append(dict(vbl=vbl,logic_frame=logic,shown_frame=shown,capture_cia_down=end,
                         photo_ticks=photo-calibration if ds>0 else None,tick_events=ev))
    if (rows[0]['logic_frame'],rows[0]['shown_frame'])!=(0,0) or (rows[-1]['logic_frame'],rows[-1]['shown_frame'])!=(ne,ne):raise ValueError('origen/final no coincide')
    final=next(i for i,r in enumerate(rows) if r['logic_frame']==ne)
    return rows,events,dict(version=ver,replay_ops=ops,initial_level_operations=1,cia_ticks_per_frame=tpf,timestamp_read_calibration=calibration,
                            raw_vbl_rows=n,active_first_vbl=1,active_last_vbl=final,drain_vbl=n-1-final)

def metrics(rows):
    om=[];ages=[];photos=[];durations=[];intervals=[];streak=longest=skipped=0
    for prev,r in zip(rows,rows[1:]):
        ds=r['shown_frame']-prev['shown_frame'];miss=int(ds==0);om.append(miss);streak=streak+1 if miss else 0;longest=max(streak,longest)
        skipped+=max(0,ds-1);ages.append(r['logic_frame']-r['shown_frame']);intervals.append(len(r['tick_events']))
        if ds:photos.append(r['photo_ticks'])
        durations.extend(e['duration_cia_ticks'] for e in r['tick_events'])
    n=len(om);width=min(250,n);worst=sum(om[:width]);start=rows[1]['vbl'];rolling=worst
    for i in range(width,n):
        rolling+=om[i]-om[i-width]
        if rolling>worst:worst,start=rolling,rows[i-width+2]['vbl']
    return dict(vbl_total=n,omitted=sum(om),omitted_percent=100*sum(om)/n,max_streak=longest,worst_window=dict(width=width,omitted=worst,first_vbl=start),
                photo_age_logic_ticks=timing(ages),intervals_without_completed_tick=intervals.count(0),intervals_with_multiple_completed_ticks=sum(v>1 for v in intervals),
                maximum_completed_ticks_in_interval=max(intervals),completed_tick_events=len(durations),net_uncompleted_ticks_at_last_vbl=n-len(durations),
                skipped_logical_photos_between_presentations=skipped,integrated_photo_cia_ticks=timing(photos),logic_cia_ticks=timing(durations),
                minimum_numeric_thresholds_met=n>=250 and sum(om)*1000<=n and longest<=1 and worst<=1)

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('raw',type=Path);ap.add_argument('--expected-ops',required=True,type=int);ap.add_argument('--out',required=True,type=Path);a=ap.parse_args()
    rows,events,meta=decode(a.raw.read_bytes(),a.expected_ops);active=rows[:meta['active_last_vbl']+1]
    result=dict(protocol='d1-vbl-events-v2',metadata=meta,active=metrics(active),full_including_deliberate_end=metrics(rows),rows=rows)
    a.out.write_text(json.dumps(result,indent=2))
    with a.out.with_name('ticks.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['logical_id','end_cia_down','duration_cia_ticks']);w.writeheader();w.writerows(events)
    # CSV v1 solo cuando cada intervalo admite un evento. Nunca colapsar varios.
    if all(len(r['tick_events'])<=1 for r in active):
        with a.out.with_name('vbl.csv').open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=['vbl','logic_frame','shown_frame','photo_ticks','tick_ticks']);w.writeheader()
            for r in active:w.writerow(dict(vbl=r['vbl'],logic_frame=r['logic_frame'],shown_frame=r['shown_frame'],photo_ticks=r['photo_ticks'],tick_ticks=r['tick_events'][0]['duration_cia_ticks'] if r['tick_events'] else None))
    print(json.dumps({k:result[k] for k in ('protocol','metadata','active','full_including_deliberate_end')},indent=2))
if __name__=='__main__':main()

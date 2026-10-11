/* G7-3 experimental: productor PF1/apoyo hardware desde la OAM de la
 * foto y el copper preparado. No hay tablas por frame ni aproximacion.
 * Un rechazo explicito retiene la ultima foto. Puertas pendientes y
 * reproducciones: docs/instrucciones-g7-3-retoma.md.
 */
typedef unsigned char u8;
typedef unsigned short u16;
typedef signed short s16;
typedef unsigned long u32;
typedef signed long s32;

extern void g7b_send(u32 count);
extern u32 g7b_save_row(u32 row);
extern void g7b_retry(void);

typedef struct { s16 x; u16 reg, value; } Event;
typedef struct { u16 lo,hi,reg,value,done; } Job;
typedef struct {
    s16 effect[256];
    u8 terrain[256], out[256];
    u16 terraincolor[256];
    u8 matches[256];
    u8 front[256];
    Event ev[64];
    u16 initial[8], first[8], locked[8], colors[16], masks[16], assign[16];
    u16 prefix, n, nc;
    Job jobs[64];
    u16 nj,body[128],end,capacity,initial2[8];
    u32 budget;
    u16 limit;
} Work;

#define advance(x) ((s16)((x)==231 ? 243 : (x)+((x)>=239 ? 8 : 16)))
static s16 xh(u16 h) {
    if(h<=192)return (s16)(8*(((s16)h-72)>>2)-1);
    if(h<=206)return h<200?243:(h<204?247:(h<206?251:255));
    return 263;
}
static void events(Work *w,u16 *seg,u16 row) {
    u16 i,reg,value,nb=0,body=0; s16 pos=-56;
    w->n=0;w->prefix=0;
    for(i=0;i<64;i++) {
        reg=seg[2*i];value=seg[2*i+1];
        if(reg==0x84)break;
        if(!body && i<2 && ((reg&1)||reg==0x1fe))continue;
        if(!body && !(reg&1) && reg!=0x1fe) {
            nb++;w->prefix=i+1;
            w->ev[w->n].x=-1;
        } else {
            if(!body){body=1;pos=-56+(nb>9?16*(nb-9):0);}
            if(reg&1) {
                pos=advance(advance(pos));
                if(pos<xh(reg&254))pos=xh(reg&254);
                continue;
            }
            w->ev[w->n].x=pos;pos=advance(pos);
        }
        w->ev[w->n].reg=reg;w->ev[w->n++].value=value;
    }
    (void)row;
}
static u16 color(Work *w,u16 r,u16 x) {
    u16 i,v=0;
    for(i=0;i<w->n;i++)if(w->ev[i].x<=(s16)x && w->ev[i].reg==0x180+2*r)
        v=w->ev[i].value&4095;
    return v;
}
static void row_colors(Work *w) {
    u16 pal[8]={0,0,0,0,0,0,0,0},e=0,x,r;
    for(x=0;x<256;x++) {
        while(e<w->n && w->ev[e].x<=(s16)x) {
            if(w->ev[e].reg>=0x182 && w->ev[e].reg<=0x18e)
                pal[(w->ev[e].reg-0x180)>>1]=w->ev[e].value&4095;
            e++;
        }
        w->terraincolor[x]=pal[w->terrain[x]];
        w->matches[x]=0;
        if(w->effect[x]>=0)for(r=1;r<8;r++)if(pal[r]==(u16)w->effect[x])w->matches[x]|=1<<r;
    }
}
static u16 pixel(u8 *bank,u16 tile,u16 x,u16 y) {
    u16 off=*(u16 *)(bank+16+2*tile),p,v=0;
    if(off==65535)return 65535;
    for(p=0;p<4;p++)v|=((*(u16 *)(bank+off+16*p+2*y)>>(15-x))&1)<<p;
    return v;
}
static u16 entry(u16 e) {
    return (e>=8 && e<12)||(e>=20 && e<32)||(e>=44 && e<56)||e>=60;
}
static u16 *flow(u16 *copper,u16 *spr,u16 ch,u16 *pos,u16 *ctl) {
    u16 *pt,*vb,i,r,hi=0,lo=0,armed=0;
    if(ch<4) {
        pt=spr+84*ch;*pos=pt[0];*ctl=pt[1];pt+=2;
        for(i=110;i<172;i+=2) {
            r=copper[i];
            if(r==0x120+4*ch)hi=copper[i+1];
            if(r==0x122+4*ch)lo=copper[i+1];
            if(r==0x140+8*ch){*pos=copper[i+1];armed=1;}
            if(r==0x142+8*ch)*ctl=copper[i+1];
        }
        if(armed)pt=(u16 *)(((u32)hi<<16)|lo);
    } else {
        vb=copper+110+8*(ch-4);
        pt=(u16 *)(((u32)vb[1]<<16)|vb[3]);*pos=vb[5];*ctl=vb[7];
    }
    return pt;
}
static u16 overlay(Work *w,u8 *bank,u8 *oam,u16 row) {
    u16 e,size,attr,tile,dx,sy,sx,v; s16 x,y,gx;
    for(dx=0;dx<256;dx++)w->effect[dx]=-1;
    for(e=0;e<64;e++)if(entry(e)) {
        x=oam[4*e]|((oam[256+e]&1)<<8);if(x>=256)x-=512;
        y=oam[4*e+1]+1;size=(oam[256+e]&2)?16:8;
        if(row<y || row>=y+size || x>=256 || x+size<=0)continue;
        attr=oam[4*e+3];tile=oam[4*e+2]|((attr&1)<<8);
        sy=row-y;if(attr&128)sy=size-1-sy;
        for(dx=0;dx<size;dx++) {
            gx=x+dx;if(gx<0 || gx>=256 || w->effect[gx]>=0)continue;
            sx=(attr&64)?size-1-dx:dx;
            v=pixel(bank,tile+(sx>>3)+16*(sy>>3),sx&7,sy&7);
            if(v==65535)return 1;
            if(v)w->effect[gx]=*(u16 *)(bank+1040+32*((attr>>1)&7)+2*v);
        }
    }
    return 0;
}
/* Canales originales: leer DATA/controles, tambien las cadenas nulas.
 * Esta mascara elimina solo sprites que pasan delante del PF1.
 */
static void hidden(Work *w,u16 *copper,u16 *spr,u16 row) {
    u16 ch,pos,ctl,*pt,*vb,loop,start,stop,mask,dx;
    s16 x;
    for(ch=0;ch<8;ch++) {
        pt=flow(copper,spr,ch,&pos,&ctl);
        for(loop=0;loop<32;loop++) {
            start=(pos>>8)|((ctl&4)<<6);stop=(ctl>>8)|((ctl&2)<<7);
            if(stop<=start)break;
            if(row+44>=start && row+44<stop) {
                mask=pt[2*(row+44-start)]|pt[2*(row+44-start)+1];
                x=2*(pos&255)+(ctl&1)-160;
                for(dx=0;dx<16;dx++)if((mask>>(15-dx))&1)
                    if(x+dx>=0 && x+dx<256 && w->front[x+dx]>(ch>>1))w->effect[x+dx]=-1;
            }
            pt+=2*(stop-start);pos=pt[0];ctl=pt[1];pt+=2;
        }
    }
}
static u16 matching(Work *w,u16 n,u16 occupied) {
    u16 r;
    if(n==w->nc)return 1;
    for(r=1;r<8;r++)if((w->masks[n]&(1<<r)) && !(occupied&(1<<r))) {
        w->assign[n]=r;
        if(matching(w,n+1,occupied|(1<<r)))return 1;
    }
    return 0;
}
/* Busqueda temporal finita, misma rejilla G2T-A que la referencia. La
 * cuenta es compartida entre asignaciones; agotarla es un rechazo.
 */
static u16 schedule(Work *w,s16 pos,u16 left,u16 count,u16 out,u16 row) {
    u16 i,k,h,n,phase,earliest=65535; s16 p,prev=-32768;
    if(!count)return out;
    if(left<count || !w->budget)return 0;
    w->budget--;
    for(i=0;i<w->nj;i++)if(!w->jobs[i].done) {
        if((s16)w->jobs[i].hi<pos)return 0;
        if(w->jobs[i].hi<earliest)earliest=w->jobs[i].hi;
    }
    for(i=0;i<w->nj;i++)if(!w->jobs[i].done && w->jobs[i].lo<=earliest) {
        prev=-32768;
        w->jobs[i].done=1;
      for(phase=0;phase<2;phase++) {
        p=pos;
        if(phase)p=advance(advance(p));
        for(n=phase?2:0;out && n<left && n<(phase?12:2);n++,p=advance(p)) {
            if(p>(s16)w->jobs[i].hi || p>(s16)w->end)break;
            if(p<(s16)w->jobs[i].lo)continue;
            for(k=0;k<n;k++){w->body[2*(out+k)]=0x1fe;w->body[2*(out+k)+1]=0;}
            w->body[2*(out+n)]=w->jobs[i].reg;w->body[2*(out+n)+1]=w->jobs[i].value;
            k=schedule(w,advance(p),left-n-1,count-1,out+n+1,row);
            if(k)return k;
        }
        if(!phase && left>=2)for(h=0x20;h<0xd0;h+=2) {
            p=advance(advance(pos));if(p<xh(h))p=xh(h);
            if(p==prev || p-pos<48 || p<(s16)w->jobs[i].lo || p>(s16)w->jobs[i].hi || p>(s16)w->end)continue;
            prev=p;
            w->body[2*out]=((row+44)&255)*256+h+1;w->body[2*out+1]=65534;
            w->body[2*out+2]=w->jobs[i].reg;w->body[2*out+3]=w->jobs[i].value;
            k=schedule(w,advance(p),left-2,count-1,out+2,row);
            if(k)return k;
        }
      }
        w->jobs[i].done=0;
    }
    return 0;
}
static u16 job(Work *w,u16 lo,u16 hi,u16 reg,u16 value) {
    Job *j;
    if(w->nj==64)return 0;
    j=&w->jobs[w->nj++];j->lo=lo;j->hi=hi;j->reg=reg;j->value=value;j->done=0;
    return 1;
}
static u16 temporal_try(Work *w,u16 *seg,u16 row) {
    u16 r,x,i,v,last=0,old=0,live,have,words,nb=0;
    w->nj=0;
    for(r=1;r<8;r++) {
        have=0;w->initial2[r]=color(w,r,0);
        for(x=0;x<256;x++) {
            live=0;v=0;
            if(w->effect[x]>=0) {
                for(i=0;i<w->nc;i++)if(w->colors[i]==(u16)w->effect[x])break;
                if(i<w->nc && w->assign[i]==r){v=w->effect[x];live=1;}
            } else if(w->terrain[x]==r){v=w->terraincolor[x];live=1;}
            if(!live)continue;
            if(!have){have=1;w->initial2[r]=v;}
            else if(v!=old && !job(w,last+1,x,0x180+2*r,v))return 0;
            last=x;old=v;
        }
    }
    for(i=0;i<w->n;i++)if(w->ev[i].x>=0 &&
        !(w->ev[i].reg>=0x182 && w->ev[i].reg<=0x18e) && w->ev[i].reg!=0x1fe)
        if(!job(w,w->ev[i].x,w->ev[i].x,w->ev[i].reg,w->ev[i].value))return 0;
    for(i=2;i<64;i++) {
        r=seg[128+2*i];if((r&1) || r==0x1fe || r==0x84)break;nb++;
    }
    if(nb<7 || nb>9 || row==211)return 0;
    w->end=351-8*nb;w->capacity=61-w->prefix;
    for(i=0;i<w->nj;i++)for(x=i+1;x<w->nj;x++)if(w->jobs[x].hi<w->jobs[i].hi) {
        Job temp=w->jobs[i];w->jobs[i]=w->jobs[x];w->jobs[x]=temp;
    }
    nb=w->prefix-2;
    words=schedule(w,-56+(nb>9?16*(nb-9):0),w->capacity,w->nj,0,row);
    if(!words && w->nj)return 0;
    /* El salto conserva su destino fisico y sus tres MOVE. */
    for(i=0;i<64;i++)if(seg[2*i]==0x84)break;
    if(i>=64)return 0;
    {u16 tail[6];for(x=0;x<6;x++)tail[x]=seg[2*i+x];
     for(x=0;x<6;x++)seg[2*(w->prefix+words)+x]=tail[x];}
    for(i=0;i<w->prefix;i++) {
        r=seg[2*i];if(r>=0x182 && r<=0x18e)seg[2*i+1]=(seg[2*i+1]&0xf000)|w->initial2[(r-0x180)>>1];
    }
    for(i=0;i<words*2;i++)seg[2*w->prefix+i]=w->body[i];
    for(x=0;x<256;x++) {
        w->out[x]=w->terrain[x];
        if(w->effect[x]>=0)for(i=0;i<w->nc;i++)if(w->colors[i]==(u16)w->effect[x]){w->out[x]=w->assign[i];break;}
    }
    return 1;
}
static u16 temporal_assign(Work *w,u16 *seg,u16 row,u16 n,u16 strict) {
    u16 r,x,first=256,last=0,ok,i,k,order[7],score[7],count,old,value,known,j;
    if(!w->budget)return 0;
    w->budget--;
    if(n==w->nc)return temporal_try(w,seg,row);
    for(x=0;x<256;x++)if(w->effect[x]==(s16)w->colors[n]){if(x<first)first=x;last=x;}
    count=0;
    for(r=1;r<8;r++) {
        ok=1;
        if(strict)for(x=first;x<=last;x++)if(w->effect[x]<0 && w->terrain[x]==r && w->terraincolor[x]!=w->colors[n]){ok=0;break;}
        if(!ok)continue;
        w->assign[n]=r;
        old=65535;k=0;
        for(x=0;x<256;x++) {
            known=0;value=0;
            if(w->effect[x]<0 && w->terrain[x]==r){value=w->terraincolor[x];known=1;}
            else if(w->effect[x]>=0)for(i=0;i<=n;i++)if(w->assign[i]==r && w->effect[x]==(s16)w->colors[i]){value=w->colors[i];known=1;break;}
            if(known && value!=old){k++;old=value;}
        }
        order[count]=r;score[count++]=k;
    }
    for(i=0;i<count;i++)for(j=i+1;j<count;j++)if(score[j]<score[i]) {
        k=score[i];score[i]=score[j];score[j]=k;k=order[i];order[i]=order[j];order[j]=k;
    }
    for(i=0;i<count;i++) {
        w->assign[n]=order[i];
        if(temporal_assign(w,seg,row,n+1,strict))return 1;
    }
    return 0;
}
/* Cota independiente de indices: 31 px permiten siete colores iniciales
 * y como mucho dos MOVE. Nueve tintas necesitan dos altas nuevas y dos
 * bajas antes de sus ranuras; si no existen, buscar asignaciones no ayuda.
 */
static u16 bound(Work *w) {
    u16 left,x,i,n,c[10],first[10],last[10],a,b,t,retire1,retire2,feasible;
    s16 v,t2;
    for(left=0;left<=200;left++) {
        n=0;
        for(x=left;x<left+31;x++) {
            if(w->effect[x]<0 && !w->terrain[x])continue;
            v=w->effect[x]>=0?w->effect[x]:w->terraincolor[x];
            for(i=0;i<n;i++)if(c[i]==(u16)v)break;
            if(i==n){if(n==9)return 1;c[n]=v;first[n]=x;last[n]=x;n++;}
            else last[i]=x;
        }
        if(n!=9)continue;
        feasible=0;
        for(a=0;a<9 && !feasible;a++)for(b=0;b<9 && !feasible;b++)if(a!=b) {
            for(t=left;t<left+31;t++)if((t&7)==7 && t<=first[a]) {
              for(t2=t+16;t2<left+31 && t2<=first[b];t2+=8) {
                retire1=retire2=0;
                for(i=0;i<9;i++)if(i!=a && i!=b) {
                    if(last[i]<t)retire1++;
                    if(last[i]<t2)retire2++;
                }
                if(last[a]<t2)retire2++;
                if(retire1 && retire2>=2){feasible=1;break;}
              }
              if(feasible)break;
            }
        }
        if(!feasible)return 1;
    }
    return 0;
}
static u16 temporal(Work *w,u16 *seg,u16 row) {
    u16 x,i;
    if(bound(w))return 2;
    w->nc=0;
    for(x=0;x<256;x++)if(w->effect[x]>=0) {
        for(i=0;i<w->nc;i++)if(w->colors[i]==(u16)w->effect[x])break;
        if(i==w->nc){if(i>=16)return 2;w->colors[w->nc++]=w->effect[x];}
    }
    w->budget=w->limit;
    if(temporal_assign(w,seg,row,0,1) || temporal_assign(w,seg,row,0,0))return 0;
    return 2;
}
static u16 plan(Work *w,u16 *seg,u16 row) {
    u16 x,r,i,v,mask,fixed,existing=1,t;
    events(w,seg,row);
    row_colors(w);
    for(x=0;x<256;x++) {
        w->out[x]=w->terrain[x];
        if(w->effect[x]<0)continue;
        for(r=1;r<8;r++)if(w->matches[x]&(1<<r))break;
        if(r==8)existing=0;else w->out[x]=r;
    }
    if(existing)return 0;
    for(r=1;r<8;r++){w->first[r]=256;w->locked[r]=0;}
    for(i=0;i<w->n;i++)if(w->ev[i].reg>=0x182 && w->ev[i].reg<=0x18e && w->ev[i].x>=0) {
        r=(w->ev[i].reg-0x180)>>1;if(w->ev[i].x<w->first[r])w->first[r]=w->ev[i].x;
    }
    for(x=0;x<256;x++) {
        r=w->terrain[x];if(r && w->effect[x]<0 && x<w->first[r])w->locked[r]=1;
    }
    w->nc=0;
    for(x=0;x<256;x++)if(w->effect[x]>=0) {
        v=w->effect[x];mask=0;fixed=0;
        for(r=1;r<8;r++) {
            if(w->locked[r] || x>=w->first[r]){if(w->matches[x]&(1<<r))fixed=1;}
            else mask|=1<<r;
        }
        if(fixed)continue;
        for(i=0;i<w->nc;i++)if(w->colors[i]==v)break;
        if(i==w->nc){if(i>=16)return 2;w->colors[i]=v;w->masks[i]=254;w->nc++;}
        w->masks[i]&=mask;
    }
    /* Primero la demanda mas restringida; no depende del frame. */
    for(i=0;i<w->nc;i++)for(r=i+1;r<w->nc;r++)if(w->masks[r]<w->masks[i]) {
        t=w->masks[r];w->masks[r]=w->masks[i];w->masks[i]=t;
        t=w->colors[r];w->colors[r]=w->colors[i];w->colors[i]=t;
    }
    if(!matching(w,0,0))return temporal(w,seg,row);
    for(i=0;i<w->nc;i++)for(x=0;x<w->prefix;x++)if(seg[2*x]==0x180+2*w->assign[i])
        seg[2*x+1]=(seg[2*x+1]&0xf000)|w->colors[i];
    events(w,seg,row);
    row_colors(w);
    for(x=0;x<256;x++)if(w->effect[x]>=0) {
        for(r=1;r<8;r++)if(w->matches[x]&(1<<r))break;
        if(r==8)return 3;w->out[x]=r;
    }
    return 0;
}

static u32 produce(u8 *bank,u8 *data,u8 *pf,u16 *copper,u8 *oam,u16 *spr,u32 cam,u16 limit) {
    Work w;u16 row,x,wx,col,off,v,p,mask,bits[3],n,q,error,active[14],e,y,size,priority=4,i;
    s16 ex;
    u16 *src,*dest,*queue=(u16 *)(bank+8576);
    w.limit=limit;
    for(row=0;row<14;row++)active[row]=0;
    for(i=0;i<86;i++)if(copper[2*i]==0x104)priority=copper[2*i+1]&7;
    for(e=0;e<64;e++)if(entry(e)) {
        ex=oam[4*e]|((oam[256+e]&1)<<8);if(ex>=256)ex-=512;
        size=(oam[256+e]&2)?16:8;y=oam[4*e+1]+1;
        if(ex>=256 || ex+size<=0 || y>=224)continue;
        for(row=y;row<y+size && row<224;row++)active[row>>4]|=1<<(row&15);
    }
    for(row=0;row<224;row++) {
        dest=copper+172+128*row;
        if(!(active[row>>4]&(1<<(row&15)))) {
            for(i=0;i<64 && dest[2*i]!=0x84;i++)if(dest[2*i]==0x104)priority=dest[2*i+1]&7;
            continue;
        }
        error=overlay(&w,bank,oam,row);if(error)return error;
        events(&w,dest,row);
        e=0;
        for(x=0;x<256;x++) {
            while(e<w.n && w.ev[e].x<=(s16)x) {if(w.ev[e].reg==0x104)priority=w.ev[e].value&7;e++;}
            w.front[x]=priority;
        }
        while(e<w.n){if(w.ev[e].reg==0x104)priority=w.ev[e].value&7;e++;}
        hidden(&w,copper,spr,row);
        n=0;for(x=0;x<256;x++)if(w.effect[x]>=0)n++;
        if(!n)continue;
        for(x=0;x<256;x++) {
            /* PF1 contiene el mapa aplicado hasta R_TSEQ y la moneda
             * animada. El mapa global puede pertenecer a una IRQ futura. */
            wx=cam+x;
            if(!x || !(wx&15))src=(u16 *)(pf+264*row+2*((wx>>4)%22));
            w.terrain[x]=0;for(p=0;p<3;p++)w.terrain[x]|=((src[44*p]>>(15-(wx&15)))&1)<<p;
        }
        error=g7b_save_row(row);if(error)return error;
        error=plan(&w,dest,row);if(error)return error|((u32)row<<8);
        q=0;x=0;
        while(x<256) {
            wx=cam+x;col=wx>>4;mask=0;bits[0]=bits[1]=bits[2]=0;
            do {
                off=15-((cam+x)&15);
                if(w.effect[x]>=0) {
                    mask|=1<<off;
                    for(p=0;p<3;p++)bits[p]|=((w.out[x]>>p)&1)<<off;
                }
                x++;
            }while(x<256 && ((cam+x)>>4)==col);
            if(!mask)continue;
            *(u32 *)(queue+8*q)=(u32)(pf+264*row+2*(col%22));
            for(p=0;p<3;p++){queue[8*q+2+p]=mask;queue[8*q+5+p]=bits[p];}q++;
        }
        g7b_send(q);
    }
    return 0;
}

static u16 spanstart(u16 pos,u16 ctl) {return (pos>>8)|((ctl&4)<<6);}
static u16 spanstop(u16 ctl) {return (ctl>>8)|((ctl&2)<<7);}
static u16 unused(u16 *copper,u16 *spr,u16 prime) {
    u16 pair,k,ch,pos[2],ctl[2],*pt[2],start,stop,row,dx,v,used=0,bits[4];s16 x;
    for(pair=0;pair<8;pair+=2) {
        for(k=0;k<2;k++)pt[k]=flow(copper,spr,pair+k,&pos[k],&ctl[k]);
        for(ch=0;ch<32;ch++) {
            start=spanstart(pos[0],ctl[0]);stop=spanstop(ctl[0]);if(stop<=start)break;
            x=2*(pos[0]&255)+(ctl[0]&1)-160;
            for(row=start;row<stop;row++) {
                for(k=0;k<2;k++){bits[2*k]=*pt[k]++;bits[2*k+1]=*pt[k]++;}
                if(row<prime+44 || row>=268)continue;
                for(dx=0;dx<16;dx++)if(x+dx>=0 && x+dx<256) {
                    v=0;for(k=0;k<4;k++)v|=((bits[k]>>(15-dx))&1)<<k;
                    if(v)used|=1<<v;
                }
            }
            for(k=0;k<2;k++){pos[k]=*pt[k]++;ctl[k]=*pt[k]++;}
        }
    }
    return (u16)~used&65534;
}
static u16 freepair(u16 *copper,u16 *spr,u16 pair) {
    u16 ch,pos,ctl,*pt,row,i,r;
    for(ch=pair;ch<pair+2;ch++) {
        pt=flow(copper,spr,ch,&pos,&ctl);(void)pt;
        if(spanstop(ctl)>spanstart(pos,ctl))return 0;
    }
    for(row=0;row<224;row++)for(i=0;i<64;i++) {
        r=copper[172+128*row+2*i];if(r==0x84)break;
        if((r>=0x120+4*pair && r<=0x126+4*pair) || (r>=0x140+8*pair && r<=0x14a+8*pair))return 0;
    }
    return 1;
}
/* Apoyo de una ficha: paleta existente exacta o indices sin propietarios
 * desde el prime. No rearma un canal en display, ni escribe flujos ajenos.
 */
static u16 hardware(u8 *bank,u16 *copper,u8 *oam,u16 *spr,u16 e,u16 pair,u16 *buf) {
    Work w;u16 row,dx,sx,sy,size,attr,tile,v,nc=0,i,r,j,y,stop,prime,original_y,first=16,final=0;
    u16 colors[16],possible[16],mapping[16],pal[16],priority=4,ev,used,reuse=1;
    u16 *seg,nb=0,len=0,extra,lastpos,ctl,pos,*dst,bit,upper;
    s16 x,gx,last=-56,p; s16 source[256];
    x=oam[4*e]|((oam[256+e]&1)<<8);if(x>=256)x-=512;
    y=oam[4*e+1]+1;size=(oam[256+e]&2)?16:8;stop=y+size;if(stop>224)stop=224;
    if(y>=224 || x>=256 || x+size<=0)return 1;
    attr=oam[4*e+3];tile=oam[4*e+2]|((attr&1)<<8);prime=y-1;original_y=y;
    for(i=0;i<256;i++)source[i]=-1;
    for(i=0;i<16;i++)pal[i]=0;
    for(i=0;i<86;i++) {
        r=copper[2*i];v=copper[2*i+1];
        if(r>=0x1a2 && r<=0x1be)pal[(r-0x1a0)>>1]=v&4095;
        if(r==0x104)priority=v&7;
    }
    for(row=0;row<224;row++) {
        seg=copper+172+128*row;events(&w,seg,row);ev=0;
        if(row>=y && row<stop) {
            if(overlay(&w,bank,oam,row))return 1;
            for(j=0;j<256;j++) {
                while(ev<w.n && w.ev[ev].x<=(s16)j) {if(w.ev[ev].reg==0x104)priority=w.ev[ev].value&7;ev++;}
                w.front[j]=priority;
            }
            hidden(&w,copper,spr,row);ev=0;
            sy=row-y;if(attr&128)sy=size-1-sy;
            for(j=0;j<256;j++) {
                while(ev<w.n && w.ev[ev].x<=(s16)j) {
                    r=w.ev[ev].reg;if(r>=0x1a2 && r<=0x1be)pal[(r-0x1a0)>>1]=w.ev[ev].value&4095;ev++;
                }
                if((s16)j<x || (s16)j>=x+size || w.effect[j]<0)continue;
                dx=j-x;sx=(attr&64)?size-1-dx:dx;
                v=pixel(bank,tile+(sx>>3)+16*(sy>>3),sx&7,sy&7);
                if(!v || v==65535)continue;
                v=*(u16 *)(bank+1040+32*((attr>>1)&7)+2*v);
                if(w.effect[j]!=(s16)v)continue;
                if(w.front[j]<=(pair>>1))return 1;
                source[(row-y)*16+dx]=v;
                for(i=0;i<nc;i++)if(colors[i]==v)break;
                if(i==nc){if(nc==16)return 1;colors[nc]=v;possible[nc++]=65534;}
                used=0;for(r=1;r<16;r++)if(pal[r]==v)used|=1<<r;
                possible[i]&=used;
            }
        }
        while(ev<w.n) {
            r=w.ev[ev].reg;v=w.ev[ev++].value;
            if(r>=0x1a2 && r<=0x1be)pal[(r-0x1a0)>>1]=v&4095;
            if(r==0x104)priority=v&7;
        }
    }
    if(!nc)return 1;
    for(row=y;row<stop;row++)for(dx=0;dx<16;dx++)if(source[(row-y)*16+dx]>=0) {
        if(row-y<first)first=row-y;final=row-y+1;
    }
    stop=y+final;y+=first;prime=y-1;
    for(i=0;i<nc;i++)if(!possible[i])reuse=0;
    used=unused(copper,spr,prime);
    for(i=0;i<nc;i++) {
        v=reuse?possible[i]:used;
        for(r=1;r<16;r++)if(v&(1<<r))break;
        if(r==16)return 1;
        mapping[i]=r;if(!reuse)used&=~(1<<r);
    }
    if(!reuse) {
        /* No permitir que un emisor ya presente cambie estas tintas. */
        for(row=y;row<stop;row++) {
            seg=copper+172+128*row;
            for(j=0;j<64 && seg[2*j]!=0x84;j++)for(i=0;i<nc;i++)
                if(seg[2*j]==0x1a0+2*mapping[i])return 1;
        }
        if(prime==211)return 1;
        seg=copper+172+128*prime;events(&w,seg,prime);
        for(i=0;i<w.n;i++)if(w.ev[i].x>=0)last=w.ev[i].x;
        for(i=2;i<64;i++){r=seg[128+2*i];if((r&1)||r==0x1fe||r==0x84)break;nb++;}
        if(nb<7 || nb>9)return 1;
        for(len=0;len<64 && seg[2*len]!=0x84;len++);
        extra=nc;
        if(263-last>=48 && 263+8*(nc-1)<=351-8*nb){p=263;extra++;}
        else {
            p=last;for(i=0;i<nc;i++)p=advance(p);
            if(last<0 || p>351-8*nb)return 1;p=-1;
        }
        if(len+extra+3>64)return 1;
        /* El prime debe quedar sin bobs para no desplazar el plan PF1. */
        if(overlay(&w,bank,oam,prime))return 1;
        for(j=0;j<256;j++)w.front[j]=4;
        hidden(&w,copper,spr,prime);
        for(j=0;j<256;j++)if(w.effect[j]>=0)return 1;
        if(g7b_save_row(prime))return 1;
        for(i=6;i;i--)seg[2*(len+extra)+i-1]=seg[2*len+i-1];
        if(p==263){seg[2*len++]=((prime+44)&255)*256+0xd1;seg[2*len-1]=65534;}
        for(i=0;i<nc;i++){seg[2*len++]=0x1a0+2*mapping[i];seg[2*len-1]=colors[i];}
    }
    for(upper=0;upper<2;upper++) {
        dst=buf+36*upper;
        pos=((y+44)&255)*256+(((x+160)>>1)&255);
        ctl=((stop+44)&255)*256+((x+160)&1)+(((y+44)>>8)&1)*4+(((stop+44)>>8)&1)*2+(upper?128:0);
        dst[0]=pos;dst[1]=ctl;
        for(row=y;row<stop;row++)for(bit=0;bit<2;bit++) {
            v=0;for(dx=0;dx<16;dx++)if(source[(row-original_y)*16+dx]>=0) {
                for(i=0;i<nc;i++)if(colors[i]==(u16)source[(row-original_y)*16+dx])break;
                v|=((mapping[i]>>(2*upper+bit))&1)<<(15-dx);
            }
            dst[2+2*(row-y)+bit]=v;
        }
        dst[2+2*(stop-y)]=dst[3+2*(stop-y)]=0;
        seg=copper+108+(pair==2?48:18)+8*upper;
        lastpos=pair+upper;
        seg[0]=0x120+4*lastpos;seg[1]=(u32)(dst+2)>>16;
        seg[2]=0x122+4*lastpos;seg[3]=(u32)(dst+2);
        seg[4]=0x140+8*lastpos;seg[5]=pos;
        seg[6]=0x142+8*lastpos;seg[7]=ctl;
    }
    return 0;
}

static u16 candidates(u8 *bank,u8 *oam,u16 row,u16 *order) {
    u16 e,size,attr,tile,sy,sx,dx,v,n=0,i,j,t,score[32];s16 x;
    for(e=0;e<64;e++)if(entry(e)) {
        size=(oam[256+e]&2)?16:8;
        if(row<oam[4*e+1]+1 || row>=oam[4*e+1]+1+size)continue;
        x=oam[4*e]|((oam[256+e]&1)<<8);if(x>=256)x-=512;
        attr=oam[4*e+3];tile=oam[4*e+2]|((attr&1)<<8);
        sy=row-oam[4*e+1]-1;if(attr&128)sy=size-1-sy;
        v=0;
        for(dx=0;dx<size;dx++)if(x+dx>=0 && x+dx<256) {
            sx=(attr&64)?size-1-dx:dx;
            if(pixel(bank,tile+(sx>>3)+16*(sy>>3),sx&7,sy&7))v++;
        }
        if(v){order[n]=e;score[n++]=v;}
    }
    for(i=0;i<n;i++)for(j=i+1;j<n;j++)if(score[j]>score[i]) {
        t=score[i];score[i]=score[j];score[j]=t;t=order[i];order[i]=order[j];order[j]=t;
    }
    return n;
}

u32 g7_render(u8 *bank,u8 *data,u8 *pf,u16 *copper,u8 *oam,u16 *spr,u32 cam) {
    u32 error;u16 row,e,f,pair,other,mask=0,slot,order[32],order2[32],n,n2,i,j;
    u16 *buf;
    slot=cam>>16;cam&=65535;buf=(u16 *)(bank+7616+320*slot);
    error=produce(bank,data,pf,copper,oam,spr,cam,64);
    if((error&255)!=2)return error;
    row=error>>8;
    if(freepair(copper,spr,2))mask|=1;
    if(freepair(copper,spr,6))mask|=2;
    /* La direccion del buffer corresponde exclusivamente a la lista libre.
     * El llamador pasa su indice en los bits altos de cam; no es un frame. */
    n=candidates(bank,oam,row,order);
    for(i=0;i<n;i++) {
        e=order[i];
        for(pair=2;pair<=6;pair+=4)if(mask&(pair==2?1:2)) {
            g7b_retry();
            if(hardware(bank,copper,oam,spr,e,pair,buf))continue;
            error=produce(bank,data,pf,copper,oam,spr,cam,64);
            if(!error)return 0;
            if((error&255)!=2)continue;
            if(mask!=3)continue;
            other=8-pair;
            n2=candidates(bank,oam,error>>8,order2);
            for(j=0;j<n2;j++)if((f=order2[j])!=e) {
                g7b_retry();
                if(hardware(bank,copper,oam,spr,e,pair,buf))continue;
                if(hardware(bank,copper,oam,spr,f,other,buf+80))continue;
                error=produce(bank,data,pf,copper,oam,spr,cam,64);
                if(!error)return 0;
            }
        }
    }
    /* Un presupuesto agotado no prueba imposibilidad de PF1. Reintentar
     * el terreno original con mas estados despues de los apoyos baratos. */
    g7b_retry();
    return produce(bank,data,pf,copper,oam,spr,cam,3000);
}

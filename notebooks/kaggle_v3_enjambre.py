#!/usr/bin/env python3
"""KAGGLE v3 — Enjambre: Madre autoriza; Reversión/Continuación independientes; Scalper hijo de Continuación."""
from __future__ import annotations
import os, json, math, random
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import torch
import gymnasium as gym
from stable_baselines3 import PPO
from sb3_contrib import RecurrentPPO
from stable_baselines3.common.vec_env import DummyVecEnv

WORKING = Path('/kaggle/working')
MODELS = WORKING / 'modelos_v3'
MODELS.mkdir(exist_ok=True)
DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'
HORIZON = 240; SL_ATR = 1.5; TP1_R = 2.0; TP2_R = 4.0
COMISION = 0.0001; SPREAD = 0.0002; SWAP = 0.000005

def leer(name):
    for dp, _, fnames in os.walk('/kaggle/input'):
        for f in fnames:
            if f.lower().endswith('.csv') and name.lower() in f.lower():
                p = Path(dp) / f
                df = pd.read_csv(p, sep='\t', engine='python')
                df.columns = [c.strip().strip('<>') for c in df.columns]
                if 'TIME' in df.columns:
                    df['datetime'] = pd.to_datetime(df['DATE'] + ' ' + df['TIME'], format='%Y.%m.%d %H:%M:%S', errors='coerce')
                else:
                    df['datetime'] = pd.to_datetime(df['DATE'], format='%Y.%m.%d', errors='coerce')
                for c in ['OPEN','HIGH','LOW','CLOSE','TICKVOL','VOL','SPREAD']:
                    if c in df.columns: df[c] = pd.to_numeric(df[c].astype(str).str.replace(',','.'), errors='coerce')
                return df.dropna(subset=['datetime','CLOSE']).set_index('datetime').sort_index()
    return None

m1 = leer('datatb.csv')
print(f'M1: {len(m1):,} filas')

def indis(d):
    c, h, l = d['CLOSE'], d['HIGH'], d['LOW']
    delta = c.diff(); d['rsi'] = 100 - 100/(1+delta.where(delta>0,0).rolling(14).mean()/(-delta.where(delta<0,0)).rolling(14).mean())
    d['ema_fast'] = c.ewm(12, adjust=False).mean(); d['ema_slow'] = c.ewm(26, adjust=False).mean()
    sma20, std20 = c.rolling(20).mean(), c.rolling(20).std()
    d['bb_upper'] = sma20+2*std20; d['bb_lower'] = sma20-2*std20; d['bb_mid'] = sma20
    bw = d['bb_upper']-d['bb_lower']; d['bb_pct_b'] = (c-d['bb_lower'])/bw; d['bbw'] = bw/d['bb_mid']
    tr = pd.concat([h-l,abs(h-c.shift()),abs(l-c.shift())],axis=1).max(axis=1)
    d['atr'] = tr.rolling(14).mean()
    pdm, mdm = h.diff().where(h.diff()>l.diff(),0), (-l.diff()).where(l.diff()>h.diff(),0)
    atrs = tr.ewm(alpha=1/14, adjust=False).mean()
    d['adx'] = (100*abs(100*pdm.ewm(alpha=1/14,adjust=False).mean()/atrs - 100*mdm.ewm(alpha=1/14,adjust=False).mean()/atrs) / (100*pdm.ewm(alpha=1/14,adjust=False).mean()/atrs + 100*mdm.ewm(alpha=1/14,adjust=False).mean()/atrs + 1e-9)).ewm(alpha=1/14,adjust=False).mean()
    e12, e26 = c.ewm(12, adjust=False).mean(), c.ewm(26, adjust=False).mean()
    d['macd'] = e12-e26; d['macd_signal'] = d['macd'].ewm(9, adjust=False).mean()
    d['volume_spike'] = d.get('TICKVOL',d.get('VOL',1))/d.get('TICKVOL',d.get('VOL',1)).ewm(20,adjust=False).mean()
    d['hour'] = d.index.hour
    return d

m1 = indis(m1)
FEATS = ['CLOSE','HIGH','LOW','OPEN','volume_spike','rsi','ema_fast','ema_slow','bb_upper','bb_lower','atr','adx','macd','macd_signal']

def norm(row, f):
    c = row['CLOSE'] or 1
    v = row.get(f,0)
    if f in ['CLOSE','HIGH','LOW','OPEN','bb_upper','bb_lower','ema_fast','ema_slow']: return v/c-1.0
    if f == 'rsi': return v/100.0
    if f == 'atr': return v/c
    if f in ['adx','bbw']: return min(v/100.0,5.0)
    if f == 'macd': return v/c
    return float(v)

class EnvBot(gym.Env):
    def __init__(self, df, feats, filt=None):
        super().__init__(); self.df=df.reset_index(drop=True); self.feats=[f for f in feats if f in df.columns]; self.filt=filt
        self.action_space=gym.spaces.Discrete(5); self.observation_space=gym.spaces.Box(-np.inf,np.inf,(len(self.feats)+2,),np.float32)
        self.sl_atr=SL_ATR; self.tp1=TP1_R; self.tp2=TP2_R; self.hor=HORIZON
    def _obs(self):
        r=self.df.iloc[self.i]; obs=[norm(r,f) for f in self.feats]; obs.append((r.get('hour',12)-12)/12.0); obs.append(self.pos); return np.array(obs,np.float32)
    def reset(self, seed=None, options=None):
        if self.filt is None: self.i=random.randint(100,len(self.df)-self.hor-10)
        else:
            for _ in range(5000):
                i=random.randint(100,len(self.df)-self.hor-10)
                if self.filt(self.df.iloc[i]): self.i=i; break
            else: self.i=random.randint(100,len(self.df)-self.hor-10)
        self.pos=0; self.sz=0; self.ent=0; self.sl=0; self.t1=0; self.t2=0; self.mf=0; self.be=False; self.h=0
        return self._obs(),{}
    def step(self, act):
        r=self.df.iloc[self.i]; p=r['CLOSE']; a=r.get('atr',p*0.001); hr=r.get('hour',12); ny=14<=hr<=21
        rew=0.0; done=False; info={'ev':'none'}
        dirc = {1:(1,0.05),2:(1,0.10),3:(-1,0.05),4:(-1,0.10)}
        if self.pos==0 and act!=0 and ny:
            self.pos,self.sz=dirc[act]; self.ent=p; self.sl=p-self.pos*a*self.sl_atr; self.t1=p+self.pos*a*self.sl_atr*self.tp1; self.t2=p+self.pos*a*self.sl_atr*self.tp2; self.mf=p; self.be=False; self.h=0; info['ev']='open'; rew-=SPREAD*10
        elif self.pos!=0:
            self.h+=1; self.mf=max(self.mf,p) if self.pos==1 else min(self.mf,p)
            cst=SPREAD+COMISION*2+SWAP*self.h
            hit_sl=(self.pos==1 and p<=self.sl) or (self.pos==-1 and p>=self.sl)
            hit_t1=(self.pos==1 and p>=self.t1) or (self.pos==-1 and p<=self.t1)
            hit_t2=(self.pos==1 and p>=self.t2) or (self.pos==-1 and p<=self.t2)
            if hit_t1 and not self.be: self.sl=self.ent; self.be=True; rew+=self.pos*(p-self.ent)/self.ent*50*self.sz; info['ev']='tp1'
            if self.be and self.h>10:
                trl=self.mf-self.pos*a*1.5
                self.sl=max(self.sl,trl) if self.pos==1 else min(self.sl,trl)
            if hit_sl: rew+=(-abs(self.ent-self.sl)/self.ent-cst)*100*self.sz; self.pos=0; done=True; info['ev']='sl'
            elif hit_t2: rew+=(abs(self.ent-self.t2)/self.ent-cst)*100*self.sz; self.pos=0; done=True; info['ev']='tp2'
            elif self.h>=self.hor: rew+=(self.pos*(p-self.ent)/self.ent-cst)*100*self.sz; self.pos=0; done=True; info['ev']='time'
            else: rew-=cst*5
        else: rew-=0.005
        self.i+=1
        if self.i>=len(self.df)-5: done=True
        return self._obs(),float(rew),done,False,info

def train(nombre, df, filt, steps=300_000):
    print(f'\n=== {nombre} ===')
    env=DummyVecEnv([lambda: EnvBot(df,FEATS,filt)])
    m=PPO('MlpPolicy',env,verbose=1,device=DEVICE,lr=3e-4,n_steps=2048,batch_size=256,n_epochs=10,gamma=0.99,gae_lambda=0.95,ent_coef=0.01,vf_coef=0.5)
    m.learn(steps); m.save(str(MODELS/f'{nombre}_ppo')); return m

def evalu(nombre,m,df,filt,n=2000):
    e=EnvBot(df,FEATS,filt); w,t,l,tt,pn=0,0,0,0,[]
    for _ in range(n):
        o,_=e.reset(); done=False; er=0
        while not done:
            a,_=m.predict(o,deterministic=True); o,r,done,_,info=e.step(int(a)); er+=r
            if done:
                ev=info['ev']
                if ev=='tp2': w+=1
                elif ev=='tp1': t+=1
                elif ev=='sl': l+=1
                elif ev=='time': tt+=1
                pn.append(er)
    tot=w+t+l+tt
    print(f'{nombre}: TP2={w} TP1={t} SL={l} Time={tt} | WR={w/tot:.1%} WR+BE={(w+t)/tot:.1%} | MR={np.mean(pn):.1f}')
    return {'winrate':w/tot,'winrate_be':(w+t)/tot,'mean_reward':float(np.mean(pn)),'tp2':w,'tp1':t,'sl':l,'time':tt}

# --- FILTROS ---
def filtro_rev(r): return (r.get('rsi',50)>70 or r.get('rsi',50)<30) and (r.get('bb_pct_b',0.5)<0.05 or r.get('bb_pct_b',0.5)>0.95)
def filtro_cont(r): return r.get('adx',0)>25 and abs(r.get('macd_confluence',0))==1
def filtro_scalp(r): return r.get('adx',0)>30 and abs(r.get('macd',0)/r['CLOSE'])>0.0005
def filtro_madre(r): return True

# --- ENTRENAMIENTO ---
model_madre = train('madre', m1, filtro_madre, steps=300_000)
stats_madre = evalu('madre', model_madre, m1, filtro_madre)

m1['macd_confluence'] = np.where((m1['macd']>m1['macd_signal'])&(m1['macd']>m1['macd'].shift(1)),1, np.where((m1['macd']<m1['macd_signal'])&(m1['macd']<m1['macd'].shift(1)),-1,0))

model_rev = train('reversion', m1, filtro_rev, steps=300_000)
stats_rev = evalu('reversion', model_rev, m1, filtro_rev)

model_cont = train('continuacion', m1, filtro_cont, steps=300_000)
stats_cont = evalu('continuacion', model_cont, m1, filtro_cont)

model_scalp = train('scalper', m1, filtro_scalp, steps=300_000)
stats_scalp = evalu('scalper', model_scalp, m1, filtro_scalp)

# --- ONNX ---
import onnx
for nom,mod in [('madre',model_madre),('reversion',model_rev),('continuacion',model_cont),('scalper',model_scalp)]:
    o=EnvBot(m1.head(1000),FEATS)
    s,_=o.reset(); t=torch.as_tensor(s, dtype=torch.float32).unsqueeze(0)
    if DEVICE=='cuda': t=t.cuda()
    try:
        torch.onnx.export(mod.policy,t,str(MODELS/f'bot_{nom}.onnx'),export_params=True,opset_version=12,input_names=['obs'],output_names=['logits'],dynamic_axes={'obs':{0:'batch'},'logits':{0:'batch'}})
        onnx.checker.check_model(onnx.load(str(MODELS/f'bot_{nom}.onnx')))
        print(f'ONNX OK: bot_{nom}.onnx')
    except Exception as e: print(f'ONNX ERR {nom}: {e}')

# --- REPORTE ---
rpt={'ts':datetime.now(timezone.utc).isoformat(),'device':DEVICE,'rows':len(m1),
     'bots':{'madre':stats_madre,'reversion':stats_rev,'continuacion':stats_cont,'scalper':stats_scalp},
     'cfg':{'horizon':HORIZON,'sl_atr':SL_ATR,'tp1':TP1_R,'tp2':TP2_R}}
with open(WORKING/'reporte_v3.json','w') as f: json.dump(rpt,f,indent=2)
import shutil; shutil.make_archive(str(WORKING/'modelos_v3'),'zip',str(MODELS))
print(f'\nZIP: {WORKING/"modelos_v3.zip"}')

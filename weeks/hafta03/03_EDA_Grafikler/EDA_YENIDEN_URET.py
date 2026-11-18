"""Reproduce Week 3 offline EDA figures from source minute-level CSVs."""
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
base=Path(__file__).resolve().parents[1]
out=Path(__file__).resolve().parent
labels=pd.read_csv(base/'02_OFFLINE_Veri/logscope_ana_dakika_etiketleri.csv')
features=pd.read_csv(base/'02_OFFLINE_Veri/logscope_ana_1200_pencere_ozellikleri.csv')
df=labels.merge(features,on='minute_start_utc',validate='one_to_one')
df['minute_start_utc']=pd.to_datetime(df['minute_start_utc'],utc=True)
assert len(df)==1200 and df['request_count'].sum()==146435
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.titleweight':'bold'})
fig,ax=plt.subplots(figsize=(12,4.6));ax.plot(df['minute_start_utc'][:240],df['request_count'][:240]);ax.set(title='İlk 240 dakika: olay hacmi (offline)',xlabel='UTC zaman',ylabel='İstek/dakika');ax.grid(alpha=.2);fig.autofmt_xdate();fig.tight_layout();fig.savefig(out/'01_Zaman_Serisi.png',dpi=165);plt.close(fig)
fig,ax=plt.subplots(figsize=(12,5.2));by=df.groupby('scenario_code')['request_count'].sum().sort_values();ax.barh(by.index.str.replace('_',' '),by.values);ax.set(title='Senaryo bazında olay hacmi (offline)',xlabel='Toplam sentetik olay');fig.tight_layout();fig.savefig(out/'02_8_Senaryo_Hacmi.png',dpi=165);plt.close(fig)
fig,ax=plt.subplots(figsize=(7,4.7));v=df['split'].value_counts().reindex(['train','validation','test']);ax.bar(['Eğitim','Doğrulama','Test'],v.values);ax.set(title='Kronolojik 60/20/20 bölünmesi',ylabel='Dakika');fig.tight_layout();fig.savefig(out/'03_Kronolojik_Bolunme.png',dpi=165);plt.close(fig)
fig,ax=plt.subplots(figsize=(10,4.4));ax.hist([df.loc[df.ground_truth=='normal','request_count'],df.loc[df.ground_truth=='anomaly','request_count']],bins=27,label=['Normal','Anormal'],alpha=.65);ax.legend();ax.set(title='Normal ve anormal hacim dağılımı',xlabel='İstek/dakika');fig.tight_layout();fig.savefig(out/'04_Hacim_Dagilimi.png',dpi=165);plt.close(fig)
print('4 offline EDA figure(s) generated from 1200 time windows / 146435 events')

"""Static schema inventory and FK validator (not a PostgreSQL execution test)."""
from pathlib import Path
from collections import defaultdict
import csv, json, re
ROOT=Path(__file__).resolve().parent
files=[ROOT/'01_research_core.sql',ROOT/'02_product_extensions.sql']
def split_commas(s):
    parts=[]; start=0; level=0; quote=False
    for i,ch in enumerate(s):
        if ch=="'": quote=not quote
        if not quote:
            if ch=='(':level+=1
            if ch==')':level-=1
            if ch==',' and level==0:parts.append(s[start:i].strip());start=i+1
    parts.append(s[start:].strip())
    return parts

def tables_in(text):
    rx=re.compile(r'CREATE TABLE IF NOT EXISTS\s+(\w+)\s*\(',re.I)
    out=[]
    for m in rx.finditer(text):
        i=m.end();j=i;level=1;quote=False
        while j<len(text) and level:
            c=text[j]
            if c=="'":quote=not quote
            elif not quote:
                if c=='(':level+=1
                elif c==')':level-=1
            j+=1
        if level!=0:raise ValueError('Unclosed CREATE TABLE: '+m.group(1))
        out.append((m.group(1),text[i:j-1]))
    return out

rows=[];relations=[];tables={}
for file in files:
    raw=file.read_text(encoding='utf-8')
    for name,body in tables_in(raw):
        if name in tables:raise ValueError('Duplicate table '+name)
        tables[name]=file.name
        chunks=split_commas(body);compound=[]
        for part in chunks:
            if re.match(r'^PRIMARY KEY',part,re.I):
                compound=re.findall(r'\w+',part[part.find('(')+1:part.rfind(')')]);continue
            m=re.match(r'^\s*([\w_]+)\s+([A-Z][A-Z\d_]*(?:\([^)]*\))?(?:\[\])?)\s*(.*)$',part,re.I|re.S)
            if not m:continue
            field,datatype,constraint=m.groups()
            if field.upper() in ('CHECK','UNIQUE','CONSTRAINT','FOREIGN','PRIMARY'):continue
            ref=re.search(r'REFERENCES\s+(\w+)\s*\(\s*(\w+)\s*\)',constraint,re.I)
            if ref:relations.append((name,field,ref.group(1),ref.group(2),'FK'))
            rows.append({'module':'research_core' if file.name.startswith('01') else 'product_extension','table':name,'field':field,'sql_type':datatype,'key':('PK' if 'PRIMARY KEY' in constraint.upper() or field in compound else '')+(' / FK' if ref else ''),'nullable':'no' if 'NOT NULL' in constraint.upper() or 'PRIMARY KEY' in constraint.upper() or field in compound else 'yes','references':(ref.group(1)+'.'+ref.group(2)) if ref else '', 'restrictions':re.sub(r'\s+',' ',constraint).strip()[:250]})
        for row in rows:
            if row['table']==name and row['field'] in compound:row['key']='PK'+(' / FK' if row['references'] else '')
# New columns added to pre-existing core tables by the extension migration.
raw=files[-1].read_text(encoding='utf-8')
for table,field,datatype,ref in re.findall(r'ALTER TABLE\s+(\w+)\s+ADD COLUMN IF NOT EXISTS\s+(\w+)\s+(\w+)\s+REFERENCES\s+(\w+)\(id\)',raw,re.I):
    if table not in tables: raise ValueError('Unknown altered table: '+table)
    relations.append((table,field,ref,'id','FK (extension)'))
    rows.append({'module':'product_extension','table':table,'field':field,'sql_type':datatype,'key':'FK','nullable':'yes','references':ref+'.id','restrictions':'Added by 02_product_extensions.sql'})
missing=sorted(set(r[2] for r in relations)-set(tables))
if missing:raise ValueError('Referenced unknown tables: '+str(missing))
if len(tables)!=27:raise AssertionError('Expected 27 tables, got '+str(len(tables)))
if len(set((r['table'],r['field']) for r in rows))!=len(rows):raise AssertionError('Duplicate columns')
fields=set((r['table'],r['field']) for r in rows)
for fromtable,field,to,pk,kind in relations:
    if (to,pk) not in fields:raise AssertionError(f'Invalid target {to}.{pk}')
    if (fromtable,field) not in fields:raise AssertionError(f'Invalid source {fromtable}.{field}')
for dest,data in [(ROOT/'veri_sozlugu_27_tablo.csv',rows)]:
    with dest.open('w',newline='',encoding='utf-8-sig') as fh:
        writer=csv.DictWriter(fh,fieldnames=rows[0].keys());writer.writeheader();writer.writerows(data)
with (ROOT/'tum_iliskiler.csv').open('w',newline='',encoding='utf-8-sig') as fh:
    wr=csv.writer(fh);wr.writerow(['source_table','source_column','referenced_table','referenced_column','relationship']);wr.writerows(relations)
counts=defaultdict(int)
for row in rows:counts[row['table']]+=1
md=['# LogScope Veritabani Tasarimi - 27 Tablo','',
    '> Bu tasarim bir PostgreSQL 15+ semasidir. SQL dosyalarinin veritabaninda calistirilmasi bu ortamda test edilmemistir.',
    '',f'**Arastirma cekirdegi:** {sum(x.startswith("01") for x in tables.values())} tablo',
    f'**Urun / SaaS genisletmesi:** {sum(x.startswith("02") for x in tables.values())} tablo',
    f'**Toplam alan:** {len(rows)}','**Yabanci anahtar iliskisi:** '+str(len(relations)),'',
    '| Tablo | Katman | Sutun | Amac |','|---|---|---:|---|']
purpose={
'users':'Kimlik ve kimlik dogrulama', 'scenario_runs':'Normal/anormal trafik senaryolari',
'ingestion_batches':'Dosya aktarim surecleri', 'synthetic_sessions':'Anonim oturumlar', 'http_events':'Gizlilik filtreli HTTP olaylari',
'traffic_windows':'1 dakikalik zaman/rota ozellikleri', 'model_versions':'Model ve esik surumleri', 'learned_patterns':'PrefixSpan sik gecisleri',
'model_scores':'Her pencere icin M1-M4 skor', 'alarms':'Hibrit kararlardan alarm kayitlari',
'alarm_signals':'Alarmi aciklayan model sinyalleri', 'alarm_reviews':'Insan incelemesi ve notlar',
'evaluation_results':'B0-B2 test sonuc metrikleri', 'workspaces':'SaaS calisma alanlari',
'workspace_memberships':'Kullanici/alan rolleri', 'user_invitations':'Ekip davet akis tasarimi',
'password_reset_requests':'Sifre sifirlama jeton hashleri', 'api_credentials':'API anahtar ozeti (duz metin degil)',
'integrations':'Django, API, Locust, JSONL konfigurasyonlari', 'onboarding_progress':'Ilk kurulum adimlari',
'notifications':'Alarm/veri sistem bildirimleri', 'notification_preferences':'Kullanici bildirim tercihleri',
'report_exports':'Rapor isleri ve artefakt referanslari', 'audit_events':'Hareketlerin denetim izi',
'product_plans':'Gelecekteki plan tanimlari', 'workspace_subscriptions':'Gelecekteki abonelik durumu',
'invoices':'Gelecekteki fatura metadata (odeme yok)'}
for table,filename in tables.items():md.append(f'| `{table}` | {"Arastirma" if filename.startswith("01") else "Urun"} | {counts[table]} | {purpose.get(table,"")} |')
md+=['','## PK ve FK kurallari','',
 '- Ana tablolar icin `id` kimligi veya bilesik PK vardir.',
 '- Her FK, PostgreSQL `REFERENCES` bagiyla gercek tablolara baglidir.',
 '- `http_events.event_uid` benzersizdir; ayni olay ikinci kez eklenmemelidir.',
 '- Zaman/rota penceresi 1 dakika ile sinirlanmistir.',
 '- `dataset_split` egitim, dogrulama ve test olarak etiketlenir; model ozelliklerine etiket veya senaryo kimligi sokulmaz.',
 '- Abonelik ve odeme ekranlari icin tablolar ticari tasarimdir, gercek para akisi aktif degildir.',
 '', '## Gorece en kritik baglantilar','']
for a,b,c,d,k in relations:md.append(f'- `{a}.{b}` -> `{c}.{d}`')
(ROOT/'VERITABANI_TABLOLAR_VE_ILISKILER.md').write_text('\n'.join(md)+'\n',encoding='utf-8')
summary={'tables':len(tables),'core_tables':13,'product_tables':14,'fields':len(rows),'foreign_keys':len(relations),'verified_references':len(relations),'database_executed':False}
(ROOT/'schema_kontrol.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps(summary,indent=2))

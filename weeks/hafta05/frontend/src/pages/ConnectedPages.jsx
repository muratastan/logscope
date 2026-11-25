import React,{useState,useEffect} from 'react';
import {Badge,Card,PageHeader,KPI,Notice,Chart,AlarmTable,Empty,DownloadButton,Icon} from '../components/Common';
import {PublicLayout} from '../components/Layout';
import {demoTimeline,demoRouteCounts,modelStages,conditions,integrationTypes,formatTime,numeric} from '../data';
export {LandingPage,LoginPage,PricingPage,AlarmsPage,BillingPage} from './Pages';
import Week5DemoFlow from '../components/Week5DemoFlow';
import {apiRequest} from '../services/api';
const goto=p=>location.hash='#'+p;
const modeNote=app=><Notice warn>{app.connected?'Bu oturumda veriler sunucudan alınır. İlk grafikler sentetik başlangıç verileridir; deney sonuçları ayrı gösterilir.':'Yerel demo kullanıyorsunuz. Yaptığınız işlemler bu tarayıcıda saklanır; sunucu verisi değildir.'}</Notice>;
const errorText=x=>x?.message||String(x);
export function RegisterPage({app}){
 const [name,setName]=useState(''),[email,setEmail]=useState(''),[password,setPassword]=useState(''),[workspace,setWorkspace]=useState(''),[error,setError]=useState(''),[working,setWorking]=useState(false);
 async function submit(e){e.preventDefault();setError('');setWorking(true);try{await app.register({name,email,password,workspace});goto('/app/onboarding')}catch(e){setError(errorText(e))}finally{setWorking(false)}}
 return <PublicLayout><form className="form-panel" onSubmit={submit}><Badge tone="teal">Çalışan hesap oluşturma</Badge><h1>LogScope hesabı oluştur</h1><p>Çalışma alanı kurun ve verilerinizi yönetin. Sunucu gerektirir.</p>
  {[['Ad soyad',name,setName,'text'],['İş e-postası',email,setEmail,'email'],['Çalışma alanı adı',workspace,setWorkspace,'text']].map(([label,value,onChange,type])=><React.Fragment key={label}><label className="field-label">{label}</label><input className="input" type={type} required maxLength={140} value={value} onChange={e=>onChange(e.target.value)}/></React.Fragment>)}
  <label className="field-label">Parola (en az 8 karakter)</label><input className="input" type="password" minLength={8} maxLength={200} autoComplete="new-password" required value={password} onChange={e=>setPassword(e.target.value)}/>
  <button disabled={working||!app.online} className="btn primary full" style={{marginTop:22}}>{working?'Hesap oluşturuluyor...':'Hesap oluştur ve kurulum aç'}</button>{!app.online&&<Notice warn>Sunucuyu başlatın. HTML demo hesap oluşturamaz.</Notice>}{error&&<Notice warn>{error}</Notice>}<div className="auth-extra"><a href="#/login">Giriş yap</a><a href="#/pricing">Paketleri incele</a></div>
 </form></PublicLayout>
}
export function PasswordResetPage({app}){
 const [email,setEmail]=useState(''),[token,setToken]=useState(''),[password,setPassword]=useState(''),[sent,setSent]=useState(false),[result,setResult]=useState(''),[working,setWorking]=useState(false);
 async function request(e){e.preventDefault();setWorking(true);try{const r=await app.requestReset(email);setSent(true);setResult(r.message);if(r.demo_token)setToken(r.demo_token)}catch(e){setResult(errorText(e))}finally{setWorking(false)}}
 async function confirm(e){e.preventDefault();setWorking(true);try{await app.confirmReset(token,password);setResult('Şifre yenilendi. Yeni şifrenizle giriş yapabilirsiniz.');setSent(false);setToken('');setPassword('')}catch(e){setResult(errorText(e))}finally{setWorking(false)}}
 return <PublicLayout><div className="form-panel"><h1>Şifremi sıfırla</h1><p>Bu yerel prototipte e-posta servisi bağlı değildir. Geliştirme modunda oluşturulan tek kullanımlık kod ekranda gösterilir.</p>
 {!sent?<form onSubmit={request}><label className="field-label">E-posta</label><input className="input" type="email" required value={email} onChange={e=>setEmail(e.target.value)}/><button className="btn primary full" disabled={!app.online||working} style={{marginTop:20}}>Sıfırlama kodu oluştur</button></form>:
 <form onSubmit={confirm}><label className="field-label">Geliştirme kodu</label><input className="input" required value={token} onChange={e=>setToken(e.target.value)}/><label className="field-label">Yeni parola</label><input type="password" className="input" minLength={8} required value={password} onChange={e=>setPassword(e.target.value)}/><button className="btn primary full" disabled={working} style={{marginTop:20}}>Parolayı güncelle</button></form>}
 {result&&<Notice>{result}</Notice>}<div className="auth-extra"><a href="#/login">Girişe dön</a></div></div></PublicLayout>
}
export function OverviewPage({app}){
 const imported=Boolean(app.windowPoints?.length && (app.dashboard?.metrics?.importedEvents>0));
 const chart=imported?app.windowPoints:(app.dashboard?.timeline?.length?app.dashboard.timeline:app.timeline||demoTimeline);
 const total=imported?chart.reduce((s,v)=>s+v.requests,0):(app.dashboard?.metrics?.requests ?? chart.reduce((s,v)=>s+v.requests,0));
 const errors=imported?chart.reduce((s,v)=>s+v.errors,0)/Math.max(total,1)*100:(app.dashboard?.metrics?.errorRate ?? chart.reduce((s,v)=>s+v.errors,0)/Math.max(total,1)*100);
 const opens=app.dashboard?.metrics?.open ?? app.alarms.filter(x=>x.state==='Yeni'||x.state==='İnceleniyor').length;
 const latency=imported?Math.max(...chart.map(x=>x.p95_ms||0)):app.dashboard?.metrics?.p95 ?? 218;
 const routes=app.dashboard?.routes?.map(v=>[v.path,v.requests])||demoRouteCounts;
 const max=Math.max(...routes.map(r=>r[1]),1);
 return <><PageHeader title="Genel bakış" subtitle="Trafik görünürlüğü, alarm inceleme ve deney sonuçları tek çalışma alanında." actions={<a href="#/app/reports" className="btn">Raporları aç</a>}/>{modeNote(app)}
 <Week5DemoFlow app={app}/>
 <div className="kpi-grid"><KPI title="HTTP istek toplamı" value={numeric(total)} foot={imported?"Yüklenen JSONL olayları":"Sentetik gösterim"}/><KPI title="İnceleme bekleyen alarm" value={numeric(opens)} foot="Veri tabanı kaydı" icon="bell"/><KPI title="Hata oranı" value={Number(errors).toFixed(2)+'%'} foot={imported?"Yüklenen olayların hata oranı":"Örnek veri"} icon="chart"/><KPI title="Gecikme göstergesi" value={Math.round(latency)+' ms'} foot={imported?"En yüksek dakikalık p95":"Demo p95 gösterimi"} icon="clock"/></div>
 <div className="two-col"><Card title="HTTP istek eğrisi" description="Zamana göre gözlenen örnek istekler"><Chart points={chart}/></Card><Card title="Rota dağılımı" description="Temsili trafik profili">{routes.map(([route,count])=><div className="barline" key={route}><span className="mono">{route}</span><div className="track"><div className="fill" style={{width:(100*count/max).toFixed(1)+'%'}}/></div><strong>{numeric(count)}</strong></div>)}</Card></div>
 <Card className="space-top" title="Son alarmlar" description="Alarmı incelemek için satıra tıklayın" actions={<a href="#/app/alarms">Bütün alarmlar →</a>}><AlarmTable alarms={app.alarms.slice(0,6)} onOpen={id=>goto('/app/alarms/'+id)}/></Card>
 {app.latestExperiment&&<Card className="space-top" title="Son sentetik deney" description={'Toplam '+numeric(app.latestExperiment.data.total_http_requests)+' simüle HTTP isteği'}><div className="goal-grid">{Object.entries(app.latestExperiment.conditions).map(([code,m])=><div className="action-card" key={code}><small>{code} · Test F1</small><h2>{Number(m.f1).toFixed(3)}</h2></div>)}</div><a href="#/app/models" className="btn">Deney ayrıntıları →</a></Card>}</>;
}
export function TrafficPage({app}){
 const [range,setRange]=useState('24h'),[route,setRoute]=useState('Tümü');
 const imported=Boolean(app.windowPoints?.length);
 const all=imported?app.windowPoints:(app.timeline?.length?app.timeline:demoTimeline);
 const chart=range==='1h'?all.slice(imported?-60:-6):range==='6h'?all.slice(imported?-360:-36):all;
 const ev=(app.events||[]).filter(x=>route==='Tümü'||x.route_template===route);
 const total=chart.reduce((s,v)=>s+v.requests,0),errs=chart.reduce((s,v)=>s+v.errors,0);
 return <><PageHeader title="Trafik analizi" subtitle="İstek, hata, gecikme ve rota dağılımlarını inceleyin." actions={<a href="#/app/sources" className="btn">JSONL yükle</a>}/>{modeNote(app)}
 <div className="filters"><select className="select" value={range} onChange={e=>setRange(e.target.value)} style={{width:180}}><option value="1h">Son 1 saat</option><option value="6h">Son 6 saat</option><option value="24h">Son 24 saat</option></select><select className="select" value={route} onChange={e=>{setRoute(e.target.value);app.loadTrafficWindows?.(e.target.value)}} style={{width:200}}><option>Tümü</option>{(app.windowRoutes?.length?app.windowRoutes:demoRouteCounts.map(v=>v[0])).map(v=><option key={v}>{v}</option>)}</select><Badge tone="gold">Örnek trafik / içe aktarılan olaylar</Badge></div>
 <div className="kpi-grid"><KPI title="İstek" value={numeric(total)} foot={imported?"Yüklenmiş olaylar, dakika bazında":"Demo zaman aralığı"}/><KPI title="Hata" value={numeric(errs)} foot={imported?"4xx + 5xx gerçekleşen olay":"Demo hata sayısı"} icon="chart"/><KPI title="Rota" value={route==='Tümü'?'Tümü':route} foot="Filtre" icon="database"/><KPI title="Yüklenen olay" value={numeric(app.events?.length||0)} foot="Persist edilmiş kayıt" icon="database"/></div><Card title="Zaman içindeki HTTP trafiği"><Chart points={chart}/>{imported&&<p className="tiny muted">Yüklenmiş JSONL kayıtlarından dakikalık gerçek sayım. Son p95: {chart.at(-1)?.p95_ms??'-'} ms; 4xx: {chart.at(-1)?.count_4xx??0}; 5xx: {chart.at(-1)?.count_5xx??0}.</p>}</Card>
 <Card className="space-top" title="JSONL olayları" description="Gizlilik filtresinden geçen kayıtlar">{ev.length?<div className="table-scroll"><table className="data-table"><thead><tr><th>Zaman</th><th>Yöntem</th><th>Rota</th><th>HTTP</th><th>Gecikme (ms)</th></tr></thead><tbody>{ev.slice(0,50).map((x,i)=><tr key={x.uid||i}><td>{formatTime(x.occurred_at)}</td><td>{x.http_method}</td><td className="mono">{x.route_template}</td><td>{x.status_code}</td><td>{x.duration_ms}</td></tr>)}</tbody></table></div>:<Empty>Henüz JSONL kaydı bulunmuyor. Veri kaynaklarından bir dosya yükleyin.</Empty>}</Card></>;
}
export function ModelsPage({app}){
 const [windows,setWindows]=useState(1200),[requests,setRequests]=useState(100),[seed,setSeed]=useState(42),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const last=app.latestExperiment;
 async function run(){setError('');setBusy(true);try{await app.runExperiment({windows,requests_per_window:requests,seed})}catch(e){setError(errorText(e))}finally{setBusy(false)}}
 return <><PageHeader title="Model merkezi" subtitle="K-Means, DBSCAN, Isolation Forest, PrefixSpan ve bağlamlı karar katmanı." actions={<a href="#/app/reports" className="btn">Sonuç raporları</a>}/>
 <Notice warn>{last?'Aşağıdaki F1/FPR değerleri bu ortamda gerçekten çalıştırılmış, kontrollü SENTETİK araştırma deneyine aittir. Gerçek ağ trafiği veya doğrulanmış güvenlik performansı değildir.':'Henüz eğitim çalıştırılmadı. Butonla sentetik bir deney başlatabilir, veri bölünmesini ve model başarımını inceleyebilirsiniz.'}</Notice>
 {app.week5Research&&<Card className="space-top" title="Hafta 5 - M1/M2 gercek calistirilmis OFFLINE model karsilastirmasi" description="K-Means, DBSCAN, Robust Z-score ve Isolation Forest; etiketli istatistiksel simulasyon, canli HTTP degil.">
  <Notice warn>Bu tablo gercek Django/Locust HTTP tespiti anlamina gelmez. Test: onceki kodda dondurulmus ayri seed 97, esikler sadece validation seed 71 uzerinden.</Notice>
  <div className="table-scroll"><table className="data-table"><thead><tr><th>Model</th><th>F1</th><th>Recall</th><th>FPR</th><th>Balanced Accuracy</th></tr></thead><tbody>{(app.week5Research.primary?.results||[]).map((x)=><tr key={x.model}><td>{x.model}</td><td>{Number(x.f1).toFixed(3)}</td><td>{Number(x.recall).toFixed(3)}</td><td>{(100*Number(x.fpr)).toFixed(2)}%</td><td>{Number(x.balanced_accuracy).toFixed(3)}</td></tr>)}</tbody></table></div>
  <p className="tiny muted">Tek holdout bolumu seed 97, testteki 240 dakikadir. Bu sonuclar canli LogScope basarisi sayilmaz.</p>
  <h4>Bes farkli OFFLINE simule tekrar - veri ureticisi farkli, capraz ortam basarisi garanti degil</h4>
  <div className="table-scroll"><table className="data-table"><thead><tr><th>Model</th><th>Ortalama F1</th><th>F1 standart sapma</th><th>Ortalama FPR</th></tr></thead><tbody>{(app.week5Research.summary||[]).map((x)=><tr key={x.model}><td>{x.model}</td><td>{Number(x.f1_mean).toFixed(3)}</td><td>{Number(x.f1_std).toFixed(3)}</td><td>{(100*Number(x.fpr_mean)).toFixed(1)}%</td></tr>)}</tbody></table></div>
  <Notice warn>Farkli bir simule ureticide Isolation Forest basarisi dusuyor. Bu, genelleme sorunudur; yalnizca ilk tablodaki yuksek F1 secilerek raporlanmamalidir.</Notice>
 </Card>}
 <div className="models-four">{modelStages.map(m=><div className="model-tile" key={m.code}><div className="model-logo"><Icon name="layers"/></div><Badge>{m.code} · {last?'Deney çalıştı':'Planlandı'}</Badge><h3>{m.title}</h3><p>{m.about}</p><hr/><strong className="small">{m.alg}</strong></div>)}</div>
 <Card className="space-top" title="Kontrollü sentetik deney çalıştır" description="8 senaryo, kronolojik %60 eğitim / %20 doğrulama / %20 bağımsız test">
 <div className="filters"><label>1 dakikalık pencere<br/><input className="input" type="number" min="120" max="2400" value={windows} onChange={e=>setWindows(Number(e.target.value))}/></label><label>Pencere başına istek<br/><input className="input" type="number" min="10" max="500" value={requests} onChange={e=>setRequests(Number(e.target.value))}/></label><label>Rastgele tohum<br/><input className="input" type="number" min="0" value={seed} onChange={e=>setSeed(Number(e.target.value))}/></label><button className="btn primary" disabled={!app.connected||busy||app.busy} onClick={run}>{busy?'Eğitim çalışıyor...':'M1–M4 eğitimini ve değerlendirmeyi çalıştır'}</button></div>
 {!app.connected&&<Notice warn>Bu işlem için sunucuyu açıp demo hesabıyla giriş yapın.</Notice>}{error&&<Notice warn>{error}</Notice>}
 </Card>
 <Card className="space-top" title="Model mimarisi"><div className="model-flow">{modelStages.map(m=><div className="flow-cell" key={m.code}><div className="code">{m.code}</div><h4>{m.title}</h4><small>{m.alg}</small></div>)}</div><div className="logic-row">B0 · B1 · B1+D · B1+S · B2 → Test kümesinde karşılaştırma</div></Card>
 {last?<><div className="kpi-grid"><KPI title="Toplam sentetik istek" value={numeric(last.data.total_http_requests)} foot="Gerçek HTTP isteği değil"/><KPI title="Zaman penceresi" value={numeric(last.data.windows)} foot="1 dakika"/><KPI title="Test penceresi" value={numeric(last.data.test_windows)} foot="Kronolojik bölüm"/><KPI title="Eğitim süresi" value={last.elapsed_ms+' ms'} foot="Yerel işlem süresi"/></div>
 <Card title="Beş deney koşulunun ölçülen sonuçları" description="F1 ≥ 0,80 ve FPR ≤ %5 önceden belirlenmiş HEDEFLERDİR; sonuçlar garanti edilmez."><div className="table-scroll"><table className="data-table"><thead><tr><th>Koşul</th><th>F1</th><th>Precision</th><th>Recall</th><th>Normal FPR</th><th>PR-AUC</th><th>Alarm</th></tr></thead><tbody>{Object.entries(last.conditions).map(([code,m])=><tr key={code}><td><strong>{code}</strong></td><td>{m.f1.toFixed(3)}</td><td>{m.precision.toFixed(3)}</td><td>{m.recall.toFixed(3)}</td><td>{(m.normal_fpr*100).toFixed(1)}%</td><td>{m.pr_auc}</td><td>{m.alarms}</td></tr>)}</tbody></table></div></Card>
 <Card className="space-top" title="PrefixSpan ile bulunan örüntüler" description="Yalnız normal eğitim oturumlarından öğrenildi."><div className="table-scroll"><table className="data-table"><thead><tr><th>Rota dizisi</th><th>Destek sayısı</th><th>Göreli destek</th></tr></thead><tbody>{last.learned_patterns.slice(0,9).map((p,i)=><tr key={i}><td className="mono">{p.sequence.join(' → ')}</td><td>{p.support_count}</td><td>{(100*p.relative_support).toFixed(2)}%</td></tr>)}</tbody></table></div></Card></>:
 <div className="half-col space-top"><Card title="Beş deney koşulu">{conditions.map((x,i)=><div className="settings-row" key={x}><b>{x}</b><span>{['Sabit eşik','Isolation Forest','M2 + yoğunluk','M2 + örüntü','Tam hibrit'][i]}</span><Badge tone="grey">Bekliyor</Badge></div>)}</Card><Card title="Başarım hedefleri">{[['F1','≥ 0,80'],['Normal FPR','≤ %5'],['API p95','< 800 ms'],['Panel güncelleme p95','≤15 sn']].map(([k,v])=><div className="settings-row" key={k}><b>{k}</b><span>{v}</span></div>)}</Card></div>}
 </>;
}
export function SourcesPage({app}){
 const [status,setStatus]=useState(''),[working,setWorking]=useState(false),[analyzing,setAnalyzing]=useState(false);
 async function upload(e){const file=e.target.files?.[0];if(!file)return;setWorking(true);try{setStatus(await app.importFile(file))}catch(err){setStatus('Hata: '+errorText(err))}finally{setWorking(false);e.target.value=''}}
 return <><PageHeader title="Veri kaynakları" subtitle="Gizlilik filtresinden geçen HTTP JSONL kayıtları." actions={<button className="btn" onClick={app.downloadSample}>Örnek JSONL indir</button>}/>{modeNote(app)}<div className="half-col"><Card title="JSONL dosyası yükle" description="Üst sınır 50 MiB / 160.000 satır"><div className="upload"><Icon name="upload" size={34}/><b>{working?'İşleniyor...':'Dosyanızı seçin'}</b><input type="file" accept=".jsonl" aria-label="JSONL dosyası" onChange={upload}/></div>{status&&<Notice>{status}</Notice>}<Notice warn>Ham IP, çerez, parola, erişim tokenı, HTTP body ve query alanları reddedilir.</Notice></Card>
 <Card title="JSONL sözleşmesi"><pre className="jsonbox">{JSON.stringify({event_uid:'uuid-001',occurred_at:'2026-10-28T14:00:00Z',http_method:'GET',route_template:'/catalog/',status_code:200,duration_ms:136.5,session_ref:'anon-session',schema_version:'1.0'},null,2)}</pre></Card></div>
 <Card className="space-top" title="Yüklenen kayıtları M1–M4 ile analiz et" description="En az 30 farklı dakika için anonim log gereklidir; etiket bulunmadığında F1 üretilmez."><button className="btn primary" disabled={!app.connected||analyzing} onClick={async()=>{setAnalyzing(true);try{await app.analyzeIngested()}catch(err){setStatus('Analiz: '+errorText(err))}finally{setAnalyzing(false)}}}>{analyzing?'Kayıtlar analiz ediliyor...':'Yüklenen logları analiz et →'}</button>{!app.connected&&<Notice warn>Çalışan FastAPI sunucusu ve giriş oturumu gerekir.</Notice>}{app.uploadedAnalysis&&<><Notice>Kaydedilmiş JSONL kayıtları: {numeric(app.uploadedAnalysis.data.events)} · Dakika: {app.uploadedAnalysis.data.minutes} · Keşifsel uyarı: {app.uploadedAnalysis.total_alerts}</Notice><div className="table-scroll"><table className="data-table"><thead><tr><th>Dakika</th><th>M1</th><th>M2</th><th>M3</th><th>M4</th><th>Gerekçe</th></tr></thead><tbody>{app.uploadedAnalysis.alarms.slice(0,12).map((x,i)=><tr key={i}><td>{formatTime(x.minute)}</td><td>{x.m1}</td><td>{x.m2}</td><td>{x.m3}</td><td>{x.score}</td><td>{x.reason}</td></tr>)}</tbody></table></div></>}</Card>
 <Card className="space-top" title="İçe aktarma geçmişi" description="Veri tabanındaki dosya aktarım kayıtları">{app.imports?.length?<div className="table-scroll"><table className="data-table"><thead><tr><th>Dosya</th><th>Kabul</th><th>Ret</th><th>Zaman</th></tr></thead><tbody>{app.imports.map((v,i)=><tr key={v.id||i}><td>{v.name}</td><td>{v.accepted}</td><td>{v.rejected}</td><td>{formatTime(v.date)}</td></tr>)}</tbody></table></div>:<Empty>Henüz dosya yüklemesi yok.</Empty>}</Card></>;
}
export function ReportsPage({app}){
 const last=app.latestExperiment;
 return <><PageHeader title="Raporlama" subtitle="Alarm, trafik ve sentetik model deneyleri için dışa aktarım." actions={<button className="btn" onClick={()=>window.print()}>PDF yazdır</button>}/>{modeNote(app)}
 <div className="three-col">{[['Alarm CSV','alarms'],['Trafik CSV','traffic'],['Deney sonuçları CSV','experiments'],['Yüklenen log analizi CSV','ingested']].map(([title,kind])=><Card key={kind} title={title} description="Veri tabanında kayıtlı verileri CSV indir"><button className="btn primary" onClick={()=>app.downloadReport(kind)} disabled={!app.connected&&kind!=='alarms'}>CSV indir →</button></Card>)}</div>
 <Card className="space-top" title="Deney geçmişi" description="Yalnız tamamlanan sentetik çalıştırmalar">{app.experiments?.length?<div className="table-scroll"><table className="data-table"><thead><tr><th>Koşu</th><th>Başlangıç</th><th>Pencere</th><th>Simüle istek</th><th>Çalışma süresi</th></tr></thead><tbody>{app.experiments.map(x=><tr key={x.id}><td>{x.id}</td><td>{formatTime(x.started_at)}</td><td>{x.windows}</td><td>{numeric(x.requests)}</td><td>{x.duration_ms} ms</td></tr>)}</tbody></table></div>:<Empty>Henüz deney yok. Model merkezinde ilk çalışmayı başlatın.</Empty>}</Card>
 <Card className="space-top" title="Araştırma yöntemi"><Chart points={app.timeline?.length?app.timeline:demoTimeline}/><Notice warn>Sentetik deney ölçümleri üretim ortamı performansını temsil etmez. Başarım hedefleri: F1 ≥0,80; normal FPR ≤%5; API p95 &lt;800ms; panel p95 ≤15sn.</Notice></Card></>;
}
export function SettingsPage({app}){
 const [name,setName]=useState(app.settings?.name||'Demo Workspace'),[tz,setTz]=useState(app.settings?.timezone||'Europe/Istanbul'),[days,setDays]=useState(app.settings?.retention_days||30),[busy,setBusy]=useState(false);
 useEffect(()=>{setName(app.settings?.name||'Demo Workspace');setTz(app.settings?.timezone||'Europe/Istanbul');setDays(app.settings?.retention_days||30)},[app.settings?.name,app.settings?.timezone,app.settings?.retention_days]);
 async function submit(e){e.preventDefault();setBusy(true);try{await app.saveSettings({name,timezone:tz,retention_days:Number(days)})}catch(err){app.notify(errorText(err))}finally{setBusy(false)}}
 return <><PageHeader title="Ayarlar" subtitle="Çalışma alanı ve veri saklama seçenekleri."/>{modeNote(app)}<div className="half-col"><Card title="Çalışma alanını düzenle"><form onSubmit={submit}><label className="field-label">Ad</label><input className="input" required value={name} onChange={e=>setName(e.target.value)}/><label className="field-label">Saat dilimi</label><select className="select" value={tz} onChange={e=>setTz(e.target.value)}><option>Europe/Istanbul</option><option>UTC</option></select><label className="field-label">Saklama (gün)</label><input type="number" min="1" max="365" className="input" value={days} onChange={e=>setDays(e.target.value)}/><button className="btn primary" disabled={busy} style={{marginTop:20}}>Ayarları kaydet</button></form><button className="btn" onClick={()=>{if(confirm('Demo verileri sıfırlansın mı?'))app.resetDemo()}} style={{marginTop:17}}>Demo kayıtlarını sıfırla</button></Card>
 <Card title="Yönetsel alanlar">{[['Ekip ve roller','team'],['Entegrasyonlar','integrations'],['Bildirim merkezi','notifications'],['Abonelik','billing'],['İlk kurulum','onboarding']].map(([label,slug])=><div className="settings-row" key={slug}><b>{label}</b><a href={'#/app/'+slug}>Aç →</a></div>)}</Card></div></>;
}
export function OnboardingPage({app}){
 const [step,setStep]=useState(app.step||0),[name,setName]=useState(app.settings?.name||'Demo Workspace'),[source,setSource]=useState('jsonl'),[privacy,setPrivacy]=useState(false),[busy,setBusy]=useState(false);
 const sections=[['Çalışma alanı','Alan adını tanımlayın'],['Veri kaynağı','Django ya da JSONL bağlantısı seçin'],['Gizlilik','Hassas alanların filtrelendiğini doğrulayın'],['İlk analiz','Model merkezinden sentetik deneyi çalıştırın']];
 async function next(){if(step===2&&!privacy){app.notify('Gizlilik onayını işaretleyin.');return}if(step===3){goto('/app/models');return}setBusy(true);try{await app.saveOnboarding({step:step+1,workspace_name:name,source_type:source,privacy_checked:privacy});setStep(step+1)}catch(e){app.notify(errorText(e))}finally{setBusy(false)}}
 return <><PageHeader title="İlk kurulum" subtitle="Çalışma alanı ve güvenli veri hattı kurulumu."/>{modeNote(app)}<div className="flow-steps">{sections.map(([label],i)=><button key={i} className={'flow-step '+(i===step?'active':i<step?'done':'')} onClick={()=>setStep(i)}><b>{i+1}</b>{label}</button>)}</div>
 <div className="half-col"><Card title={sections[step][0]} description={sections[step][1]}>{step===0?<><label className="field-label">Çalışma alanı adı</label><input className="input" value={name} onChange={e=>setName(e.target.value)}/></>:step===1?<><label className="field-label">Kaynak</label><select className="select" value={source} onChange={e=>setSource(e.target.value)}><option value="jsonl">JSONL dosya</option><option value="django">Django Middleware</option><option value="rest_api">REST API (taslak)</option></select><Notice>Gerçek ağ bağlantısı yalnızca entegrasyon ayarları hazır olduğunda etkinleşebilir.</Notice></>:step===2?<><label className="checkline"><input type="checkbox" checked={privacy} onChange={e=>setPrivacy(e.target.checked)}/> IP, token, parola ve HTTP gövdesi alanları saklanmayacak.</label></>:<Notice>Kontrollü sentetik deney için Model Merkezi'ni açabilirsiniz.</Notice>}
 <div className="hero-actions" style={{marginTop:28}}><button className="btn" onClick={()=>setStep(Math.max(step-1,0))} disabled={step===0}>Geri</button><button className="btn primary" onClick={next} disabled={busy}>{step===3?'Model merkezini aç':'Kaydet ve devam et'}</button></div></Card>
 <Card title="Kurulum kontrol listesi">{sections.map(([label,detail],i)=><div className="checkline" key={i}><span>{i<step?'✓':i+1}</span><div><strong>{label}</strong><p className="small muted">{detail}</p></div></div>)}</Card></div></>;
}
export function IntegrationsPage({app}){
 const providers=['django','rest_api','locust','postgresql','jsonl','webhook'];
 const configured=Object.fromEntries((app.integrations||[]).map(i=>[i.provider,i]));
 return <><PageHeader title="Entegrasyonlar" subtitle="Veri giriş kaynakları ve entegrasyon taslaklarını yönetin."/>{modeNote(app)}<div className="card-grid-3">{integrationTypes.map((v,i)=>{const existing=configured[providers[i]];return <Card key={v[0]} title={v[0]} description={v[1]} className="integr-card"><div className="mini-logo"><Icon name="link"/></div><Badge tone={existing?.status==='configured'?'teal':'gold'}>{existing?.status==='configured'?'Yapılandırma kaydedildi':'Taslak'}</Badge><button className="btn" onClick={async()=>{try{await app.integration(providers[i],v[0],existing?.status==='configured'?'draft':'configured')}catch(e){app.notify(errorText(e))}}}>{existing?.status==='configured'?'Taslağa döndür':'Yapılandırma taslağını kaydet'}</button></Card>})}</div><Card title="Entegrasyon güvenliği" className="space-top"><Notice>Bu ekran gerçek servis anahtarı veya URL bağlantısı oluşturmaz. Gizli anahtarları prototipe girmeyin.</Notice></Card></>;
}
export function TeamPage({app}){
 const [email,setEmail]=useState(''),[role,setRole]=useState('analyst'),[busy,setBusy]=useState(false);
 async function submit(e){e.preventDefault();setBusy(true);try{await app.invite(email,role);setEmail('')}catch(err){app.notify(errorText(err))}finally{setBusy(false)}}
 return <><PageHeader title="Ekip ve yetkiler" subtitle="Çalışma alanı üyeleri, roller ve davet taslakları."/>{modeNote(app)}<Card title="Ekip üyeleri" description="Üye davetleri kaydedilir, gerçek e-posta gönderilmez."><form className="filters" onSubmit={submit}><input className="input" type="email" placeholder="kullanici@kurum.com" required value={email} onChange={e=>setEmail(e.target.value)} style={{maxWidth:350}}/><select className="select" value={role} onChange={e=>setRole(e.target.value)}><option value="analyst">Analist</option><option value="reviewer">İnceleyici</option><option value="admin">Yönetici</option></select><button className="btn primary" disabled={busy}>Davet taslağı oluştur</button></form><div className="table-scroll"><table className="data-table"><thead><tr><th>E-posta</th><th>Rol</th><th>Durum</th></tr></thead><tbody>{(app.members||[]).map((m,i)=><tr key={i}><td>{m.email}</td><td>{m.role}</td><td><Badge tone="teal">{m.state||'Etkin'}</Badge></td></tr>)}</tbody></table></div></Card><Card title="Rol bazlı yetkilendirme" className="space-top">{[['Yönetici','Ayarlar, ekip ve entegrasyonlar'],['Analist','Trafik, model, alarm, raporlama'],['İnceleyici','Alarm inceleme ve notlar']].map(([k,v])=><div className="settings-row" key={k}><b>{k}</b><span>{v}</span></div>)}</Card></>;
}
export function NotificationsPage({app}){
 const [unread,setUnread]=useState(false);const items=(app.notifications||[]).filter(n=>!unread||!n.read);
 return <><PageHeader title="Bildirim merkezi" subtitle="Alarm, veri yükleme ve deney bildirimleri." actions={<button className="btn" onClick={app.markAllRead}>Tümünü okundu işaretle</button>}/>{modeNote(app)}<div className="filters"><label><input type="checkbox" checked={unread} onChange={e=>setUnread(e.target.checked)}/> Yalnız okunmamış</label></div><Card title="Son bildirimler" description={'Gösterilen: '+items.length}>{items.length?<div className="notify-feed">{items.map(n=><div className={'notify-item '+(!n.read?'unread':'')} key={n.id}><span className="dot"/><div className="note-body"><h3>{n.title}</h3><p>{n.text}</p></div><time>{n.date&&n.date!=='Demo'?formatTime(n.date):n.date}</time><button className="btn small" onClick={()=>app.toggleNotification(n.id)}>{n.read?'Okunmadı':'Okundu'}</button></div>)}</div>:<Empty>Bildirim bulunamadı.</Empty>}</Card></>;
}
const guideData=[
 ['Hızlı başlangıç','Giriş yapın; ilk kurulumda çalışma alanını ve JSONL kaynağını seçin. Veri kaynaklarında örnek JSONL dosyasını indirin; yükleme sonrasında trafik ve alarm sayfalarını inceleyin.'],
 ['JSONL veri sözleşmesi','Alanlar: event_uid, occurred_at (UTC ISO-8601), http_method, route_template, status_code, duration_ms, session_ref, schema_version. Ham IP, parola, token, çerez, body ve query saklanmaz.'],
 ['Alarm inceleme','Alarm Merkezi listesinden bir satır açın. M1, M2, M3 skorlarını ve açıklamayı değerlendirin. İnceleme durumunu seçip gerekçeli not kaydedin. İşlem veri tabanına yazılır.'],
 ['Model merkezi','M1: K-Means ve DBSCAN trafik kümelemesi; M2: Isolation Forest sapması; M3: PrefixSpan sıra örüntüleri; M4: karar birleşimi. Eğitim verisi yalnız normal pencerelerden seçilir. Eşik doğrulamada belirlenir.'],
 ['Raporlama','Raporlar ekranından alarm, trafik ve deney CSV dosyalarını indirebilirsiniz. Deney verileri kontrollü simülasyona aittir; üretim ölçümleri değildir.'],
 ['Gizlilik','Sistem yalnız izin verilen alanları kabul eder. Olay akışlarında ham IP, cookie, token, yetkilendirme başlığı veya HTTP gövdesi kalıcı olarak saklanmaz.']
];
export function HelpPage({app}){
 const [query,setQuery]=useState(''),[active,setActive]=useState(-1);
 const filtered=guideData.filter(g=>g.join(' ').toLocaleLowerCase('tr').includes(query.toLocaleLowerCase('tr')));
 return <><PageHeader title="Yardım merkezi" subtitle="Gerçek kullanım kılavuzları ve sık sorulan sorular."/><Card title="Kılavuzlarda ara"><input className="input" value={query} onChange={e=>setQuery(e.target.value)} placeholder="Kurulum, veri şeması, alarm..."/></Card><div className="card-grid-3 space-top">{filtered.map(([title,body])=>{const i=guideData.findIndex(x=>x[0]===title);return <Card key={title} title={title} description={body.slice(0,70)+'...'}><button className="btn" onClick={()=>setActive(active===i?-1:i)}>{active===i?'Kapat':'Kılavuzu aç →'}</button>{active===i&&<p style={{marginTop:18,lineHeight:1.7}}>{body}</p>}</Card>})}</div><Card className="space-top" title="Sık sorulan sorular"><details className="faq-card"><summary>Bir model sonucu ne zaman gerçek sayılır?</summary><p>Model merkezindeki deney çalıştırılırsa gerçek hesaplama yapılır; ancak kullanılan veri sentetiktir. Gerçek Django/Locust trafik deneyleri ayrıca yürütülmelidir.</p></details><details className="faq-card"><summary>JSONL yüklemesinde veri güvenliği nasıl sağlanır?</summary><p>Backend yalnız izin verilen beyaz liste alanlarını doğrular. Diğer anahtarlar saklanmaz, ilgili kayıt reddedilir.</p></details><details className="faq-card"><summary>Ödeme ve e-posta özellikleri aktif mi?</summary><p>Hayır. Üyelik yerel FastAPI sunucusunda saklanır; davet e-postası ve ödeme tahsilatı yapılmaz.</p></details></Card></>;
}


export function AlarmDetailPage({app,id}) {
  const [remote,setRemote]=useState(null);
  const [loading,setLoading]=useState(false);
  const [error,setError]=useState('');
  const [status,setStatus]=useState('Yeni');
  const [note,setNote]=useState('');
  const [saving,setSaving]=useState(false);
  const connected=Boolean(app.connected);
  useEffect(()=>{
    let active=true;
    setRemote(null);setError('');
    if(!connected)return()=>{active=false};
    setLoading(true);
    apiRequest('/alarms/'+encodeURIComponent(id)).then(row=>{
      if(!active)return;
      setRemote(row);setStatus(row.state||'Yeni');setNote(row.notes||'');
    }).catch(e=>{if(active)setError(e.message)}).finally(()=>{if(active)setLoading(false)});
    return()=>{active=false};
  },[id,connected]);
  const listed=(app.alarms||[]).find(x=>x.id===id);
  const a=connected?(remote||listed):listed;
  if(loading&&!a)return <Notice>Alarm ayrıntıları sunucudan yükleniyor…</Notice>;
  if(!a)return <Notice warn>Alarm bulunamadı. {error}</Notice>;
  const evidence=typeof a.evidence==='string'?(()=>{try{return JSON.parse(a.evidence)}catch{return {}}})():a.evidence||{};
  async function save(){
    setSaving(true);setError('');
    try{
      await app.saveReview(a.id,status,note);
      if(connected){const row=await apiRequest('/alarms/'+encodeURIComponent(id));setRemote(row);setStatus(row.state||'Yeni');setNote(row.notes||'');}
    }catch(e){setError(e.message)}finally{setSaving(false)}
  }
  return <>
    <PageHeader title={'Alarm '+a.id} subtitle={(a.reason||'Alarm incelemesi')+' · '+formatTime(a.occurred_at)} actions={<a href="#/app/alarms" className="btn">← Alarm merkezine dön</a>}/>
    <Notice warn>{connected?'Bu alarmın durumu, inceleme notu ve kanıtı FastAPI üzerinden okunur. Kayıtlar çalışma alanınızla sınırlıdır.':'Yerel demo kullanılıyor; kayıtlar tarayıcıda kalır ve gerçek alarm doğruluğu iddia edilmez.'}</Notice>
    {error&&<Notice warn>İşlem hatası: {error}</Notice>}
    <div className="two-col">
      <Card title="Alarm açıklaması ve kanıt" actions={<Badge tone="gold">{Math.round(Number(a.score||0)*100)}% anomali puanı</Badge>}>
        <dl className="detail-list">{[['Rota',a.route],['Gerekçe',a.reason],['Önem',a.severity],['İnceleme durumu',a.state],['Zaman',formatTime(a.occurred_at)]].map(([k,v])=><React.Fragment key={k}><dt>{k}</dt><dd>{v||'–'}</dd></React.Fragment>)}</dl>
        <h3>Model sinyalleri</h3>
        <div className="signals">{[['M1 · Trafik profili',a.m1],['M2 · Isolation Forest',a.m2],['M3 · Oturum örüntüsü',a.m3]].map(([label,value])=><div key={label}>
          <div className="signal-top"><span>{label}</span><strong>{Math.round(Number(value||0)*100)}%</strong></div>
          <div className="progress"><div className="value" style={{width:Math.max(0,Math.min(100,Math.round(Number(value||0)*100)))+'%'}}/></div>
        </div>)}</div>
        <h3>Sunucudan gelen kanıt</h3>
        <pre className="jsonbox">{JSON.stringify(evidence,null,2)}</pre>
      </Card>
      <div>
        <Card title="Analist incelemesi" description="Seçilen durum ve not FastAPI üzerinden kaydedilir.">
          <label className="field-label" htmlFor="inceleme-durumu">Durum</label>
          <select id="inceleme-durumu" className="select" value={status} onChange={e=>setStatus(e.target.value)}>{['Yeni','İnceleniyor','Doğrulandı','Yanlış alarm'].map(v=><option key={v}>{v}</option>)}</select>
          <label className="field-label" htmlFor="inceleme-notu">İnceleme notu</label>
          <textarea id="inceleme-notu" className="textarea" maxLength="800" value={note} onChange={e=>setNote(e.target.value)} placeholder="Gerekçeli değerlendirme yazın"/>
          <button className="btn primary full" type="button" disabled={saving} style={{marginTop:14}} onClick={save}>{saving?'Kaydediliyor…':'İncelemeyi kaydet'}</button>
        </Card>
        <Card className="space-top" title="İnceleme geçmişi">{a.reviews?.length?<div>{a.reviews.map((r,i)=><p className="small" key={r.id||i}><b>{r.state}</b> · {r.note||'Not eklenmedi'} · {r.created_at?formatTime(r.created_at):''}</p>)}</div>:<Empty>Henüz inceleme kaydı bulunmuyor.</Empty>}</Card>
      </div>
    </div>
  </>;
}

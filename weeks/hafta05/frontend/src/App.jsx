import React,{useCallback,useEffect,useState} from 'react';
import {ProductLayout} from './components/Layout';
import {demoAlarms,demoTimeline,safeSample} from './data';
import {apiRequest,downloadText,downloadBlob} from './services/api';
import {LandingPage,LoginPage,RegisterPage,PasswordResetPage,PricingPage,OverviewPage,TrafficPage,ModelsPage,AlarmsPage,AlarmDetailPage,SourcesPage,ReportsPage,SettingsPage,OnboardingPage,IntegrationsPage,TeamPage,NotificationsPage,HelpPage,BillingPage} from './pages/ConnectedPages';

const STORE='logscope-react-mvp-v2';
const START_NOTIFICATIONS=[{id:1,title:'Örnek alarm bildirimi',text:'Sentetik trafik analizi',date:'Demo',kind:'alarm',read:false}];
function seed(){return {alarms:demoAlarms.map(a=>({...a,source:'demo'})),timeline:demoTimeline,events:[],imports:[],members:[{email:'demo@logscope.local',role:'owner',state:'Etkin'}],invitations:[],notifications:START_NOTIFICATIONS,integrations:[],latestExperiment:null,experiments:[],settings:{name:'Demo Workspace',timezone:'Europe/Istanbul',retention_days:30},draft:{},step:0,demo:true};}
function loaded(){try{const obj=JSON.parse(localStorage.getItem(STORE)||'{}');return obj&&typeof obj==='object'?obj:{}}catch{return {}}}
const allowed=new Set(['event_uid','occurred_at','http_method','route_template','status_code','duration_ms','session_ref','schema_version']);
function validEvent(v){if(!v||typeof v!=='object'||Array.isArray(v))return false;
 if(Object.keys(v).some(x=>!allowed.has(x)))return false;
 return typeof v.event_uid==='string' && /^[-\w.]{1,96}$/.test(v.event_uid) && /^\/[\w/{}/-]{0,150}$/.test(v.route_template||'')&&
 ['GET','POST','PUT','PATCH','DELETE','HEAD','OPTIONS'].includes(v.http_method) && Number.isInteger(v.status_code)&&v.status_code>=100&&v.status_code<=599&&
 Number.isFinite(v.duration_ms)&&v.duration_ms>=0&&typeof v.occurred_at==='string'&&!Number.isNaN(Date.parse(v.occurred_at));
}
const sampleCSV=[['id','reason','route','severity','score','state'],...demoAlarms.map(a=>[a.id,a.reason,a.route,a.severity,a.score,a.state])];
function csvCell(v){let s=String(v??'');if(/^[\s]*[+=@\-]/.test(s))s="'"+s;return '"'+s.replaceAll('"','""')+'"';}
function saveLocalCSV(alarms){const h=['id','reason','route','severity','score','state'];downloadText('logscope_demo_alarmlar.csv',[h.join(','),...alarms.map(a=>h.map(k=>csvCell(a[k])).join(','))].join('\r\n'),'text/csv;charset=utf-8')}
export default function App(){
 const [page,setPage]=useState(location.hash.slice(1)||'/');
 const [data,setData]=useState(()=>({...seed(),...loaded()}));
 const [apiOnline,setApiOnline]=useState(false);
 const [connected,setConnected]=useState(false);
 const [initializing,setInitializing]=useState(true);
 const [notice,setNotice]=useState('');
 const [busy,setBusy]=useState(false);
 useEffect(()=>{const h=()=>setPage(location.hash.slice(1)||'/');window.addEventListener('hashchange',h);return()=>window.removeEventListener('hashchange',h)},[]);
 useEffect(()=>{try{localStorage.setItem(STORE,JSON.stringify(data))}catch{}},[data]);
 const notify=msg=>setNotice(msg);
 const mutate=(key,fn)=>setData(d=>({...d,[key]:fn(d[key])}));
 const refresh=useCallback(async()=>{
  const paths=['/dashboard','/alarms','/batches','/team','/notifications','/integrations','/models','/experiments','/onboarding','/settings','/traffic','/traffic/windows','/research/week5'];
  const ans=await Promise.allSettled(paths.map(p=>apiRequest(p)));
  const get=i=>ans[i].status==='fulfilled'?ans[i].value:null;
  const board=get(0),alerts=get(1),batch=get(2),team=get(3),notifs=get(4),integr=get(5),models=get(6),exps=get(7),onboard=get(8),settings=get(9),traffic=get(10),windows=get(11),week5research=get(12);
  setData(d=>({
    ...d,
    alarms:alerts?.alarms||d.alarms,
    timeline:board?.timeline||d.timeline,
    dashboard:board||d.dashboard,
    events:traffic?.events?.map(v=>({...v,http_method:v.method,route_template:v.route,status_code:v.status}))||d.events,
    windowPoints:windows?.points||d.windowPoints||[],windowRoutes:windows?.routes||d.windowRoutes||[],
    imports:batch?.batches?.map(v=>({...v,name:v.filename,date:v.created_at}))||d.imports,
    members:team? [...team.members.map(m=>({...m,state:'Etkin'})),...team.invitations.map(m=>({...m,email:m.email,state:'Davet taslağı'}))]:d.members,
    invitations:team?.invitations||d.invitations,
    notifications:notifs?.notifications?.map(n=>({...n,date:n.created_at}))||d.notifications,
    integrations:integr?.integrations||d.integrations,
    latestExperiment:models?.latest||d.latestExperiment,
    experiments:exps?.experiments||d.experiments,
    week5Research:week5research||d.week5Research,
    settings:settings||d.settings,
    step:onboard?.step??d.step,
    demo:false
  }));
  return ans;
 },[]);
 useEffect(()=>{let ignore=false;(async()=>{
    try{await apiRequest('/health');if(ignore)return;setApiOnline(true);
        try{const user=await apiRequest('/session');if(!ignore){setConnected(true);setData(d=>({...d,currentUser:user,demo:false}));await refresh();}}catch{}
    }catch{if(!ignore){setApiOnline(false);setConnected(false);}}
    if(!ignore)setInitializing(false);
  })();return()=>{ignore=true}},[refresh]);
 const login=async(email,password)=>{if(!apiOnline)throw new Error('Sunucu çalışmıyor. Yerel demo seçeneğini kullanabilirsiniz.');
   const r=await apiRequest('/login',{method:'POST',body:JSON.stringify({email,password})});setConnected(true);setData(d=>({...d,currentUser:r.user,demo:false}));await refresh();return r;};
 const register=async(payload)=>{if(!apiOnline)throw new Error('Gerçek kayıt için FastAPI sunucusunu başlatın.');
    const res=await apiRequest('/register',{method:'POST',body:JSON.stringify(payload)});setConnected(true);setData(d=>({...d,currentUser:res.user,demo:false}));await refresh();return res;};
 const logout=async()=>{if(connected)try{await apiRequest('/logout',{method:'POST'})}catch{}setConnected(false);setData(d=>({...d,currentUser:null,demo:true}));location.hash='#/login'};
 const useDemo=()=>{setConnected(false);setData(d=>({...d,demo:true}));};
 const loadTrafficWindows=async(route='Tümü')=>{
    if(!connected)return;
    const v=await apiRequest('/traffic/windows?route='+encodeURIComponent(route));
    setData(d=>({...d,windowPoints:v.points,windowRoutes:v.routes}));
  };
 const saveReview=async(id,status,note)=>{
   try{if(connected){await apiRequest('/alarms/'+encodeURIComponent(id)+'/review',{method:'POST',body:JSON.stringify({state:status,note})});await refresh();notify('Alarm kararı sunucudaki veri tabanına kaydedildi.');}
   else{mutate('alarms',a=>a.map(x=>x.id===id?{...x,state:status,notes:note,reviews:[...(x.reviews||[]),{state:status,note}]}:x));notify('Alarm kararı yalnızca yerel demoya kaydedildi.');}}
   catch(err){notify('Kayıt başarısız: '+err.message);throw err}
 };
 const importFile=async file=>{
   if(file.size>50*1024*1024)throw Error('En fazla 50 MiB JSONL yüklenebilir.');
   if(connected){const form=new FormData();form.append('file',file);const r=await apiRequest('/ingest',{method:'POST',body:form});await refresh();return `${r.accepted} kayıt sunucuya kaydedildi, ${r.rejected} satır reddedildi.`;}
   const lines=(await file.text()).split(/\r?\n/).filter(Boolean);if(lines.length>2000)throw Error('En fazla 2.000 satır.');
   let accepted=[],rejected=0;const uids=new Set();for(const line of lines){try{const v=JSON.parse(line);if(validEvent(v)&&!uids.has(v.event_uid)){accepted.push(v);uids.add(v.event_uid);}else rejected++;}catch{rejected++;}}
   setData(d=>({...d,events:[...accepted,...d.events].slice(0,2000),imports:[{name:file.name,accepted:accepted.length,rejected,date:new Date().toISOString()},...d.imports]}));return `${accepted.length} kayıt yalnızca yerel demoya alındı, ${rejected} reddedildi.`;
 };
 const analyzeIngested=async()=>{
   if(!connected)throw Error('Yüklenen log analizi için sunucu oturumu gerekir.');
   setBusy(true);try{
     const res=await apiRequest('/ingested/analyze',{method:'POST'});
     setData(d=>({...d,uploadedAnalysis:res.result}));
     notify(`${res.result.data.minutes} dakikalık yüklenmiş olay incelendi; ${res.result.total_alerts} keşifsel uyarı bulundu.`);
     return res.result;
   }finally{setBusy(false)}
 };
 const downloadSample=async()=>{if(connected){try{const blob=await apiRequest('/sample.jsonl');downloadBlob('logscope_ornek.jsonl',blob);return}catch{}}
   downloadText('logscope_ornek.jsonl',safeSample.map(v=>JSON.stringify(v)).join('\n')+'\n','application/x-ndjson');};
 const downloadReport=async(kind)=>{if(connected){try{const blob=await apiRequest('/export/'+kind+'.csv');downloadBlob('logscope_'+kind+'.csv',blob);return}catch(err){notify(err.message);return}}
   if(kind==='alarms')saveLocalCSV(data.alarms);else notify('Sunucu olmadan yalnızca alarm CSV demosu indirilebilir.');};
 const runExperiment=async(config)=>{if(!connected)throw Error('Gerçek sentetik model deneyi için sunucuya giriş yapmalısınız.');
   setBusy(true);try{const result=await apiRequest('/experiments/run',{method:'POST',body:JSON.stringify(config)});await refresh();notify(`Sentetik deney tamamlandı: ${result.result.data.windows} zaman penceresi değerlendirildi.`);return result.result;}
   finally{setBusy(false)} };
 const saveOnboarding=async(payload)=>{if(connected){await apiRequest('/onboarding',{method:'PUT',body:JSON.stringify(payload)});await refresh();}else{mutate('step',()=>payload.step);notify('Kurulum yalnızca yerel demoda ilerledi.');}};
 const saveSettings=async(payload)=>{if(connected){await apiRequest('/settings',{method:'PUT',body:JSON.stringify(payload)});await refresh();notify('Ayarlar veri tabanına kaydedildi.');}
 else{mutate('settings',()=>payload);notify('Ayarlar yalnızca yerel demoda değiştirildi.');}};
 const invite=async(email,role)=>{if(connected){const r=await apiRequest('/team/invitations',{method:'POST',body:JSON.stringify({email,role})});await refresh();notify('Davet taslağı veri tabanına kaydedildi. E-posta gönderilmedi.');return r;}
 mutate('members',v=>[...v,{email,role,state:'Yerel davet taslağı'}]);notify('Yerel davet taslağı eklendi; e-posta gönderilmedi.');};
 const integration=async(provider,name,status)=>{if(connected){await apiRequest('/integrations',{method:'POST',body:JSON.stringify({provider,name,status})});await refresh();notify('Entegrasyon taslağı kaydedildi. Harici servise bağlanılmadı.');}
 else{mutate('integrations',arr=>[...arr.filter(x=>x.provider!==provider),{provider,name,status}]);notify('Entegrasyon yerel demo taslağına eklendi.');}};
 const markAllRead=async()=>{if(connected){await apiRequest('/notifications/read-all',{method:'POST'});await refresh();}else mutate('notifications',v=>v.map(n=>({...n,read:true})));};
 const toggleNotification=async(id)=>{if(connected){await apiRequest('/notifications/'+id+'/toggle',{method:'POST'});await refresh();}else mutate('notifications',v=>v.map(n=>n.id===id?{...n,read:!n.read}:n));};
 const resetDemo=async()=>{if(connected){await apiRequest('/reset',{method:'POST'});await refresh();notify('Sunucudaki demo verileri sıfırlandı.');}
 else{setData(seed());notify('Yerel demo sıfırlandı.');}};
 const app={...data,online:apiOnline,connected,busy,initializing,notify,login,register,useDemo,logout,saveReview,importFile,loadTrafficWindows,downloadSample,
   exportAlarms:()=>downloadReport('alarms'),downloadReport,runExperiment,analyzeIngested,refresh,resetDemo,saveOnboarding,saveSettings,invite,integration,
   markAllRead,toggleNotification,requestReset:async email=>apiRequest('/password/reset/request',{method:'POST',body:JSON.stringify({email})}),
   confirmReset:async(token,new_password)=>apiRequest('/password/reset/confirm',{method:'POST',body:JSON.stringify({token,new_password})}),
   setStep:value=>mutate('step',()=>value),setDraft:value=>mutate('draft',()=>value)};
 const publicPages={'/':<LandingPage/>,'/login':<LoginPage app={app}/>,'/register':<RegisterPage app={app}/>,
 '/reset-password':<PasswordResetPage app={app}/>,'/pricing':<PricingPage/>};
 const appPages={'/app/overview':<OverviewPage app={app}/>,'/app/traffic':<TrafficPage app={app}/>,'/app/models':<ModelsPage app={app}/>,
 '/app/alarms':<AlarmsPage app={app}/>,'/app/sources':<SourcesPage app={app}/>,'/app/reports':<ReportsPage app={app}/>,
 '/app/settings':<SettingsPage app={app}/>,'/app/onboarding':<OnboardingPage app={app}/>,'/app/integrations':<IntegrationsPage app={app}/>,
 '/app/team':<TeamPage app={app}/>,'/app/notifications':<NotificationsPage app={app}/>,'/app/help':<HelpPage app={app}/>,'/app/billing':<BillingPage app={app}/>};
 const match=page.match(/^\/app\/alarms\/(LS-\d+|EXP-\d+-\d+)$/);
 let main;
 if(publicPages[page])main=publicPages[page];
 else if(page.startsWith('/app/')&&initializing)main=<div style={{padding:60}}>Çalışma alanı yükleniyor...</div>;
 else if(page.startsWith('/app/')&&apiOnline&&!connected&&!data.demo)main=<LoginPage app={app}/>;
 else main=<ProductLayout page={page} connected={connected} apiOnline={apiOnline} logout={logout} exportAlarms={()=>downloadReport('alarms')}><div className={connected?'connected-app':'local-demo-app'}>{match?<AlarmDetailPage app={app} id={match[1]}/>:appPages[page]||<div className="app-card">Sayfa bulunamadı. <a href="#/app/overview">Genel bakış</a></div>}</div></ProductLayout>;
 return <>{main}{notice&&<div role="status" className="toast" onClick={()=>setNotice('')} style={{position:'fixed',right:22,bottom:22,zIndex:100,maxWidth:450}}>{notice} · Kapat</div>}</>;
}

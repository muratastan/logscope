// Deterministic synthetic demonstration data; not trained model predictions.
export const routes = [
 ['/', 'Home'], ['/app/overview','Dashboard'], ['/app/traffic','Traffic'],
 ['/app/models','Models'], ['/app/alarms','Alerts'], ['/app/alarms/LS-1042','Alert detail'],
 ['/app/sources','Data sources'], ['/app/reports','Reports'], ['/app/settings','Settings'],
 ['/login','Login'], ['/register','Register'], ['/reset-password','Password reset'],
 ['/pricing','Pricing'], ['/app/onboarding','Onboarding'], ['/app/integrations','Integrations'],
 ['/app/team','Team'], ['/app/notifications','Notifications'], ['/app/help','Help'],
 ['/app/billing','Billing']
];
export const navItems = [
 ['overview','Genel bak\u0131\u015f','dashboard'], ['traffic','Trafik analizi','chart'],
 ['models','Model merkezi','layers'], ['alarms','Alarm merkezi','bell'],
 ['sources','Veri kaynaklar\u0131','database'], ['reports','Raporlar','file'],
 ['integrations','Entegrasyonlar','link'], ['team','Ekip ve roller','users'],
 ['notifications','Bildirimler','bell'], ['help','Yard\u0131m merkezi','info'],
 ['onboarding','\u0130lk kurulum','check'], ['billing','Abonelik','file'],
 ['settings','Ayarlar','settings']
];
const reasons=['Ba\u015far\u0131s\u0131z giri\u015f art\u0131\u015f\u0131','5xx hata oran\u0131nda sapma','Nadir rota ge\u00e7i\u015fi','Yan\u0131t gecikmesinde art\u0131\u015f','Yo\u011funluk profili sapmas\u0131'];
export const demoAlarms = Array.from({length:18},(_,i)=>({
 id:`LS-${1042-i}`,occurred_at:new Date(Date.UTC(2026,9,28,14)-i*33*60000).toISOString(),
 severity:['Kritik','Y\u00fcksek','Orta','D\u00fc\u015f\u00fck'][i%4],
 reason:reasons[i%5],route:['/auth/login/','/catalog/','/search/','/items/{id}/','/forms/checkout/'][i%5],
 score:Number((.89-(i%9)*.044).toFixed(3)),m1:.35+i%4*.12,m2:.84-i%3*.10,m3:.18+i%4*.16,
 state:i%5===0?'\u0130nceleniyor':i%9===0?'Do\u011fruland\u0131':'Yeni',notes:'',reviews:[],
 evidence:{occurred_at:'2026-10-28T14:00:00Z',http_method:'GET',route_template:'/auth/login/',status_code:401,duration_ms:182.3,session_ref:'demo-session'}
}));
export const demoTimeline = Array.from({length:36},(_,i)=>({
 ts:new Date(Date.UTC(2026,9,28,14)-((35-i)*10*60000)).toISOString(),
 requests:Math.round(305+Math.sin(i*.45)*69+Math.sin(i*.17)*90+(i>20&&i<29?97:0)),
 errors:Math.max(2,Math.round(7+Math.sin(i*.61)*3+(i>23&&i<27?24:0)))
}));
export const demoRouteCounts=[['/auth/login/',21940],['/catalog/',18170],['/search/',14510],['/items/{id}/',13500],['/forms/checkout/',7210]];
export const modelStages=[
 {code:'M1',title:'Trafik profili',alg:'K-Means / DBSCAN',about:'Dakika ve rota seviyesinde yo\u011funluk ba\u011flam\u0131'},
 {code:'M2',title:'Anomali tespiti',alg:'Isolation Forest',about:'\u00c7ok de\u011fi\u015fkenli sapma puan\u0131'},
 {code:'M3',title:'Davran\u0131\u015f \u00f6r\u00fcnt\u00fcs\u00fc',alg:'PrefixSpan',about:'Oturum i\u00e7i rota ge\u00e7i\u015fleri'},
 {code:'M4',title:'Karar katman\u0131',alg:'Hibrit birle\u015fim',about:'Ba\u011flam odakl\u0131 alarm gerek\u00e7esi'}
];
export const conditions=['B0','B1','B1+D','B1+S','B2'];
export const integrationTypes=[['Django Middleware','JSONL olay \u00fcretimi','Yap\u0131land\u0131rma'],['REST API','Uygulama kaynaklar\u0131ndan g\u00fcvenli aktar\u0131m','Taslak'],['Locust','Sekiz kontroll\u00fc trafik senaryosu','Demo'],['PostgreSQL','Analiz ve alarm depolama tasar\u0131m\u0131','\u015eema'],['JSONL / CSV','Dosya do\u011frulama ve i\u00e7e aktarma','Demo'],['Webhook','Alarm bildirim entegrasyonu','Planland\u0131']];
export const safeSample=[{event_uid:'example-001',occurred_at:'2026-10-28T14:00:00Z',http_method:'GET',route_template:'/catalog/',status_code:200,duration_ms:136.5,session_ref:'synthetic-s1',schema_version:'1.0'},{event_uid:'example-002',occurred_at:'2026-10-28T14:01:00Z',http_method:'POST',route_template:'/auth/login/',status_code:401,duration_ms:178.8,session_ref:'synthetic-s2',schema_version:'1.0'}];
export const numeric = n=>Number(n||0).toLocaleString('tr-TR');
export const formatTime = v=>new Date(v).toLocaleString('tr-TR',{timeZone:'Europe/Istanbul',day:'2-digit',month:'short',hour:'2-digit',minute:'2-digit'});

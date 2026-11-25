import fs from 'node:fs';
const text=fs.readFileSync(new URL('../src/App.jsx',import.meta.url),'utf8');
const extract=(begin,end)=>{
  const start=text.indexOf(begin);
  if(start<0)throw new Error('Route mapping not found: '+begin);
  const stop=text.indexOf(end,start+begin.length);
  if(stop<0)throw new Error('Route mapping not closed: '+begin);
  return [...text.slice(start,stop).matchAll(/'([^']+)':/g)].map(x=>x[1]);
};
const publicRoutes=extract('const publicPages={','};');
const appRoutes=extract('const appPages={','};');
const detail=/const match=page\.match\(\^?/.test(text)||text.includes('const match=page.match(/^\\/app\\/alarms\\/');
const expectedPublic=['/','/login','/register','/reset-password','/pricing'];
const expectedApp=['/app/overview','/app/traffic','/app/models','/app/alarms','/app/sources','/app/reports','/app/settings',
  '/app/onboarding','/app/integrations','/app/team','/app/notifications','/app/help','/app/billing'];
const same=(xs,ys)=>xs.length===ys.length&&xs.every(x=>ys.includes(x));
if(!same(publicRoutes,expectedPublic)||!same(appRoutes,expectedApp)||!detail){
 console.error('Route mismatch',JSON.stringify({publicRoutes,appRoutes,detail},null,2));process.exit(1);
}
console.log('Static React route inventory verified: 5 public + 13 panel + 1 dynamic alarm detail = 19 screens.');

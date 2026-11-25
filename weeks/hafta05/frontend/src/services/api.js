export const apiBase=import.meta.env.VITE_API_BASE ?? '/api';
export async function apiRequest(path,options={}){
  const r=await fetch(apiBase+path,{credentials:'include',...options,headers:{...(options.body instanceof FormData?{}:{'Content-Type':'application/json'}),...(options.headers||{})}});
  if(!r.ok){let msg=`HTTP ${r.status}`;try{let data=await r.json();msg=data.detail||msg;if(typeof msg!=='string')msg=JSON.stringify(msg)}catch{}throw new Error(msg)}
  const c=r.headers.get('content-type')||'';
  if(c.includes('json'))return r.json();
  return r.blob();
}
export function downloadBlob(filename,blob){let url=URL.createObjectURL(blob);let a=document.createElement('a');a.href=url;a.download=filename;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)}
export function downloadText(filename,contents,type='text/plain;charset=utf-8'){downloadBlob(filename,new Blob([contents],{type}))}

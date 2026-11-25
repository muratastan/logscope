import {defineConfig} from 'vite';
// Docker resolves the API by Compose service name; native Windows uses localhost.
const target=process.env.API_PROXY_TARGET||'http://127.0.0.1:8000';
export default defineConfig({server:{host:'127.0.0.1',port:5173,proxy:{'/api':{target,changeOrigin:true}}}});

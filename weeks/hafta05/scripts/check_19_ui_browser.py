"""Visual browser QA for the 19-screen self-contained HTML demo.
Chromium executable must be locally available; does not require npm.
This validates fallback HTML navigation, NOT a built React bundle.
"""
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from functools import partial
import threading
import json
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
FILENAME='19_Ekran_Calisan_Demo.html'
ROUTES=['/','/login','/register','/reset-password','/pricing','/app/overview','/app/traffic','/app/models',
        '/app/alarms','/app/alarms/LS-1042','/app/sources','/app/reports','/app/settings','/app/onboarding',
        '/app/integrations','/app/team','/app/notifications','/app/help','/app/billing']


def run():
    out=ROOT/'reports/hafta5/browser'
    out.mkdir(parents=True,exist_ok=True)
    results=[];errors=[]
    http=ThreadingHTTPServer(('127.0.0.1',0),partial(SimpleHTTPRequestHandler,directory=str(ROOT/'prototip')))
    threading.Thread(target=http.serve_forever,daemon=True).start()
    url=f'http://127.0.0.1:{http.server_address[1]}/{FILENAME}'
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-gpu'])
        desktop=browser.new_page(viewport={'width':1440,'height':900},device_scale_factor=1)
        desktop.on('pageerror',lambda err:errors.append(str(err)))
        desktop.goto(url+'#/',wait_until='load')
        # Activate existing offline demo with the in-page UI before checking auth routes.
        demo=desktop.locator('[data-action="quick-demo"]')
        if demo.count():
            demo.first.click()
            desktop.wait_for_timeout(200)
        # Some browsers do not persist file:// sessionStorage consistently;
        # page is kept in one context so the existing offline demo session survives.
        for idx,route in enumerate(ROUTES):
            desktop.evaluate('r => window.location.hash = "#"+r',route)
            desktop.wait_for_timeout(140)
            body=desktop.locator('#app').inner_text()
            title=desktop.title()
            broken='İçerik yüklenemedi' in body or 'İçerik bulunamadı' in body
            record={'route':route,'title':title,'content_chars':len(body),'broken':broken}
            results.append(record)
            if idx in (0,5,6,7,8,9,10,15):
                desktop.screenshot(path=str(out/f'{idx+1:02d}_{route.strip("/").replace("/","_") or "landing"}.png'),full_page=False)
        mobile=browser.new_page(viewport={'width':390,'height':844},device_scale_factor=1)
        mobile.goto(url+'#/login')
        m=mobile.locator('[data-action="quick-demo"]')
        if m.count():m.first.click()
        for route in ['/app/overview','/app/alarms','/app/sources']:
            mobile.evaluate('r => window.location.hash = "#"+r',route)
            mobile.wait_for_timeout(160)
            overflow=mobile.evaluate('({vw:innerWidth,scroll:document.documentElement.scrollWidth})')
            results.append({'route':route,'viewport':'mobile','horizontal_overflow':overflow['scroll']>overflow['vw']+3,**overflow})
        mobile.screenshot(path=str(out/'mobile_390.png'),full_page=False)
        browser.close()
    http.shutdown()
    output={'tested_routes':19,'routes':results,'javascript_errors':errors,
            'failed_routes':[r for r in results if r.get('broken') or r.get('horizontal_overflow') or r.get('content_chars',1)<30],
            'scope':'standalone HTML demo; React npm bundle not verified'}
    (out/'browser_19_summary.json').write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'tested_routes':19,'failed_routes':output['failed_routes'],'javascript_errors':errors},ensure_ascii=False,indent=2))
    return output

if __name__=='__main__':run()

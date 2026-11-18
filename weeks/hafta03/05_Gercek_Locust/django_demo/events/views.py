"""Synthetic Django website with real HTML templates (distinct from React SaaS UI)."""
import time
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import render

ITEMS=[{'id':1,'name':'Örnek ürünü incele','category':'demo','stock':'Mevcut'},
       {'id':2,'name':'Trafik analiz kartı','category':'demo','stock':'Mevcut'},
       {'id':3,'name':'Sentetik paket','category':'demo','stock':'Sınırlı'}]

def home(request): return render(request,'home.html',{'items':ITEMS})
def catalog(request): return render(request,'catalog.html',{'items':ITEMS})
def search(request):
    term=(request.GET.get('q') or '').strip().lower()[:40]
    data=[x for x in ITEMS if term in x['name'].lower()] if term else ITEMS
    return render(request,'search.html',{'items':data,'query':term})
def item(request,item_id):
    obj=next((x for x in ITEMS if x['id']==item_id),None)
    if obj is None: return HttpResponse('Örnek ürün bulunamadı',status=404)
    return render(request,'item.html',{'item':obj})
def checkout(request): return render(request,'checkout.html',{'completed':request.method=='POST'})
def login(request):
    # Explicitly simulated failed authentication for LOCAL Locust experiments.
    # No password, identity or real account is sent or stored.
    if (settings.LOGSCOPE_ENABLE_ANOMALY_ENDPOINTS
            and request.method == 'GET'
            and request.GET.get('simulate_failure') == '1'):
        return HttpResponse('Controlled simulated login failure', status=401)
    return render(request,'login.html')
def rare_export(request): return render(request,'rare_export.html')
def test_error(request):
    if not settings.LOGSCOPE_ENABLE_ANOMALY_ENDPOINTS:return HttpResponse(status=404)
    return HttpResponse('Synthetic server error',status=503)
def test_slow(request):
    if not settings.LOGSCOPE_ENABLE_ANOMALY_ENDPOINTS:return HttpResponse(status=404)
    time.sleep(.45)
    return render(request,'slow.html')

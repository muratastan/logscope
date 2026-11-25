import React from 'react';
import {Badge,Card,Icon} from './Common';
import './week5-flow.css';

const DEMO_ADIMLARI = [
  {num:'01',name:'Giriş / çalışma alanı',url:'#/login',description:'Yerel demo veya API oturumuyla açın.',icon:'lock'},
  {num:'02',name:'Genel bakış',url:'#/app/overview',description:'Trafik özeti ve son alarm tablosu.',icon:'dashboard'},
  {num:'03',name:'Trafik analizi',url:'#/app/traffic',description:'Dakika/rota ve 4xx–5xx filtreleri.',icon:'chart'},
  {num:'04',name:'Model merkezi',url:'#/app/models',description:'M1 K-Means/DBSCAN, M2 Isolation Forest.',icon:'layers'},
  {num:'05',name:'Alarm merkezi',url:'#/app/alarms',description:'Alarm seçimi, arama ve durum filtreleri.',icon:'bell'},
  {num:'06',name:'Alarm detayı',url:'#/app/alarms/LS-1042',description:'Kanıt, inceleme kararı ve not geçmişi.',icon:'file'}
];

export default function Week5DemoFlow({app}) {
  return <section className="hafta5-demo-flow" aria-label="Beşinci hafta ara demo adımları">
    <div className="hafta5-demo-head">
      <div><div className="hafta5-eyebrow">HAFTA 5 · REACT + FASTAPI</div>
        <h2>Ara demo akışı</h2>
        <p>Öneri formundaki altı temel ekranı sırayla açın. Sadece rota değil, ekranın yaptığı işlemi de kontrol edin.</p>
      </div>
      <Badge tone={app.connected?'teal':'gold'}>{app.connected?'API oturumu açık':'Yerel örnek veri'}</Badge>
    </div>
    <ol className="hafta5-demo-grid">
      {DEMO_ADIMLARI.map(a=><li key={a.num}>
        <a href={a.url} className="hafta5-demo-link" title={a.description}>
          <span className="hafta5-demo-no">{a.num}</span>
          <span className="hafta5-demo-icon"><Icon name={a.icon}/></span>
          <span className="hafta5-demo-text"><strong>{a.name}</strong><small>{a.description}</small></span>
          <span aria-hidden="true">›</span>
        </a>
      </li>)}
    </ol>
    <div className="hafta5-demo-bottom">
      <span>Veri kaynağını eklemek için <a href="#/app/sources">JSONL yükleme ekranı</a> kullanılır.</span>
      <span>{app.connected?'API: giriş başarılı; detay ve karar kaydı veritabanına bağlanır.':'API bağlı değilken gerçek kayıt/sonuç üretilmez.'}</span>
    </div>
  </section>;
}

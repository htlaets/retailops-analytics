const money = new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',notation:'compact',maximumFractionDigits:1});
const integer = new Intl.NumberFormat('en-US');
let records = [];
const state = {region:'All',channel:'All'};

const sum = (rows,key) => rows.reduce((total,row)=>total+row[key],0);
const group = (rows,key) => rows.reduce((acc,row)=>{(acc[row[key]]??=[]).push(row);return acc},{});
const weightedOnTime = rows => sum(rows,'orders') ? rows.reduce((n,r)=>n+r.on_time*r.orders,0)/sum(rows,'orders') : 0;

function filtered(){return records.filter(r=>(state.region==='All'||r.region===state.region)&&(state.channel==='All'||r.channel===state.channel))}
function setText(id,value){document.getElementById(id).textContent=value}

function renderKpis(rows){
  const revenue=sum(rows,'revenue'),profit=sum(rows,'profit'),orders=sum(rows,'orders');
  setText('revenue',money.format(revenue));setText('profit',money.format(profit));setText('orders',integer.format(orders));
  setText('margin',`${(profit/revenue*100||0).toFixed(1)}% margin`);setText('aov',`${money.format(revenue/orders||0)} average order`);
  setText('ontime',`${weightedOnTime(rows).toFixed(1)}%`);
}

function renderTrend(rows){
  const months=group(rows,'month');
  const values=Array.from({length:12},(_,i)=>{const rs=months[i+1]||[];return {label:rs[0]?.month_name||'',revenue:sum(rs,'revenue'),profit:sum(rs,'profit')}});
  const max=Math.max(...values.map(v=>v.revenue),1),w=760,h=230,p={l:8,r:12,t:10,b:28};
  const x=i=>p.l+i*(w-p.l-p.r)/11,y=v=>p.t+(h-p.t-p.b)*(1-v/max);
  const path=key=>values.map((v,i)=>`${i?'L':'M'} ${x(i)} ${y(v[key])}`).join(' ');
  const grids=[0,.25,.5,.75,1].map(t=>`<line class="gridline" x1="${p.l}" y1="${y(max*t)}" x2="${w-p.r}" y2="${y(max*t)}"/>`).join('');
  const labels=values.map((v,i)=>`<text class="axis-label" text-anchor="middle" x="${x(i)}" y="${h-3}">${v.label}</text>`).join('');
  const points=values.map((v,i)=>`<circle class="point" cx="${x(i)}" cy="${y(v.revenue)}" r="3"><title>${v.label}: ${money.format(v.revenue)}</title></circle>`).join('');
  const area=`${path('revenue')} L ${x(11)} ${h-p.b} L ${x(0)} ${h-p.b} Z`;
  document.getElementById('trend').innerHTML=`<svg viewBox="0 0 ${w} ${h}" preserveAspectRatio="none"><defs><linearGradient id="areaFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#67e8c2" stop-opacity=".18"/><stop offset="1" stop-color="#67e8c2" stop-opacity="0"/></linearGradient></defs>${grids}<path class="area" d="${area}"/><path class="revenue-line" d="${path('revenue')}"/><path class="profit-line" d="${path('profit')}"/>${points}${labels}</svg>`;
}

function renderCategories(rows){
  const grouped=group(rows,'category'),total=sum(rows,'revenue');
  const values=Object.entries(grouped).map(([name,rs])=>({name,value:sum(rs,'revenue')})).sort((a,b)=>b.value-a.value);
  document.getElementById('categories').innerHTML=values.map(v=>`<div class="bar-row"><span class="bar-name">${v.name}</span><span class="bar-track"><span class="bar-fill" style="display:block;width:${v.value/values[0].value*100}%"></span></span><span class="bar-value">${(v.value/total*100).toFixed(0)}%</span></div>`).join('');
}

function renderRegions(rows){
  const grouped=group(rows,'region');
  document.getElementById('region-table').innerHTML=Object.entries(grouped).map(([name,rs])=>{const revenue=sum(rs,'revenue'),profit=sum(rs,'profit'),onTime=weightedOnTime(rs);return `<tr data-region="${name}"><td><span class="status ${onTime<85?'warn':''}">${name}</span></td><td>${money.format(revenue)}</td><td>${money.format(profit)}</td><td>${(profit/revenue*100).toFixed(1)}%</td><td>${onTime.toFixed(1)}%</td></tr>`}).join('');
  document.querySelectorAll('tbody tr').forEach(row=>row.onclick=()=>{state.region=row.dataset.region;document.getElementById('region').value=state.region;render()});
}
function render(){const rows=filtered();renderKpis(rows);renderTrend(rows);renderCategories(rows);renderRegions(records.filter(r=>state.channel==='All'||r.channel===state.channel))}
function setupFilters(){
  for(const [id,key] of [['region','region'],['channel','channel']]){const el=document.getElementById(id);[...new Set(records.map(r=>r[key]))].sort().forEach(value=>el.add(new Option(value,value)));el.onchange=e=>{state[key]=e.target.value;render()}}
  document.getElementById('reset').onclick=()=>{state.region=state.channel='All';document.getElementById('region').value='All';document.getElementById('channel').value='All';render()};
}
fetch('data.json').then(r=>{if(!r.ok)throw new Error('Data unavailable');return r.json()}).then(data=>{records=data.records;setText('updated',data.generated_at);setupFilters();render()}).catch(()=>{document.querySelector('main').insertAdjacentHTML('beforeend','<p>Run the data pipeline, then refresh this page.</p>')});

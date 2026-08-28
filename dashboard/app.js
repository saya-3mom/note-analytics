const files=["../articles.csv","../observations.csv"];

async function csv(path){
  const r=await fetch(path);
  if(!r.ok) throw new Error(path+" を読み込めません");
  return parse(await r.text());
}
function parse(text){
  const rows=[];let row=[],cell="",q=false;
  for(let i=0;i<text.length;i++){
    const c=text[i];
    if(c==='"'){
      if(q&&text[i+1]==='"'){cell+='"';i++}else q=!q;
    }else if(c===","&&!q){row.push(cell);cell=""}
    else if((c==="\n"||c==="\r")&&!q){
      if(c==="\r"&&text[i+1]==="\n")i++;
      row.push(cell);if(row.some(x=>x!==""))rows.push(row);row=[];cell="";
    }else cell+=c;
  }
  if(cell||row.length){row.push(cell);if(row.some(x=>x!==""))rows.push(row)}
  if(!rows.length)return[];
  const h=rows[0].map(x=>x.replace(/^\ufeff/,""));
  return rows.slice(1).map(r=>Object.fromEntries(h.map((x,i)=>[x,r[i]??""])));
}
const n=x=>Number(x||0);
const fmt=x=>n(x).toLocaleString("ja-JP");
const esc=x=>String(x??"").replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;");

async function main(){
  const [articles,obs]=await Promise.all(files.map(csv));
  const groups={};
  obs.forEach(o=>(groups[o.management_id]??=[]).push(o));

  const latest=articles
    .filter(a=>a.management_id)
    .map(a=>{
      const rows=(groups[a.management_id]||[]).sort((x,y)=>x.observed_at.localeCompare(y.observed_at));
      if(!rows.length)return null;
      const x=rows.at(-1),p=rows.length>1?rows.at(-2):null;
      const views=n(x.views),likes=n(x.likes),comments=n(x.comments);
      return {...a,views,likes,comments,
        diff:p?views-n(p.views):null, observed:x.observed_at,
        rate:views?likes/views*100:0};
    }).filter(Boolean);

  const total=latest.reduce((s,a)=>s+a.views,0);
  const diff=latest.reduce((s,a)=>s+(a.diff??0),0);
  const rate=latest.length?latest.reduce((s,a)=>s+a.rate,0)/latest.length:0;
  document.querySelector("#count").textContent=latest.length;
  document.querySelector("#views").textContent=fmt(total);
  document.querySelector("#diff").textContent=(diff>=0?"+":"")+fmt(diff);
  document.querySelector("#rate").textContent=rate.toFixed(1)+"%";
  document.querySelector("#updated").textContent="最終観測："+latest.map(a=>a.observed).sort().at(-1);

  latest.sort((a,b)=>b.views-a.views);
  document.querySelector("#table").innerHTML=latest.map(a=>`
    <tr>
      <td>${esc(a.management_id)}</td>
      <td title="${esc(a.title)}">
        <a href="${esc(a.url)}" target="_blank" rel="noopener noreferrer">
          ${esc(a.title)}
        </a>
      </td>
      <td>${fmt(a.views)}</td>
      <td class="${a.diff>0?"up":""}">${a.diff===null?"—":(a.diff>=0?"+":"")+fmt(a.diff)}</td>
      <td>${fmt(a.likes)}</td><td>${a.rate.toFixed(1)}%</td><td>${fmt(a.comments)}</td>
    </tr>`).join("");

  const ranking=[...latest].filter(a=>a.diff!==null).sort((a,b)=>b.diff-a.diff).slice(0,5);
  document.querySelector("#ranking").innerHTML=ranking.length?ranking.map((a,i)=>`
    <div class="rank">
      <div class="rankno">${i+1}</div>
      <div class="rid">${esc(a.management_id)}</div>
      <div class="rtitle">
        <a href="${esc(a.url)}" target="_blank" rel="noopener noreferrer">
          ${esc(a.title)}
        </a>
      </div>
      <div class="rdiff">${a.diff>=0?"+":""}${fmt(a.diff)} views</div>
    </div>`).join(""):`<div class="empty">比較できる観測データがまだありません。</div>`;
}
main().catch(e=>{
  document.querySelector("main").innerHTML=`<section class="card"><h2>読み込みエラー</h2><p>${esc(e.message)}</p><p>articles.csv と observations.csv をこの画面と同じ場所に置いてください。</p></section>`;
});

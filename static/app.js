const $ = (s) => document.querySelector(s);
const state = { feeds: [], sources: [], current: null, items: [] };

async function api(path, options={}) {
  const res = await fetch(path, { headers: { 'Content-Type': 'application/json' }, ...options });
  if (!res.ok) throw new Error((await res.text()) || `HTTP ${res.status}`);
  return res.json();
}
function esc(s='') { return String(s).replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c])); }
function toast(msg) { const el=$('#toast'); el.textContent=msg; el.classList.remove('hidden'); setTimeout(()=>el.classList.add('hidden'),2600); }
function currentSlug() { const m=location.pathname.match(/^\/f\/([^/]+)/); return m ? decodeURIComponent(m[1]) : null; }

async function loadShell() {
  const [feeds, sources] = await Promise.all([api('/api/feeds'), api('/api/sources')]);
  state.feeds = feeds; state.sources = sources;
  renderNav(); renderSources();
  const slug = currentSlug();
  if (slug) await showFeed(slug); else showHome();
}

function renderNav() {
  $('#feedNav').innerHTML = state.feeds.map(f => `<a href="/f/${encodeURIComponent(f.slug)}" class="${state.current?.feed?.slug===f.slug?'active':''}"><span class="nav-icon">${esc(f.icon)}</span><span>${esc(f.name)}</span></a>`).join('');
}
function renderSources() {
  $('#sourceMini').innerHTML = state.sources.slice(0,6).map(s => `<div class="source-mini-row"><span>${esc(s.name)}</span><span>${s.configured?'●':'○'}</span></div>`).join('');
  $('#sourceGrid').innerHTML = state.sources.map(s => `<div class="source-card"><div><div class="source-name">${esc(s.name)}</div><div class="source-state">${s.last_run ? `${esc(s.last_run.status)} · ${s.last_run.fetched} fetched` : 'not run yet'}</div></div><span class="dot ${s.configured?'live':'off'}"></span></div>`).join('');
}
function showHome() {
  state.current=null; $('#homeView').classList.remove('hidden'); $('#feedView').classList.add('hidden');
  $('#pageTitle').textContent='Feedify Alpha'; $('#pageDescription').textContent='Compile noisy sources into signals you actually want.'; $('#eyebrow').textContent='PERSONAL INTELLIGENCE NETWORK';
  $('#shareBtn').classList.add('hidden'); $('#installBtn').classList.add('hidden'); renderNav();
  $('#feedCards').innerHTML = state.feeds.map(f => `<a class="feed-card" href="/f/${encodeURIComponent(f.slug)}"><div class="feed-card-icon">${esc(f.icon)}</div><h3>${esc(f.name)}</h3><p>${esc(f.description || f.prompt)}</p><div class="feed-card-foot"><span>${f.public?'SHAREABLE':'PRIVATE'}</span><span>OPEN →</span></div></a>`).join('');
}
async function showFeed(slug) {
  const data = await api(`/api/feeds/${encodeURIComponent(slug)}?limit=100`); state.current=data; state.items=data.items;
  $('#homeView').classList.add('hidden'); $('#feedView').classList.remove('hidden');
  $('#pageTitle').textContent=`${data.feed.icon} ${data.feed.name}`; $('#pageDescription').textContent=data.feed.description || 'Personal Feedify feed'; $('#eyebrow').textContent='CUSTOM FEED APP';
  $('#feedPrompt').textContent=data.feed.prompt; $('#shareBtn').classList.remove('hidden'); $('#installBtn').classList.remove('hidden'); renderNav(); renderSignals();
}
function renderSignals() {
  const min = Number($('#scoreFilter').value || 0); $('#scoreValue').textContent=min.toFixed(2);
  const items=state.items.filter(x=>x.score>=min);
  $('#signalList').innerHTML = items.length ? items.map(x => `<article class="signal"><div class="signal-score">${Math.round(x.score*100)}</div><div><h3>${esc(x.title)}</h3><div class="signal-summary">${esc(x.summary)}</div><div class="why"><strong>Why it matters:</strong> ${esc(x.why_it_matters)}</div><div class="tags">${[x.type,x.domain,...(x.tags||[])].slice(0,8).map(t=>`<span class="tag">${esc(t)}</span>`).join('')}</div></div><div class="signal-meta"><span class="source">${esc(x.source.type || '')}</span>${x.source.url ? `<a href="${esc(x.source.url)}" target="_blank" rel="noopener">source ↗</a>` : ''}</div></article>`).join('') : `<div class="empty">No signals pass this threshold yet. Refresh sources or loosen the feed.</div>`;
}

async function createFeed(ev) {
  ev.preventDefault(); const fd=new FormData(ev.target); const payload={ name:fd.get('name'), prompt:fd.get('prompt'), icon:fd.get('icon')||'⚡', public:fd.get('public')==='true' };
  try { const out=await api('/api/feeds',{method:'POST',body:JSON.stringify(payload)}); $('#feedDialog').close(); location.href=`/f/${out.slug}`; } catch(e) { toast(e.message); }
}
async function refreshSignals() {
  const btn=$('#ingestBtn'); const old=btn.textContent; btn.disabled=true; btn.textContent='Refreshing…';
  try { const out=await api('/api/ingest',{method:'POST',body:JSON.stringify({limit:20})}); const ok=out.filter(x=>x.status==='ok').length; toast(`Signal refresh complete · ${ok} sources updated`); await loadShell(); }
  catch(e){ toast(`Refresh failed: ${e.message}`); } finally { btn.disabled=false; btn.textContent=old; }
}
async function shareFeed() {
  const url=location.href; if (navigator.share) { try { await navigator.share({title:state.current.feed.name,text:state.current.feed.description,url}); return; } catch {} }
  await navigator.clipboard.writeText(url); toast('Feed link copied');
}
function installFeed() {
  const isIOS=/iphone|ipad|ipod/i.test(navigator.userAgent);
  if (isIOS) toast('Safari: Share → Add to Home Screen. This feed already has its own name + icon.');
  else toast('Use your browser menu → Install app / Add to Home Screen.');
}
function openDialog(){ $('#feedDialog').showModal(); }

$('#newFeedBtn').addEventListener('click',openDialog); $('#heroCreateBtn').addEventListener('click',openDialog); $('#closeDialog').addEventListener('click',()=>$('#feedDialog').close());
$('#feedForm').addEventListener('submit',createFeed); $('#ingestBtn').addEventListener('click',refreshSignals); $('#shareBtn').addEventListener('click',shareFeed); $('#installBtn').addEventListener('click',installFeed); $('#scoreFilter').addEventListener('input',renderSignals);
loadShell().catch(e=>toast(e.message));

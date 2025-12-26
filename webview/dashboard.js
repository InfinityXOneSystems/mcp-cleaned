(async function(){
  const API_BASE = '/api/dashboard/data';
  const select = document.getElementById('systemSelect');

  function el(html){
    const d = document.createElement('div');
    d.innerHTML = html.trim();
    return d.firstElementChild;
  }

  function formatPercent(v){ return (v*100).toFixed(0) + '%'; }

  async function load(system='all'){
    try{
      const res = await fetch(`${API_BASE}?system=${encodeURIComponent(system)}`);
      if(!res.ok) throw new Error('Network');
      const payload = await res.json();

      // populate selector once
      if(select && (select.options.length === 0) && Array.isArray(payload.systems)){
        // add "all" option first
        const optAll = document.createElement('option'); optAll.value='all'; optAll.text='All Systems'; select.appendChild(optAll);
        payload.systems.forEach(s=>{
          const o = document.createElement('option'); o.value = s; o.text = s.replace('_',' ').toUpperCase(); select.appendChild(o);
        });
        // restore previous selection from URL hash or default to system
        const current = new URLSearchParams(location.search).get('system') || system;
        select.value = current || 'all';
        select.addEventListener('change', ()=> {
          const val = select.value;
          // update query param without reload
          const u = new URL(location);
          u.searchParams.set('system', val);
          history.replaceState({}, '', u);
          load(val);
        });
      }

      document.getElementById('last-updated').textContent = new Date(payload.updated_at).toLocaleString();

      // KPIs
      const kpiRow = document.getElementById('kpi-row');
      kpiRow.innerHTML = '';
      const kpis = payload.kpis || [];
      kpis.forEach(k=>{
        const card = el(`<div class="kpi"><div class="label">${k.label}</div><div class="value">${k.value}</div><div class="muted">${k.delta || ''}</div></div>`);
        kpiRow.appendChild(card);
      });

      // Recent table
      const tbody = document.querySelector('#recentTable tbody');
      tbody.innerHTML = '';
      (payload.recent || []).forEach(r=>{
        const tr = document.createElement('tr');
        tr.innerHTML = `<td>${new Date(r.created_at).toLocaleString()}</td><td>${r.agent}</td><td>${r.summary}</td><td>${formatPercent(r.confidence)}</td>`;
        tbody.appendChild(tr);
      });

      // Confidence timeline chart
      const labels = (payload.timeline || []).map(t=>new Date(t.ts).toLocaleTimeString());
      const data = (payload.timeline || []).map(t=>Math.round(t.confidence*100));
      // recreate charts (simple approach)
      if(window._confidenceChart) window._confidenceChart.destroy();
      const ctx = document.getElementById('confidenceChart').getContext('2d');
      window._confidenceChart = new Chart(ctx,{type:'line',data:{labels, datasets:[{label:'Confidence',data, borderColor:'#29b6f6', backgroundColor:'rgba(41,182,246,0.08)', tension:0.2}]}, options:{plugins:{legend:{display:false}}}});

      if(window._categoryChart) window._categoryChart.destroy();
      const ctx2 = document.getElementById('categoryChart').getContext('2d');
      const cats = payload.by_category || {};
      window._categoryChart = new Chart(ctx2,{type:'doughnut',data:{labels:Object.keys(cats), datasets:[{data:Object.values(cats), backgroundColor:['#29b6f6','#7c4dff','#ffb86b','#6ee7b7']}]}));
    }catch(e){
      console.error('Dashboard load error', e);
    }
  }

  // initial load: pick system from query param
  const initialSystem = new URLSearchParams(location.search).get('system') || 'all';
  load(initialSystem);
  setInterval(()=> load(select.value || 'all'), 30_000);
})();

(() => {
  'use strict';
  const DATA = window.GITS_DATA;
  const $ = (id) => document.getElementById(id);
  const num = (n, d = 0) => (n == null ? '—' : Number(n).toFixed(d));

  function applyFilter() {
    const code = $('lineFilter').value;
    const line = DATA[code] || DATA.ALL;
    const isAll = code === 'ALL';

    $('pagesub').textContent = isAll ? 'vdm_dev.silver — visas tinklas' : `vdm_dev.silver — ${line.name}`;

    $('kpi-km').innerHTML = `${num(line.total, 1)}<span class="unit">km</span>`;
    $('kpi-sw').innerHTML = `${num(line.switches)}<span class="unit">vnt</span>`;
    $('kpi-sig').innerHTML = `${num(line.signals)}<span class="unit">vnt</span>`;

    for (const [key, val] of Object.entries(line.tracks)) {
      const pct = line.total > 0 ? (val / line.total) * 100 : 0;
      document.querySelector(`[data-track="${key}"]`).textContent = `${num(val, 1)} km`;
      document.querySelector(`[data-track-bar="${key}"]`).style.width = `${pct.toFixed(1)}%`;
    }

    document.querySelectorAll('tr[data-line]').forEach((tr) => {
      tr.classList.toggle('is-active', tr.dataset.line === code);
    });

    const url = new URL(location.href);
    isAll ? url.searchParams.delete('kryptis') : url.searchParams.set('kryptis', code);
    history.replaceState(null, '', url);
  }

  const initial = new URLSearchParams(location.search).get('kryptis');
  if (initial && DATA[initial]) $('lineFilter').value = initial;
  $('lineFilter').addEventListener('change', applyFilter);
  applyFilter();
})();

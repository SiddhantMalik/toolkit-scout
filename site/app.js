// Findings table: filter by verdict / category / name; click a row for evidence, blockers and open questions.
const APPS = JSON.parse(document.getElementById('data').textContent);
const state = {verdict: 'all', category: 'all', query: ''};

const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]));
const el = (tag, cls, html) => { const e = document.createElement(tag); if (cls) e.className = cls; if (html !== undefined) e.innerHTML = html; return e; };
const list = v => Array.isArray(v) ? v : (v ? [v] : []);
const shortUrl = u => esc((u || '').replace(/^https?:\/\//, '').slice(0, 60));

function buildFilters() {
  const bar = document.getElementById('chips');
  ['all', 'easy', 'caveat', 'hard', 'no', 'unknown'].forEach(v => {
    const b = el('button', v === 'all' ? 'on' : '', v);
    b.onclick = () => { state.verdict = v; [...bar.querySelectorAll('button')].forEach(x => x.classList.toggle('on', x === b)); render(); };
    bar.appendChild(b);
  });
  const select = el('select');
  const categories = [...new Set(APPS.map(a => a.category))];
  select.innerHTML = '<option value="all">all categories</option>' + categories.map(c => `<option>${esc(c)}</option>`).join('');
  select.onchange = () => { state.category = select.value; render(); };
  const search = el('input'); search.placeholder = 'search app…';
  search.oninput = () => { state.query = search.value.toLowerCase(); render(); };
  bar.append(select, search);
}

function matches(a) {
  return (state.verdict === 'all' || a.verdict === state.verdict)
      && (state.category === 'all' || a.category === state.category)
      && a.name.toLowerCase().includes(state.query);
}

function rowFor(a) {
  const tr = el('tr', '', `<td>${a.id}</td><td><b>${esc(a.name)}</b><br><small>${esc(a.category)}</small></td>
    <td>${esc(list(a.auth).join(', '))}</td><td>${esc(a.access_dev)} → ${esc(a.access_prod)}</td>
    <td>${esc(list(a.api_styles).join(', '))}<br><small>${esc(a.api_breadth)}</small></td><td>${esc(a.mcp_type)}</td>
    <td>${esc(list(a.blockers).join(', ')) || '<small>none</small>'}<br><span class="pill v-${a.verdict}">${a.verdict}</span></td><td>${esc(a.confidence)}</td>`);
  const quotes = list(a.evidence).map(e =>
    `<li><b>${esc(e.field)}</b>: “${esc(e.quote)}” <a href="${esc(e.url)}" target="_blank" rel="noopener">${shortUrl(e.url)}</a></li>`).join('');
  const detail = el('tr', 'det', `<td></td><td colspan="7">${esc(a.description)}<br>
    Entity: ${esc(a.entity_status)} ${esc(a.entity_note || '')} · rule ${esc(a.rule)} · tenancy ${esc(a.tenancy)} ·
    quotes found ${a.quotes_verified}, web-only ${a.quotes_web_only}, failed ${a.quotes_failed}<br>
    ${a.needs_human ? '<b>Open question:</b> ' + esc(a.needs_human) + '<br>' : ''}
    <a href="${esc(a.docs_url)}" target="_blank" rel="noopener">docs</a><ul>${quotes}</ul></td>`);
  tr.onclick = () => tr.classList.toggle('open');
  return [tr, detail];
}

function render() {
  const body = document.querySelector('#apps tbody');
  const rows = [];
  for (const app of APPS.filter(matches)) {
    try { rows.push(...rowFor(app)); }
    catch (err) { rows.push(el('tr', '', `<td>${app.id}</td><td colspan="7">could not render ${esc(app.name)}: ${esc(err.message)}</td>`)); }
  }
  body.replaceChildren(...rows);
}

function wireCopyButton() {
  const button = document.getElementById('copy-run');
  if (!button) return;
  button.onclick = () => {
    const text = document.getElementById('run-cmd').textContent;
    (navigator.clipboard ? navigator.clipboard.writeText(text) : Promise.reject()).then(
      () => { button.textContent = 'copied'; }, () => { button.textContent = 'select the text and copy'; });
  };
}

buildFilters(); render(); wireCopyButton();

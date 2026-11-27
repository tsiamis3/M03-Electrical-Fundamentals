// Shared code for every page of the M03 site: header + arc, language switch, question bank, quiz, local stats.
// Pages load: data/lessons.js, data/bank.js (when they need questions), then this file.

// ---- Site configuration: header links and course texts ----
const SITE = {
  TITLE: 'Electrical Fundamentals',
  KICKER: 'EASA Part-66 · Module 3',
  LINKS: [
    {label: 'Home', href: 'index.html'},
    {label: 'Lessons', href: 'lessons.html'},
    {label: 'Practice', href: 'practice.html'},
    {label: 'Formulas', href: 'formulas.html'},
    {label: 'Units', href: 'units.html'},
    {label: 'Simulations', href: 'sims.html'}
  ],
  STUDENT_STATUSES: ['new', 'approved'],  // statuses students see; 'fix' and 'retired' stay hidden
  PASS: 0.75
};

const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]));
const $ = id => document.getElementById(id);
const shuffle = a => { a = a.slice(); for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; };

// Small wrapper around localStorage that never throws (private mode, blocked storage).
class Store {
  static get(k, d) { try { const v = localStorage.getItem('m3-' + k); return v === null ? d : JSON.parse(v); } catch (e) { return d; } }
  static set(k, v) { try { localStorage.setItem('m3-' + k, JSON.stringify(v)); } catch (e) {} }
}

// Question language: 'en', 'el' or 'both' (both = English first, Greek underneath).
class Lang {
  static get() { return Store.get('lang', 'en'); }
  static set(v) { Store.set('lang', v); document.dispatchEvent(new CustomEvent('langchange')); }
  // Render a {en, el} pair as HTML in the chosen language.
  static t(o) {
    if (o == null || typeof o !== 'object') return esc(o);
    const l = Lang.get();
    if (l === 'both' && o.el && o.en && o.el !== o.en) return esc(o.en) + `<span class="alt" lang="el">${esc(o.el)}</span>`;
    return esc(l === 'el' ? (o.el || o.en) : (o.en || o.el));
  }
}

// The Tesla arc in the header: a jagged bolt between two copper electrodes, redrawn for a moment on load
// and whenever the title is clicked. With reduced motion it is drawn once and stays still.
class Arc {
  constructor(svg) { this.svg = svg; this.bolts = svg.querySelectorAll('.bolt'); this.timer = null; }
  path(x0, x1, y, amp) {
    const steps = 22, pts = [];
    for (let i = 0; i <= steps; i++) {
      const x = x0 + (x1 - x0) * i / steps;
      const env = Math.sin(Math.PI * i / steps);           // pinned at both electrodes
      pts.push(`${x.toFixed(1)},${(y + (Math.random() * 2 - 1) * amp * env).toFixed(1)}`);
    }
    return 'M' + pts.join(' L');
  }
  draw() {
    const w = this.svg.viewBox.baseVal.width;
    this.bolts.forEach((b, i) => b.setAttribute('d', this.path(34, w - 34, 32, i ? 22 : 14)));
  }
  zap(ms = 1400) {
    this.draw();
    if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    clearInterval(this.timer);
    const t0 = performance.now();
    this.timer = setInterval(() => { this.draw(); if (performance.now() - t0 > ms) clearInterval(this.timer); }, 70);
  }
}

class Site {
  // Build the header on every page. `sub` is the one-line description under the title.
  static header(sub) {
    const page = location.pathname.split('/').pop() || 'index.html';
    const l = Lang.get();
    const nav = SITE.LINKS.map(x => `<a href="${x.href}"${x.href === page ? ' aria-current="page"' : ''}>${esc(x.label)}</a>`).join('');
    const langs = [['en', 'EN'], ['el', 'ΕΛ'], ['both', 'EN+ΕΛ']].map(([k, t]) =>
      `<button type="button" data-lang="${k}" aria-pressed="${l === k}">${t}</button>`).join('');
    const head = document.createElement('header');
    head.className = 'lab-head';
    head.innerHTML = `<div class="wrap">
      <h1 id="title" title="Click for a spark"><small>${esc(SITE.KICKER)}</small>${esc(SITE.TITLE)}</h1>
      <svg class="arc" viewBox="0 0 1000 64" preserveAspectRatio="none" aria-hidden="true">
        <defs><radialGradient id="copperGrad" cx="35%" cy="30%"><stop offset="0" stop-color="#f3b27a"/><stop offset=".55" stop-color="#c8773d"/><stop offset="1" stop-color="#6b3a18"/></radialGradient></defs>
        <path class="bolt faint"/><path class="bolt"/>
        <circle class="electrode" cx="18" cy="32" r="16"/><circle class="electrode" cx="982" cy="32" r="16"/>
      </svg>
      ${sub ? `<p>${sub}</p>` : ''}
      <nav class="site-nav" aria-label="Site">${nav}<span class="lang" role="group" aria-label="Question language">${langs}</span></nav>
    </div>`;
    document.body.prepend(head);
    const arc = new Arc(head.querySelector('.arc'));
    arc.zap();
    head.querySelector('#title').addEventListener('click', () => arc.zap(900));
    head.querySelectorAll('.lang button').forEach(b => b.addEventListener('click', () => {
      head.querySelectorAll('.lang button').forEach(x => x.setAttribute('aria-pressed', x === b));
      Lang.set(b.dataset.lang);
    }));
  }

  static lessons() { return (window.M3_LESSONS && window.M3_LESSONS.lessons) || []; }
  static lesson(id) { return Site.lessons().find(x => x.id === id); }
  // Course units (A–F + R), in teaching order (the order of their first lesson).
  static units() {
    const u = (window.M3_LESSONS && window.M3_LESSONS.units) || {}, ls = Site.lessons();
    const first = k => { const i = ls.findIndex(l => l.unit === k); return i < 0 ? 1e9 : i; };
    return Object.keys(u).sort((a, b) => first(a) - first(b)).map(k => ({id: k, ...u[k], lessons: ls.filter(l => l.unit === k)}));
  }
  static unitName(k) { const u = ((window.M3_LESSONS || {}).units || {})[k]; return u ? (k === 'R' ? '' : `Unit ${k}: `) + u.title.en : ''; }
  static published() { return Site.lessons().filter(x => x.status === 'published'); }
  static fmtDate(iso) {
    const d = new Date(iso + 'T12:00:00');
    return d.toLocaleDateString('en-GB', {weekday: 'short', day: 'numeric', month: 'short'});
  }
  // Markdown → HTML. Uses marked (loaded from the CDN on lesson pages); falls back to plain paragraphs.
  static md(src) {
    if (window.marked) return window.marked.parse(src);
    return src.split(/\n{2,}/).map(p => `<p>${esc(p)}</p>`).join('');
  }
}

// The question bank (data/bank.js). Same question format as the M02 bank, plus `lesson` and `status`.
class Bank {
  constructor(raw) {
    this.meta = (raw && raw.meta) || {topics: {}};
    this.misc = (raw && raw.misc) || {};
    this.all = (raw && raw.questions) || [];
  }
  // Questions students may see, optionally filtered.
  pick({lessons, topics, d, statuses = SITE.STUDENT_STATUSES} = {}) {
    return this.all.filter(q => statuses.includes(q.status || 'new') &&
      (!lessons || !lessons.length || lessons.includes(q.lesson)) &&
      (!topics || !topics.length || topics.includes(q.topic)) &&
      (!d || !d.length || d.includes(q.d)));
  }
  countBy(key, list = this.pick()) { const c = {}; list.forEach(q => c[q[key]] = (c[q[key]] || 0) + 1); return c; }
  topicName(t) { return this.meta.topics[t] || {en: t, el: t}; }
}

// A list of questions on one page. mode 'practice': instant feedback per question.
// mode 'test': answer everything, then "Check answers" marks the paper. Results go to Store under `key`.
class Quiz {
  constructor(el, questions, {mode = 'practice', key = '', bank = null, onDone = null} = {}) {
    this.el = el; this.mode = mode; this.key = key; this.bank = bank; this.onDone = onDone;
    // Shuffle the options of each question once; remember where the correct one went.
    this.qs = questions.map(q => {
      const order = shuffle(q.o.map((_, i) => i));
      return {...q, order, answer: null};
    });
    this.checked = false;
    document.addEventListener('langchange', () => this.render());
  }
  letter(i) { return 'abcd'[i]; }
  render() {
    if (!this.qs.length) { this.el.innerHTML = '<p class="mute">No questions here yet.</p>'; return; }
    const show = q => this.mode === 'practice' ? q.answer !== null : this.checked;
    this.el.innerHTML = this.qs.map((q, n) => {
      const opts = q.order.map((oi, k) => {
        let cls = 'opt';
        if (show(q)) { if (oi === q.a) cls += ' ok'; else if (oi === q.answer) cls += ' bad'; }
        else if (oi === q.answer) cls += ' sel';
        return `<button class="${cls}" data-q="${n}" data-o="${oi}"${show(q) ? ' disabled' : ''}><b>${this.letter(k)}</b><span>${Lang.t(q.o[oi])}</span></button>`;
      }).join('');
      let expl = '';
      if (show(q)) {
        const tag = q.answer !== null && q.answer !== q.a && q.tags ? q.tags[q.answer] : null;
        const tip = tag && this.bank && this.bank.misc[tag] ? `<p>${Lang.t(this.bank.misc[tag])}</p>` : '';
        expl = `<div class="expl">${tip}<p>${Lang.t(q.x)}</p></div>`;
      }
      const meta = [`Q${n + 1}`, q.topic, ['', 'easy', 'medium', 'hard'][q.d] || '', q.units === '—' ? '' : q.units].filter(Boolean).join(' / ');
      return `<div class="qcard"><div class="qmeta">${esc(meta)}</div><p class="qtext">${Lang.t(q.q)}</p>${opts}${expl}</div>`;
    }).join('') + this.footer();
    this.el.querySelectorAll('.opt').forEach(b => b.addEventListener('click', () => this.choose(+b.dataset.q, +b.dataset.o)));
    const c = this.el.querySelector('[data-check]');
    if (c) c.addEventListener('click', () => this.finish());
    const r = this.el.querySelector('[data-retry]');
    if (r) r.addEventListener('click', () => { this.qs.forEach(q => { q.answer = null; q.order = shuffle(q.order); }); this.checked = false; this.render(); });
  }
  choose(n, oi) {
    const q = this.qs[n];
    if (this.mode === 'practice' ? q.answer !== null : this.checked) return;
    q.answer = oi;
    this.render();
    if (this.mode === 'practice' && this.qs.every(x => x.answer !== null)) this.finish();
  }
  footer() {
    const done = this.qs.filter(q => q.answer !== null).length, ok = this.qs.filter(q => q.answer === q.a).length;
    if (this.mode === 'test' && !this.checked)
      return `<div class="row" style="margin-top:12px"><span class="mute">${done} of ${this.qs.length} answered</span><span class="spacer"></span><button class="btn" data-check>Check answers</button></div>`;
    const finished = this.mode === 'test' ? this.checked : done === this.qs.length;
    const pct = Math.round(100 * ok / this.qs.length);
    return `<div class="row" style="margin-top:14px"><span class="score ${finished ? (ok / this.qs.length >= SITE.PASS ? 'pass' : 'fail') : ''}">${ok}/${this.qs.length}</span>` +
      `<span class="mute">${finished ? pct + '% correct' : done + ' answered'}</span><span class="spacer"></span>` +
      (finished ? '<button class="btn alt" data-retry>Try again</button>' : '') + '</div>';
  }
  finish() {
    this.checked = true;
    const ok = this.qs.filter(q => q.answer === q.a).length;
    if (this.key) {
      const best = Store.get('best', {});
      const prev = best[this.key];
      if (!prev || ok / this.qs.length > prev.ok / prev.n) best[this.key] = {ok, n: this.qs.length, at: Date.now()};
      Store.set('best', best);
    }
    this.render();
    if (this.onDone) this.onDone(ok, this.qs.length);
  }
}

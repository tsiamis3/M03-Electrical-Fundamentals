// Interactive figures for the "going deeper" pages. A page asks for one with
//   <div class="sim" data-sim="skin"></div>      (skin | paschen | antenna)
// and deep.html calls Sims.mount(container) after the Markdown is rendered.
// Everything is drawn on a <canvas>; no libraries.

const MU0 = 4e-7 * Math.PI;

// A small 2-D plot: linear or log axes, grid, curves, markers. Redraws to the width of its box.
class Plot {
  constructor(canvas, {x, y, xlog = false, ylog = false, xlabel = '', ylabel = ''}) {
    this.c = canvas; this.ctx = canvas.getContext('2d');
    Object.assign(this, {x, y, xlog, ylog, xlabel, ylabel});
    this.ink = '#22201b'; this.grid = 'rgba(34,32,27,.15)';
    this.pad = {l: 58, r: 24, t: 12, b: 42};
  }
  size() {
    const w = this.c.parentElement.clientWidth, h = Math.max(220, Math.min(320, w * 0.62)), r = window.devicePixelRatio || 1;
    this.c.width = w * r; this.c.height = h * r; this.c.style.width = w + 'px'; this.c.style.height = h + 'px';
    this.ctx.setTransform(r, 0, 0, r, 0, 0); this.w = w; this.h = h;
  }
  tx(v) { const [a, b] = this.x, f = this.xlog ? (Math.log10(v) - Math.log10(a)) / (Math.log10(b) - Math.log10(a)) : (v - a) / (b - a);
    return this.pad.l + f * (this.w - this.pad.l - this.pad.r); }
  ty(v) { const [a, b] = this.y, f = this.ylog ? (Math.log10(v) - Math.log10(a)) / (Math.log10(b) - Math.log10(a)) : (v - a) / (b - a);
    return this.h - this.pad.b - f * (this.h - this.pad.t - this.pad.b); }
  ticks(range, log) {
    const [a, b] = range;
    if (log) { const out = []; for (let e = Math.ceil(Math.log10(a)); e <= Math.floor(Math.log10(b)); e++) out.push(10 ** e); return out; }
    const step = 10 ** Math.floor(Math.log10((b - a) / 4)), n = (b - a) / step, s = n > 8 ? step * 2 : step, out = [];
    for (let v = Math.ceil(a / s) * s; v <= b + 1e-12; v += s) out.push(+v.toPrecision(10));
    return out;
  }
  fmt(v, log) {
    if (!log) return String(+v.toPrecision(4));
    const e = Math.round(Math.log10(v)), sup = '⁰¹²³⁴⁵⁶⁷⁸⁹';
    if (e >= 0 && e <= 2) return String(v);
    return '10' + (e < 0 ? '⁻' : '') + String(Math.abs(e)).split('').map(d => sup[+d]).join('');
  }
  axes() {
    const g = this.ctx; g.clearRect(0, 0, this.w, this.h);
    g.font = '12px system-ui, sans-serif'; g.fillStyle = this.ink; g.strokeStyle = this.grid; g.lineWidth = 1;
    for (const v of this.ticks(this.x, this.xlog)) { const X = this.tx(v); g.beginPath(); g.moveTo(X, this.pad.t); g.lineTo(X, this.h - this.pad.b); g.stroke();
      g.textAlign = 'center'; g.fillText(this.fmt(v, this.xlog), X, this.h - this.pad.b + 15); }
    for (const v of this.ticks(this.y, this.ylog)) { const Y = this.ty(v); g.beginPath(); g.moveTo(this.pad.l, Y); g.lineTo(this.w - this.pad.r, Y); g.stroke();
      g.textAlign = 'right'; g.fillText(this.fmt(v, this.ylog), this.pad.l - 5, Y + 4); }
    g.strokeStyle = this.ink; g.beginPath(); g.moveTo(this.pad.l, this.pad.t); g.lineTo(this.pad.l, this.h - this.pad.b); g.lineTo(this.w - this.pad.r, this.h - this.pad.b); g.stroke();
    g.textAlign = 'center'; g.fillText(this.xlabel, (this.pad.l + this.w - this.pad.r) / 2, this.h - 6);
    g.save(); g.translate(13, (this.pad.t + this.h - this.pad.b) / 2); g.rotate(-Math.PI / 2); g.fillText(this.ylabel, 0, 0); g.restore();
  }
  curve(xs, ys, color, width = 2.2) {
    const g = this.ctx; g.strokeStyle = color; g.lineWidth = width; g.beginPath(); let on = false;
    xs.forEach((x, i) => { const y = ys[i]; if (!isFinite(y) || y < this.y[0] || y > this.y[1]) { on = false; return; }
      const X = this.tx(x), Y = this.ty(y); on ? g.lineTo(X, Y) : g.moveTo(X, Y); on = true; });
    g.stroke();
  }
  dot(x, y, color, label) {
    const g = this.ctx, X = this.tx(x), Y = this.ty(y);
    g.fillStyle = color; g.beginPath(); g.arc(X, Y, 5, 0, 2 * Math.PI); g.fill();
    if (label) { g.font = '600 12px system-ui, sans-serif'; g.textAlign = X > this.w * 0.6 ? 'right' : 'left'; g.fillText(label, X + (X > this.w * 0.6 ? -9 : 9), Y - 8); }
  }
  vline(x, color) { const g = this.ctx, X = this.tx(x); g.strokeStyle = color; g.setLineDash([4, 4]); g.lineWidth = 1.2;
    g.beginPath(); g.moveTo(X, this.pad.t); g.lineTo(X, this.h - this.pad.b); g.stroke(); g.setLineDash([]); }
}

const logspace = (a, b, n) => Array.from({length: n}, (_, i) => 10 ** (Math.log10(a) + (Math.log10(b) - Math.log10(a)) * i / (n - 1)));
const linspace = (a, b, n) => Array.from({length: n}, (_, i) => a + (b - a) * i / (n - 1));
const num = (v, d = 3) => Number(v).toLocaleString('el-GR', {maximumSignificantDigits: d});

// Base class: builds the box (controls + canvas + readout) and redraws on input and on resize.
class Sim {
  constructor(el) {
    this.el = el; el.classList.add('sim-box');
    el.innerHTML = `<div class="sim-controls">${this.controls()}</div><canvas></canvas><p class="sim-out"></p>`;
    this.canvas = el.querySelector('canvas'); this.out = el.querySelector('.sim-out');
    el.querySelectorAll('input, select').forEach(i => i.addEventListener('input', () => this.draw()));
    window.addEventListener('resize', () => this.draw());
    this.draw();
  }
  val(name) { const i = this.el.querySelector(`[name="${name}"]`); return i.type === 'range' ? +i.value : i.value; }
  slider(name, label, min, max, step, value) {
    return `<label>${label} <span data-show="${name}"></span><input type="range" name="${name}" min="${min}" max="${max}" step="${step}" value="${value}"></label>`;
  }
  show(name, text) { this.el.querySelector(`[data-show="${name}"]`).textContent = text; }
}

// Skin depth: choose the material and the frequency; see δ and the current profile.
class SkinSim extends Sim {
  static MATERIALS = {cu: ['Χαλκός', 1.68e-8, 1], al: ['Αλουμίνιο', 2.65e-8, 1], ss: ['Ανοξείδωτος χάλυβας', 7.2e-7, 1], fe: ['Μαλακός χάλυβας (μr≈100)', 1.6e-7, 100]};
  controls() {
    return `<label>Υλικό <select name="mat">${Object.entries(SkinSim.MATERIALS).map(([k, m]) => `<option value="${k}"${k === 'al' ? ' selected' : ''}>${m[0]}</option>`).join('')}</select></label>` +
      this.slider('logf', 'Συχνότητα', 1, 7, 0.001, Math.log10(400));
  }
  draw() {
    const [, rho, mur] = SkinSim.MATERIALS[this.val('mat')], f = 10 ** this.val('logf');
    const d = Math.sqrt(2 * rho / (2 * Math.PI * f * MU0 * mur)) * 1e3;           // mm
    this.show('logf', f >= 1e6 ? num(f / 1e6) + ' MHz' : f >= 1e3 ? num(f / 1e3) + ' kHz' : num(f) + ' Hz');
    const xmax = Math.min(Math.max(5 * d, 0.05), 20);
    const p = new Plot(this.canvas, {x: [0, xmax], y: [0, 1.05], xlabel: 'βάθος από την επιφάνεια (mm)', ylabel: '|J| / |J επιφάνειας|'});
    p.size(); p.axes();
    const xs = linspace(0, xmax, 200);
    p.curve(xs, xs.map(x => Math.exp(-x / d)), '#b8622b');
    p.dot(d, Math.exp(-1), '#b23a2a', `δ = ${num(d)} mm (37 %)`);
    this.out.innerHTML = `Βάθος διείσδυσης <b>δ = ${num(d)} mm</b>. Στα 3δ = ${num(3 * d)} mm έχει μείνει μόνο το 5 % της επιφανειακής πυκνότητας ρεύματος.` +
      (d < 1 ? ' Ένας έλεγχος δινορρευμάτων σε αυτή τη συχνότητα «βλέπει» μόνο την επιφάνεια.' : '');
  }
}

// Paschen: choose altitude and gap; see where the point sits on the breakdown curve.
class PaschenSim extends Sim {
  static A = 15; static B = 365; static G = 0.01;
  static vb(pd) { const k = Math.log(Math.log(1 + 1 / PaschenSim.G)); return PaschenSim.B * pd / (Math.log(PaschenSim.A * pd) - k); }
  static isa(h) { return h <= 11000 ? 1013.25 * (1 - 2.25577e-5 * h) ** 5.25588 : 226.32 * Math.exp(-(h - 11000) / 6341.6); }
  controls() { return this.slider('h', 'Ύψος', 0, 20000, 100, 12000) + this.slider('gap', 'Διάκενο', -1, 1, 0.01, 0); }
  draw() {
    const h = this.val('h'), gap = 10 ** this.val('gap');                         // gap in mm
    this.show('h', num(h / 1000, 3) + ' km'); this.show('gap', num(gap, 2) + ' mm');
    const p_hpa = PaschenSim.isa(h), pd = p_hpa * 0.750062 * gap / 10, V = PaschenSim.vb(pd);
    const k = Math.log(Math.log(1 + 1 / PaschenSim.G)), pdmin = Math.exp(k) / PaschenSim.A * 1.05;
    const plot = new Plot(this.canvas, {x: [0.3, 1000], y: [100, 1e5], xlog: true, ylog: true, xlabel: 'p · d (Torr · cm)', ylabel: 'τάση διάσπασης (V)'});
    plot.size(); plot.axes();
    const xs = logspace(pdmin, 1000, 300); plot.curve(xs, xs.map(PaschenSim.vb), '#b8622b');
    const g = plot.ctx; g.strokeStyle = '#8a8577'; g.setLineDash([4, 4]); g.beginPath(); g.moveTo(plot.tx(0.3), plot.ty(540)); g.lineTo(plot.tx(1000), plot.ty(540)); g.stroke(); g.setLineDash([]);
    if (pd > pdmin) plot.dot(pd, V, '#1d5f86', num(V, 3) + ' V');
    this.out.innerHTML = `Πίεση <b>${num(p_hpa, 3)} hPa</b>, p·d = ${num(pd, 3)} Torr·cm, τάση διάσπασης ≈ <b>${pd > pdmin ? num(V, 3) + ' V' : '—'}</b>.` +
      (pd > pdmin && V < 540 ? ' <b>Κάτω από τα 540 V</b> ενός δικτύου ±270 V DC: κίνδυνος τόξου.' : '') +
      ' Η διακεκομμένη γραμμή είναι τα 540 V.';
  }
}

// Dipole antenna: choose the length in wavelengths and the frequency; see the power pattern.
class AntennaSim extends Sim {
  controls() { return this.slider('L', 'Μήκος L / λ', 0.05, 2, 0.01, 0.5) + this.slider('f', 'Συχνότητα', 30, 1100, 1, 125); }
  pattern(th, L) { const kl2 = Math.PI * L, s = Math.sin(th); if (Math.abs(s) < 1e-6) return 0;
    return ((Math.cos(kl2 * Math.cos(th)) - Math.cos(kl2)) / s) ** 2; }
  draw() {
    const L = this.val('L'), f = this.val('f') * 1e6, lam = 299792458 / f;
    this.show('L', num(L, 2)); this.show('f', num(f / 1e6, 4) + ' MHz');
    const c = this.canvas, w = c.parentElement.clientWidth, h = Math.min(320, w * 0.75), r = window.devicePixelRatio || 1;
    c.width = w * r; c.height = h * r; c.style.width = w + 'px'; c.style.height = h + 'px';
    const g = c.getContext('2d'); g.setTransform(r, 0, 0, r, 0, 0); g.clearRect(0, 0, w, h);
    const cx = w / 2, cy = h / 2, R = h * 0.44, ths = linspace(0, 2 * Math.PI, 721), vals = ths.map(t => this.pattern(t, L)), mx = Math.max(...vals);
    g.strokeStyle = 'rgba(34,32,27,.18)'; g.lineWidth = 1;
    for (const q of [0.5, 1]) { g.beginPath(); g.arc(cx, cy, R * q, 0, 2 * Math.PI); g.stroke(); }
    g.beginPath(); g.moveTo(cx - R, cy); g.lineTo(cx + R, cy); g.moveTo(cx, cy - R); g.lineTo(cx, cy + R); g.stroke();
    g.strokeStyle = '#1d5f86'; g.lineWidth = 2.2; g.beginPath();
    ths.forEach((t, i) => { const rr = R * vals[i] / mx, X = cx + rr * Math.sin(t), Y = cy - rr * Math.cos(t); i ? g.lineTo(X, Y) : g.moveTo(X, Y); });
    g.stroke();
    g.strokeStyle = '#22201b'; g.lineWidth = 4; g.beginPath(); g.moveTo(cx, cy - R * 0.25); g.lineTo(cx, cy + R * 0.25); g.stroke();
    g.fillStyle = '#22201b'; g.font = '12px system-ui, sans-serif'; g.textAlign = 'left';
    g.fillText('κεραία (κατακόρυφη)', cx + 8, cy - R * 0.25);
    this.out.innerHTML = `Στα ${num(f / 1e6, 4)} MHz: λ = <b>${num(lam, 3)} m</b>, η κεραία έχει μήκος <b>${num(L * lam, 3)} m</b>. ` +
      `Μονόπολο λ/4 πάνω στην άτρακτο: <b>${num(lam / 4 * 100, 3)} cm</b>.` +
      (L > 1.05 ? ' Πάνω από 1 λ το διάγραμμα σπάει σε λοβούς: η κεραία στέλνει σε «λάθος» γωνίες.' : '');
  }
}

const Sims = {
  kinds: {skin: SkinSim, paschen: PaschenSim, antenna: AntennaSim},
  mount(root) { root.querySelectorAll('[data-sim]').forEach(el => { const K = Sims.kinds[el.dataset.sim]; if (K) new K(el); }); }
};

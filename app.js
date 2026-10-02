// Ego2Act page: lazy autoplay clips, case comparison and per-category failure carousels.
(function () {
  'use strict';
  var hasIO = 'IntersectionObserver' in window;

  function play(v) {
    if (!v.getAttribute('src')) v.src = v.dataset.src;
    var p = v.play(); if (p && p.catch) p.catch(function () {});
  }
  function unload(v) {
    if (v.getAttribute('src')) { v.pause(); v.removeAttribute('src'); v.load(); }
  }
  // A clip plays only while it is both in the viewport and (inside a carousel) in the visible part of the track.
  function sync(v) {
    if (v._vp && v._tr !== false) setTimeout(function () { if (v._vp && v._tr !== false) play(v); }, 200);
    else v.pause();
  }
  var vp = hasIO && new IntersectionObserver(function (es) {
    es.forEach(function (en) { en.target._vp = en.isIntersecting; sync(en.target); });
  }, { rootMargin: '150px 0px' });
  function watch(v, track) {
    if (!hasIO) { play(v); return; }
    vp.observe(v);
    if (track) {
      track._io = track._io || new IntersectionObserver(function (es) {
        es.forEach(function (en) { en.target._tr = en.isIntersecting; sync(en.target); });
      }, { root: track, threshold: 0.25 });
      v._tr = false; track._io.observe(v);
    }
  }

  function el(tag, cls, text) {
    var n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text != null) n.textContent = text;
    return n;
  }
  function media(base, label) {
    var box = el('div', 'media'), img = el('img', 'poster'), v = el('video');
    img.loading = 'lazy'; img.decoding = 'async'; img.alt = ''; img.src = base + '.webp';
    v.muted = true; v.loop = true; v.playsInline = true; v.preload = 'none';
    v.setAttribute('aria-label', label); v.dataset.src = base + '.mp4';
    box.appendChild(img); box.appendChild(v); watch(v);
    return box;
  }
  function cls(x) { if (x == null) return 'na'; x = Math.round(x);   // band follows the number shown on the badge
    return x >= 70 ? 'hi' : x >= 60 ? 'gd' : x >= 30 ? 'mid' : 'lo'; }
  function title(id) { return id.replace(/_/g, ' '); }

  // ---- failure carousels (markup is in the page)
  document.querySelectorAll('.car').forEach(function (car) {
    var track = car.querySelector('.track'), prev = car.querySelector('.prev'), next = car.querySelector('.next');
    track.querySelectorAll('video').forEach(function (v) { watch(v, track); });
    function step(dir) {
      var card = track.querySelector('.fcard');
      track.scrollBy({ left: dir * (card ? card.offsetWidth + 14 : track.clientWidth * 0.8), behavior: 'smooth' });
    }
    function ends() {
      prev.disabled = track.scrollLeft < 4;
      next.disabled = track.scrollLeft + track.clientWidth > track.scrollWidth - 4;
    }
    prev.onclick = function () { step(-1); };
    next.onclick = function () { step(1); };
    track.addEventListener('scroll', ends, { passive: true });
    track.addEventListener('keydown', function (ev) {
      if (ev.key === 'ArrowRight' || ev.key === 'ArrowLeft') { ev.preventDefault(); step(ev.key === 'ArrowRight' ? 1 : -1); }
    });
    window.addEventListener('resize', ends); ends();
  });
  document.addEventListener('click', function (ev) {      // "Paper frames" toggle: annotated figure strip
    var b = ev.target.closest('.fbtn'); if (!b) return;
    var card = b.closest('.fcard'), on = b.getAttribute('aria-pressed') !== 'true', fr = card.querySelector('.frames');
    if (!fr) {
      fr = el('img', 'frames'); fr.alt = 'Annotated frames from the paper'; fr.src = b.dataset.frames;
      card.querySelector('.media').appendChild(fr);
    }
    b.setAttribute('aria-pressed', on); card.classList.toggle('show-frames', on);
  });

  // ---- comparison: start image + human + six generators for one selected case
  fetch('data/examples.json').then(function (r) { return r.json(); }).then(function (D) {
    // small outline icons for the example cases; parts animate on hover / when selected
    var CASE_ICON = {
      make_coffee: '<svg viewBox="0 0 24 24" class="ci ci-coffee"><path d="M4 10h12v5a5 5 0 0 1-5 5H9a5 5 0 0 1-5-5z"/><path d="M16 12h1.5a2.5 2.5 0 0 1 0 5H16"/><path class="st" d="M8 7c0-1 1-1.5 1-2.5M12 7c0-1 1-1.5 1-2.5"/></svg>',
      line_marker_calculator: '<svg viewBox="0 0 24 24" class="ci ci-marker"><rect x="5" y="3" width="14" height="18" rx="2"/><path class="ln" pathLength="12" d="M12 6.5v11"/></svg>',
      pour_milk: '<svg viewBox="0 0 24 24" class="ci ci-milk"><g class="box"><path d="M7 8l2-4h6l2 4v12H7z"/><path d="M7 8h10"/></g><path class="drop" d="M5 14q-1 2 0 3"/></svg>',
      toothbrush_case: '<svg viewBox="0 0 24 24" class="ci ci-brush"><rect x="3" y="13" width="18" height="6" rx="3"/><g class="br"><path d="M6 10h11"/><path d="M15 8v2M17 8v2"/></g></svg>'
    };
    var sel = document.getElementById('cmp-sel'), cmp = document.getElementById('cmp');
    // Caption = [logo or person icon] name [score pill]; mirrors the markup tools/build.py writes.
    var LOGO = { seedance_2_0: ['bytedance', 'ByteDance'], kling_v3_pro: ['kuaishou', 'Kuaishou'], wan_2_7: ['alibaba', 'Alibaba'],
      grok_imagine_video_1_5: ['xai', 'xAI'], minimax_h3: ['minimax', 'MiniMax'], cosmos_3: ['nvidia', 'NVIDIA'] };
    var PERSON = '<svg class=pic viewBox="0 0 24 24" width=18 height=18 aria-hidden=true><circle cx="10" cy="7" r="4" fill="currentColor"/>' +
      '<path d="M2 21c0-4.4 3.6-8 8-8 1.6 0 3 .4 4.3 1.2" fill="currentColor"/><circle cx="17" cy="17" r="6" fill="#15803d"/>' +
      '<path d="M14.2 17.1l2 2 3.6-3.8" fill="none" stroke="#fff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>';
    function who(key, name) {
      var w = el('span', 'who');
      if (key === 'human') w.innerHTML = PERSON;
      else if (LOGO[key]) {
        var i = el('img'); i.src = 'assets/logos/' + LOGO[key][0] + '.png'; i.alt = LOGO[key][1]; i.width = i.height = 18;
        i.onerror = function () { i.remove(); }; w.appendChild(i);
      }
      w.appendChild(el('span', null, name)); return w;
    }
    function tile(node, key, cap, sc) {
      var f = el('figure', 'tile'); f.appendChild(node);
      var fc = el('figcaption'); fc.appendChild(who(key, cap));
      if (sc !== undefined) fc.appendChild(el('b', 'score ' + cls(sc), sc == null ? '–' : Math.round(sc)));
      f.appendChild(fc); return f;
    }
    function copyText(t, btn) {
      var done = function () { var o = btn.textContent; btn.textContent = 'Copied'; btn.classList.add('done');
        setTimeout(function () { btn.textContent = o; btn.classList.remove('done'); }, 1400); };
      if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(t).then(done, fb); else fb();
      function fb() { var a = document.createElement('textarea'); a.value = t; document.body.appendChild(a); a.select();
        try { document.execCommand('copy'); done(); } catch (e) {} document.body.removeChild(a); }
    }
    function copyImage(src, id, btn) {  // PNG to clipboard; falls back to downloading the original file
      function flash(t) { var o = btn.textContent; btn.textContent = t; btn.classList.add('done');
        setTimeout(function () { btn.textContent = o; btn.classList.remove('done'); }, 1400); }
      function download() { var a = document.createElement('a'); a.href = src; a.download = id + '_start.jpg';
        document.body.appendChild(a); a.click(); a.remove(); flash('Downloaded'); }
      if (!(navigator.clipboard && window.ClipboardItem)) return download();
      var png = new Promise(function (res, rej) {
        var im = new Image(); im.onload = function () { var cv = document.createElement('canvas');
          cv.width = im.naturalWidth; cv.height = im.naturalHeight; cv.getContext('2d').drawImage(im, 0, 0);
          cv.toBlob(function (b) { b ? res(b) : rej(); }, 'image/png'); }; im.onerror = rej; im.src = src; });
      navigator.clipboard.write([new ClipboardItem({ 'image/png': png })]).then(function () { flash('Copied'); }, download);
    }
    function showCase(id) {
      var c = D.cases[id];
      cmp.querySelectorAll('video').forEach(function (v) { unload(v); if (hasIO) vp.unobserve(v); });
      cmp.textContent = '';
      var st = el('div', 'media'), im = el('img', 'poster');
      im.src = c.start; im.alt = 'Start image'; im.loading = 'lazy'; st.appendChild(im);
      if (c.prompt) {  // hover actions: take the exact prompt and start image to try another video model
        var acts = el('div', 'try');
        var bp = el('button', 'tbtn', 'Copy prompt'); bp.type = 'button';
        bp.addEventListener('click', function () { copyText(c.prompt, bp); });
        var bi = el('button', 'tbtn', 'Copy image'); bi.type = 'button';
        bi.addEventListener('click', function () { copyImage(c.start_full || c.start, id, bi); });
        acts.appendChild(bp); acts.appendChild(bi); st.appendChild(acts);
        st.appendChild(el('div', 'pview', c.prompt));
        st.appendChild(el('span', 'tryhint', 'Try it yourself \u2014 hover to copy'));
      }
      cmp.appendChild(tile(st, null, 'Start image'));
      if (c.human) cmp.appendChild(tile(media(c.human, 'Human (correct) recording'), 'human', 'Human (correct)'));
      D.models.forEach(function (m) {
        var it = c.models[m[0]];
        if (it) cmp.appendChild(tile(media(it.v, m[1]), m[0], m[1], it.f));
      });
      var g = document.getElementById('cmp-goal'); g.textContent = '';
      g.appendChild(el('span', null, title(id))); g.appendChild(document.createTextNode(c.goal));
      sel.querySelectorAll('button').forEach(function (b) { b.setAttribute('aria-selected', b.dataset.c === id); });
    }
    D.compare.forEach(function (id) {
      var b = el('button', 'chip cchip', ''); b.type = 'button'; b.dataset.c = id; b.setAttribute('role', 'tab');
      b.innerHTML = (CASE_ICON[id] || '') + '<span>' + title(id) + '</span>';
      b.onclick = function () { showCase(id); }; sel.appendChild(b);
    });
    showCase(D.compare[0]);
  });
})();

// Heatmap metric toggle + hover tooltip, hero pause off-screen, active section in the nav.
(function () {
  'use strict';
  var wrap = document.querySelector('.hm-wrap'), tip = wrap && wrap.querySelector('.hm-tip');
  document.querySelectorAll('.hm-ctl .chip').forEach(function (b) {
    b.onclick = function () {
      document.querySelectorAll('.hm-ctl .chip').forEach(function (x) { x.setAttribute('aria-selected', x === b); });
      document.querySelectorAll('table.hm').forEach(function (t) { t.hidden = t.dataset.m !== b.dataset.m; });
    };
  });
  if (wrap) {
    wrap.addEventListener('mouseover', function (ev) {
      var td = ev.target.closest('td[data-t]'); if (!td) { tip.classList.remove('on'); return; }
      tip.textContent = td.dataset.t;
      var w = wrap.getBoundingClientRect(), r = td.getBoundingClientRect();
      tip.classList.add('on');
      var x = r.left - w.left + r.width / 2 - tip.offsetWidth / 2;
      tip.style.left = Math.max(0, Math.min(x, w.width - tip.offsetWidth)) + 'px';
      tip.style.top = (r.top - w.top - tip.offsetHeight - 6) + 'px';
    });
    wrap.addEventListener('mouseleave', function () { tip.classList.remove('on'); });
  }
  if (!('IntersectionObserver' in window)) return;
  var hero = document.querySelector('.herovid');
  if (hero) new IntersectionObserver(function (es) {
    es.forEach(function (e) { if (e.isIntersecting) { var p = hero.play(); if (p && p.catch) p.catch(function () {}); } else hero.pause(); });
  }).observe(hero);
  var links = {};
  document.querySelectorAll('.toc a').forEach(function (a) { links[a.getAttribute('href').slice(1)] = a; });
  var io = new IntersectionObserver(function (es) {
    es.forEach(function (e) {
      if (!e.isIntersecting || !links[e.target.id]) return;
      Object.keys(links).forEach(function (k) { links[k].classList.toggle('on', k === e.target.id); });
      var a = links[e.target.id], bar = a.parentNode;
      bar.scrollTo({ left: a.offsetLeft - (bar.clientWidth - a.offsetWidth) / 2, behavior: 'smooth' });
    });
  }, { rootMargin: '-45% 0px -50% 0px' });
  Object.keys(links).forEach(function (id) { var s = document.getElementById(id); if (s) io.observe(s); });
})();

// judge tree: casual one-paragraph explanation on hover / focus
(function () {
  var wrap = document.querySelector('.jtree-wrap'); if (!wrap) return;
  var tip = wrap.querySelector('.jtip');
  function show(g) {
    tip.textContent = g.getAttribute('data-tip');
    var r = g.getBoundingClientRect(), w = wrap.getBoundingClientRect();
    tip.classList.add('on');
    var left = Math.min(Math.max(r.left - w.left + r.width / 2 - tip.offsetWidth / 2, 0), w.width - tip.offsetWidth);
    tip.style.left = left + 'px'; tip.style.top = (r.bottom - w.top + 8) + 'px';
  }
  function hide() { tip.classList.remove('on'); }
  wrap.querySelectorAll('[data-tip]').forEach(function (g) {
    g.addEventListener('mouseenter', function () { show(g); }); g.addEventListener('mouseleave', hide);
    g.addEventListener('focus', function () { show(g); }); g.addEventListener('blur', hide);
    g.addEventListener('click', function () { show(g); });
  });
})();

// failures: tiles open one category at a time (accordion); others stay hidden and unloaded
(function () {
  var tiles = document.querySelectorAll('.fov-t'); if (!tiles.length) return;
  tiles.forEach(function (a) {
    a.setAttribute('role', 'button'); a.setAttribute('aria-expanded', 'false');
    a.addEventListener('click', function (e) {
      e.preventDefault();
      var id = a.getAttribute('href').slice(1), panel = document.getElementById(id), was = a.getAttribute('aria-expanded') === 'true';
      tiles.forEach(function (t) { t.setAttribute('aria-expanded', 'false'); });
      document.querySelectorAll('#q4 .fcat.open').forEach(function (c) {
        c.classList.remove('open'); c.querySelectorAll('video').forEach(function (v) { v.pause(); });
      });
      if (!was && panel) {
        a.setAttribute('aria-expanded', 'true'); panel.classList.add('open');
        panel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }
    });
  });
  // open the first category by default so people see the tiles expand
  var first = tiles[0], fp = first && document.getElementById(first.getAttribute('href').slice(1));
  if (fp) { first.setAttribute('aria-expanded', 'true'); fp.classList.add('open'); }
})();

// key findings: fade in and count the headline numbers up when scrolled into view
(function () {
  var cards = document.querySelectorAll('.kf'); if (!cards.length) return;
  var still = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var io = new IntersectionObserver(function (es) {
    es.forEach(function (e) {
      if (!e.isIntersecting) return; io.unobserve(e.target);
      var c = e.target, i = Array.prototype.indexOf.call(cards, c);
      setTimeout(function () { c.classList.add('in'); }, still ? 0 : i * 90);
      var n = c.querySelector('.kf-num'); if (!n || still) return;
      var to = parseFloat(n.textContent), dec = (n.textContent.split('.')[1] || '').length, t0 = null;
      function step(ts) { t0 = t0 || ts; var k = Math.min((ts - t0) / 900, 1), v = to * (1 - Math.pow(1 - k, 3));
        n.textContent = v.toFixed(dec); if (k < 1) requestAnimationFrame(step); }
      requestAnimationFrame(step);
    });
  }, { threshold: 0.25 });
  cards.forEach(function (c) { io.observe(c); });
})();

// BibTeX copy button
(function () {
  var b = document.querySelector('.bib .copy'); if (!b) return;
  b.addEventListener('click', function () {
    var txt = b.parentNode.querySelector('code').textContent;
    function ok() { b.textContent = 'Copied'; b.classList.add('done'); setTimeout(function () { b.textContent = 'Copy'; b.classList.remove('done'); }, 1600); }
    if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(txt).then(ok, fallback); else fallback();
    function fallback() { var a = document.createElement('textarea'); a.value = txt; document.body.appendChild(a); a.select();
      try { document.execCommand('copy'); ok(); } catch (e) {} document.body.removeChild(a); }
  });
})();

// "More analysis" charts: animate on first open, shared tooltip, model highlight, per-video toggle
(function () {
  var d = document.querySelector('details.charts'); if (!d) return;
  function start() {
    if (d.open) requestAnimationFrame(function () { requestAnimationFrame(function () { d.classList.add('play'); }); });
    else d.classList.remove('play');   // stops the looping dash animation while closed
  }
  d.addEventListener('toggle', start); start();
  d.querySelectorAll('.chbox').forEach(function (box) {
    var tip = box.querySelector('.ctip'), svg = box.querySelector('svg');
    function show(g) {
      tip.textContent = g.getAttribute('data-tip');
      var b = box.getBoundingClientRect(), r = g.getBoundingClientRect();
      tip.classList.add('on');
      var x = r.left - b.left + r.width / 2 - tip.offsetWidth / 2, y = r.top - b.top - tip.offsetHeight - 8;
      if (y < 0) y = r.bottom - b.top + 8;
      tip.style.left = Math.max(0, Math.min(b.width - tip.offsetWidth, x)) + 'px'; tip.style.top = y + 'px';
      if (g.matches('.mdl,.all')) { svg.classList.add('hov'); g.classList.add('on'); }
    }
    function hide() {
      tip.classList.remove('on'); svg.classList.remove('hov');
      svg.querySelectorAll('.on').forEach(function (e) { e.classList.remove('on'); });
    }
    svg.querySelectorAll('[data-tip]').forEach(function (g) {
      g.addEventListener('mouseenter', function () { hide(); show(g); }); g.addEventListener('mouseleave', hide);
      g.addEventListener('focus', function () { hide(); show(g); }); g.addEventListener('blur', hide);
      g.addEventListener('click', function () { hide(); show(g); });
    });
  });
  var t = d.querySelector('.vtog'), sc = d.querySelector('.sc-ch');
  if (t) t.addEventListener('change', function () { sc.classList.toggle('vshow', t.checked); });
})();

// quote above the showcase: fast typing effect, caret keeps blinking afterwards
(function () {
  var q = document.querySelector('.lead-q em'); if (!q) return;
  var full = q.textContent, caret = document.createElement('span'); caret.className = 'caret';
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) { q.appendChild(caret); return; }
  q.textContent = ''; var txt = document.createTextNode(''); q.appendChild(txt); q.appendChild(caret);
  // type once, fast; the caret keeps blinking
  function run() { var i = 0; (function type() { txt.data = full.slice(0, ++i); if (i < full.length) setTimeout(type, 14); })(); }
  run();
})();

// suite construction strip: steps assemble in order and counters count up once scrolled into view
(function () {
  var b = document.querySelector('.build'); if (!b) return;
  var still = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  function run() {
    b.classList.add('in'); if (still) return;
    b.querySelectorAll('.bn').forEach(function (n, i) {
      var to = +n.getAttribute('data-to'), t0 = null;
      n.textContent = '0';
      setTimeout(function () { requestAnimationFrame(function step(ts) {
        t0 = t0 || ts; var k = Math.min((ts - t0) / 1000, 1);
        n.textContent = Math.round(to * (1 - Math.pow(1 - k, 3))).toLocaleString('en-US');
        if (k < 1) requestAnimationFrame(step); }); }, i * 350);
    });
  }
  if (!('IntersectionObserver' in window)) { b.classList.add('in'); return; }
  var io = new IntersectionObserver(function (es) { if (es[0].isIntersecting) { io.disconnect(); run(); } }, { threshold: 0.35 });
  io.observe(b);
})();

// SCRIPT — interactive touches and the 3D scene.
// The only thing you might want to change is the "3D SETTINGS" block below.

document.documentElement.classList.add('js');

var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
var finePointer = window.matchMedia('(hover: hover) and (pointer: fine)').matches;

// Current Persian (solar) year in the footer, e.g. ۱۴۰۵
var year = document.getElementById('year');
if (year) {
  try {
    year.textContent = new Intl.DateTimeFormat('fa-IR-u-ca-persian', { year: 'numeric' })
      .format(new Date()).replace(/[^۰-۹]/g, '');
  } catch (e) {}
}

// Light / dark mode button
var root = document.documentElement;
var themeBtn = document.getElementById('theme-toggle');
function isDark() {
  return (root.dataset.theme || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')) === 'dark';
}
if (themeBtn) {
  themeBtn.addEventListener('click', function () {
    var next = isDark() ? 'light' : 'dark';
    root.dataset.theme = next;
    try { localStorage.setItem('theme', next); } catch (e) {}
    document.dispatchEvent(new Event('themechange'));
  });
}

// Mobile menu
var menuBtn = document.getElementById('menu-toggle');
var nav = document.getElementById('nav');
if (menuBtn && nav) {
  var setMenu = function (open) {
    nav.classList.toggle('open', open);
    menuBtn.setAttribute('aria-expanded', String(open));
    menuBtn.setAttribute('aria-label', open ? 'بستن منو' : 'باز کردن منو');
  };
  menuBtn.addEventListener('click', function () { setMenu(!nav.classList.contains('open')); });
  nav.querySelectorAll('a').forEach(function (a) { a.addEventListener('click', function () { setMenu(false); }); });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') setMenu(false); });
}

// Thin line under the header once you scroll
var header = document.querySelector('.site-header');
var onScroll = function () { if (header) header.classList.toggle('scrolled', window.scrollY > 8); };
window.addEventListener('scroll', onScroll, { passive: true });
onScroll();

// Fade sections in as they scroll into view
var items = document.querySelectorAll('.reveal');
if ('IntersectionObserver' in window) {
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) { entry.target.classList.add('visible'); io.unobserve(entry.target); }
    });
  }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
  items.forEach(function (el) { io.observe(el); });
} else {
  items.forEach(function (el) { el.classList.add('visible'); });
}

// Highlight the menu link for the section you're looking at
var links = document.querySelectorAll('.nav a');
if ('IntersectionObserver' in window) {
  var navIo = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (!entry.isIntersecting) return;
      links.forEach(function (a) { a.classList.toggle('active', a.getAttribute('href') === '#' + entry.target.id); });
    });
  }, { rootMargin: '-45% 0px -50% 0px' });
  links.forEach(function (a) { var s = document.querySelector(a.getAttribute('href')); if (s) navIo.observe(s); });
}

// 3D tilt: cards lean toward the mouse (computers only)
if (finePointer && !reduceMotion) {
  document.querySelectorAll('.tilt').forEach(function (card) {
    card.addEventListener('pointermove', function (e) {
      var r = card.getBoundingClientRect();
      var x = (e.clientX - r.left) / r.width - 0.5;
      var y = (e.clientY - r.top) / r.height - 0.5;
      card.classList.add('tilting');
      card.style.transform = 'rotateX(' + (-y * 10).toFixed(2) + 'deg) rotateY(' + (x * 12).toFixed(2) + 'deg)';
    });
    card.addEventListener('pointerleave', function () {
      card.classList.remove('tilting');
      card.style.transform = '';
    });
  });
}

// ================= 3D SCENE (top of the page) =================
// ✏️ 3D SETTINGS — colours of the shapes (light mode, dark mode)
var SHAPE_COLOR_LIGHT = 0xc2502e;
var SHAPE_COLOR_DARK = 0xec7a55;
var RING_COLOR_LIGHT = 0x1c1b19;
var RING_COLOR_DARK = 0xf1ede6;

(function () {
  var holder = document.getElementById('hero-3d');
  if (!holder || !window.THREE) return; // if 3D can't load, a simple 2D ball shows instead

  var renderer;
  try {
    renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  } catch (e) { return; }
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    holder.appendChild(renderer.domElement);

  var scene = new THREE.Scene();
  var camera = new THREE.PerspectiveCamera(40, 1, 0.1, 100);
  camera.position.set(0, 0, 9);

  var group = new THREE.Group();
  scene.add(group);

  // Main shape: a glossy knot
  var mainMat = new THREE.MeshPhysicalMaterial({ color: SHAPE_COLOR_LIGHT, roughness: 0.25, metalness: 0.2, clearcoat: 1, clearcoatRoughness: 0.15 });
  var knot = new THREE.Mesh(new THREE.TorusKnotGeometry(1.35, 0.42, 220, 32, 2, 3), mainMat);
  group.add(knot);

  // Thin ring around it
  var ringMat = new THREE.MeshStandardMaterial({ color: RING_COLOR_LIGHT, roughness: 0.4, metalness: 0.6 });
  var ring = new THREE.Mesh(new THREE.TorusGeometry(2.7, 0.025, 16, 160), ringMat);
  ring.rotation.x = Math.PI / 2.3;
  group.add(ring);

  // Small floating spheres
  var balls = [];
  var ballMat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.3, metalness: 0.1 });
  for (var i = 0; i < 7; i++) {
    var b = new THREE.Mesh(new THREE.SphereGeometry(0.08 + Math.random() * 0.12, 24, 24), i % 2 ? ballMat : mainMat);
    b.userData = { r: 2.2 + Math.random() * 1.2, speed: 0.15 + Math.random() * 0.25, phase: Math.random() * Math.PI * 2, tilt: (Math.random() - 0.5) * 1.6 };
    group.add(b);
    balls.push(b);
  }

  // Lights
  scene.add(new THREE.AmbientLight(0xffffff, 0.3));
  var key = new THREE.DirectionalLight(0xffffff, 0.9); key.position.set(4, 5, 6); scene.add(key);
  var warm = new THREE.PointLight(0xffb38a, 0.7, 30); warm.position.set(-5, -2, 4); scene.add(warm);
  var cool = new THREE.PointLight(0x8fb3ff, 0.8, 30); cool.position.set(5, -4, -3); scene.add(cool);

  function applyTheme() {
    var dark = isDark();
    mainMat.color.setHex(dark ? SHAPE_COLOR_DARK : SHAPE_COLOR_LIGHT);
    ringMat.color.setHex(dark ? RING_COLOR_DARK : RING_COLOR_LIGHT);
    ballMat.color.setHex(dark ? 0xd9d2c5 : 0xffffff);
  }
  applyTheme();
  document.addEventListener('themechange', applyTheme);
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', applyTheme);

  function resize() {
    var w = holder.clientWidth, h = holder.clientHeight;
    if (!w || !h) return;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.position.z = w < 500 ? 12 : 12.5;
    camera.updateProjectionMatrix();
  }
  window.addEventListener('resize', resize);
  resize();

  // Follow the mouse
  var target = { x: 0, y: 0 };
  window.addEventListener('pointermove', function (e) {
    target.x = (e.clientX / window.innerWidth - 0.5) * 0.8;
    target.y = (e.clientY / window.innerHeight - 0.5) * 0.6;
  }, { passive: true });

  // Only animate while the top of the page is on screen (saves battery)
  var visible = true;
  if ('IntersectionObserver' in window) {
    new IntersectionObserver(function (e) { visible = e[0].isIntersecting; }).observe(holder);
  }

  var clock = new THREE.Clock();
  function frame() {
    var t = clock.getElapsedTime();
    knot.rotation.x = t * 0.18;
    knot.rotation.y = t * 0.25;
    group.rotation.y += (target.x - group.rotation.y) * 0.05;
    group.rotation.x += (target.y - group.rotation.x) * 0.05;
    group.position.y = Math.sin(t * 0.8) * 0.15;
    balls.forEach(function (b) {
      var d = b.userData, a = t * d.speed + d.phase;
      b.position.set(Math.cos(a) * d.r, Math.sin(a * 1.3) * d.tilt, Math.sin(a) * d.r);
    });
    renderer.render(scene, camera);
  }

  holder.classList.add('ready');
  if (reduceMotion) { frame(); return; } // still image for people who prefer less motion
  renderer.setAnimationLoop(function () { if (visible) frame(); });
})();

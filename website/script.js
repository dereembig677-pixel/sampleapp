// SCRIPT — small interactive touches. You don't need to edit this file.

document.documentElement.classList.add('js');

// Current year in the footer
var year = document.getElementById('year');
if (year) year.textContent = new Date().getFullYear();

// Light / dark mode button
var root = document.documentElement;
var themeBtn = document.getElementById('theme-toggle');
if (themeBtn) {
  themeBtn.addEventListener('click', function () {
    var current = root.dataset.theme ||
      (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    var next = current === 'dark' ? 'light' : 'dark';
    root.dataset.theme = next;
    try { localStorage.setItem('theme', next); } catch (e) {}
  });
}

// Mobile menu
var menuBtn = document.getElementById('menu-toggle');
var nav = document.getElementById('nav');
if (menuBtn && nav) {
  var setMenu = function (open) {
    nav.classList.toggle('open', open);
    menuBtn.setAttribute('aria-expanded', String(open));
    menuBtn.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
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
var sections = Array.prototype.map.call(links, function (a) { return document.querySelector(a.getAttribute('href')); });
if ('IntersectionObserver' in window) {
  var navIo = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (!entry.isIntersecting) return;
      links.forEach(function (a) { a.classList.toggle('active', a.getAttribute('href') === '#' + entry.target.id); });
    });
  }, { rootMargin: '-45% 0px -50% 0px' });
  sections.forEach(function (s) { if (s) navIo.observe(s); });
}

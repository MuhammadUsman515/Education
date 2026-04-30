/* EduManage Pro — Main JavaScript */

// ── Sidebar Toggle ──────────────────────────────────────────────
const sidebar = document.getElementById('sidebar');
const menuBtn = document.getElementById('menuToggle');
if (menuBtn && sidebar) {
  menuBtn.addEventListener('click', () => sidebar.classList.toggle('open'));
}

// Auto-close sidebar on mobile when link is clicked
document.querySelectorAll('.sidebar .nav-link').forEach(link => {
  link.addEventListener('click', () => {
    if (window.innerWidth < 768) sidebar.classList.remove('open');
  });
});

// ── Active Nav Link ─────────────────────────────────────────────
(function highlightActive() {
  const path = window.location.pathname;
  document.querySelectorAll('.sidebar .nav-link').forEach(link => {
    const href = link.getAttribute('href');
    if (href && path.startsWith(href) && href !== '/') {
      link.classList.add('active');
    }
  });
})();

// ── Auto-dismiss alerts ─────────────────────────────────────────
document.querySelectorAll('.alert-auto-dismiss').forEach(el => {
  setTimeout(() => {
    el.style.transition = 'opacity .5s';
    el.style.opacity = '0';
    setTimeout(() => el.remove(), 500);
  }, 4000);
});

// ── Confirm Delete ──────────────────────────────────────────────
document.querySelectorAll('[data-confirm]').forEach(el => {
  el.addEventListener('click', e => {
    const msg = el.getAttribute('data-confirm') || 'Are you sure?';
    if (!confirm(msg)) e.preventDefault();
  });
});

// ── Form confirm on submit ──────────────────────────────────────
document.querySelectorAll('form[data-confirm]').forEach(form => {
  form.addEventListener('submit', e => {
    const msg = form.getAttribute('data-confirm') || 'Are you sure?';
    if (!confirm(msg)) e.preventDefault();
  });
});

// ── Topbar Page Title from H1 ───────────────────────────────────
(function setTopbarTitle() {
  const h1 = document.querySelector('.page-title');
  const topbar = document.querySelector('.topbar-title');
  if (h1 && topbar) topbar.textContent = h1.textContent;
})();

// ── DataTable init (if library present) ────────────────────────
if (typeof $.fn !== 'undefined' && typeof $.fn.DataTable !== 'undefined') {
  document.querySelectorAll('.datatable').forEach(table => {
    $(table).DataTable({
      responsive: true,
      pageLength: 25,
      language: { search: '', searchPlaceholder: 'Search...' },
    });
  });
}

// ── Chart defaults ──────────────────────────────────────────────
if (typeof Chart !== 'undefined') {
  Chart.defaults.font.family = 'Inter, -apple-system, sans-serif';
  Chart.defaults.font.size = 12;
  Chart.defaults.color = '#64748b';
  Chart.defaults.plugins.legend.labels.usePointStyle = true;
  Chart.defaults.plugins.legend.labels.padding = 20;
}

// ── Fee amount auto-fill ────────────────────────────────────────
const feeStructureSelect = document.getElementById('fee_structure_id');
if (feeStructureSelect) {
  feeStructureSelect.addEventListener('change', function() {
    const selected = this.options[this.selectedIndex];
    const amountDue = document.getElementById('amount_due');
    if (amountDue && selected.dataset.amount) {
      amountDue.value = selected.dataset.amount;
    }
  });
}

// ── Print button ────────────────────────────────────────────────
document.querySelectorAll('.btn-print').forEach(btn => {
  btn.addEventListener('click', () => window.print());
});

// ── Tooltip init ────────────────────────────────────────────────
if (typeof bootstrap !== 'undefined') {
  const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
  tooltips.forEach(el => new bootstrap.Tooltip(el));
  const popovers = document.querySelectorAll('[data-bs-toggle="popover"]');
  popovers.forEach(el => new bootstrap.Popover(el));
}

// ── Subject filter for attendance ──────────────────────────────
const subjectFilter = document.getElementById('subject_filter');
if (subjectFilter) {
  subjectFilter.addEventListener('change', function() {
    const url = new URL(window.location);
    url.searchParams.set('subject_id', this.value);
    window.location = url.toString();
  });
}

// ── Search form debounce ────────────────────────────────────────
const searchInput = document.getElementById('searchInput');
if (searchInput) {
  let debounceTimer;
  searchInput.addEventListener('input', function() {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      const form = this.closest('form');
      if (form) form.submit();
    }, 400);
  });
}

// ── Number formatting ───────────────────────────────────────────
function formatCurrency(amount) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount);
}

// ── Animate stat numbers on load ────────────────────────────────
function animateNumbers() {
  document.querySelectorAll('.stat-number[data-target]').forEach(el => {
    const target = parseInt(el.dataset.target, 10);
    let current = 0;
    const step = Math.ceil(target / 40);
    const timer = setInterval(() => {
      current = Math.min(current + step, target);
      el.textContent = current.toLocaleString();
      if (current >= target) clearInterval(timer);
    }, 30);
  });
}
document.addEventListener('DOMContentLoaded', animateNumbers);

// ── Mobile overlay close ────────────────────────────────────────
document.addEventListener('click', e => {
  if (window.innerWidth < 768 && sidebar && sidebar.classList.contains('open')) {
    if (!sidebar.contains(e.target) && (!menuBtn || !menuBtn.contains(e.target))) {
      sidebar.classList.remove('open');
    }
  }
});

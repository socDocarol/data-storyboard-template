/* Browser shell: hash routing, one bookmarkable selection, record dialog, menu.
   The server owns the data; this file only mirrors the URL fragment into Shiny
   (`dashboard_state`) and keeps native controls, focus, and history in sync. */
(() => {
  'use strict';
  const start = () => {
    const header = document.getElementById('city-header');
    const menu = document.getElementById('city-menu');
    const dialog = document.getElementById('record-dialog');
    const main = document.getElementById('main');
    const routes = new Set([...document.querySelectorAll('[data-route]')].map(section => section.dataset.route));
    const defaultSample = main.dataset.defaultSample || '';
    // Selection keys that survive switching to another data source.
    const keepOnSourceChange = new Set(['condition', 'compare_by', 'order']);
    let currentPage = '', lastRecord = '', pendingDrill = false, searchTimer, ready = false, searchFocus = null;
    const read = () => {
      const [route, query = ''] = location.hash.slice(1).split('?');
      return {page: routes.has(route) ? route : 'home', params: new URLSearchParams(query)};
    };
    const href = (page, params) => `#${page}?${params.toString()}`;
    const reveal = () => header.classList.remove('is-scroll-hidden');
    const send = () => {
      if (ready && window.Shiny && Shiny.setInputValue) {
        const {params} = read();
        Shiny.setInputValue('dashboard_state', {sample: defaultSample, ...Object.fromEntries(params)}, {priority: 'event'});
      }
    };
    const syncDialog = () => {
      const record = read().params.get('record');
      const content = dialog.querySelector('[data-record-content]');
      if (record && content?.dataset.recordContent === record) {
        if (!dialog.open) {
          lastRecord = record;
          dialog.showModal();
          dialog.querySelector('#record-title').focus();
        }
      } else if (dialog.open) {
        dialog.close();
        const previous = [...document.querySelectorAll('[data-record-id]')].find(e => e.dataset.recordId === lastRecord);
        (previous || document.querySelector(`[data-route="${read().page}"] h1`)).focus({preventScroll: true});
      }
    };
    const route = () => {
      const {page, params} = read();
      document.querySelectorAll('[data-route]').forEach(section => { section.hidden = section.dataset.route !== page; });
      document.querySelectorAll('[data-page]').forEach(link => {
        link.href = href(link.dataset.page, params);
        if (link.dataset.page === page) link.setAttribute('aria-current', 'page');
        else link.removeAttribute('aria-current');
      });
      for (const [key, fallback] of [['sample', defaultSample], ['condition', 'ready']]) {
        const control = document.getElementById(key);
        if (control) control.value = params.get(key) || fallback;
      }
      menu.open = false;
      reveal();
      if (currentPage && page !== currentPage) {
        document.querySelector(`[data-route="${page}"] h1`).focus({preventScroll: true});
        window.scrollTo({top: 0, behavior: 'instant'});
      }
      currentPage = page;
      syncDialog();
      send();
      window.dispatchEvent(new Event('resize'));
    };
    const change = (key, value, replace = false) => {
      const {page, params} = read();
      if ((params.get(key) || '') === value) return;
      params.delete('record');
      if (key === 'sample') [...params.keys()].filter(k => !keepOnSourceChange.has(k)).forEach(k => params.delete(k));
      if (key === 'compare_by') ['left', 'right'].forEach(k => params.delete(k));
      if (value) params.set(key, value); else params.delete(key);
      if (replace) { history.replaceState(null, '', href(page, params)); route(); }
      else location.hash = href(page, params);
    };
    const closeRecord = () => change('record', '');
    dialog.addEventListener('cancel', event => { event.preventDefault(); closeRecord(); });
    document.addEventListener('change', event => {
      const key = event.target.dataset.state || (['sample', 'condition'].includes(event.target.id) ? event.target.id : null);
      if (key && key !== 'query') change(key, event.target.value);
    });
    document.addEventListener('input', event => {
      if (event.target.dataset.state !== 'query') return;
      clearTimeout(searchTimer);
      const value = event.target.value;
      searchTimer = setTimeout(() => change('query', value, true), 350);
    });
    document.addEventListener('click', event => {
      if (event.target.closest('[data-close-record]')) closeRecord();
      const link = event.target.closest('a');
      if (link && !event.ctrlKey && !event.metaKey && !event.shiftKey && event.button === 0) {
        const target = link.getAttribute('href');
        if (link.classList.contains('skip-link')) {
          event.preventDefault(); main.focus();
        } else if (target?.startsWith('#') && target !== '#main') {
          const destination = target.slice(1).split('?')[0];
          if (routes.has(destination)) {
            event.preventDefault();
            pendingDrill = link.hasAttribute('data-drill');
            const {page, params} = read();
            const next = target.includes('?') ? new URLSearchParams(target.split('?')[1]) : params;
            location.hash = href(link.hasAttribute('data-keep-page') ? page : destination, next);
          }
        }
      }
      if (!menu.contains(event.target)) menu.open = false;
    });
    document.addEventListener('keydown', event => {
      if (event.key === 'Escape' && menu.open) { menu.open = false; menu.querySelector('summary').focus(); }
    });
    new MutationObserver(syncDialog).observe(document.getElementById('record_details'), {childList: true, subtree: true});
    new MutationObserver(() => {
      if (searchFocus && read().page === 'explore') {
        const field = document.getElementById('search');
        if (field && document.activeElement === document.body) {
          field.focus({preventScroll: true});
          field.setSelectionRange(...searchFocus);
        }
        searchFocus = null;
      }
    }).observe(document.getElementById('filters'), {childList: true, subtree: true});
    new MutationObserver(() => {
      if (pendingDrill && document.getElementById('drill-title')) {
        document.getElementById('drill-title').focus({preventScroll: true}); pendingDrill = false;
      }
    }).observe(document.getElementById('overview'), {childList: true, subtree: true});
    window.addEventListener('hashchange', route);
    if (window.jQuery) {
      jQuery(document).on('shiny:sessioninitialized', () => { ready = true; send(); });
      jQuery(document).on('shiny:value', event => {
        const field = document.activeElement;
        if (event.name === 'filters' && field?.id === 'search') searchFocus = [field.selectionStart, field.selectionEnd];
      });
    }
    route();
    header.addEventListener('focusin', reveal);
    menu.addEventListener('toggle', reveal);
    let previous = window.scrollY, pending = false;
    window.addEventListener('scroll', () => {
      if (pending) return;
      pending = true;
      requestAnimationFrame(() => {
        const current = window.scrollY;
        const pinned = current <= 16 || menu.open || header.contains(document.activeElement);
        if (pinned || current < previous) reveal();
        else if (current > 96 && current > previous) header.classList.add('is-scroll-hidden');
        previous = current; pending = false;
      });
    }, {passive: true});
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start);
  else start();
})();

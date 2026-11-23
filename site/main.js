for (const button of document.querySelectorAll('[data-copy]')) {
  if (!navigator.clipboard?.writeText) continue;
  button.hidden = false;
  const command = button.closest('.install').querySelector('code');
  const status = button.closest('.install').querySelector('[role="status"]');
  button.addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(command.textContent);
      status.textContent = 'Command copied.';
    } catch {
      status.textContent = 'Clipboard unavailable. Select the command to copy it.';
    }
  });
}

for (const list of document.querySelectorAll('[role="tablist"]')) {
  const tabs = [...list.querySelectorAll('[role="tab"]')];
  const select = (tab) => {
    for (const t of tabs) {
      t.setAttribute('aria-selected', t === tab);
      t.tabIndex = t === tab ? 0 : -1;
      document.getElementById(t.getAttribute('aria-controls')).hidden = t !== tab;
    }
  };
  list.hidden = false;
  select(tabs[0]);
  list.addEventListener('click', (event) => event.target.role === 'tab' && select(event.target));
  list.addEventListener('keydown', (event) => {
    const step = { ArrowRight: 1, ArrowLeft: -1 }[event.key];
    if (!step) return;
    const next = tabs[(tabs.indexOf(event.target) + step + tabs.length) % tabs.length];
    select(next);
    next.focus();
  });
}

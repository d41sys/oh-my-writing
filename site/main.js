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

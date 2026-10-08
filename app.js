document.addEventListener('DOMContentLoaded', () => {
  const toggle = document.querySelector('[data-sidebar-toggle]');
  const sidebar = document.getElementById('sidebar');
  if (toggle && sidebar) toggle.addEventListener('click', () => sidebar.classList.toggle('open'));
  document.querySelectorAll('.flash').forEach((el) => setTimeout(() => el.remove(), 6000));

  const modal = document.getElementById('confirm-modal');
  const message = document.getElementById('confirm-message');
  const confirmButton = document.querySelector('[data-modal-confirm]');
  const cancelButton = document.querySelector('[data-modal-cancel]');
  let pendingForm = null;

  document.querySelectorAll('[data-confirm]').forEach((el) => {
    el.addEventListener('click', (event) => {
      if (!modal) return;
      event.preventDefault();
      pendingForm = el.closest('form');
      message.textContent = el.getAttribute('data-confirm') || 'Confirmar esta ação?';
      modal.hidden = false;
      confirmButton.focus();
    });
  });
  const closeModal = () => { pendingForm = null; if (modal) modal.hidden = true; };
  if (cancelButton) cancelButton.addEventListener('click', closeModal);
  if (confirmButton) confirmButton.addEventListener('click', () => {
    const form = pendingForm;
    closeModal();
    if (form) form.submit();
  });
  if (modal) modal.addEventListener('click', (event) => { if (event.target === modal) closeModal(); });
  document.addEventListener('keydown', (event) => { if (event.key === 'Escape' && modal && !modal.hidden) closeModal(); });
});

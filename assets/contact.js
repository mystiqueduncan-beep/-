/* Shared copy behaviour; never report success when clipboard access fails. */
let toastTimer;
function showToast(text) {
  const toast = document.getElementById('toastMsg');
  const label = document.getElementById('toastText') || toast;
  label.textContent = text;
  toast.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove('show'), 4000);
}
async function copyValue(value, label) {
  try {
    if (!navigator.clipboard || !navigator.clipboard.writeText) throw new Error('Clipboard unavailable');
    await navigator.clipboard.writeText(value);
    showToast('已成功複製' + label + '：' + value);
  } catch {
    showToast('無法自動複製，請手動選取' + label + '：' + value);
  }
}
function copyPhone() { return copyValue('0989591825', '電話號碼'); }
function copyEmail() { return copyValue('mystiqueduncan@gmail.com', '電子郵件'); }

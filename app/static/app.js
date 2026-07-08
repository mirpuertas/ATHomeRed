// Frontend mínimo para registrar, loguear y mostrar /auth/me (DB)
const $ = (sel) => document.querySelector(sel);

const regBtn = $('#reg-btn');
const loginBtn = $('#login-btn');
const meBtn = $('#me-btn');
const logoutBtn = $('#logout-btn');
const panel = $('#panel');
const panelEmpty = $('#panel-empty');
const tokenPre = $('#token');
const mePre = $('#me');
const regErrors = $('#reg-errors');
const regErrorsList = $('#reg-errors-list');
const regPasswordInput = $('#reg-password');

// Modal
const authModal = $('#auth-modal');
const modalToken = $('#modal-token');
const modalMePre = $('#modal-me');
const modalMeBtn = $('#modal-me-btn');
const modalLogoutBtn = $('#modal-logout-btn');
const modalClose = $('#modal-close');
const modalOverlay = $('#modal-overlay');

let token = null;

// Helpers
function msgFromErr(err, fallback = 'Error') {
  try {
    if (!err) return fallback;
    const d = err.detail ?? err.message ?? err.error ?? err.msg ?? err?.errors;
    if (Array.isArray(d)) {
      const parts = d.map(x => x?.msg || x?.message || x?.detail || (typeof x === 'string' ? x : JSON.stringify(x))).filter(Boolean);
      return parts.join(' | ') || fallback;
    }
    if (typeof d === 'string') return d;
    if (typeof d === 'object' && d !== null) {
      if (d.msg || d.message || d.detail) return d.msg || d.message || d.detail;
      return JSON.stringify(d);
    }
    // If no recognized shape, stringify the whole error
    if (typeof err === 'string') return err;
    return JSON.stringify(err);
  } catch {
    return fallback;
  }
}

function showPanel(active) {
  if (active) {
    panel.classList.remove('hidden');
    panelEmpty.classList.add('hidden');
  } else {
    panel.classList.add('hidden');
    panelEmpty.classList.remove('hidden');
  }
}

function openModal() {
  authModal.classList.add('show');
  modalOverlay.classList.add('show');
}

function closeModal() {
  authModal.classList.remove('show');
  modalOverlay.classList.remove('show');
}

// Password policy checks (carteles personalizados)
function passwordIssues(pw, nombre, apellido) {
  const issues = [];
  const hasUpper = /[A-Z]/.test(pw);
  const hasLower = /[a-z]/.test(pw);
  const hasSpecial = /[^A-Za-z0-9]/.test(pw);
  if (pw.length < 8) {
    issues.push('La contraseña debe tener al menos 8 caracteres.');
  }
  if (!hasUpper) {
    issues.push('La contraseña debe tener al menos una mayúscula.');
  }
  if (hasUpper && !hasLower) {
    issues.push('La contraseña debe tener al menos una minúscula.');
  }
  if (!hasSpecial) {
    issues.push('La contraseña debe tener al menos un carácter especial.');
  }
  // No debe contener el nombre de la persona (case-insensitive, si el nombre tiene al menos 3 chars)
  const n = (nombre || '').trim();
  if (n.length >= 3 && pw.toLowerCase().includes(n.toLowerCase())) {
    issues.push('La contraseña no debe contener el nombre de la persona.');
  }
  // Ni el apellido (case-insensitive, si el apellido tiene al menos 3 chars)
  const a = (apellido || '').trim();
  if (a.length >= 3 && pw.toLowerCase().includes(a.toLowerCase())) {
    issues.push('La contraseña no debe contener el apellido de la persona.');
  }
  return issues;
}

function renderRegErrors(issues) {
  if (!regErrors || !regErrorsList) return;
  regErrorsList.innerHTML = '';
  if (!issues || issues.length === 0) {
    regErrors.classList.add('hidden');
    return;
  }
  issues.forEach(msg => {
    const li = document.createElement('li');
    li.textContent = msg;
    regErrorsList.appendChild(li);
  });
  regErrors.classList.remove('hidden');
}

async function doRegister() {
  const nombre = $('#reg-nombre').value.trim();
  const apellido = $('#reg-apellido').value.trim();
  const email = $('#reg-email').value.trim();
  const password = $('#reg-password').value;
  const rol = $('#reg-rol').value; // 'solicitante' o 'profesional'
  
  if (!nombre || !apellido || !email || !password) return alert('Todos los campos son requeridos');

  // Validación previa con carteles personalizados
  const issues = passwordIssues(password, nombre, apellido);
  if (issues.length) {
    renderRegErrors(issues);
    return; // no llamamos al backend hasta que cumpla
  } else {
    renderRegErrors([]); // ocultar si ya cumple
  }

  const payload = {
    nombre,
    apellido,
    email,
    celular: null,
    password,
    es_profesional: rol === 'profesional',
    es_solicitante: rol === 'solicitante',
  };

  const resp = await fetch('/api/v1/auth/register-json', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!resp.ok) {
    let msg = 'Error de registro';
    try {
      const err = await resp.json();
      msg = msgFromErr(err, msg);
    } catch {
      try { const t = await resp.text(); if (t) msg = t; } catch {}
    }
    return alert(msg);
  }
  const data = await resp.json();
  alert('Registrado. usuario_id: ' + (data.usuario_id || 'desconocido'));
  // limpiar y ocultar panel de sesión
  token = null;
  tokenPre.textContent = '';
  mePre.textContent = '';
  showPanel(false);
}

async function doLogin() {
  const email = $('#login-email').value.trim();
  const password = $('#login-password').value;
  if (!email || !password) return alert('Email y contraseña son requeridos');
  const resp = await fetch('/api/v1/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  if (!resp.ok) {
    let msg = 'Credenciales inválidas';
    try {
      const err = await resp.json();
      msg = msgFromErr(err, msg);
    } catch {
      try { const t = await resp.text(); if (t) msg = t; } catch {}
    }
    return alert(msg);
  }
  const data = await resp.json();
  token = data.access_token;
  tokenPre.textContent = token;
  modalToken.textContent = token;
  modalMePre.textContent = '';
  showPanel(true);
  openModal();
}

async function viewMe() {
  if (!token) return alert('Primero obtené un token');
  const resp = await fetch('/api/v1/auth/me', { headers: { Authorization: 'Bearer ' + token } });
  if (!resp.ok) {
    let msg = 'Token inválido o expirado';
    try {
      const err = await resp.json();
      msg = msgFromErr(err, msg);
    } catch {
      try { const t = await resp.text(); if (t) msg = t; } catch {}
    }
    return alert(msg);
  }
  const data = await resp.json();
  const pretty = JSON.stringify(data, null, 2);
  if (mePre) mePre.textContent = pretty;
  if (modalMePre) modalMePre.textContent = pretty;
}

function logout() {
  token = null;
  tokenPre.textContent = '';
  mePre.textContent = '';
  showPanel(false);
  if (modalToken) modalToken.textContent = '';
  if (modalMePre) modalMePre.textContent = '';
  closeModal();
}

regBtn?.addEventListener('click', doRegister);
loginBtn?.addEventListener('click', doLogin);
meBtn?.addEventListener('click', viewMe);
logoutBtn?.addEventListener('click', logout);

modalMeBtn?.addEventListener('click', viewMe);
modalLogoutBtn?.addEventListener('click', logout);
modalClose?.addEventListener('click', closeModal);
modalOverlay?.addEventListener('click', closeModal);

// Si en el futuro queremos persistir la sesión, podemos usar localStorage.

// Validación en tiempo real mientras el usuario escribe la contraseña de registro
regPasswordInput?.addEventListener('input', () => {
  const pw = regPasswordInput.value || '';
  const nombre = document.querySelector('#reg-nombre')?.value?.trim() || '';
  const apellido = document.querySelector('#reg-apellido')?.value?.trim() || '';
  renderRegErrors(passwordIssues(pw, nombre, apellido));
});

// Y si cambia el nombre o el apellido, revalidamos con el password actual
document.querySelector('#reg-nombre')?.addEventListener('input', () => {
  const pw = regPasswordInput?.value || '';
  const nombre = document.querySelector('#reg-nombre')?.value?.trim() || '';
  const apellido = document.querySelector('#reg-apellido')?.value?.trim() || '';
  renderRegErrors(passwordIssues(pw, nombre, apellido));
});
document.querySelector('#reg-apellido')?.addEventListener('input', () => {
  const pw = regPasswordInput?.value || '';
  const nombre = document.querySelector('#reg-nombre')?.value?.trim() || '';
  const apellido = document.querySelector('#reg-apellido')?.value?.trim() || '';
  renderRegErrors(passwordIssues(pw, nombre, apellido));
});

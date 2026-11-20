const API = '/api';
const $ = (id) => document.getElementById(id);

let departments = [];

// ---------- helpers ----------
function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, (c) => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
  ));
}

const money = (n) => Number(n ?? 0).toLocaleString('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 2 });

async function request(url, options = {}) {
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    credentials: 'same-origin',
    ...options,
  });
  if (res.status === 401) {
    window.location.href = '/login';
    throw new Error('Session expired');
  }
  if (!res.ok) {
    let message = 'Something went wrong';
    try { message = (await res.json()).message || message; } catch (_) { /* ignore */ }
    throw new Error(message);
  }
  return res.status === 204 ? null : res.json();
}

function toast(message, type = 'success') {
  const box = $('toast');
  box.textContent = message;
  box.className = `alert ${type}`;
  box.hidden = false;
  setTimeout(() => { box.hidden = true; }, 3000);
}

// ---------- employees ----------
async function loadEmployees() {
  const q = $('searchInput').value.trim();
  const list = await request(`${API}/employees${q ? `?search=${encodeURIComponent(q)}` : ''}`);
  const body = $('employeeTable');
  body.innerHTML = list.map((e) => `
    <tr>
      <td>${e.id}</td>
      <td>${escapeHtml(e.firstName)} ${escapeHtml(e.lastName)}</td>
      <td>${escapeHtml(e.email)}</td>
      <td>${escapeHtml(e.phone)}</td>
      <td>${escapeHtml(e.departmentName)}</td>
      <td>${money(e.salary)}</td>
      <td>${escapeHtml(e.hireDate)}</td>
      <td class="actions-cell">
        <button class="btn outline small" data-edit="${e.id}">Edit</button>
        <button class="btn danger small" data-delete="${e.id}">Delete</button>
      </td>
    </tr>`).join('');
  $('emptyMsg').hidden = list.length > 0;
}

async function loadStats() {
  const s = await request(`${API}/employees/stats`);
  $('statEmployees').textContent = s.totalEmployees;
  $('statDepartments').textContent = s.totalDepartments;
  $('statPayroll').textContent = money(s.totalPayroll);
  $('statAverage').textContent = money(s.averageSalary);
}

async function loadDepartments() {
  departments = await request(`${API}/departments`);
  $('department').innerHTML = departments
    .map((d) => `<option value="${d.id}">${escapeHtml(d.name)}</option>`).join('');
  $('deptList').innerHTML = departments.map((d) => `
    <li><span>${escapeHtml(d.name)}</span>
        <button class="btn danger small" data-dept-delete="${d.id}">Delete</button></li>`).join('');
}

function refreshAll() {
  return Promise.all([loadEmployees(), loadStats()]);
}

// ---------- add / edit dialog ----------
function openForm(employee) {
  $('formError').hidden = true;
  $('employeeForm').reset();
  $('dialogTitle').textContent = employee ? 'Edit Employee' : 'Add Employee';
  $('empId').value = employee?.id ?? '';
  if (employee) {
    $('firstName').value = employee.firstName;
    $('lastName').value = employee.lastName;
    $('email').value = employee.email;
    $('phone').value = employee.phone ?? '';
    $('department').value = employee.departmentId;
    $('salary').value = employee.salary;
    $('hireDate').value = employee.hireDate ?? '';
  }
  $('employeeDialog').showModal();
}

$('addBtn').addEventListener('click', () => openForm(null));
$('cancelBtn').addEventListener('click', () => $('employeeDialog').close());

$('employeeForm').addEventListener('submit', async (event) => {
  event.preventDefault();
  const id = $('empId').value;
  const payload = {
    firstName: $('firstName').value,
    lastName: $('lastName').value,
    email: $('email').value,
    phone: $('phone').value,
    departmentId: Number($('department').value),
    salary: Number($('salary').value),
    hireDate: $('hireDate').value || null,
  };
  try {
    await request(id ? `${API}/employees/${id}` : `${API}/employees`, {
      method: id ? 'PUT' : 'POST',
      body: JSON.stringify(payload),
    });
    $('employeeDialog').close();
    toast(id ? 'Employee updated' : 'Employee added');
    await refreshAll();
  } catch (err) {
    $('formError').textContent = err.message;
    $('formError').hidden = false;
  }
});

// ---------- table actions (edit / delete) ----------
$('employeeTable').addEventListener('click', async (event) => {
  const editId = event.target.dataset.edit;
  const deleteId = event.target.dataset.delete;
  try {
    if (editId) {
      openForm(await request(`${API}/employees/${editId}`));
    } else if (deleteId && confirm('Delete this employee?')) {
      await request(`${API}/employees/${deleteId}`, { method: 'DELETE' });
      toast('Employee deleted');
      await refreshAll();
    }
  } catch (err) {
    toast(err.message, 'error');
  }
});

// ---------- search (debounced) ----------
let timer;
$('searchInput').addEventListener('input', () => {
  clearTimeout(timer);
  timer = setTimeout(() => loadEmployees().catch((e) => toast(e.message, 'error')), 300);
});

// ---------- departments ----------
$('deptBtn').addEventListener('click', () => {
  $('deptError').hidden = true;
  $('deptDialog').showModal();
});
$('deptClose').addEventListener('click', () => $('deptDialog').close());

$('deptForm').addEventListener('submit', async (event) => {
  event.preventDefault();
  try {
    await request(`${API}/departments`, { method: 'POST', body: JSON.stringify({ name: $('deptName').value }) });
    $('deptName').value = '';
    $('deptError').hidden = true;
    await loadDepartments();
    await loadStats();
  } catch (err) {
    $('deptError').textContent = err.message;
    $('deptError').hidden = false;
  }
});

$('deptList').addEventListener('click', async (event) => {
  const id = event.target.dataset.deptDelete;
  if (!id) return;
  try {
    await request(`${API}/departments/${id}`, { method: 'DELETE' });
    $('deptError').hidden = true;
    await loadDepartments();
    await loadStats();
  } catch (err) {
    $('deptError').textContent = err.message;
    $('deptError').hidden = false;
  }
});

// ---------- logout ----------
$('logoutBtn').addEventListener('click', async () => {
  await fetch('/logout', { method: 'POST', credentials: 'same-origin' });
  window.location.href = '/login?logout=1';
});

// ---------- init ----------
(async () => {
  try {
    await loadDepartments();
    await refreshAll();
  } catch (err) {
    toast(err.message, 'error');
  }
})();

// Supplier CRUD for admin panel
document.addEventListener("DOMContentLoaded", async function() {
    while (!window.Auth || !window.api) { await new Promise(r => setTimeout(r, 50)); }
    await window.Auth.init();
    if (!window.Auth.redirectIfNotAdmin()) return;

    var toastContainer = document.getElementById('toast-container');
    function showToast(msg, type) {
        var e = document.createElement('div');
        e.className = 'toast toast-' + type;
        e.textContent = msg;
        toastContainer.appendChild(e);
        setTimeout(function() { if (e && e.remove) e.remove(); }, 4000);
    }

    function openModal() { document.getElementById('supplier-modal').style.display = 'block'; }
    function closeModal() {
        document.getElementById('supplier-modal').style.display = 'none';
        document.getElementById('supplier-form').reset();
        document.getElementById('supplier-id').value = '';
        document.getElementById('modal-title').textContent = 'Add Supplier';
    }

    document.getElementById('add-supplier-btn').onclick = function() { closeModal(); openModal(); };
    document.getElementById('modal-close').onclick = closeModal;
    document.getElementById('modal-cancel').onclick = closeModal;
    document.querySelector('.modal-backdrop').onclick = closeModal;

    document.getElementById('modal-save').onclick = async function(e) {
        e.preventDefault();
        var id = document.getElementById('supplier-id').value;
        var payload = {
            name: document.getElementById('sup-name').value.trim(),
            country: document.getElementById('sup-country').value.trim() || null,
            contact_name: document.getElementById('sup-contact').value.trim() || null,
            contact_email: document.getElementById('sup-email').value.trim() || null,
            contact_phone: document.getElementById('sup-phone').value.trim() || null,
            lead_time_days: parseInt(document.getElementById('sup-lead').value) || 7,
            address: document.getElementById('sup-address').value.trim() || null,
            api_endpoint: document.getElementById('sup-api').value.trim() || null,
            notes: document.getElementById('sup-notes').value.trim() || null,
        };
        try {
            if (id) {
                await window.api.updateSupplier(id, payload);
                showToast('Supplier updated', 'success');
            } else {
                await window.api.createSupplier(payload);
                showToast('Supplier created', 'success');
            }
            closeModal();
            load();
        } catch(err) {
            showToast('Failed to save supplier', 'error');
        }
    };

    async function load() {
        try {
            var data = await window.api.getSuppliers();
            var items = data.items || [];
            var el = document.getElementById('suppliers-table');
            if (!items.length) {
                el.innerHTML = '<p class="text-muted text-center" style="padding:2rem;">No suppliers yet.</p>';
                return;
            }
            var h = '<table><thead><tr><th>Name</th><th>Country</th><th>Lead</th><th>Products</th><th>Status</th><th>Actions</th></tr></thead><tbody>';
            for (var i = 0; i < items.length; i++) {
                var s = items[i];
                h += '<tr data-id="' + Security.escapeHtml(s.id) + '">';
                h += '<td><strong>' + Security.escapeHtml(s.name) + '</strong></td>';
                h += '<td>' + Security.escapeHtml(s.country || '-') + '</td>';
                h += '<td>' + s.lead_time_days + 'd</td>';
                h += '<td>' + (s.product_count || 0) + '</td>';
                h += '<td><span class="badge badge-' + (s.is_active ? 'active' : 'inactive') + '">' + (s.is_active ? 'Active' : 'Inactive') + '</span></td>';
                h += '<td><button class="btn btn-sm btn-ghost edit-btn">Edit</button> <button class="btn btn-sm btn-ghost del-btn">Deactivate</button></td>';
                h += '</tr>';
            }
            h += '</tbody></table>';
            el.innerHTML = h;

            el.querySelectorAll('.edit-btn').forEach(function(btn) {
                btn.onclick = function() {
                    var id = this.closest('tr').dataset.id;
                    var s = items.find(function(x){return x.id===id;});
                    if(!s) return;
                    document.getElementById('supplier-id').value = s.id;
                    document.getElementById('sup-name').value = s.name;
                    document.getElementById('sup-country').value = s.country || '';
                    document.getElementById('sup-contact').value = s.contact_name || '';
                    document.getElementById('sup-email').value = s.contact_email || '';
                    document.getElementById('sup-phone').value = s.contact_phone || '';
                    document.getElementById('sup-lead').value = s.lead_time_days || 7;
                    document.getElementById('sup-address').value = s.address || '';
                    document.getElementById('sup-api').value = s.api_endpoint || '';
                    document.getElementById('sup-notes').value = s.notes || '';
                    document.getElementById('modal-title').textContent = 'Edit Supplier';
                    openModal();
                };
            });
            el.querySelectorAll('.del-btn').forEach(function(btn) {
                btn.onclick = function() {
                    var id = this.closest('tr').dataset.id;
                    if(!confirm('Deactivate this supplier?')) return;
                    window.api.deleteSupplier(id).then(function(){
                        showToast('Deactivated', 'success');
                        load();
                    }).catch(function(){ showToast('Failed', 'error'); });
                };
            });
        } catch(e) {
            document.getElementById('suppliers-table').innerHTML = '<p class="text-muted">Failed to load.</p>';
        }
    }
    load();
});
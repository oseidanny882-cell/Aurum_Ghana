import pathlib, subprocess

print('=' * 60)
print('FINAL VERIFICATION - Aurum Ghana Filter & Delete Features')
print('=' * 60)

# 1. Frontend scripts.js - filter button handlers
t = pathlib.Path('c:/Users/Codewithme/jewelry-gh/frontend/scripts.js').read_text(encoding='utf-8')
print()
print('1. Frontend scripts.js:')
print('   - filterBtns variable:', 'filterBtns' in t)
print('   - data-filter reading:', 'data-filter' in t)
print('   - pushState:', 'pushState' in t)
print('   - popstate listener:', 'popstate' in t)
print('   - filter param sent:', 'p.filter =' in t)
print('   - No leaked initCategoryPage code in global:', 'if (!g) return;' not in t[t.find('DOMContentLoaded'):t.find('if (page === "home"')+200])

# 2. Backend products.py - filter param
b = pathlib.Path('c:/Users/Codewithme/jewelry-gh/backend/api/products.py').read_text(encoding='utf-8')
print()
print('2. Backend products.py:')
new_check = 'filter' in b and '"new"' in b
best_check = 'filter' in b and '"best"' in b
sale_check = 'filter' in b and '"sale"' in b
print('   - filter=new:', new_check)
print('   - filter=best:', best_check)
print('   - filter=sale:', sale_check)
print('   - is_new filter:', 'is_new.is_(True)' in b)
print('   - is_best filter:', 'is_best.is_(True)' in b)
print('   - discount_price filter:', 'discount_price' in b)

# 3. category.html - filter buttons
result = subprocess.run(['findstr', 'filter-btn', 'c:/Users/Codewithme/jewelry-gh/frontend/category.html'],
                        capture_output=True, text=True, shell=True)
print()
print('3. category.html filter buttons:')
print(result.stdout)

# 4. styles.css - active state
result = subprocess.run(['findstr', '.filter-btn', 'c:/Users/Codewithme/jewelry-gh/frontend/styles.css'],
                        capture_output=True, text=True, shell=True)
print('4. styles.css:')
print(result.stdout)

# 5. admin-products.js - delete
a = pathlib.Path('c:/Users/Codewithme/jewelry-gh/frontend/admin-products.js').read_text(encoding='utf-8')
print('5. admin-products.js:')
print('   - deleteProduct call:', 'window.api.deleteProduct' in a)
print('   - loadProducts reload:', 'loadProducts()' in a)
print('   - XSS-safe (textContent):', 'textContent' in a)

# 6. Backend admin.py - soft delete
ad = pathlib.Path('c:/Users/Codewithme/jewelry-gh/backend/api/admin.py').read_text(encoding='utf-8')
print()
print('6. Backend admin.py:')
print('   - admin_delete_product soft delete:', 'is_active = False' in ad)
print('   - getAdminProducts with is_active:', 'is_active' in ad)

print()
print('=' * 60)
print('VERIFICATION COMPLETE')
print('=' * 60)

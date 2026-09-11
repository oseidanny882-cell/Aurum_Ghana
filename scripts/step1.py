import pathlib

p = pathlib.Path('c:/Users/Codewithme/jewelry-gh/frontend/scripts.js')
t = p.read_text(encoding='utf-8')
old = chr(10).join([chr(32)*4+'async function initCategoryPage() {','',chr(32)*8+'var g = document.getElementById(product-grid), cnt = document.getElementById(product-count), sort = document.getElementById(sort-select);','',chr(32)*8+'if (!g) return;'])
print('old found:', old in t)
print('Length old:', len(old))
print('t length:', len(t))
print('idx:', t.find(old))

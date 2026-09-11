import os, re
v = '1789200000'
for r, d, fs in os.walk('frontend'):
    for f in fs:
        if f.endswith('.html'):
            p = os.path.join(r, f)
            c = open(p).read()
            c = re.sub(r'cart\.js?v=d+', 'cart.js?v=' + v, c)
            c = c.replace('cart.js"></script>', 'cart.js?v=' + v + '</script>')
            open(p, 'w').write(c)
            print('Updated', f)

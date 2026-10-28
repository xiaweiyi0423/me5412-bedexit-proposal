import re, subprocess, os, hashlib, concurrent.futures as cf
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
url = "https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@500;700;900&family=Inter+Tight:wght@500;700;800;900&family=JetBrains+Mono:wght@500;700&display=block"
css = subprocess.run(["curl", "-sSL", "-A", UA, url], capture_output=True, text=True).stdout
urls = sorted(set(re.findall(r"url\((https://[^)]+)\)", css)))
os.makedirs("f", exist_ok=True)
def get(u):
    fn = "f/" + hashlib.md5(u.encode()).hexdigest()[:12] + ".woff2"
    if not os.path.exists(fn): subprocess.run(["curl", "-sSL", "--retry", "3", "-o", fn, u], check=True)
    return u, fn
with cf.ThreadPoolExecutor(16) as ex:
    m = dict(ex.map(get, urls))
for u, fn in m.items(): css = css.replace(u, fn)
open("fonts.css", "w").write(css); print(len(urls), "files")

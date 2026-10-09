#!/usr/bin/env python3
"""
Gera um site de fotos (HTML estatico) a partir de subpastas.

Como usar:
  1. Copie este arquivo para dentro da pasta que tem as subpastas de fotos
     (a pasta "comprimidas").
  2. Rode:  python gerar_site.py
  3. Abra o index.html para conferir e suba tudo no GitHub Pages.

Cada subpasta vira uma pagina. Fotos soltas na raiz viram a pagina "Outras fotos".
Nao precisa de nenhuma biblioteca extra.
"""
import html
import re
import unicodedata
from pathlib import Path
from urllib.parse import quote

RAIZ = Path(__file__).resolve().parent
TITULO_SITE = "Minhas Fotos"
EXTENSOES = {".jpg", ".jpeg", ".png", ".webp", ".gif"}
IGNORAR = {".git", "paginas", "__pycache__"}


def slug(texto):
    s = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return s or "pasta"


def url(caminho_relativo):
    # codifica espacos, acentos etc. mantendo as barras
    return "/".join(quote(p) for p in Path(caminho_relativo).parts)


def listar_fotos(pasta, so_nivel_atual=False):
    padrao = pasta.glob("*") if so_nivel_atual else pasta.rglob("*")
    fotos = [p for p in padrao if p.is_file() and p.suffix.lower() in EXTENSOES]
    return sorted(fotos, key=lambda p: [int(t) if t.isdigit() else t.lower()
                                        for t in re.split(r"(\d+)", str(p))])


CSS = """
*{box-sizing:border-box;margin:0}
body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;background:#111;color:#eee;padding:16px}
header{max-width:1100px;margin:0 auto 20px;display:flex;align-items:center;gap:12px;flex-wrap:wrap}
h1{font-size:1.5rem}
a{color:inherit;text-decoration:none}
nav{position:sticky;top:0;z-index:5;background:#111;margin:-16px -16px 16px;padding:10px 16px;border-bottom:1px solid #2a2a2a;display:flex;gap:8px;overflow-x:auto;white-space:nowrap;-webkit-overflow-scrolling:touch;scrollbar-width:none}
nav::-webkit-scrollbar{display:none}
nav a{background:#222;padding:8px 14px;border-radius:999px;font-size:.9rem;flex:0 0 auto}
nav a.ativo{background:#eee;color:#111;font-weight:600}
.grade{max-width:1100px;margin:0 auto;display:grid;gap:10px;grid-template-columns:repeat(auto-fill,minmax(150px,1fr))}
.grade img{width:100%;aspect-ratio:1/1;object-fit:cover;border-radius:8px;display:block;background:#222;cursor:zoom-in}
.cartoes{max-width:1100px;margin:0 auto;display:grid;gap:14px;grid-template-columns:repeat(auto-fill,minmax(220px,1fr))}
.cartao{background:#1c1c1c;border-radius:12px;overflow:hidden;display:block}
.cartao img{width:100%;aspect-ratio:4/3;object-fit:cover;display:block;background:#222}
.cartao div{padding:10px 12px}
.cartao b{display:block;font-size:1rem}
.cartao span{font-size:.85rem;color:#999}
#lb{position:fixed;inset:0;background:rgba(0,0,0,.95);display:none;align-items:center;justify-content:center;z-index:10}
#lb.on{display:flex}
#lb img{max-width:100%;max-height:100%;object-fit:contain}
#lb button{position:absolute;background:rgba(255,255,255,.15);color:#fff;border:0;font-size:1.8rem;width:48px;height:48px;border-radius:50%;cursor:pointer}
#fechar{top:12px;right:12px}#ant{left:8px;top:50%}#prox{right:8px;top:50%}
"""

JS = """
const imgs=[...document.querySelectorAll('.grade img')];
const lb=document.getElementById('lb'),big=lb.querySelector('img');let i=0;
function abrir(n){i=(n+imgs.length)%imgs.length;big.src=imgs[i].dataset.full;lb.classList.add('on')}
imgs.forEach((im,n)=>im.addEventListener('click',()=>abrir(n)));
document.getElementById('fechar').onclick=()=>lb.classList.remove('on');
document.getElementById('ant').onclick=e=>{e.stopPropagation();abrir(i-1)};
document.getElementById('prox').onclick=e=>{e.stopPropagation();abrir(i+1)};
lb.addEventListener('click',e=>{if(e.target===lb)lb.classList.remove('on')});
document.addEventListener('keydown',e=>{if(!lb.classList.contains('on'))return;
 if(e.key==='Escape')lb.classList.remove('on');
 if(e.key==='ArrowLeft')abrir(i-1);if(e.key==='ArrowRight')abrir(i+1)});
let x0=null;lb.addEventListener('touchstart',e=>x0=e.touches[0].clientX);
lb.addEventListener('touchend',e=>{if(x0===null)return;const d=e.changedTouches[0].clientX-x0;
 if(Math.abs(d)>50)abrir(i+(d<0?1:-1));x0=null});
"""


def menu(grupos, atual):
    """Barra de links no topo, igual em todas as paginas."""
    links = [("index.html", "Início", atual == "index")]
    links += [(f"{s}.html", nome, s == atual) for nome, s, _ in grupos]
    itens = "".join(
        f'<a href="{quote(h)}"{" class=ativo" if ativo else ""}>{html.escape(t)}</a>'
        for h, t, ativo in links)
    return f"<nav>{itens}</nav>"


def pagina(titulo, corpo, extra_js="", nav=""):
    return f"""<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(titulo)}</title><style>{CSS}</style></head>
<body>{nav}{corpo}{extra_js}</body></html>"""


def main():
    grupos = []  # (nome, slug, [fotos])
    nomes_usados = set()

    for pasta in sorted((p for p in RAIZ.iterdir() if p.is_dir() and p.name not in IGNORAR
                         and not p.name.startswith(".")), key=lambda p: p.name.lower()):
        fotos = listar_fotos(pasta)
        if not fotos:
            continue
        s, n = slug(pasta.name), 2
        while s in nomes_usados:
            s, n = f"{slug(pasta.name)}-{n}", n + 1
        nomes_usados.add(s)
        grupos.append((pasta.name, s, fotos))

    soltas = listar_fotos(RAIZ, so_nivel_atual=True)
    if soltas:
        grupos.append(("Outras fotos", "outras-fotos", soltas))

    if not grupos:
        print("Nenhuma foto encontrada. Rode o script dentro da pasta com as subpastas.")
        return

    # paginas de galeria
    for nome, s, fotos in grupos:
        itens = "\n".join(
            f'<img loading="lazy" src="{url(f.relative_to(RAIZ))}" '
            f'data-full="{url(f.relative_to(RAIZ))}" alt="">' for f in fotos)
        corpo = f"""<header><h1>{html.escape(nome)}</h1><span>{len(fotos)} fotos</span></header>
<div class="grade">{itens}</div>
<div id="lb"><button id="fechar">&times;</button><button id="ant">&#8249;</button>
<img alt=""><button id="prox">&#8250;</button></div>"""
        (RAIZ / f"{s}.html").write_text(
            pagina(nome, corpo, f"<script>{JS}</script>", menu(grupos, s)), encoding="utf-8")

    # pagina inicial
    cartoes = "\n".join(
        f'<a class="cartao" href="{s}.html"><img loading="lazy" '
        f'src="{url(fotos[0].relative_to(RAIZ))}" alt="">'
        f'<div><b>{html.escape(nome)}</b><span>{len(fotos)} fotos</span></div></a>'
        for nome, s, fotos in grupos)
    corpo = f'<header><h1>{html.escape(TITULO_SITE)}</h1></header><div class="cartoes">{cartoes}</div>'
    (RAIZ / "index.html").write_text(
        pagina(TITULO_SITE, corpo, nav=menu(grupos, "index")), encoding="utf-8")

    total = sum(len(f) for _, _, f in grupos)
    print(f"Pronto! {len(grupos)} paginas, {total} fotos. Abra o index.html para conferir.")


if __name__ == "__main__":
    main()

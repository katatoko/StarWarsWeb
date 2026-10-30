import re, os, sys, collections, datetime, csv
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak

ROOT = Path(sys.argv[1]).resolve()
OUT = Path(__file__).parent
SKIP = {"bin", "obj", "node_modules", ".git", "wwwroot", "Migrations"}


def files(*exts):
    for dp, dn, fn in os.walk(ROOT):
        dn[:] = [d for d in dn if d not in SKIP]
        for f in fn:
            if f.endswith(exts) and not f.endswith((".g.cs", ".Designer.cs", ".designer.cs")):
                yield Path(dp) / f


def read(p):
    return p.read_text(encoding="utf-8-sig", errors="ignore")


def rel(p):
    try:
        return str(Path(p).resolve().relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(p).replace("\\", "/")


def project(p):
    for s in rel(p).split("/"):
        if s.endswith((".Api", ".Services", ".Tests")) or s in ("StarWarsWeb", "StarWarsWeb.Client", "WebApp", "DTOs", "Entities", "Domain"):
            return s
    return rel(p).split("/")[0]


src = list(files(".cs", ".razor"))
loc = collections.Counter()
nfiles = collections.Counter()
comments = collections.Counter()
for p in src:
    pr = project(p)
    nfiles[pr] += 1
    for l in read(p).splitlines():
        s = l.strip()
        if not s:
            continue
        if s.startswith("//"):
            comments[pr] += 1
        loc[pr] += 1

SIG = re.compile(r"^\s*(?:\[[^\]]*\]\s*)*(?:public|private|protected|internal)\s+(?:static\s+|async\s+|override\s+|virtual\s+)*[\w<>\[\],\.\?\s]+?\s+(\w+)\s*\([^;]*?\)\s*(?:where [^{]+)?\{?\s*$")
CC = re.compile(r"\b(if|for|foreach|while|case|catch)\b|&&|\|\||\?\?")
methods = []
for p in files(".cs"):
    if "Tests" in project(p):
        continue
    lines = read(p).splitlines()
    i = 0
    while i < len(lines):
        m = SIG.match(lines[i])
        if m and not re.search(r"\b(class|interface|record|struct|enum|namespace)\b", lines[i]):
            j = i
            depth = 0
            started = False
            while j < len(lines):
                depth += lines[j].count("{") - lines[j].count("}")
                if "{" in lines[j]:
                    started = True
                if started and depth <= 0:
                    break
                if not started and j - i > 6:
                    break
                j += 1
            if started:
                body = "\n".join(lines[i:j + 1])
                methods.append((rel(p), m.group(1), i + 1, j - i + 1, 1 + len(CC.findall(body))))
                i = j
        i += 1
long_m = sorted([m for m in methods if m[3] > 60], key=lambda x: -x[3])
cx_m = sorted([m for m in methods if m[4] >= 15], key=lambda x: -x[4])

RULES = [
    ("Seguridad", "Alta", "Posible credencial/secreto en código", r"(?i)\b(password|pwd|secret|apikey|api_key|jwtkey)\w*\s*[:=]\s*\"[^\"{}$]{6,}\"", (".cs", ".json", ".razor")),
    ("Seguridad", "Alta", "SQL crudo (riesgo de inyección)", r"\b(FromSqlRaw|ExecuteSqlRaw|ExecuteSqlRawAsync|SqlQuery|SqlQueryRaw)\b", (".cs",)),
    ("Seguridad", "Media", "Endpoint con [AllowAnonymous]", r"\[AllowAnonymous\]", (".cs",)),
    ("Seguridad", "Media", "Validación de certificado/HTTPS deshabilitada", r"ServerCertificateCustomValidationCallback|DangerousAcceptAnyServerCertificateValidator|RequireHttpsMetadata\s*=\s*false", (".cs",)),
    ("Seguridad", "Media", "CORS abierto (AllowAnyOrigin)", r"AllowAnyOrigin", (".cs",)),
    ("Seguridad", "Baja", "Validación JWT relajada (Validate*=false)", r"Validate(Issuer|Audience|Lifetime|IssuerSigningKey)\s*=\s*false", (".cs",)),
    ("Fiabilidad", "Alta", "catch vacío (excepción silenciada)", r"catch\s*(\([^)]*\))?\s*\{\s*\}", (".cs", ".razor")),
    ("Fiabilidad", "Alta", "async void (fuera de manejadores de eventos)", r"\basync\s+void\b", (".cs", ".razor")),
    ("Fiabilidad", "Media", "Bloqueo síncrono (.Wait()/GetResult())", r"\.Wait\(\)|GetAwaiter\(\)\.GetResult\(\)", (".cs",)),
    ("Fiabilidad", "Baja", "catch (Exception) genérico", r"catch\s*\(\s*Exception\b", (".cs",)),
    ("Mantenibilidad", "Baja", "Console.WriteLine en lugar de ILogger", r"Console\.(WriteLine|Write)\(", (".cs",)),
    ("Mantenibilidad", "Baja", "Marcadores TODO/FIXME/HACK", r"//\s*(TODO|FIXME|HACK)\b", (".cs", ".razor")),
    ("Mantenibilidad", "Baja", "#pragma warning disable", r"#pragma\s+warning\s+disable", (".cs",)),
    ("Mantenibilidad", "Baja", "URL localhost/IP fija en código", r"\"https?://(localhost|\d{1,3}(?:\.\d{1,3}){3})[:/\"]", (".cs", ".razor")),
    ("Corrección", "Media", "DateTime.Now (dependiente de zona horaria)", r"\bDateTime\.Now\b", (".cs",)),
    ("Corrección", "Baja", "new HttpClient() directo (usar IHttpClientFactory)", r"new\s+HttpClient\s*\(", (".cs",)),
]
findings = collections.defaultdict(list)
for cat, sev, name, rx, exts in RULES:
    r = re.compile(rx)
    for p in files(*exts):
        if "Tests" in project(p):
            continue
        for n, l in enumerate(read(p).splitlines(), 1):
            if l.strip().startswith("//") and "TODO" not in name:
                continue
            if name.startswith("async void") and re.search(r"EventArgs|object\??\s+sender", l):
                continue
            if r.search(l):
                findings[(cat, sev, name)].append((rel(p), n, l.strip()[:110]))

ctrl_total = ctrl_noauth = ctrl_ctx = 0
ctrl_ctx_list = []
ctrl_noauth_list = []
for p in files(".cs"):
    if p.name.endswith("Controller.cs"):
        t = read(p)
        ctrl_total += 1
        if "[Authorize" not in t:
            ctrl_noauth += 1
            ctrl_noauth_list.append(rel(p))
        if re.search(r"\b(DbContext|_context|_db)\b", t) and re.search(r"\.(Where|ToListAsync|FirstOrDefaultAsync|SaveChangesAsync)\(", t):
            ctrl_ctx += 1
            ctrl_ctx_list.append(rel(p))
dup_using = []
for p in files(".cs"):
    us = [l.strip() for l in read(p).splitlines() if l.startswith("using ") and l.strip().endswith(";") and "=" not in l]
    d = [u for u, c in collections.Counter(us).items() if c > 1]
    if d:
        dup_using.append((rel(p), d))

W = re.compile(r"^(.*?)\((\d+),\d+\): (warning|error) (\w+): (.*)$")
warns = []
for l in (OUT / "advertencias-compilador.txt").read_text(encoding="utf-8", errors="ignore").splitlines():
    m = W.match(l.strip())
    if m and "\\obj\\" not in m.group(1) and "/obj/" not in m.group(1):
        warns.append((rel(m.group(1)), int(m.group(2)), m.group(4), m.group(5)[:120]))
wc = collections.Counter(w[2] for w in warns)
wf = collections.Counter(w[0] for w in warns)
wp = collections.Counter(project(w[0]) for w in warns)
CAT = {"CS86": "Nulabilidad", "CA18": "Rendimiento", "CA17": "Rendimiento", "CA13": "Globalización", "CA23": "Fiabilidad",
       "CA10": "Diseño/Nombres", "CA27": "Seguridad", "CA20": "Fiabilidad", "CS01": "Código muerto/ocultamiento", "BL00": "Blazor", "CA21": "Fiabilidad", "CA11": "Diseño/Nombres"}
DESC = {"CA1861": "Arrays constantes como argumento (usar static readonly)", "BL0005": "Asignación directa a parámetro de componente Blazor",
        "CA1707": "Guiones bajos en identificadores", "CS8604": "Posible argumento nulo", "CS8625": "Literal null a tipo no anulable",
        "CA1822": "Miembro que puede ser estático", "CA1805": "Inicialización innecesaria al valor por defecto", "CS8602": "Desreferencia de posible nulo",
        "CS8620": "Nulabilidad de argumento no coincide", "CA1305": "Falta IFormatProvider (cultura)", "CS0108": "Miembro oculta al heredado (falta new)",
        "CA1848": "Usar LoggerMessage en vez de ILogger.Log*", "CA1304": "Falta CultureInfo", "CA1311": "ToUpper/ToLower sin cultura",
        "CA1309": "Comparación de cadenas no ordinal", "CS8603": "Posible retorno de referencia nula", "CA1852": "Tipo puede sellarse (sealed)",
        "CA1873": "Evaluación costosa de argumentos de log", "CS8629": "Valor nullable puede ser nulo", "CS8618": "Propiedad no anulable sin inicializar",
        "CA2012": "Uso incorrecto de ValueTask", "CA1716": "Identificador coincide con palabra reservada", "CS8981": "Tipo con solo minúsculas",
        "CA1860": "Preferir Length/Count a Any()", "CA1725": "Nombre de parámetro difiere de la base", "CS0169": "Campo nunca usado",
        "CS0168": "Variable declarada y no usada", "CS0067": "Evento nunca usado", "CS8714": "Tipo no cumple restricción notnull", "CS8600": "Conversión de null a tipo no anulable"}


def cat_of(code):
    return next((v for k, v in CAT.items() if code.startswith(k)), "Otros")


by_cat = collections.Counter()
for c, n in wc.items():
    by_cat[cat_of(c)] += n


def chart(path, labels, vals, title, color):
    fig, ax = plt.subplots(figsize=(7.2, max(2.2, .32 * len(labels) + .8)))
    ax.barh(labels[::-1], vals[::-1], color=color)
    for i, v in enumerate(vals[::-1]):
        ax.text(v, i, f" {v:,}", va="center", fontsize=8)
    ax.set_title(title, fontsize=10, loc="left")
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(labelsize=8)
    plt.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


top_w = wc.most_common(12)
lp = loc.most_common()
chart(OUT / "g_warn.png", [c for c, _ in top_w], [n for _, n in top_w], "Advertencias por regla (top 12)", "#2f6db5")
chart(OUT / "g_loc.png", [k for k, _ in lp], [v for _, v in lp], "Líneas de código por proyecto", "#3a8f6b")

total_loc = sum(loc.values())
cnt = lambda s: sum(len(v) for (c, sv, n), v in findings.items() if sv == s)
n_alta, n_med, n_low = cnt("Alta"), cnt("Media"), cnt("Baja")
null_w = by_cat.get("Nulabilidad", 0)

# ---------- calificación ----------
PESO = {"Alta": 5.0, "Media": 2.0, "Baja": 0.25}
kloc = sum(v for k, v in loc.items() if not k.endswith(".Tests")) / 1000.0
LIMITE = 10.0  # puntos ponderados por KLOC que llevan la dimensión a 0


def pts_patrones(cat):
    return sum(PESO[s] * len(v) for (c, s, n), v in findings.items() if c == cat)


def pts_warn(prefijos, peso=1.0):
    return peso * sum(n for c, n in wc.items() if c.startswith(prefijos))


dims = {
    "Seguridad": pts_patrones("Seguridad") + pts_warn(("CA27", "CA53", "CA55")),
    "Fiabilidad": pts_patrones("Fiabilidad") + pts_warn(("CS86", "CA20", "CA23")),
    "Mantenibilidad": pts_patrones("Mantenibilidad") + len(long_m) * 1.0 + len(cx_m) * 1.0 + len(dup_using) * 0.25
                      + ctrl_ctx * 2.0 + pts_warn(("CA10", "CA17", "CA18") if False else ("CA1707", "CA1822", "CA1805", "CA1852", "CA1716", "CA1725", "CS01", "CS8981"), 0.5),
    "Rendimiento y buenas prácticas": pts_patrones("Corrección") + pts_warn(("CA1861", "CA1848", "CA1873", "CA1860", "CA13", "BL00"), 0.5),
}
PESOS_DIM = {"Seguridad": .30, "Fiabilidad": .30, "Mantenibilidad": .25, "Rendimiento y buenas prácticas": .15}
scores = {d: max(0.0, 100.0 - 100.0 * (p / kloc) / LIMITE) for d, p in dims.items()}
overall = sum(scores[d] * PESOS_DIM[d] for d in scores)


def grade(s):
    return "A" if s >= 90 else "B" if s >= 80 else "C" if s >= 65 else "D" if s >= 50 else "E"


GCOL = {"A": "#2e9b5f", "B": "#7ab648", "C": "#e0b030", "D": "#e07b30", "E": "#c8403a"}
GDESC = {"A": "Excelente", "B": "Buena", "C": "Aceptable, con mejoras necesarias", "D": "Deficiente", "E": "Crítica"}
fig, ax = plt.subplots(figsize=(7.2, 2.4))
names = list(scores)
ax.barh(names[::-1], [scores[n] for n in names[::-1]], color=[GCOL[grade(scores[n])] for n in names[::-1]])
for i, n in enumerate(names[::-1]):
    ax.text(min(scores[n], 96) + 1, i, f"{scores[n]:.0f}  ({grade(scores[n])})", va="center", fontsize=8)
ax.set_xlim(0, 112)
ax.axvline(80, color="grey", lw=.5, ls="--")
ax.set_title("Puntuación por dimensión (0-100)", fontsize=10, loc="left")
ax.spines[["top", "right"]].set_visible(False)
ax.tick_params(labelsize=8)
plt.tight_layout()
fig.savefig(OUT / "g_score.png", dpi=150)
plt.close(fig)

ss = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=ss["Heading1"], fontSize=16, textColor=colors.HexColor("#1f3d6b"), spaceBefore=10)
H2 = ParagraphStyle("H2", parent=ss["Heading2"], fontSize=12, textColor=colors.HexColor("#2f6db5"), spaceBefore=8)
B = ParagraphStyle("B", parent=ss["BodyText"], fontSize=9.5, leading=13)
S = ParagraphStyle("S", parent=B, fontSize=7.5, leading=9)


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def tbl(data, widths, small=True):
    st = S if small else B
    rows = [[Paragraph(esc(str(c)), st) for c in r] for r in data]
    t = Table(rows, colWidths=widths, repeatRows=1)
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dfe8f5")), ("GRID", (0, 0), (-1, -1), .25, colors.grey),
                           ("VALIGN", (0, 0), (-1, -1), "TOP"), ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f6f8fb")])]))
    return t


def img(path, w=15 * cm):
    i = Image(str(path))
    return Image(str(path), width=w, height=w * i.imageHeight / i.imageWidth)


def footer(c, d):
    c.saveState()
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.grey)
    c.drawString(2 * cm, 1.2 * cm, "StarWarsWeb - Informe de análisis estático")
    c.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Pág. {d.page}")
    c.restoreState()


doc = SimpleDocTemplate(str(OUT / "Informe-Analisis-Estatico-StarWarsWeb.pdf"), pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm,
                        topMargin=1.8 * cm, bottomMargin=1.8 * cm, title="Informe de análisis estático - StarWarsWeb")
E = []
E.append(Paragraph("Informe de análisis estático de código", ParagraphStyle("T", parent=ss["Title"], fontSize=22, textColor=colors.HexColor("#1f3d6b"))))
E.append(Paragraph(f"Solución StarWarsWeb · rama develop · {datetime.date.today():%d/%m/%Y}", B))
gl = grade(overall)
E.append(Paragraph("Calificación general de calidad", H1))
big = Table([[Paragraph(f'<font size="40" color="{GCOL[gl]}"><b>{gl}</b></font>', ParagraphStyle("g", alignment=1, leading=46)),
              Paragraph(f'<b>{overall:.1f} / 100</b> - {GDESC[gl]}<br/>'
                        f'{kloc:.1f} KLOC de producción analizadas (sin tests)', B)]], colWidths=[3 * cm, 14 * cm])
big.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("BOX", (0, 0), (-1, -1), .5, colors.grey), ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f6f8fb"))]))
E.append(big)
E.append(Spacer(1, 6))
E.append(img(OUT / "g_score.png"))
E.append(tbl([["Dimensión", "Peso", "Puntos ponderados", "Puntos / KLOC", "Puntuación", "Nota"]] +
             [[d, f"{PESOS_DIM[d]:.0%}", f"{dims[d]:.0f}", f"{dims[d] / kloc:.1f}", f"{scores[d]:.0f}", grade(scores[d])] for d in scores], [5.6 * cm, 1.5 * cm, 3 * cm, 2.6 * cm, 2.2 * cm, 1.5 * cm]))
E.append(Spacer(1, 4))
E.append(Paragraph(f"<b>Cómo se calcula:</b> cada hallazgo suma puntos (patrón Alta = {PESO['Alta']}, Media = {PESO['Media']}, Baja = {PESO['Baja']}; advertencias de analizador = 0,5 a 1; "
                   f"método largo o complejo = 1). Los puntos se dividen entre las KLOC de producción y la puntuación es 100 - 100 x (puntos/KLOC) / {LIMITE:.0f}, con mínimo 0. "
                   "La nota general es el promedio ponderado (Seguridad 30 %, Fiabilidad 30 %, Mantenibilidad 25 %, Rendimiento 15 %). "
                   "Escala: A >= 90, B >= 80, C >= 65, D >= 50, E < 50. Es un indicador relativo y heurístico, útil para comparar entre ejecuciones; no sustituye una revisión de código.", S))
E.append(PageBreak())
E.append(Paragraph("1. Resumen ejecutivo", H1))
E.append(Paragraph(f"Se analizaron <b>{len(src)}</b> archivos (.cs y .razor, excluyendo bin/obj/Migrations) con <b>{total_loc:,}</b> líneas no vacías en {len(loc)} proyectos. "
                   "El análisis combinó (a) el compilador de .NET con analizadores Roslyn (AnalysisMode=Recommended) sobre las 5 APIs y la WebApp, "
                   "(b) reglas de patrones propias en Python y (c) métricas de tamaño y complejidad ciclomática aproximada.", B))
E.append(Spacer(1, 6))
E.append(tbl([["Indicador", "Valor"],
              ["Advertencias de compilador/analizadores", len(warns)], ["   de ellas, nulabilidad (CS86xx)", null_w],
              ["Hallazgos de patrones - severidad Alta", n_alta], ["Hallazgos de patrones - severidad Media", n_med], ["Hallazgos de patrones - severidad Baja", n_low],
              ["Métodos con más de 60 líneas", len(long_m)], ["Métodos con complejidad >= 15", len(cx_m)],
              [f"Controladores sin [Authorize] (de {ctrl_total})", ctrl_noauth], ["Controladores con acceso directo a DbContext", ctrl_ctx],
              ["Archivos con using duplicados", len(dup_using)]], [11 * cm, 4 * cm], small=False))
E.append(Spacer(1, 6))
E.append(Paragraph("<b>Alcance y limitaciones:</b> MovilApp y DesktopApp no se compilaron (requieren cargas de trabajo Android/Windows no instaladas); "
                   "sólo se les aplicaron patrones y métricas. La complejidad y longitud de métodos son aproximaciones léxicas, no un AST completo. "
                   "Los hallazgos son indicios que requieren revisión humana.", B))
E.append(Paragraph("2. Tamaño de la solución", H1))
E.append(img(OUT / "g_loc.png"))
E.append(tbl([["Proyecto", "Archivos", "Líneas", "Líneas de comentario"]] + [[k, nfiles[k], v, comments[k]] for k, v in lp], [6 * cm, 2.5 * cm, 3 * cm, 3.5 * cm]))
E.append(PageBreak())
E.append(Paragraph("3. Compilador y analizadores Roslyn", H1))
E.append(img(OUT / "g_warn.png"))
E.append(tbl([["Regla", "Categoría", "Cantidad", "Descripción"]] + [[c, cat_of(c), n, DESC.get(c, "")] for c, n in wc.most_common()], [2 * cm, 3.5 * cm, 1.8 * cm, 9.7 * cm]))
E.append(Paragraph("Por proyecto", H2))
E.append(tbl([["Proyecto", "Advertencias"]] + [[k, v] for k, v in wp.most_common()], [8 * cm, 3 * cm]))
E.append(Paragraph("Archivos con más advertencias", H2))
E.append(tbl([["Archivo", "Advertencias"]] + [[k, v] for k, v in wf.most_common(15)], [13 * cm, 3 * cm]))
E.append(PageBreak())
E.append(Paragraph("4. Hallazgos por patrones", H1))
order = {"Alta": 0, "Media": 1, "Baja": 2}
srt = sorted(findings.items(), key=lambda kv: (order[kv[0][1]], -len(kv[1])))
E.append(tbl([["Severidad", "Categoría", "Regla", "Ocurrencias"]] + [[s, c, n, len(v)] for (c, s, n), v in srt], [2 * cm, 2.8 * cm, 9.2 * cm, 3 * cm]))
for (c, s, n), v in srt:
    if s == "Baja" and len(v) > 30:
        continue
    E.append(Paragraph(f"{s} - {n} ({len(v)})", H2))
    E.append(tbl([["Ubicación", "Línea de código"]] + [[f"{f}:{ln}", t] for f, ln, t in v[:12]], [7.2 * cm, 9.8 * cm]))
    if len(v) > 12:
        E.append(Paragraph(f"... y {len(v) - 12} más (ver hallazgos.csv).", S))
E.append(PageBreak())
E.append(Paragraph("5. Arquitectura y controladores", H1))
E.append(Paragraph(f"De {ctrl_total} controladores, <b>{ctrl_noauth}</b> no declaran [Authorize] en el archivo (puede haber autorización global o por política; verificar) "
                   f"y <b>{ctrl_ctx}</b> parecen usar el contexto de datos directamente, contraviniendo la convención del proyecto de mantener la lógica en servicios.", B))
if ctrl_noauth_list:
    E.append(Spacer(1, 4))
    E.append(tbl([["Sin [Authorize]"]] + [[x] for x in ctrl_noauth_list[:25]], [17 * cm]))
if ctrl_ctx_list:
    E.append(Spacer(1, 6))
    E.append(tbl([["Acceso directo a datos en controlador"]] + [[x] for x in ctrl_ctx_list[:25]], [17 * cm]))
if dup_using:
    E.append(Paragraph("Directivas using duplicadas", H2))
    E.append(tbl([["Archivo", "Duplicados"]] + [[f, ", ".join(d)] for f, d in dup_using[:15]], [9 * cm, 8 * cm]))
E.append(Paragraph("6. Métodos largos y complejos", H1))
E.append(tbl([["Archivo", "Método", "Línea", "Líneas", "CC"]] + [[f, n, l, ln, cc] for f, n, l, ln, cc in long_m[:20]], [8 * cm, 4 * cm, 1.5 * cm, 1.7 * cm, 1.3 * cm]))
E.append(Paragraph("Mayor complejidad ciclomática (aprox.)", H2))
E.append(tbl([["Archivo", "Método", "Línea", "Líneas", "CC"]] + [[f, n, l, ln, cc] for f, n, l, ln, cc in cx_m[:20]], [8 * cm, 4 * cm, 1.5 * cm, 1.7 * cm, 1.3 * cm]))
E.append(Paragraph("7. Recomendaciones priorizadas", H1))
recs = []
if n_alta:
    recs.append("Revisar primero los hallazgos de severidad Alta (secretos, SQL crudo, catch vacíos, async void); mover secretos a variables de entorno o user-secrets.")
if null_w:
    recs.append(f"Resolver las {null_w} advertencias de nulabilidad (CS86xx): son la fuente más probable de NullReferenceException.")
if wc.get("BL0005"):
    recs.append(f"Blazor: {wc['BL0005']} asignaciones directas a [Parameter]; usar un campo local o EventCallback.")
if ctrl_ctx:
    recs.append("Mover el acceso a datos de los controladores a la capa de servicios.")
if ctrl_noauth:
    recs.append("Confirmar la política de autorización de los controladores sin [Authorize] y definir una política global por defecto.")
if wc.get("CA1305") or wc.get("CA1304") or wc.get("CA1311"):
    recs.append("Globalización: especificar CultureInfo.InvariantCulture u ordinal en ToString/ToUpper/comparaciones.")
if wc.get("CA1861"):
    recs.append("Rendimiento: extraer arrays constantes a campos static readonly (CA1861).")
if long_m or cx_m:
    recs.append("Refactorizar los métodos más largos y complejos de la sección 6.")
recs.append("Integrar el análisis en CI con un .editorconfig compartido y un umbral para nuevas advertencias.")
for i, r in enumerate(recs, 1):
    E.append(Paragraph(f"{i}. {r}", B))
doc.build(E, onFirstPage=footer, onLaterPages=footer)

with open(OUT / "hallazgos.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f)
    w.writerow(["origen", "severidad/regla", "descripcion", "archivo", "linea", "detalle"])
    for (c, s, n), v in findings.items():
        for fl, ln, t in v:
            w.writerow(["patron", s, n, fl, ln, t])
    for fl, ln, c, m in warns:
        w.writerow(["compilador", c, m, fl, ln, ""])
print("OK", round(kloc,1), {d: (round(dims[d]), round(scores[d])) for d in scores}, round(overall), grade(overall))

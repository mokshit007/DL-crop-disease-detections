"""Build the IEEE two-column conference .docx from the exported paper markdown.

Usage: python build_ieee_docx.py <paper.md> <out.docx>
Figures are taken from results/paper/figs; equations become native Word equations.
"""
import re
import sys
from pathlib import Path

import latex2mathml.converter
from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt
from lxml import etree

ROOT = Path(__file__).resolve().parents[1]
FIGS = ROOT / "figs"
XSL = Path(r"C:\Program Files\Microsoft Office\root\Office16\MML2OMML.XSL")
FIG_FILES = [  # in order of the placeholders in the markdown
    ("fig1_methodology.png", True),
    ("fig2_architecture.png", True),
    ("fig4_robustness.png", True),
    ("fig7_gradcam.png", False),
]
WIDE_TABLES = {"I", "III", "IV", "VI"}
COL_W = 3.5
PAGE_W = 7.25
# Captions rewritten to match the PNG figures (the doc's Figs. 1-3 were redrawn widgets).
FIG_CAPTIONS = {
    "1": "Proposed methodology and system workflow: (a) development path, from the leakage audit and "
         "leaf-disjoint split to training and evaluation; (b) diagnosis path of the deployed application.",
    "3": "Test accuracy (%) of the five models under clean and six corrupted conditions (FA: field "
         "augmentation). Field augmentation raises accuracy under blur and noise; the head type changes the "
         "result mainly under motion blur, sensor noise and low light.",
}

xslt = etree.XSLT(etree.parse(str(XSL)))


# ---------- low-level helpers ----------
def set_cols(section, n, space_in=0.25):
    sectPr = section._sectPr
    cols = sectPr.find(qn("w:cols"))
    if cols is None:
        cols = OxmlElement("w:cols")
        sectPr.append(cols)
    cols.set(qn("w:num"), str(n))
    cols.set(qn("w:space"), str(int(space_in * 1440)))


def set_margins(section):
    section.page_width, section.page_height = Inches(8.5), Inches(11)
    section.top_margin = Inches(0.75)
    section.bottom_margin = Inches(1.0)
    section.left_margin = section.right_margin = Inches(0.625)


def new_section(doc, ncols):
    s = doc.add_section(WD_SECTION.CONTINUOUS)
    set_margins(s)
    set_cols(s, ncols)
    return s


def fmt(p, size=10, align=WD_ALIGN_PARAGRAPH.JUSTIFY, indent=0.2, before=0, after=0, keep=False):
    pf = p.paragraph_format
    pf.alignment = align
    pf.first_line_indent = Inches(indent) if indent else None
    pf.space_before, pf.space_after = Pt(before), Pt(after)
    pf.line_spacing = 1.0
    pf.keep_with_next = keep
    p._size = size
    return p


def unescape(s):
    s = s.replace("&#91;", "[")
    return re.sub(r"\\([\[\]_*&#])", r"\1", s)


INLINE = re.compile(r"(\*\*.+?\*\*|\*.+?\*|`.+?`|\^\{.+?\}|(?<=[A-Za-zμσ])_[a-z0-9]\b)")


def add_runs(p, text, size=10, bold=False, italic=False, smallcaps=False):
    text = unescape(text)
    for tok in INLINE.split(text):
        if not tok:
            continue
        b, i, sup, sub, mono = bold, italic, False, False, False
        if tok.startswith("**") and tok.endswith("**") and len(tok) > 4:
            tok, b = tok[2:-2], True
        elif tok.startswith("*") and tok.endswith("*") and len(tok) > 2:
            tok, i = tok[1:-1], True
        elif tok.startswith("`") and tok.endswith("`"):
            tok, mono = tok[1:-1], True
        elif tok.startswith("^{"):
            tok, sup = tok[2:-1], True
        elif re.fullmatch(r"_[a-z0-9]", tok):
            tok, sub = tok[1:], True
        r = p.add_run(tok)
        r.font.size = Pt(size)
        r.font.name = "Courier New" if mono else "Times New Roman"
        r.bold, r.italic = b, i
        r.font.small_caps = smallcaps
        r.font.superscript, r.font.subscript = sup, sub
    return p


def para(doc, text, **kw):
    size = kw.pop("size", 10)
    rk = {k: kw.pop(k) for k in ("bold", "italic", "smallcaps") if k in kw}
    p = fmt(doc.add_paragraph(), size=size, **kw)
    return add_runs(p, text, size=size, **rk)


def omml(tex):
    tex = re.sub(r"\\[bB]ig[lr]?", "", tex)
    mml = latex2mathml.converter.convert(tex)
    return xslt(etree.fromstring(mml.encode())).getroot()


def equation(doc, tex, num):
    p = fmt(doc.add_paragraph(), indent=0, align=WD_ALIGN_PARAGRAPH.LEFT, before=3, after=3)
    ts = p.paragraph_format.tab_stops
    ts.add_tab_stop(Inches(COL_W / 2), WD_TAB_ALIGNMENT.CENTER)
    ts.add_tab_stop(Inches(COL_W), WD_TAB_ALIGNMENT.RIGHT)
    p.add_run("\t")
    p._p.append(etree.fromstring(etree.tostring(omml(tex))))  # re-parse into the docx oxml tree
    r = p.add_run(f"\t({num})")
    r.font.size = Pt(10)
    r.font.name = "Times New Roman"


def table_borders(tbl):
    tblPr = tbl._tbl.tblPr
    b = OxmlElement("w:tblBorders")
    for edge in ("top", "bottom", "insideH"):
        e = OxmlElement(f"w:{edge}")
        e.set(qn("w:val"), "single")
        e.set(qn("w:sz"), "4")
        e.set(qn("w:color"), "000000")
        b.append(e)
    look = tblPr.find(qn("w:tblLook"))
    if look is not None:
        look.addprevious(b)
    else:
        tblPr.append(b)
    mar = OxmlElement("w:tblCellMar")
    for side in ("left", "right"):
        e = OxmlElement(f"w:{side}")
        e.set(qn("w:w"), "50")
        e.set(qn("w:type"), "dxa")
        mar.append(e)
    look = tblPr.find(qn("w:tblLook"))
    if look is not None:
        look.addprevious(mar)
    else:
        tblPr.append(mar)


def add_table(doc, rows, width_in, size=7):
    ncols = len(rows[0])
    # column widths proportional to longest text, with a floor
    lens = [max(min(len(unescape(r[c])), 60) for r in rows) for c in range(ncols)]
    lens = [max(l, 5) ** 0.8 for l in lens]
    widths = [width_in * l / sum(lens) for l in lens]
    floor = 0.5
    short = [w < floor for w in widths]
    spare = sum(floor - w for w in widths if w < floor)
    big = sum(w for w, sh in zip(widths, short) if not sh)
    widths = [floor if sh else w - spare * w / big for w, sh in zip(widths, short)]
    tbl = doc.add_table(rows=len(rows), cols=ncols)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False
    table_borders(tbl)
    for ri, row in enumerate(rows):
        for ci, cell_text in enumerate(row):
            cell = tbl.cell(ri, ci)
            cell.width = Inches(widths[ci])
            p = cell.paragraphs[0]
            fmt(p, size=size, indent=0, align=WD_ALIGN_PARAGRAPH.CENTER if ri == 0 or ci > 0 and len(cell_text) < 12 else WD_ALIGN_PARAGRAPH.LEFT)
            add_runs(p, cell_text, size=size, bold=(ri == 0))
    # header repeats / rows do not split
    for r in tbl.rows:
        trPr = r._tr.get_or_add_trPr()
        cs = OxmlElement("w:cantSplit")
        trPr.append(cs)
    return tbl


def caption_table(doc, num, title):
    para(doc, f"TABLE {num}", size=8, indent=0, align=WD_ALIGN_PARAGRAPH.CENTER, before=6, keep=True)
    para(doc, title, size=8, indent=0, align=WD_ALIGN_PARAGRAPH.CENTER, smallcaps=True, after=3, keep=True)


def figure(doc, fname, width_in, num, caption):
    p = fmt(doc.add_paragraph(), indent=0, align=WD_ALIGN_PARAGRAPH.CENTER, before=6, keep=True)
    p.add_run().add_picture(str(FIGS / fname), width=Inches(width_in))
    cp = fmt(doc.add_paragraph(), size=8, indent=0, align=WD_ALIGN_PARAGRAPH.JUSTIFY, after=6)
    add_runs(cp, f"Fig. {num}. ", size=8)
    add_runs(cp, caption, size=8)


# ---------- markdown walk ----------
def parse_table(lines, i):
    rows = []
    while i < len(lines) and lines[i].startswith("|"):
        cells = [c.strip() for c in re.split(r"(?<!\\)\|", lines[i].strip())[1:-1]]
        if not all(re.fullmatch(r"-+", c) for c in cells):
            rows.append(cells)
        i += 1
    return rows, i


def build(md_path, out_path):
    lines = Path(md_path).read_text(encoding="utf8").splitlines()
    start = next(i for i, l in enumerate(lines) if l.startswith("## Paper title"))
    end = next(i for i, l in enumerate(lines) if l.startswith("## Open items"))
    lines = lines[start + 1:end]

    doc = Document()
    st = doc.styles["Normal"]
    st.font.name, st.font.size = "Times New Roman", Pt(10)
    st.element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    set_margins(doc.sections[0])
    set_cols(doc.sections[0], 1)

    eq_num = fig_idx = 0
    pending_table = None  # (num, title)
    in_refs = in_alg = False
    pending_fig_caption = None
    i = 0
    while i < len(lines):
        l = lines[i].rstrip()
        if not l:
            i += 1
            continue
        # title block
        if l.startswith("**EfficientNetV2-MSAF"):
            para(doc, l.strip("*"), size=20, indent=0, align=WD_ALIGN_PARAGRAPH.CENTER, after=10)
            i += 1
            continue
        if l.startswith("&#91;Author 1"):
            for t in ("[Author 1], [Author 2], [Author 3]",
                      "[Department], [University]",
                      "[City], India",
                      "[email addresses]   ·   Guide: [Name, Designation]"):
                para(doc, t, size=10, indent=0, align=WD_ALIGN_PARAGRAPH.CENTER, italic=t.startswith("[Dep"))
            new_section(doc, 2)
            i += 1
            continue
        if l.startswith("**Abstract.**"):
            p = fmt(doc.add_paragraph(), size=9, indent=0.2, before=10)
            add_runs(p, "Abstract", size=9, bold=True, italic=True)
            add_runs(p, "—" + l[len("**Abstract.** "):], size=9, bold=True)
            i += 1
            continue
        if l.startswith("**Index Terms:**"):
            p = fmt(doc.add_paragraph(), size=9, indent=0.2, before=4, after=4)
            add_runs(p, "Index Terms", size=9, bold=True, italic=True)
            txt = l[len("**Index Terms:** "):]
            add_runs(p, "—" + txt[0].upper() + txt[1:], size=9, bold=True)
            i += 1
            continue
        if l.startswith("## "):
            head = l[3:]
            in_refs = head == "References"
            m = re.match(r"([IVX]+)\. (.*)", head)
            text = f"{m.group(1)}. {m.group(2)}" if m else head
            para(doc, text.upper() if not m else text, size=10, indent=0, align=WD_ALIGN_PARAGRAPH.CENTER,
                 smallcaps=True, before=6, after=3, keep=True)
            i += 1
            continue
        if l.startswith("### "):
            para(doc, l[4:], size=10, indent=0, align=WD_ALIGN_PARAGRAPH.LEFT, italic=True, before=4, after=2,
                 keep=True)
            i += 1
            continue
        if in_refs:
            if l.startswith("&#91;") or l.startswith("\\["):
                txt = unescape(l)
                m = re.match(r"(\[\d+\])\s*(.*)", txt)
                p = fmt(doc.add_paragraph(), size=8, indent=0, align=WD_ALIGN_PARAGRAPH.JUSTIFY)
                p.paragraph_format.left_indent = Inches(0.3)
                p.paragraph_format.first_line_indent = Inches(-0.3)
                p.paragraph_format.tab_stops.add_tab_stop(Inches(0.3))
                p.paragraph_format.line_spacing = Pt(9)
                add_runs(p, m.group(1) + "\t" + m.group(2).replace("[", "&#91;"), size=8)
            i += 1
            continue
        m = re.match(r"\*\*TABLE ([IVX]+)\. (.*)\*\*$", l)
        if m:
            pending_table = (m.group(1), m.group(2))
            i += 1
            continue
        if l.startswith("|"):
            rows, i = parse_table(lines, i)
            num, title = pending_table
            wide = num in WIDE_TABLES
            if wide:
                new_section(doc, 1)
            caption_table(doc, num, title)
            add_table(doc, rows, PAGE_W if wide else COL_W, size=7 if wide else 7.5)
            fmt(doc.add_paragraph(), size=4, indent=0, after=2)
            if wide:
                new_section(doc, 2)
            pending_table = None
            continue
        if l.startswith("```latex"):
            tex = lines[i + 1].strip()
            tex = re.sub(r"\\qquad \((\d+)\)$", "", tex).strip()
            if tex.startswith(r"M_s(F')"):  # residual output F + M_s(F') (x) F' is stated in the text
                tex = r"M_s(F')=\sigma(f^{7\times7}([\mathrm{AvgPool}_c(F');\mathrm{MaxPool}_c(F')]))"
            if tex.startswith("z="):  # classifier y = W Dropout(z) + b is stated in the text
                tex = tex.split(r",\qquad")[0]
            eq_num += 1
            equation(doc, tex, eq_num)
            i += 3
            continue
        if l.startswith("&#91;embedded content") or l.startswith("&#91;image"):
            fname, wide = FIG_FILES[fig_idx]
            fig_idx += 1
            # caption line follows
            j = i + 1
            while not lines[j].strip():
                j += 1
            cm = re.match(r"\*\*Fig\. (\d+)\.\*\* (.*)", lines[j])
            num, cap = cm.group(1), FIG_CAPTIONS.get(cm.group(1), cm.group(2))
            if wide:
                new_section(doc, 1)
                figure(doc, fname, 5.5, num, cap)
                new_section(doc, 2)
            else:
                figure(doc, fname, COL_W, num, cap)
            i = j + 1
            continue
        if l.startswith("**Algorithm 1"):
            p = para(doc, "Algorithm 1: Diagnosis pipeline", size=8, indent=0, bold=True, before=6, keep=True)
            border(p, "top"), border(p, "bottom")
            in_alg = True
            i += 1
            continue
        m = re.match(r"(\d+)\. (.*)", l)
        if m:
            n = m.group(1)
            p = fmt(doc.add_paragraph(), size=8 if in_alg else 10, indent=0, align=WD_ALIGN_PARAGRAPH.JUSTIFY)
            p.paragraph_format.left_indent = Inches(0.25)
            p.paragraph_format.first_line_indent = Inches(-0.25)
            p.paragraph_format.tab_stops.add_tab_stop(Inches(0.25))
            add_runs(p, f"{n}:\t" if in_alg else f"{n})\t", size=8 if in_alg else 10)
            add_runs(p, m.group(2), size=8 if in_alg else 10)
            nxt = i + 1
            while nxt < len(lines) and not lines[nxt].strip():
                nxt += 1
            if in_alg and not re.match(r"\d+\. ", lines[nxt]):
                border(p, "bottom")
                in_alg = False
            i += 1
            continue
        # body paragraph; bold run-in lead becomes italic
        rm = re.match(r"\*\*(.+?)\*\* (.*)", l)
        p = fmt(doc.add_paragraph(), size=10)
        if rm:
            add_runs(p, rm.group(1) + " ", italic=True)
            add_runs(p, rm.group(2))
        else:
            add_runs(p, l)
        i += 1

    doc.save(out_path)
    print("saved", out_path, "equations:", eq_num, "figures:", fig_idx)


def border(p, edge):
    pPr = p._p.get_or_add_pPr()
    bdr = pPr.find(qn("w:pBdr"))
    if bdr is None:
        bdr = OxmlElement("w:pBdr")
        pPr.insert_element_before(bdr, "w:shd", "w:tabs", "w:spacing", "w:ind", "w:jc", "w:rPr", "w:sectPr")
    e = OxmlElement(f"w:{edge}")
    e.set(qn("w:val"), "single")
    e.set(qn("w:sz"), "6")
    e.set(qn("w:space"), "1")
    e.set(qn("w:color"), "000000")
    bdr.append(e)


if __name__ == "__main__":
    build(sys.argv[1], sys.argv[2])

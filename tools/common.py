"""Shared helpers for the CV Match Agent tools. Standard library only, except optional PDF support."""
from __future__ import annotations

import csv
import datetime as dt
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
CV_DIR = DATA / "cvs"
TEAM_DIR = DATA / "team"
WORK = Path(os.environ.get("CVMATCH_WORK") or ROOT / ".work")  # overridable for tests
RUNS = WORK / "runs"

CV_EXTENSIONS = {".pptx", ".ppt", ".docx", ".pdf", ".txt", ".md", ".doc", ".odt", ".rtf"}
TEAM_EXTENSIONS = {".xlsx", ".csv"}
OUTDATED_MONTHS = 12

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
S = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
R = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
PR = "{http://schemas.openxmlformats.org/package/2006/relationships}"
A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
P = "{http://schemas.openxmlformats.org/presentationml/2006/main}"


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------- text extraction

def _docx_text(path: Path) -> tuple[str, str | None]:
    """Return (text, modified_date) from a .docx using only the standard library."""
    with zipfile.ZipFile(path) as z:
        root = ET.fromstring(z.read("word/document.xml"))
        modified = _core_modified(z)
    lines = []
    body = root.find(f"{W}body")
    for block in body.iter():
        if block.tag == f"{W}p":
            parts = []
            for node in block.iter():
                if node.tag == f"{W}t" and node.text:
                    parts.append(node.text)
                elif node.tag == f"{W}tab":
                    parts.append("\t")
                elif node.tag in (f"{W}br", f"{W}cr"):
                    parts.append("\n")
            line = "".join(parts).strip()
            if line:
                lines.append(line)
    return "\n".join(lines), modified


def _core_modified(z: zipfile.ZipFile) -> str | None:
    if "docProps/core.xml" not in z.namelist():
        return None
    m = re.search(rb"<dcterms:modified[^>]*>([^<]+)<", z.read("docProps/core.xml"))
    return m.group(1).decode()[:10] if m else None


def _pptx_text(path: Path) -> tuple[str, str | None]:
    """Return (text, modified_date) from a .pptx, slides in presentation order, standard library only."""
    with zipfile.ZipFile(path) as z:
        names = set(z.namelist())
        order = []
        if "ppt/presentation.xml" in names and "ppt/_rels/presentation.xml.rels" in names:
            rels = {r.get("Id"): r.get("Target") for r in
                    ET.fromstring(z.read("ppt/_rels/presentation.xml.rels")).iter(f"{PR}Relationship")}
            pres = ET.fromstring(z.read("ppt/presentation.xml"))
            for sld in pres.iter(f"{P}sldId"):
                target = rels.get(sld.get(f"{R}id"), "")
                target = target.lstrip("/")
                order.append(target if target.startswith("ppt/") else f"ppt/{target}")
        if not order:
            order = sorted((n for n in names if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)),
                           key=lambda n: int(re.search(r"(\d+)", n.rsplit("/", 1)[1]).group(1)))
        chunks = []
        for i, slide in enumerate(order, 1):
            if slide not in names:
                continue
            root = ET.fromstring(z.read(slide))
            lines = []
            for para in root.iter(f"{A}p"):
                line = "".join(t.text or "" for t in para.iter(f"{A}t")).strip()
                if line:
                    lines.append(line)
            if lines:
                chunks.append(f"--- Slide {i} ---\n" + "\n".join(lines))
        return "\n\n".join(chunks), _core_modified(z)


def _load_pypdf():
    """Import pypdf, falling back to a project .venv if the system install is missing or broken."""
    try:
        import pypdf  # noqa: F401
        return pypdf
    except BaseException:  # a broken optional dependency can raise non-ImportError errors
        pass
    for site in glob.glob(str(ROOT / ".venv" / "lib" / "python*" / "site-packages")) + [str(ROOT / ".venv" / "Lib" / "site-packages")]:
        if Path(site).is_dir() and site not in sys.path:
            sys.path.insert(0, site)
    for name in [m for m in sys.modules if m.startswith(("pypdf", "cryptography"))]:
        del sys.modules[name]
    try:
        import pypdf
        return pypdf
    except BaseException:
        return None


def _pdf_text(path: Path) -> tuple[str, str | None]:
    pypdf = _load_pypdf()
    if pypdf is not None:
        reader = pypdf.PdfReader(str(path))
        text = "\n".join((page.extract_text() or "") for page in reader.pages)
        modified = None
        meta = reader.metadata or {}
        raw = str(meta.get("/ModDate") or meta.get("/CreationDate") or "")
        m = re.search(r"(\d{4})(\d{2})(\d{2})", raw)
        if m:
            modified = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
        return text, modified
    if shutil.which("pdftotext"):
        out = subprocess.run(["pdftotext", "-layout", str(path), "-"], capture_output=True, text=True, check=True)
        return out.stdout, None
    raise RuntimeError("no PDF support: run `pip install -r requirements.txt` (pypdf) or install pdftotext")


def _office_text(path: Path) -> tuple[str, str | None]:
    office = shutil.which("soffice") or shutil.which("libreoffice")
    if not office:
        raise RuntimeError(f"{path.suffix} needs LibreOffice to convert; save the CV as .docx or .pdf instead")
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run([office, "--headless", "--convert-to", "txt:Text", "--outdir", tmp, str(path)],
                       capture_output=True, check=True, timeout=120)
        out = next(Path(tmp).glob("*.txt"), None)
        if out is None:
            raise RuntimeError("LibreOffice conversion produced no text")
        return out.read_text(encoding="utf-8", errors="replace"), None


def extract_text(path: Path) -> tuple[str, str | None]:
    """Return (plain text, document modified date or None). Raises on unreadable files."""
    ext = path.suffix.lower()
    if ext == ".pptx":
        return _pptx_text(path)
    if ext == ".docx":
        return _docx_text(path)
    if ext == ".pdf":
        return _pdf_text(path)
    if ext in (".txt", ".md"):
        return path.read_text(encoding="utf-8", errors="replace"), None
    if ext in (".ppt", ".doc", ".odt", ".rtf"):
        return _office_text(path)
    raise RuntimeError(f"unsupported file type {ext}")


# ---------------------------------------------------------------- team list

def _xlsx_rows(path: Path) -> list[list[str]]:
    """Rows of the first worksheet of an .xlsx, as strings (dates as YYYY-MM-DD where formatted as dates)."""
    with zipfile.ZipFile(path) as z:
        names = set(z.namelist())
        shared = []
        if "xl/sharedStrings.xml" in names:
            for si in ET.fromstring(z.read("xl/sharedStrings.xml")).iter(f"{S}si"):
                shared.append("".join(t.text or "" for t in si.iter(f"{S}t")))
        wb = ET.fromstring(z.read("xl/workbook.xml"))
        first = wb.find(f"{S}sheets/{S}sheet")
        rid = first.get(f"{R}id")
        rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        target = next(r.get("Target") for r in rels.iter(f"{PR}Relationship") if r.get("Id") == rid)
        target = target.lstrip("/")
        sheet_path = target if target.startswith("xl/") else f"xl/{target}"
        date_styles = set()
        if "xl/styles.xml" in names:
            styles = ET.fromstring(z.read("xl/styles.xml"))
            custom = {n.get("numFmtId"): n.get("formatCode", "") for n in styles.iter(f"{S}numFmt")}
            xfs = styles.find(f"{S}cellXfs")
            for i, xf in enumerate(xfs if xfs is not None else []):
                fid = xf.get("numFmtId", "0")
                code = custom.get(fid, "")
                if fid in {"14", "15", "16", "17", "22"} or (re.search(r"[dy]", code, re.I) and "[" not in code[:1]):
                    date_styles.add(str(i))
        sheet = ET.fromstring(z.read(sheet_path))
    rows = []
    for row in sheet.iter(f"{S}row"):
        cells = {}
        for c in row.iter(f"{S}c"):
            ref = c.get("r", "")
            col = 0
            for ch in re.match(r"[A-Z]+", ref).group(0) if ref else "":
                col = col * 26 + (ord(ch) - 64)
            col -= 1
            t = c.get("t")
            v = c.find(f"{S}v")
            if t == "s" and v is not None:
                val = shared[int(v.text)]
            elif t == "inlineStr":
                val = "".join(x.text or "" for x in c.iter(f"{S}t"))
            elif v is not None and v.text is not None:
                val = v.text
                if c.get("s") in date_styles:
                    try:
                        val = (dt.date(1899, 12, 30) + dt.timedelta(days=float(val))).isoformat()
                    except ValueError:
                        pass
            else:
                val = ""
            cells[col if col >= 0 else len(cells)] = val.strip()
        if cells:
            rows.append([cells.get(i, "") for i in range(max(cells) + 1)])
    return rows


def _csv_rows(path: Path) -> list[list[str]]:
    raw = path.read_text(encoding="utf-8-sig", errors="replace")
    try:
        dialect = csv.Sniffer().sniff(raw[:4096], delimiters=",;\t")
    except csv.Error:
        dialect = csv.excel
    return [[c.strip() for c in r] for r in csv.reader(raw.splitlines(), dialect) if any(c.strip() for c in r)]


COLUMN_SYNONYMS = {
    "name": ["name", "full name", "employee", "employee name", "person", "mitarbeiter", "mitarbeitername", "vollständiger name"],
    "first_name": ["first name", "firstname", "given name", "vorname"],
    "last_name": ["last name", "lastname", "surname", "family name", "nachname"],
    "id": ["id", "person id", "employee id", "pseudonym", "cv id", "code", "kürzel", "kuerzel", "mitarbeiter id", "personalnummer"],
    "availability": ["availability", "available", "verfügbarkeit", "verfuegbarkeit", "free capacity", "freie kapazität", "capacity"],
    "available_from": ["available from", "free from", "verfügbar ab", "verfuegbar ab", "from"],
    "level": ["level", "career level", "grade", "karrierestufe", "stufe"],
    "cv_file": ["cv file", "cv", "file", "datei", "lebenslauf"],
}


def _norm_header(h: str) -> str:
    return re.sub(r"[\s_\-/]+", " ", h.strip().lower())


def map_columns(headers: list[str], override: dict | None) -> dict[str, int]:
    """Map logical fields to column indexes, using data/team/columns.json overrides first, then synonyms."""
    normed = [_norm_header(h) for h in headers]
    mapping = {}
    for field, col_name in (override or {}).items():
        if col_name and _norm_header(col_name) in normed:
            mapping[field] = normed.index(_norm_header(col_name))
    for field, names in COLUMN_SYNONYMS.items():
        if field in mapping:
            continue
        for i, h in enumerate(normed):
            if h in names and i not in mapping.values():
                mapping[field] = i
                break
    return mapping


def parse_availability(raw: str) -> float | None:
    """Normalise an availability cell to 0-100 (% free). None if it can't be read."""
    s = (raw or "").strip().lower()
    if not s:
        return None
    m = re.fullmatch(r"(\d+(?:[.,]\d+)?)\s*%?", s)
    if m:
        n = float(m.group(1).replace(",", "."))
        return max(0.0, min(100.0, n * 100 if n <= 1 and "%" not in s else n))
    if s in {"free", "available", "yes", "y", "ja", "frei", "verfügbar", "verfuegbar"}:
        return 100.0
    if s in {"booked", "no", "n", "nein", "busy", "not available", "nicht verfügbar", "belegt", "gebucht"}:
        return 0.0
    return None


def parse_date(raw: str) -> str | None:
    s = (raw or "").strip()
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y", "%Y-%m", "%m/%Y", "%m.%Y"):
        try:
            return dt.datetime.strptime(s[:10], fmt).date().isoformat()
        except ValueError:
            continue
    return None


# ---------------------------------------------------------------- text normalisation for evidence checks

def normalise(text: str) -> str:
    t = unicodedata.normalize("NFKC", text).lower()
    t = re.sub(r"[‐-―−]", "-", t)
    t = re.sub(r"[‘’‚`´]", "'", t)
    t = re.sub(r"[“”„]", '"', t)
    t = re.sub(r"[•●▪◦·]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def quote_in_text(quote: str, norm_text: str) -> bool:
    """True if the quote (fragments split by ... or …) appears in order in the normalised text."""
    fragments = [normalise(f) for f in re.split(r"\.\.\.|…", quote)]
    pos = 0
    found_any = False
    for frag in fragments:
        frag = frag.strip(" .,;:")
        if not frag:
            continue
        idx = norm_text.find(frag, pos)
        if idx < 0:
            return False
        pos = idx + len(frag)
        found_any = True
    return found_any


# ---------------------------------------------------------------- name matching

NAME_NOISE = {"cv", "lebenslauf", "profile", "profil", "resume", "final", "neu", "new", "copy", "kopie", "draft",
              "version", "dr", "prof", "mba", "msc", "bsc", "phd", "dipl", "ing", "de", "en", "ger", "eng", "v"}


def name_tokens(name: str) -> list[str]:
    """Lower-case name tokens with accents and German umlaut spellings folded (Müller = Mueller = Muller)."""
    t = name.lower().replace("ß", "ss")
    t = unicodedata.normalize("NFKD", t)
    t = "".join(ch for ch in t if not unicodedata.combining(ch))
    tokens = []
    for tok in re.split(r"[^a-z]+", t):
        tok = tok.replace("ae", "a").replace("oe", "o").replace("ue", "u")
        if len(tok) >= 2 and tok not in NAME_NOISE:
            tokens.append(tok)
    return tokens


def name_match(team_name: str, other: str) -> str | None:
    """Compare a team-list name with a file name or CV heading.

    Returns "exact" (same tokens, any order), "strong" (one name's tokens contained in the other's,
    at least two shared, e.g. an extra middle name), "probable" (two shared tokens, or very similar
    spelling), or None.
    """
    a, b = name_tokens(team_name), name_tokens(other)
    if not a or not b:
        return None
    sa, sb = set(a), set(b)
    shared = sa & sb
    if sa == sb:
        return "exact"
    if len(shared) >= 2 and (sa <= sb or sb <= sa):
        return "strong"
    if len(shared) >= 2:
        return "probable"
    if len(a) >= 2 and len(b) >= 2:
        import difflib
        if difflib.SequenceMatcher(None, " ".join(sorted(a)), " ".join(sorted(b))).ratio() >= 0.88:
            return "probable"
    return None


def slug(name: str) -> str:
    """File-safe person key: lower case, accents removed, but spelling otherwise kept (Manuela stays manuela)."""
    t = unicodedata.normalize("NFKD", name.lower().replace("ß", "ss"))
    t = "".join(ch for ch in t if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")

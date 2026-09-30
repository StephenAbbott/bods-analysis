"""Shared helpers for the MEIP x UK PSC comparison."""
import re, unicodedata

# Copied verbatim in behaviour from opencheck/identifiers.py (Phase 177):
_CH_NUMBER_SHAPE = re.compile(r"^([A-Z]{0,2})([0-9]{1,8})$")
def normalise_ch_company_number(value):
    if value is None: return None
    raw = str(value).strip().upper().replace(" ", "")
    if not raw: return None
    m = _CH_NUMBER_SHAPE.match(raw)
    if m is None: return None
    prefix, digits = m.group(1), m.group(2)
    width = 8 - len(prefix)
    if len(digits) > width: return None
    return f"{prefix}{digits.zfill(width)}"

# Legal-form words folded to one token each, so "LIMITED"=="LTD" etc.
_FORMS = [
    (r"\bPUBLIC LIMITED COMPANY\b", "PLC"), (r"\bP\.?L\.?C\.?\b", "PLC"),
    (r"\bLIMITED LIABILITY PARTNERSHIP\b", "LLP"), (r"\bLIMITED PARTNERSHIP\b", "LP"),
    (r"\bLIMITED LIABILITY COMPANY\b", "LLC"), (r"\bL\.?L\.?C\.?\b", "LLC"),
    (r"\bLIMITED\b", "LTD"), (r"\bINCORPORATED\b", "INC"), (r"\bCORPORATION\b", "CORP"),
    (r"\bCOMPANY\b", "CO"), (r"\bAKTIENGESELLSCHAFT\b", "AG"), (r"\bSOCIETE ANONYME\b", "SA"),
    (r"\bNAAMLOZE VENNOOTSCHAP\b", "NV"), (r"\bBESLOTEN VENNOOTSCHAP\b", "BV"),
    (r"\bGESELLSCHAFT MIT BESCHRANKTER HAFTUNG\b", "GMBH"), (r"\bHOLDINGS\b", "HOLDING"),
    (r"\b&\b", "AND"),
]
FORM_TOKENS = {"PLC","LLP","LP","LLC","LTD","INC","CORP","CO","AG","SA","NV","BV","GMBH",
               "SE","SAS","SPA","SRL","AB","AS","ASA","OYJ","KK","PTE","PTY","BHD","SDN","THE","DAC","ULC","LTDA","SARL"}

_UMLAUT = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "Ä": "Ae", "Ö": "Oe", "Ü": "Ue", "ß": "ss"})

def norm_name(s, expand_umlauts=False):
    """Strict key: upper-case, accents stripped, punctuation removed, legal forms folded.
    expand_umlauts=True writes ä/ö/ü/ß as ae/oe/ue/ss first (German transliteration),
    so "Münchener" can meet "Muenchener"; callers use both variants."""
    if not s: return ""
    if expand_umlauts: s = str(s).translate(_UMLAUT)
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    s = s.upper().replace("&", " AND ")
    s = re.sub(r"[\.,'`’\"()\[\]/\\\-]", " ", s)
    s = re.sub(r"\s+", " ", s)
    # Re-join initialisms split by removed dots: "S A" -> "SA", "S P A" -> "SPA", "U K" -> "UK"
    s = re.sub(r"\b(?:[A-Z] )+[A-Z]\b", lambda m: m.group(0).replace(" ", ""), s)
    for pat, rep in _FORMS: s = re.sub(pat, rep, s)
    return re.sub(r"\s+", " ", s).strip()

def stem_name(s, expand_umlauts=False):
    """Loose key: strict key with legal-form tokens and 'THE' removed."""
    toks = [t for t in norm_name(s, expand_umlauts).split() if t not in FORM_TOKENS]
    return " ".join(toks)

def strict_keys(s): return {k for k in (norm_name(s), norm_name(s, True)) if k}
def loose_keys(s): return {k for k in (stem_name(s), stem_name(s, True)) if k}

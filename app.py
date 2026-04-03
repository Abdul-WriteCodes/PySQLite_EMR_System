import streamlit as st
import anthropic
import json
import re
import time
import zipfile
import io
from pathlib import Path

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SLR Analyser",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Inject CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Global ─────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* ── Sidebar ─────────────────────────────── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
    border-right: 1px solid #334155;
}
[data-testid="stSidebar"] * { color: #e2e8f0 !important; }
[data-testid="stSidebar"] .stMarkdown h1,
[data-testid="stSidebar"] .stMarkdown h2,
[data-testid="stSidebar"] .stMarkdown h3 { color: #f8fafc !important; }

/* ── Main header ──────────────────────────── */
.main-header {
    background: linear-gradient(135deg, #1e3a5f 0%, #1e40af 50%, #1d4ed8 100%);
    border-radius: 16px;
    padding: 2rem 2.5rem;
    margin-bottom: 2rem;
    box-shadow: 0 4px 24px rgba(30,64,175,0.25);
}
.main-header h1 { color: #f0f9ff; font-size: 2rem; font-weight: 700; margin: 0; }
.main-header p  { color: #bae6fd; margin: 0.5rem 0 0; font-size: 1rem; }

/* ── Cards ────────────────────────────────── */
.paper-card {
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    transition: box-shadow .2s;
}
.paper-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.1); }

.theme-card {
    background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
    border: 1px solid #bfdbfe;
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1rem;
}

.meta-badge {
    display: inline-block;
    background: #dbeafe;
    color: #1e40af;
    border-radius: 6px;
    padding: 2px 10px;
    font-size: 0.78rem;
    font-weight: 600;
    margin: 3px 4px 3px 0;
}
.meta-badge.green  { background: #dcfce7; color: #166534; }
.meta-badge.purple { background: #f3e8ff; color: #6b21a8; }
.meta-badge.amber  { background: #fef3c7; color: #92400e; }

/* ── Step indicator ───────────────────────── */
.step-bar {
    display: flex;
    gap: 8px;
    margin-bottom: 1.5rem;
    align-items: center;
}
.step {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 0.82rem;
    font-weight: 600;
}
.step.done    { background:#dcfce7; color:#166534; }
.step.active  { background:#dbeafe; color:#1e40af; }
.step.pending { background:#f1f5f9; color:#94a3b8; }

/* ── Progress ─────────────────────────────── */
.progress-label { font-size: 0.85rem; color: #64748b; margin-bottom: 4px; }

/* ── Export button ─────────────────────────── */
div[data-testid="stDownloadButton"] button {
    background: linear-gradient(135deg, #1e40af, #1d4ed8) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}
</style>
""", unsafe_allow_html=True)

# ── Helpers ────────────────────────────────────────────────────────────────────

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from a PDF using pypdf."""
    try:
        import pypdf, io
        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        pages = [p.extract_text() or "" for p in reader.pages]
        return "\n\n".join(pages)
    except Exception as e:
        return f"[PDF extraction error: {e}]"


def extract_text_from_docx(file_bytes: bytes) -> str:
    """Extract text from a docx using python-docx."""
    try:
        import docx, io
        doc = docx.Document(io.BytesIO(file_bytes))
        return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())
    except Exception as e:
        return f"[DOCX extraction error: {e}]"


def extract_text(file_name: str, file_bytes: bytes) -> str:
    ext = Path(file_name).suffix.lower()
    if ext == ".pdf":
        return extract_text_from_pdf(file_bytes)
    elif ext in (".docx", ".doc"):
        return extract_text_from_docx(file_bytes)
    elif ext == ".txt":
        return file_bytes.decode("utf-8", errors="replace")
    else:
        return file_bytes.decode("utf-8", errors="replace")


def call_claude(prompt: str, system: str = "", max_tokens: int = 2000) -> str:
    """Call Claude API and return text response."""
    client = anthropic.Anthropic(api_key=st.session_state.api_key)
    messages = [{"role": "user", "content": prompt}]
    kwargs = dict(
        model="claude-sonnet-4-20250514",
        max_tokens=max_tokens,
        messages=messages,
    )
    if system:
        kwargs["system"] = system
    resp = client.messages.create(**kwargs)
    return resp.content[0].text


def abstract_paper(title: str, text: str) -> dict:
    """Run data abstraction on a single paper."""
    system = (
        "You are an expert systematic literature review assistant. "
        "Extract structured metadata from academic papers. "
        "Always respond with valid JSON only — no markdown fences, no commentary."
    )
    prompt = f"""Extract the following fields from this paper. If a field cannot be determined, use null.

Return ONLY a JSON object with these exact keys:
- "title": string
- "authors": list of strings
- "year": string or null
- "journal_or_venue": string or null
- "methodology_design": string (e.g., RCT, qualitative, systematic review, survey, case study, mixed methods)
- "sample_size": string or null
- "main_findings": string (2-4 sentences)
- "contributions": string (1-3 bullet points as a single string)
- "limitations": string or null
- "keywords": list of strings (up to 8)

PAPER TITLE (from filename): {title}

PAPER TEXT (first 6000 chars):
{text[:6000]}
"""
    raw = call_claude(prompt, system=system, max_tokens=1000)
    raw = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
    try:
        data = json.loads(raw)
    except Exception:
        data = {
            "title": title, "authors": [], "year": None,
            "journal_or_venue": None, "methodology_design": "Unknown",
            "sample_size": None, "main_findings": raw[:500],
            "contributions": "", "limitations": None, "keywords": []
        }
    if not data.get("title") or data["title"] == "null":
        data["title"] = title
    return data


def identify_themes(abstractions: list[dict]) -> str:
    """Identify key themes across all papers."""
    system = (
        "You are an expert systematic review analyst. "
        "Synthesise findings across multiple studies into coherent thematic narratives."
    )
    summaries = []
    for i, p in enumerate(abstractions, 1):
        summaries.append(
            f"Paper {i}: {p.get('title','N/A')}\n"
            f"  Year: {p.get('year','?')} | Method: {p.get('methodology_design','?')}\n"
            f"  Findings: {p.get('main_findings','')}\n"
            f"  Contributions: {p.get('contributions','')}\n"
            f"  Keywords: {', '.join(p.get('keywords',[]))}"
        )
    combined = "\n\n".join(summaries)
    prompt = f"""You have been given data abstractions from {len(abstractions)} academic papers.

{combined}

Perform a thematic synthesis:
1. Identify 4-7 major themes that cut across the papers.
2. For each theme: give it a clear title, explain it in 3-5 sentences citing which papers support it, and note any contradictions or gaps.
3. Write a concluding paragraph about overall research trajectory and future directions.

Format your response in clean markdown with ## headings for each theme.
"""
    return call_claude(prompt, system=system, max_tokens=3000)


def write_synthesis_report(abstractions: list[dict], themes_text: str) -> str:
    """Write a full synthesis narrative."""
    system = "You are an expert academic writer specialising in systematic literature reviews."
    metadata_summary = f"{len(abstractions)} papers | Years: " + ", ".join(
        sorted({str(p.get('year','?')) for p in abstractions if p.get('year')})
    )
    prompt = f"""Write a comprehensive synthesis section for a systematic literature review.

METADATA OVERVIEW: {metadata_summary}

THEMATIC ANALYSIS:
{themes_text}

Write the synthesis in formal academic prose (600-900 words). Include:
- An opening paragraph contextualising the body of literature
- A paragraph for each major theme (weaving evidence from multiple papers)
- Discussion of methodological diversity and any notable limitations
- A concluding paragraph on implications and research gaps

Use hedged academic language. Do not use first person. Use markdown formatting.
"""
    return call_claude(prompt, system=system, max_tokens=3000)


def build_export(abstractions: list[dict], themes: str, synthesis: str) -> bytes:
    """Package all results into a downloadable zip."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        # JSON data
        zf.writestr("abstractions.json", json.dumps(abstractions, indent=2))
        # Themes markdown
        zf.writestr("themes.md", themes)
        # Synthesis markdown
        zf.writestr("synthesis_report.md", synthesis)
        # CSV summary
        import csv, io as sio
        csv_buf = sio.StringIO()
        fields = ["title","authors","year","journal_or_venue","methodology_design",
                  "sample_size","main_findings","contributions","limitations","keywords"]
        writer = csv.DictWriter(csv_buf, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for p in abstractions:
            row = {k: (", ".join(v) if isinstance(v, list) else v) for k,v in p.items()}
            writer.writerow(row)
        zf.writestr("abstractions_summary.csv", csv_buf.getvalue())
    return buf.getvalue()


# ── Session state init ─────────────────────────────────────────────────────────
for key, default in {
    "api_key": "",
    "step": 0,           # 0=upload, 1=abstracting, 2=theming, 3=done
    "abstractions": [],
    "themes": "",
    "synthesis": "",
    "files_processed": [],
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🔬 SLR Analyser")
    st.markdown("---")
    st.markdown("### ⚙️ Configuration")
    api_key_input = st.text_input(
        "Anthropic API Key",
        type="password",
        value=st.session_state.api_key,
        placeholder="sk-ant-...",
        help="Get your key at console.anthropic.com"
    )
    if api_key_input:
        st.session_state.api_key = api_key_input

    st.markdown("---")
    st.markdown("### 📋 What this tool does")
    st.markdown("""
- **Extracts** text from PDF, DOCX, TXT
- **Abstracts** each paper (authors, year, method, findings, contributions)
- **Identifies** key themes across the corpus
- **Writes** a synthesis narrative
- **Exports** JSON, CSV, and Markdown
""")
    st.markdown("---")
    st.markdown("### 📖 Supported formats")
    st.markdown("`.pdf` · `.docx` · `.txt`")

    if st.session_state.step > 0:
        st.markdown("---")
        if st.button("🔄 Start New Review", use_container_width=True):
            for k in ["step","abstractions","themes","synthesis","files_processed"]:
                st.session_state[k] = [] if k in ("abstractions","files_processed") else ("" if k in ("themes","synthesis") else 0)
            st.rerun()


# ── Main layout ────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
  <h1>🔬 Systematic Literature Review Analyser</h1>
  <p>Upload your papers · Extract structured data · Identify themes · Generate synthesis</p>
</div>
""", unsafe_allow_html=True)

# Step bar
steps = ["📤 Upload", "🔍 Abstract", "🧵 Themes", "✅ Results"]
step_html = '<div class="step-bar">'
for i, label in enumerate(steps):
    if i < st.session_state.step:
        cls = "done"
    elif i == st.session_state.step:
        cls = "active"
    else:
        cls = "pending"
    step_html += f'<div class="step {cls}">{label}</div>'
    if i < len(steps)-1:
        step_html += '<span style="color:#cbd5e1">›</span>'
step_html += '</div>'
st.markdown(step_html, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# STEP 0 — Upload
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.step == 0:
    st.markdown("### Step 1 — Upload Papers")

    uploaded = st.file_uploader(
        "Drop your papers here (PDF, DOCX, or TXT)",
        type=["pdf", "docx", "txt"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    if uploaded:
        st.success(f"✅ {len(uploaded)} file(s) ready")
        cols = st.columns(3)
        for i, f in enumerate(uploaded):
            cols[i % 3].markdown(
                f'<div class="paper-card" style="padding:.75rem 1rem">'
                f'<b style="font-size:.85rem">📄 {f.name}</b><br>'
                f'<span style="font-size:.75rem;color:#64748b">{f.size/1024:.1f} KB</span>'
                f'</div>',
                unsafe_allow_html=True
            )

        st.markdown("")
        col1, col2 = st.columns([1, 3])
        with col1:
            if not st.session_state.api_key:
                st.warning("⚠️ Enter API key in sidebar first")
            else:
                if st.button("🚀 Start Analysis", type="primary", use_container_width=True):
                    st.session_state.files_to_process = [
                        (f.name, f.read()) for f in uploaded
                    ]
                    st.session_state.step = 1
                    st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# STEP 1 — Abstraction
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == 1:
    st.markdown("### Step 2 — Data Abstraction")
    st.info("Extracting structured metadata from each paper using Claude AI…")

    files = st.session_state.get("files_to_process", [])
    progress_bar = st.progress(0)
    status_box   = st.empty()
    results_box  = st.container()

    abstractions = []
    for idx, (fname, fbytes) in enumerate(files):
        status_box.markdown(f'<p class="progress-label">Processing <b>{fname}</b> ({idx+1}/{len(files)})…</p>', unsafe_allow_html=True)
        text = extract_text(fname, fbytes)
        try:
            data = abstract_paper(fname, text)
        except Exception as e:
            data = {"title": fname, "main_findings": f"Error: {e}", "authors": [],
                    "year": None, "methodology_design": "Error", "contributions": "",
                    "limitations": None, "keywords": [], "journal_or_venue": None, "sample_size": None}
        abstractions.append(data)
        progress_bar.progress((idx + 1) / len(files))
        time.sleep(0.3)  # brief pause between API calls

    st.session_state.abstractions = abstractions
    status_box.success(f"✅ Abstracted {len(abstractions)} papers!")
    st.session_state.step = 2
    time.sleep(1)
    st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# STEP 2 — Theme identification
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == 2:
    st.markdown("### Step 3 — Theme Identification & Synthesis")
    st.info("Identifying cross-cutting themes and generating synthesis narrative…")

    with st.spinner("Analysing themes across papers…"):
        try:
            themes = identify_themes(st.session_state.abstractions)
            st.session_state.themes = themes
        except Exception as e:
            st.session_state.themes = f"Theme analysis error: {e}"

    with st.spinner("Writing synthesis report…"):
        try:
            synthesis = write_synthesis_report(st.session_state.abstractions, st.session_state.themes)
            st.session_state.synthesis = synthesis
        except Exception as e:
            st.session_state.synthesis = f"Synthesis error: {e}"

    st.session_state.step = 3
    st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# STEP 3 — Results
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == 3:
    abstractions = st.session_state.abstractions
    themes       = st.session_state.themes
    synthesis    = st.session_state.synthesis

    # ── Top metrics
    years = [p.get("year") for p in abstractions if p.get("year")]
    methods = [p.get("methodology_design","") for p in abstractions]
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("📄 Papers Analysed", len(abstractions))
    m2.metric("📅 Year Range", f"{min(years, default='?')} – {max(years, default='?')}")
    unique_methods = len({m for m in methods if m and m != "Unknown"})
    m3.metric("🧪 Study Designs", unique_methods)
    all_kws = [k for p in abstractions for k in (p.get("keywords") or [])]
    m4.metric("🔑 Unique Keywords", len(set(all_kws)))

    st.markdown("---")
    tab1, tab2, tab3 = st.tabs(["📑 Paper Abstractions", "🧵 Themes & Synthesis", "📊 Overview"])

    # ── Tab 1: Paper cards
    with tab1:
        st.markdown(f"#### {len(abstractions)} Paper Abstractions")
        for p in abstractions:
            with st.expander(f"📄 {p.get('title','Untitled')}", expanded=False):
                c1, c2 = st.columns([3,1])
                with c1:
                    authors = p.get("authors") or []
                    if authors:
                        st.markdown(f"**Authors:** {', '.join(authors[:5])}{'...' if len(authors)>5 else ''}")
                    st.markdown(f"**Journal/Venue:** {p.get('journal_or_venue') or 'Not identified'}")
                with c2:
                    badges = ""
                    if p.get("year"):
                        badges += f'<span class="meta-badge amber">{p["year"]}</span>'
                    if p.get("methodology_design"):
                        badges += f'<span class="meta-badge purple">{p["methodology_design"]}</span>'
                    if p.get("sample_size"):
                        badges += f'<span class="meta-badge green">n={p["sample_size"]}</span>'
                    st.markdown(badges, unsafe_allow_html=True)

                st.markdown("**Main Findings:**")
                st.markdown(p.get("main_findings") or "_Not available_")
                st.markdown("**Contributions:**")
                st.markdown(p.get("contributions") or "_Not available_")
                if p.get("limitations"):
                    st.markdown("**Limitations:**")
                    st.markdown(p["limitations"])
                kws = p.get("keywords") or []
                if kws:
                    kw_html = " ".join(f'<span class="meta-badge">{k}</span>' for k in kws)
                    st.markdown(f"**Keywords:** {kw_html}", unsafe_allow_html=True)

    # ── Tab 2: Themes & Synthesis
    with tab2:
        t1, t2 = st.tabs(["🧵 Key Themes", "✍️ Synthesis Narrative"])
        with t1:
            st.markdown(themes)
        with t2:
            st.markdown(synthesis)

    # ── Tab 3: Overview table
    with tab3:
        st.markdown("#### Corpus Overview Table")
        import pandas as pd
        rows = []
        for p in abstractions:
            rows.append({
                "Title": (p.get("title") or "")[:60] + ("…" if len(p.get("title",""))>60 else ""),
                "Year": p.get("year") or "?",
                "Method": p.get("methodology_design") or "?",
                "Authors (1st)": (p.get("authors") or ["?"])[0],
                "Venue": (p.get("journal_or_venue") or "?")[:40],
                "Keywords": ", ".join((p.get("keywords") or [])[:4]),
            })
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)

    # ── Export
    st.markdown("---")
    st.markdown("### 📦 Export Results")
    col1, col2 = st.columns([2,3])
    with col1:
        zip_bytes = build_export(abstractions, themes, synthesis)
        st.download_button(
            label="⬇️ Download Full Package (.zip)",
            data=zip_bytes,
            file_name="slr_results.zip",
            mime="application/zip",
            use_container_width=True,
        )
    with col2:
        st.caption("Contains: `abstractions.json` · `abstractions_summary.csv` · `themes.md` · `synthesis_report.md`")

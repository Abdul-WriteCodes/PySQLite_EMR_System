import streamlit as st
from core.exporter import (
    papers_to_csv,
    papers_to_excel,
    papers_to_latex,
    papers_to_json,
)
import json


def render():
    papers = st.session_state.get("extracted_papers", [])
    synthesis = st.session_state.get("synthesis_result")

    st.markdown("""
    <div class="page-header">
        <div class="page-eyebrow">Step 04 · Export</div>
        <h1 class="page-title">Export <em>Intelligence</em></h1>
        <p class="page-subtitle">
            Download your extracted data in multiple formats — 
            ready for literature reviews, presentations, or further analysis.
        </p>
    </div>
    """, unsafe_allow_html=True)

    if not papers:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-state-icon">📥</div>
            <div class="empty-state-title">Nothing to export yet</div>
            <div class="empty-state-desc">Extract papers first to enable exports.</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("← Upload Papers"):
            st.session_state["page"] = "upload"
            st.rerun()
        return

    st.markdown(f"**{len(papers)} paper(s)** ready for export.")
    st.markdown("---")

    # ── Paper Extraction Exports ───────────────────────────────────
    st.markdown("### 📊 Paper Extraction Data")
    st.markdown("Export the structured empirical summary table.")

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown("""
        <div class="export-card">
            <span class="export-icon">📋</span>
            <div class="export-name">CSV</div>
            <div class="export-desc">Universal spreadsheet format</div>
        </div>
        """, unsafe_allow_html=True)
        try:
            csv_bytes = papers_to_csv(papers)
            st.download_button(
                "Download CSV",
                data=csv_bytes,
                file_name="empiricx_results.csv",
                mime="text/csv",
                use_container_width=True,
                key="dl_csv"
            )
        except Exception as e:
            st.error(f"CSV error: {e}")

    with c2:
        st.markdown("""
        <div class="export-card">
            <span class="export-icon">📗</span>
            <div class="export-name">Excel</div>
            <div class="export-desc">Formatted .xlsx with styling</div>
        </div>
        """, unsafe_allow_html=True)
        try:
            excel_bytes = papers_to_excel(papers)
            st.download_button(
                "Download Excel",
                data=excel_bytes,
                file_name="empiricx_results.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                key="dl_excel"
            )
        except Exception as e:
            st.error(f"Excel error: {e}")

    with c3:
        st.markdown("""
        <div class="export-card">
            <span class="export-icon">📝</span>
            <div class="export-name">LaTeX</div>
            <div class="export-desc">Ready-to-compile longtable</div>
        </div>
        """, unsafe_allow_html=True)
        try:
            latex_str = papers_to_latex(papers)
            st.download_button(
                "Download LaTeX",
                data=latex_str.encode("utf-8"),
                file_name="empiricx_table.tex",
                mime="text/plain",
                use_container_width=True,
                key="dl_latex"
            )
        except Exception as e:
            st.error(f"LaTeX error: {e}")

    with c4:
        st.markdown("""
        <div class="export-card">
            <span class="export-icon">🔧</span>
            <div class="export-name">JSON</div>
            <div class="export-desc">Raw structured data</div>
        </div>
        """, unsafe_allow_html=True)
        try:
            json_str = papers_to_json(papers)
            st.download_button(
                "Download JSON",
                data=json_str.encode("utf-8"),
                file_name="empiricx_results.json",
                mime="application/json",
                use_container_width=True,
                key="dl_json"
            )
        except Exception as e:
            st.error(f"JSON error: {e}")

    # ── Synthesis Export ───────────────────────────────────────────
    if synthesis:
        st.markdown("---")
        st.markdown("### 🔗 Synthesis Report")
        st.markdown("Export the cross-paper synthesis intelligence.")

        col1, col2 = st.columns(2)

        with col1:
            synthesis_json = json.dumps(synthesis, indent=2, ensure_ascii=False)
            st.download_button(
                "📥  Download Synthesis JSON",
                data=synthesis_json.encode("utf-8"),
                file_name="empiricx_synthesis.json",
                mime="application/json",
                use_container_width=True,
                key="dl_synth_json"
            )

        with col2:
            synthesis_md = _synthesis_to_markdown(synthesis)
            st.download_button(
                "📄  Download Synthesis Markdown",
                data=synthesis_md.encode("utf-8"),
                file_name="empiricx_synthesis.md",
                mime="text/markdown",
                use_container_width=True,
                key="dl_synth_md"
            )

    # ── LaTeX Preview ──────────────────────────────────────────────
    st.markdown("---")
    with st.expander("👁  Preview LaTeX Table"):
        try:
            latex_preview = papers_to_latex(papers)
            st.code(latex_preview, language="latex")
        except Exception as e:
            st.error(f"Preview error: {e}")


def _synthesis_to_markdown(s: dict) -> str:
    lines = ["# EmpiricX — Cross-Paper Synthesis Report\n"]

    if s.get("overall_summary"):
        lines.append(f"## Overview\n\n{s['overall_summary']}\n")

    sections = [
        ("common_findings", "Common Findings"),
        ("conflicting_results", "Conflicting Results"),
        ("methodology_patterns", "Methodology Patterns"),
        ("research_gaps", "Research Gaps"),
        ("common_weaknesses", "Common Weaknesses"),
        ("future_directions", "Future Research Directions"),
        ("underexplored_variables", "Underexplored Variables"),
    ]

    for key, title in sections:
        items = s.get(key, [])
        if items:
            lines.append(f"## {title}\n")
            for item in items:
                lines.append(f"- {item}")
            lines.append("")

    if s.get("dominant_methodology"):
        lines.append(f"## Dominant Methodology\n\n{s['dominant_methodology']}\n")

    return "\n".join(lines)

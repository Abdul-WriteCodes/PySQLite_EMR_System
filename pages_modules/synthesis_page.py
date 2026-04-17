import streamlit as st
from core.extractor import synthesize_papers


def render():
    papers = st.session_state.get("extracted_papers", [])
    synthesis = st.session_state.get("synthesis_result")

    st.markdown("""
    <div class="page-header">
        <div class="page-eyebrow">Step 03 · Synthesize</div>
        <h1 class="page-title">Cross-Paper <em>Intelligence</em></h1>
        <p class="page-subtitle">
            EmpiricX synthesizes patterns, conflicts, and gaps across your entire paper set — 
            the insight layer that transforms a literature review from tedious to strategic.
        </p>
    </div>
    """, unsafe_allow_html=True)

    if not papers:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-state-icon">🔗</div>
            <div class="empty-state-title">No papers to synthesize</div>
            <div class="empty-state-desc">Upload and extract at least 2 papers to run synthesis.</div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("← Upload Papers"):
            st.session_state["page"] = "upload"
            st.rerun()
        return

    if len(papers) < 2:
        st.info("Upload at least 2 papers for meaningful cross-paper synthesis.")
        return

    # ── Run / Re-run ──────────────────────────────────────────────
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"**{len(papers)} papers** loaded and ready for synthesis.")
    with col2:
        run_btn = st.button(
            "🔗  Run Synthesis" if not synthesis else "🔄  Re-run",
            type="primary",
            use_container_width=True
        )

    if run_btn:
        with st.spinner("🧠 Synthesizing across papers… this may take 15–30 seconds"):
            try:
                result = synthesize_papers(papers)
                st.session_state["synthesis_result"] = result
                synthesis = result
                st.success("Synthesis complete!")
            except Exception as e:
                st.error(f"Synthesis failed: {e}")
                return

    if not synthesis:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-state-icon">⚡</div>
            <div class="empty-state-title">Ready to synthesize</div>
            <div class="empty-state-desc">Click "Run Synthesis" to generate cross-paper intelligence.</div>
        </div>
        """, unsafe_allow_html=True)
        return

    # ── Render Synthesis ──────────────────────────────────────────
    _render_synthesis(synthesis)


def _render_synthesis(s: dict):
    # Overall summary
    if s.get("overall_summary"):
        st.markdown(f"""
        <div class="x-card x-card-accent" style="margin-bottom: 1.5rem;">
            <div class="page-eyebrow">Overall Summary</div>
            <div style="font-size: 0.95rem; color: var(--text-secondary); line-height: 1.7;">
                {s['overall_summary']}
            </div>
        </div>
        """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        # Common Findings
        _synth_block(
            "📈 Common Findings",
            s.get("common_findings", []),
            dot_class="synth-dot"
        )
        # Conflicting Results
        _synth_block(
            "⚡ Conflicting Results",
            s.get("conflicting_results", []),
            dot_class="synth-dot synth-dot-red"
        )
        # Methodology Patterns
        _synth_block(
            "⚙️ Methodology Patterns",
            s.get("methodology_patterns", []),
            dot_class="synth-dot"
        )

    with col2:
        # Research Gaps
        _synth_block(
            "🔭 Research Gaps Identified",
            s.get("research_gaps", []),
            dot_class="synth-dot synth-dot-gold"
        )
        # Common Weaknesses
        _synth_block(
            "⚠️ Common Weaknesses",
            s.get("common_weaknesses", []),
            dot_class="synth-dot synth-dot-red"
        )
        # Future Directions
        _synth_block(
            "🚀 Future Research Directions",
            s.get("future_directions", []),
            dot_class="synth-dot synth-dot-green"
        )

    # Underexplored Variables — tag cloud style
    unexplored = s.get("underexplored_variables", [])
    if unexplored:
        tags_html = "".join(f'<span class="gap-tag">{v}</span>' for v in unexplored)
        st.markdown(f"""
        <div class="synth-block" style="margin-top: 0.5rem;">
            <div class="synth-block-title">
                <span class="synth-block-icon">🔮</span>
                Underexplored Variables
            </div>
            <div style="margin-top: 8px;">{tags_html}</div>
        </div>
        """, unsafe_allow_html=True)

    # Dominant methodology
    dom = s.get("dominant_methodology", "")
    if dom:
        st.markdown(f"""
        <div class="x-card" style="margin-top: 0.5rem; display: flex; align-items: center; gap: 16px;">
            <div style="font-size: 2rem;">⚙️</div>
            <div>
                <div style="font-family: var(--font-mono); font-size: 0.65rem; letter-spacing: 2px;
                            text-transform: uppercase; color: var(--text-muted);">Dominant Methodology</div>
                <div style="font-family: var(--font-display); font-size: 1.1rem; color: var(--accent); margin-top: 4px;">
                    {dom}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    if st.button("📥  Export All →", type="primary"):
        st.session_state["page"] = "export"
        st.rerun()


def _synth_block(title: str, items: list, dot_class: str = "synth-dot"):
    if not items:
        return

    items_html = ""
    for item in items:
        items_html += f"""
        <div class="synth-item">
            <div class="{dot_class}"></div>
            <div>{item}</div>
        </div>
        """

    st.markdown(f"""
    <div class="synth-block">
        <div class="synth-block-title">{title}</div>
        {items_html}
    </div>
    """, unsafe_allow_html=True)

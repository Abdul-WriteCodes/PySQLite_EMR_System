"""
Upload logic — extraction is triggered from the sidebar Extract button.
Styled SaaS processing UI version.
"""
import streamlit as st
import time
from utils.parser import extract_text, smart_truncate
from core.extractor import extract_paper


# -------------------------------
# 🎨 GLOBAL STYLES (LOAD ONCE)
# -------------------------------
def load_styles():
    st.markdown("""
    <style>
    .proc-card {
        background: #0f172a;
        border: 1px solid #1e293b;
        border-radius: 12px;
        padding: 14px 16px;
        margin-bottom: 10px;
        color: #e2e8f0;
        display: flex;
        align-items: center;
        gap: 12px;
        transition: all 0.3s ease;
    }

    .proc-card.processing { border-left: 4px solid #3b82f6; }
    .proc-card.success    { border-left: 4px solid #22c55e; }
    .proc-card.error      { border-left: 4px solid #ef4444; }

    .proc-title {
        font-weight: 600;
        font-size: 14px;
    }

    .proc-sub {
        font-size: 12px;
        color: #94a3b8;
    }

    .spinner {
        width: 14px;
        height: 14px;
        border: 2px solid #334155;
        border-top: 2px solid #3b82f6;
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }

    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    </style>
    """, unsafe_allow_html=True)


# -------------------------------
# 🚀 MAIN FUNCTION
# -------------------------------
def run_extraction_from_queue():
    load_styles()

    queued = st.session_state.get("queued_files", [])
    extracted = st.session_state.get("extracted_papers", [])
    extracted_names = {p.get("_source_file") for p in extracted}

    pending = [f for f in queued if f["name"] not in extracted_names]
    if not pending:
        return

    total = len(pending)

    # Top UI
    status = st.empty()
    progress = st.progress(0.0)
    log_box = st.container()

    errors = []

    status.info(f"🚀 Processing {total} paper(s)...")

    # -------------------------------
    # 🔁 PROCESS LOOP
    # -------------------------------
    for i, finfo in enumerate(pending):
        fname = finfo["name"]
        fobj = finfo.get("obj")

        # Create UI slot for this file
        file_slot = log_box.empty()

        start_time = time.time()

        # 🔵 STEP 1: Parsing
        file_slot.markdown(f"""
        <div class="proc-card processing">
            <div class="spinner"></div>
            <div>
                <div class="proc-title">{fname}</div>
                <div class="proc-sub">Parsing document...</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        try:
            raw_bytes = fobj.read() if fobj else b""
            if not raw_bytes:
                raise ValueError("File is empty or could not be read.")

            text = extract_text(raw_bytes, fname)

            if len(text.strip()) < 150:
                raise ValueError("Too little text extracted — file may be image-based.")

            text = smart_truncate(text, max_tokens=12000)

            # 🧠 STEP 2: Extraction
            file_slot.markdown(f"""
            <div class="proc-card processing">
                <div class="spinner"></div>
                <div>
                    <div class="proc-title">{fname}</div>
                    <div class="proc-sub">Extracting empirical insights...</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            result = extract_paper(text, filename=fname)
            extracted.append(result)

            duration = round(time.time() - start_time, 2)

            # ✅ STEP 3: Success
            file_slot.markdown(f"""
            <div class="proc-card success">
                <div>✔</div>
                <div>
                    <div class="proc-title">{fname}</div>
                    <div class="proc-sub">Completed in {duration}s</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        except Exception as e:
            errors.append(f"**{fname}**: {e}")

            # ❌ ERROR STATE
            file_slot.markdown(f"""
            <div class="proc-card error">
                <div>⚠</div>
                <div>
                    <div class="proc-title">{fname}</div>
                    <div class="proc-sub">{e}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # 📊 Progress update
        progress.progress((i + 1) / total)

    # -------------------------------
    # 🧾 FINAL STATE
    # -------------------------------
    st.session_state["extracted_papers"] = extracted
    st.session_state["synthesis_result"] = None
    st.session_state["processing_errors"] = errors

    progress.empty()

    if extracted:
        status.success(f"✅ {len(extracted)} paper(s) extracted and ready.")

    if errors:
        for e in errors:
            st.warning(e)
# 🔬 Systematic Literature Review Analyser

An AI-powered Streamlit app that automates data abstraction and thematic synthesis across a corpus of academic papers.

## Features

- **Bulk upload** — PDF, DOCX, and TXT papers
- **AI data abstraction** — extracts authors, year, methodology, findings, contributions, limitations, keywords per paper
- **Theme identification** — Claude identifies 4–7 cross-cutting themes across the entire corpus
- **Synthesis narrative** — generates a formal academic synthesis section
- **Export** — downloads a `.zip` with JSON, CSV, and two Markdown reports

## Local Setup

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open http://localhost:8501 and enter your Anthropic API key in the sidebar.

## Streamlit Cloud Deployment

1. Push this folder to a GitHub repo
2. Go to https://share.streamlit.io → New app
3. Select your repo and set **Main file path** to `app.py`
4. (Optional) Add `ANTHROPIC_API_KEY` as a secret in **Advanced settings** — if set, the sidebar key field will auto-fill

### Using Streamlit Secrets (recommended for production)

Add to your app's **Secrets** in Streamlit Cloud:

```toml
ANTHROPIC_API_KEY = "sk-ant-..."
```

Then in `app.py` you can auto-load it by replacing the sidebar input with:

```python
import os
st.session_state.api_key = os.environ.get("ANTHROPIC_API_KEY", "")
```

## File Structure

```
slr_analyser/
├── app.py            # Main Streamlit application
├── requirements.txt  # Python dependencies
└── README.md         # This file
```

## Export Package Contents

| File | Description |
|------|-------------|
| `abstractions.json` | Full structured data for every paper |
| `abstractions_summary.csv` | Spreadsheet-friendly flat table |
| `themes.md` | Thematic analysis with citations to papers |
| `synthesis_report.md` | Formal academic synthesis narrative |

# EmpiricX — Research Intelligence Engine

> Transform academic papers into structured empirical intelligence — helping researchers analyze, compare, and identify gaps in minutes instead of weeks.

## What It Does

EmpiricX is an AI-powered empirical research analysis tool that:

1. **Ingests** PDF, DOCX, and TXT research papers
2. **Extracts** structured empirical data using GPT-4o:
   - Author & Year, Research Context, Methodology
   - Independent/Dependent/Control Variables
   - Key Findings, Contributions, Strengths, Limitations
   - APA / MLA / Harvard citations
3. **Synthesizes** cross-paper intelligence:
   - Common Findings & Conflicting Results
   - Research Gaps & Underexplored Variables
   - Methodology Patterns & Future Directions
4. **Exports** in CSV, Excel (.xlsx), LaTeX longtable, and JSON

## Deployment on Streamlit Cloud

1. Push this repository to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repo — set **main file** to `app.py`
4. Add your OpenAI API key as a secret:
   - In Streamlit Cloud → App Settings → Secrets
   - Add: `OPENAI_API_KEY = "sk-..."`
   - Or enter it directly in the sidebar at runtime

## Local Development

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Stack

- **Frontend**: Streamlit + Custom CSS (dark academic aesthetic)
- **AI**: OpenAI GPT-4o (temperature 0.1 for extraction, 0.2 for synthesis)
- **PDF Parsing**: PyMuPDF (fitz)
- **DOCX Parsing**: python-docx
- **Exports**: openpyxl (Excel), custom LaTeX generator
- **Session State**: Streamlit native

## Project Structure

```
empiricx/
├── app.py                    # Main entry point
├── requirements.txt
├── .streamlit/config.toml    # Theme & server config
├── assets/
│   └── style.css             # Custom dark theme
├── core/
│   ├── extractor.py          # GPT-4o extraction + synthesis engine
│   └── exporter.py           # CSV / Excel / LaTeX / JSON exporters
├── utils/
│   ├── parser.py             # PDF / DOCX text extraction
│   └── session.py            # Session state management
└── pages_modules/
    ├── upload_page.py         # File upload + processing
    ├── results_page.py        # Extraction table + detail view
    ├── synthesis_page.py      # Cross-paper synthesis
    └── export_page.py         # Download exports
```

## Notes on Hallucination Prevention

- GPT-4o is instructed to use `"Not specified"` for any field it cannot determine
- Temperature is kept at 0.1 for extraction
- `response_format: json_object` ensures structured output
- Text is truncated intelligently (prioritizing Abstract, Methods, Results sections)

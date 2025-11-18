This folder contains example configuration to run the local MVP pipeline.

Place a test PDF named `sample.pdf` in this folder and run from the repo root:

```bash
PYTHONPATH=. python -m diligent_ai.cli example/sample.pdf --config .config.yaml
```

Notes:
- The included `.config.yaml` in this folder is an example and contains the API key you provided. For production, store secrets outside the repo and use the top-level `.config.yaml` which is gitignored.
- If you don't have `PyPDF2` installed, the PDF extractor will return a fallback message. Install it with `pip install PyPDF2`.


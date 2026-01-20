# Drive Search Service (Google Drive + Elasticsearch)

This project indexes files stored in Google Drive and provides a search API over the content.

## Features
- Connects to Google Drive via Service Account.
- Extracts text from TXT/CSV/PDF/PNG/JPEG files (OCR supported if `tesseract` is installed).
- Indexes content + metadata into Elasticsearch.
- Exposes a FastAPI `/search` endpoint and a CLI client.

## Prerequisites
- Python 3.10+
- Elasticsearch 8.x running locally or remotely
- Google Cloud project with Drive API enabled + Service account JSON credentials

### Optional (for OCR)
- Tesseract OCR installed and available on PATH

## Setup

1) Create and activate a virtual environment.
2) Install dependencies:

```bash
pip install -r requirements.txt
```

3) Create `.env` from `.env.example` and set:
- `GOOGLE_APPLICATION_CREDENTIALS` and optional `GOOGLE_DRIVE_FOLDER_ID`
- `ES_URL` / `ES_INDEX` for Elasticsearch
   - If Elasticsearch uses HTTPS with self-signed certs, set `ES_URL=https://...` and `ES_VERIFY_CERTS=false`.
   - `GOOGLE_DRIVE_FOLDER_ID` must be the folder ID only (not the full URL).

4) Share the target Drive folder (or specific files) with the service account email.
   If Google Drive indexing fails, confirm the Drive API is enabled and the service account has access.

## Indexing

Set the module path for local execution:

```bash
export PYTHONPATH=src
```

Windows PowerShell:

```powershell
$env:PYTHONPATH = "src"
```

Run the sync script to index Drive content into Elasticsearch:

```bash
python scripts/index_drive.py
```

You can also trigger indexing via the API:

```bash
curl -X POST http://127.0.0.1:8000/sync
```

## Run the API

```bash
uvicorn app.api:app --host 127.0.0.1 --port 8000
```

## Search API

```bash
curl "http://127.0.0.1:8000/search?q=invoice"
```

Example of a not-found search (exact format):

```text
https://<search-service-host>/search?q="notfound-term"
```

Response:

```json
{
  "results": [
    {
      "name": "Invoice-2024.pdf",
      "web_view_link": "https://drive.google.com/..."
    }
  ]
}
```

## CLI Client

```bash
python -m app.cli sync
python -m app.cli search --query "invoice"
```

## Notes
- Deleted files are removed from the index on the next sync.
- Large Drives may need pagination tuning; `DocumentIndexer` currently fetches up to 10k indexed docs to detect stale entries.

## High-level Design Diagram
See `docs/diagram.svg` (image) or `docs/diagram.mmd` (Mermaid source).

## Postman Collection
Import `docs/postman_collection.json` and set the `baseUrl` variable.

## Example Workflow (Matches Assessment)
1) Create files in a Drive folder:
   - `File1.txt`: `a,b,c,d,e`
   - `File2.txt`: `c,d,e`
   - `File3.txt`: `g,h`
2) Set `GOOGLE_DRIVE_FOLDER_ID` to that folder and run sync:
   - `curl -X POST http://127.0.0.1:8000/sync`
3) Search:
   - `curl "http://127.0.0.1:8000/search?q=c"`
   - Expect `File1.txt` and `File2.txt` in results.
4) Delete `File1.txt` in Drive, then re-sync:
   - `curl -X POST http://127.0.0.1:8000/sync`
5) Search again:
   - `curl "http://127.0.0.1:8000/search?q=c"`
   - Expect only `File2.txt` in results.

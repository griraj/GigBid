# Interface redesign — top navigation

## Delivered

- Replaced the left-hand sidebar with a full-width sticky header and horizontally arranged navigation tabs: Overview, Job inbox, Pipeline, Messages, Analytics and Settings.
- Preserved all navigation destinations and the connected API flows; changed layout rather than introducing nonfunctional menu links.
- Placed the marketplace mode, human approval reminder, display-density control and sign-out button in the top bar.
- Added persistent Compact/Comfortable density settings using browser localStorage.
- Made mobile tabs horizontally scrollable so navigation remains accessible on narrow screens.
- Increased the usable width for the job listings, requirement/evidence matrix and proposal studio.
- Fixed `pyproject.toml` package discovery for Windows editable installation.

## Operating the updated UI on Windows

Stop the frontend server (Ctrl+C), replace the existing project folder with the updated release or overwrite the modified files, then run:

```powershell
cd C:\Users\mohit\Downloads\GigBid
python -m pip install -e ".[test]" langgraph-checkpoint-sqlite
python -m uvicorn apps.api.main:app --reload --host 127.0.0.1 --port 8000
```

In a second terminal:

```powershell
cd C:\Users\mohit\Downloads\GigBid\apps\web
npm.cmd install
npm.cmd run dev
```

Open `http://localhost:5173/` and use the configured reviewer token. If a previous Vite tab remains open, refresh the page with Ctrl+Shift+R.

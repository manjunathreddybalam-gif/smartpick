# SmartPick — Product Recommendation Website

A beginner-friendly Flask + SQLite product discovery website.

## Features
- Product search by name, category, description and features
- Category and maximum-price filters
- Sort by price or rating
- Basic recommendations (rating descending, then price)
- Compare up to three products
- Product affiliate/seller links
- Local product manager to add, edit and delete products
- SQLite database created automatically on first run

## Requirements
- Python 3.10 or newer
- Internet connection for initial Flask install and optional remote images/fonts
- VS Code recommended

## Windows 11 setup
Open PowerShell in this project folder and run:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python app.py
```

If PowerShell blocks activation, you can avoid activation and use:
```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

Open http://127.0.0.1:5000 in your browser.
Product manager: http://127.0.0.1:5000/admin

Stop the server with Ctrl+C in the terminal.

## Product data
The first run creates `smartpick.db` and inserts six sample products. Add your own products at `/admin`.
For real affiliate marketing, replace sample URLs with your own approved affiliate links. The sample links point to Amazon India home page and do not represent trackable affiliate links.

## Important security notes
- `/admin` and product write API routes have no authentication in this learning version.
- Run only on your own computer. Do not deploy this exact version publicly.
- Before public deployment, add admin authentication, CSRF protection, input/rate limiting, secure configuration, and production hosting.
- `app.run(debug=True)` is for local development only, not production.
- Prices, ratings, product images and sample data are examples. Verify details before publishing.
- Add a clear affiliate disclosure and follow the current rules of each affiliate program.

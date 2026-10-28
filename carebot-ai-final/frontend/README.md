# Frontend

The original HTML page shell and `css/style.css` are retained. Static design constants are in `js/constants.js`; no mock data is used. Every protected page uses the same-origin API wrapper with cookie authentication and CSRF protection. Additional controls in originally unfinished pages reuse the existing style classes, with small additions in `css/features.css`.

Run the project from its root with `python run.py`, then open http://localhost:5000. Do not use Live Server or open the HTML files through file://. See the root README for complete setup.

# Family Campsite Availability Finder (Japan)

This repository contains a demo Streamlit application that simulates campsite availability
for family-friendly sites in Japan. It is designed to be run locally on a macOS machine and
viewed across devices on the same local network (for example, viewing from Safari on an iPhone).

## Key features

- Search horizon: 30 / 60 / 90 days
- Priority day filters: weekends, Japanese national holidays, individual weekdays
- Accommodation filters: Cabin/Cottage, Tent Site, Glamping/Dome
- Grouped results per campsite with activity highlights and a reservation link
- Deterministic simulated availability engine (MD5 seeds) for reproducible demo results

## Prerequisites

- macOS with Python 3.8+ (system Python or a pyenv/conda environment)
- A device on the same LAN/Wi‑Fi network for remote browsing

## Quickstart (macOS)

1. Make the launcher executable:

```bash
chmod +x run_mac.sh
```

2. Run the launcher. It will create a `venv`, install dependencies from `requirements.txt`,
	 and start Streamlit bound to `0.0.0.0:8501`:

```bash
./run_mac.sh
```

3. The script prints the LAN-accessible URL, for example `http://192.168.1.40:8501` — open that
	 address in Safari on your Mac or in a browser on any device on the same Wi‑Fi (e.g. iPhone).

### Manual run (optional)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

## Developer notes

- The simulated availability logic lives in `app.py` in `simulate_availability()` — it is deterministic
	for testing and demonstration (based on MD5 seeds). Replace with live scraping or API calls
	for production usage.
- `app.py` includes a small link probing routine to find a working reservation URL. If you have a
	canonical reservation URL for a campsite, update the entry in the `CAMPSITES` list.
- Logs for the background Streamlit process (when launched with `run_mac.sh`) are written to
	`/tmp/streamlit_nohup.log`.

## Security

- Do NOT commit credentials, API keys, or other secrets to the repository. This repo's `.gitignore`
	excludes `venv/`, `__pycache__/`, and `.DS_Store` to reduce accidental commits of common files.

## Contributing

- Fork and open a pull request to add real scrapers, tests, CI, or more campsite entries.

## License

- Demo code — adapt and relicense as required for your use.

# Athlete Events Dash App

A standalone Dash project where [athlete_events.py](athlete_events.py) is the entrypoint and the UI is split into components and assets.

## Project Layout

```text
athlete_events_project/
├── athlete_events.csv
├── athlete_events.py
├── components/
│   ├── __init__.py
│   ├── layout.py
│   └── callbacks.py
├── assets/
│   └── styles.css
├── setup.sh
├── requirements.txt
└── README.md
```

## Architecture

- [athlete_events.py](athlete_events.py): loads data, creates Dash app, points to assets folder, and registers callbacks.
- [components/layout.py](components/layout.py): containerized layout for each analysis view.
- [components/callbacks.py](components/callbacks.py): all callbacks bound to component IDs.
- [assets/styles.css](assets/styles.css): static styling auto-loaded by Dash.

## Reproducible Setup

1. One-command setup:

```bash
./setup.sh
```

2. Optional recreation of virtual environment:

```bash
./setup.sh --recreate
```

3. Start the app:

```bash
source .venv/bin/activate
python athlete_events.py
```

## Run With Optional Arguments

```bash
python athlete_events.py --csv athlete_events.csv --title "Athlete Events Dashboard" --port 8050
```

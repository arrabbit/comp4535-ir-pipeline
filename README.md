# COMP 4535 Group Project – Automated Incident Report Pipeline

A tool that reads the logs from an attacked web app and automatically generates an incident report showing what happened, when, and what data may have been exposed.

COMP 4535 (Computer Security), Mount Royal University, Fall 2026.

**Note:** `stage1-container` is an intentionally vulnerable app. Only run it locally.

## Team

| Member | Stage |
|---|---|
| Anna Running Rabbit | 1 – Attack simulation and dataset |
| Paul Novencido | 2 – Log aggregator (C) |
| Austin Vande Cappelle | 3 – Detection (rules + local LLM) |
| Mihika Paliwal | 4 – Incident report and evaluation |

## Project structure

```
stage1-container/    Docker setup, vulnerable Flask app, attack notes
stage2-aggregator/   C log aggregator and tests
stage3-detector/     Rule engine and LLM classifier
stage4-report/       Report generator and evaluation script
data/                Logs, ground truth, events, detections
docs/                Project plan, report, slides
run_pipeline.sh      Runs all four stages
```

Each stage folder has its own README with instructions for that stage.

## Requirements

- Docker Desktop
- Python 3
- gcc or clang
- Burp Suite Community Edition
- Ollama

## Running it

```bash
git clone https://github.com/arrabbit/comp4535-ir-pipeline.git
cd comp4535-ir-pipeline
./run_pipeline.sh
```

On Windows, run the script from Git Bash or WSL.

## Data files

- `ground_truth.csv`: one row per attack or normal session (what actually happened)
- `events.jsonl`: parsed log events from the aggregator
- `detections.jsonl`: events labelled by the detector

All timestamps are in UTC.

## References

- OWASP WebGoat (source of attack payloads)
- Palma, G., Cecchi, G., Caronna, M., & Rizzo, A. (2025). Leveraging Large Language Models for Scalable and Explainable Cybersecurity Log Analysis. *Journal of Cybersecurity and Privacy*, 5(3), 55. https://doi.org/10.3390/jcp5030055
# Replication Package — How Architectural Views Should Be: Simple, Informal, and Automated


This repository is a replication package for the following publication, submitted to the [IEEE Transactions on Software Engineering](https://ieeexplore.ieee.org/xpl/RecentIssue.jsp?punumber=32):
> Leonardo Scommegna, Roberto Verdecchia, Ivano Malavolta, Patricia Lago and Enrico Vicario. 2026. How Architectural Views Should Be: Simple, Informal, and Automated

In particular, it contains the survey instrument, the (anonymized) raw and coded responses, the analysis code that produces every figure in the paper, and the scripts used to recruit and contact participants.

## Structure

```
replicationPackage/
├── README.md                                   # this file
├── survey-structure-googleForm.pdf             # the survey instrument
│
├── coding/                                      # raw & coded survey responses 
│   ├── ... - Original results.csv               # raw survey export
│   ├── ... - Coding.csv                         # consolidated coding used for analysis
│   ├── ... - Second coding.csv                  # independent second coding (inter-rater)
│   ├── ... - Tool Classification.csv            # tool classification coding
│   ├── ... - Tool Classification - second.csv   # second tool classification coding
│   └── ... - tool-classification-occurrence.csv # tool classification weighted by occurrence
│
├── data-processing/                             # analysis + figure generation (self-contained)
│   ├── README.md                                # detailed instructions (venv, requirements, run)
│   ├── requirements.txt
│   ├── data/                                    # working copies of the CSVs the scripts read
│   ├── generate_all.py                          # entrypoint: regenerates every figure
│   ├── *.py                                      # one module per figure family
│   └── plot/                                     # OUTPUT — generated figures (PDF) + reports
│
├── recruiting/                                  # how candidate participants were collected
│   ├── ECSA24-dataset.csv                        # GitHub repositories studied (repo metadata only)
│   ├── api-scraper.py                            # scrapes recent contributors via the GitHub API
│   └── address-validator.py                      # filters / validates the collected e-mail addresses
│
└── survey-dissemination/                        # how the survey was sent out
    └── mail-sender.py                            # sends the survey invitation e-mail (SMTP)
```

> **Note on `recruiting/` and `survey-dissemination/`.** These scripts are
> provided for transparency about how participants were reached. Secrets and
> personally identifying information have been removed and replaced with the
> placeholder `ANONYMIZED` (GitHub API token, SMTP host, credentials path,
> survey link). They are **not** runnable as-is and are not needed to reproduce
> the results. The analysis in `data-processing/` is fully self-contained.
> The exact text of the recruitment e-mail sent to candidate participants is
> included in [`survey-dissemination/mail-sender.py`](survey-dissemination/mail-sender.py)
> (the message body, with the survey link).

## Reproducing the plots (`data-processing/`)

All figures are produced from the data in `data-processing/data/` by a single
command. From the `data-processing/` folder, using a Python 3.10+ environment:

```bash
cd data-processing

# create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate          # Linux / macOS  (Windows: .venv\Scripts\activate)

# install dependencies and generate every figure
pip install -r requirements.txt
python generate_all.py
```

The figures (PDF) and the inter-rater agreement report appear in
`data-processing/plot/`. Each figure family can also be generated on its own
(e.g. `python bar_charts.py`, `python likert_charts.py`).

See [`data-processing/README.md`](data-processing/README.md) for the full list
of outputs and additional details.

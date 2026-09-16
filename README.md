# Replication Package — How Architectural Views Should Be: Simple, Informal, and Automated


This repository is a replication package for the following publication, submitted to the [IEEE Transactions on Software Engineering](https://ieeexplore.ieee.org/xpl/RecentIssue.jsp?punumber=32):
> Leonardo Scommegna, Roberto Verdecchia, Ivano Malavolta, Patricia Lago and Enrico Vicario. 2026. How Architectural Views Should Be: Simple, Informal, and Automated

In particular, it contains the survey instrument, the (anonymized) raw and coded responses together with the codebook of the qualitative coding, the analysis code that produces every figure and the inter-rater agreement report in the paper, and the scripts used to recruit and contact participants.


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
│   ├── codebook.csv                             # one row per code (question, code,
│   │                                            #   definition, type, frequency)
│   ├── coding_summary.md                        # macro-categories of the open-ended
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

## Qualitative coding (`coding/`)

Free-text answers were analyzed via manual coding with a twofold purpose: (i) mapping the free-text ("other") answers of the nine semi-closed questions (Q5, Q13, Q14, Q17, Q20, Q21, Q22, Q23, Q31) onto the closed-ended option they refer to, or onto a new category not anticipated by the questionnaire (e.g., `Academic/Researcher` for Q5, `Diagram as code` and `VCS friendly` for Q21, `Stakeholders` for Q23); (ii) identifying the themes emerging from the four open-ended questions (Q19, Q30, Q32, Q33).

**Procedure.** Two researchers coded the same answers independently in a shared spreadsheet, following open coding (fine-grained codes extracted from the raw answers) and axial coding (grouping of codes into macro-categories). Coding is multi-label: an answer containing several concepts receives several codes, separated by commas. Disagreements were resolved by discussion; the reconciled result is `... - Coding.csv`, the independent second coding is `... - Second coding.csv`. The 17 respondents who failed the screening question (Q1) are kept in the sheets but excluded from all analyses.

**Outcome.** 490 free-text answers to 13 questions were coded. For each `[CODED]` column, `codebook.csv` lists every code with its definition, type (predefined option vs. emergent category), and frequency over the 411 valid respondents; `coding_summary.md` reports the macro-categories of the open-ended questions (e.g., Q32: AI/LLM-centered 47, automation 18, code–view coupling 15, no change 7, ...). The coding aimed at descriptive synthesis: axial categories group codes hierarchically and do not encode causal relationships.

**Agreement.** Inter-rater reliability (Krippendorff's alpha per code, one-vs-rest, macro-averaged per question) is computed by the analysis pipeline and written to `data-processing/plot/` (see below).



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

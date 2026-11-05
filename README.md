# The Pre-FOMC Announcement Drift: A Replication

This repo replicates portions of Lucca and Moench (2015), "The Pre-FOMC Announcement Drift," and extends the main result through 2026.

Lucca and Moench document large average excess returns on U.S. equities in the twenty-four hours before scheduled FOMC announcements, before anyone can know what the committee decided. The effect is big enough to account for a substantial share of the equity premium since 1994, it is not explained by the policy surprise itself, and it does not appear before other macroeconomic releases.

The daily half of the replication needs only a calendar and CRSP. The intraday half is harder: the paper's headline window is a 2pm-to-2pm return that spans the overnight session, so it requires an instrument that trades overnight.

**Citation:** Lucca, David O., and Emanuel Moench. "The Pre-FOMC Announcement Drift." *The Journal of Finance* 70, no. 1 (2015): 329-371. <https://doi.org/10.1111/jofi.12196>

**Paper PDF:** [`references/LuccaMoench2015PreFOMCAnnouncementDrift.pdf`](references/LuccaMoench2015PreFOMCAnnouncementDrift.pdf) (New York Fed Staff Report 512)

## Status

Replication work has not started. The repo currently holds a project template: `dodo.py` still defines tasks from earlier coursework, and the `reports/` files are template examples.

## Tasks

- [ ] **Data cleaning.** Assemble the FOMC calendar and the return panel: scheduled and unscheduled meeting dates, daily S&P 500 excess returns, and the 2pm-to-2pm intraday windows. Reproduce Table 1 (summary statistics).
- [ ] **Main daily results.** Replicate Table 2 (the pre-FOMC dummy in daily S&P 500 returns, with the paper's standard errors) and Table 4 (alternative samples).
- [ ] **Around the announcement.** Replicate Figure 1 (cumulative returns around the announcement) and Table 5 (returns before, at, and after the FOMC news).
- [ ] **Other assets and placebo.** Replicate Table 8 (fixed income instruments), Table 6 (international indices), and Table 7 (other economic news, the placebo that makes the result interesting).
- [ ] **Out of sample.** Replicate Table 12 (out-of-sample analysis).
- [ ] **Update through 2026.** The drift is widely claimed to have weakened after publication. Settle the question on our own data and say so plainly either way.

## Data Sources

| Data | Source | Used for |
| --- | --- | --- |
| Daily returns | CRSP and Ken French's data library | Daily S&P 500 excess returns |
| FOMC calendar | Federal Reserve Board website | Scheduled and unscheduled meeting dates |
| E-mini S&P 500 futures | Databento `GLBX.MDP3` | Intraday windows from June 2010 |
| SPY | Daily TAQ | Intraday windows from 2003 |
| Fed funds futures | Machinery built in HW 2 (reuse rather than rebuild) | Kuttner policy surprise |

## Known Limitations

The paper's intraday data come from Thomson Reuters TickHistory and Tickdata.com, and we have neither. The E-mini and TAQ substitutes cover 2003 onward. The 1994-2002 intraday evidence is out of reach, and we report it as such rather than approximating it.

## Project Conventions

### Directory structure

- `src/`: source code. `src/settings.py` loads paths and other settings, and other scripts should get them by importing `config` from it.
- `references/`: the paper.
- `reports/`: LaTeX sources for reports and slides.
- `_data/`: pulled data. Not tracked by Git, and safe to delete because the code can pull it again.
- `_output/`: generated tables, figures, and dataframes. Not tracked by Git, and safe to delete because the code can regenerate it.
- `data_manual/`: data that can't be recreated automatically. Tracked by Git, and created when first needed.

### Environment variables

Private paths and credentials go in a `.env` file, which Git ignores. `.env.example` shows the expected format. To export the variables to a Linux or Mac shell:

```bash
set -a  # automatically export all variables
source .env
set +a
```

### Task runner

The pipeline will run through [`doit`](https://pydoit.org/), with tasks defined in `dodo.py`. Run `doit` from the repo root.

### Naming

Files or functions that pull data from an external source start with `pull_`, as in `pull_fred.py`. Functions that load data already cached in `_data/` start with `load_`.

### Formatting

This project uses [Ruff](https://docs.astral.sh/ruff/) for linting and formatting:

```bash
ruff format . && ruff check --select I --fix . && ruff check --fix .
```

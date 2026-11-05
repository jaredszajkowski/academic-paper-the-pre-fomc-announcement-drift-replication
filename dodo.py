import sys
from os import environ
from pathlib import Path

sys.path.insert(1, "./src/")

import shutil

from settings import config

DATA_DIR = Path(config("DATA_DIR"))
OUTPUT_DIR = Path(config("OUTPUT_DIR"))

OS_TYPE = config("OS_TYPE")

## Helpers for handling Jupyter Notebook tasks
# fmt: off
## Helper functions for automatic execution of Jupyter notebooks
environ["PYDEVD_DISABLE_FILE_VALIDATION"] = "1"
def jupyter_execute_notebook(notebook):
    return f"jupyter nbconvert --execute --to notebook --ClearMetadataPreprocessor.enabled=True --log-level WARN --inplace ./src/{notebook}.ipynb"
def jupyter_to_html(notebook, output_dir=OUTPUT_DIR):
    return f"jupyter nbconvert --to html --log-level WARN --output-dir={output_dir} ./src/{notebook}.ipynb"
def jupyter_to_md(notebook, output_dir=OUTPUT_DIR):
    """Requires jupytext"""
    return f"jupytext --to markdown --log-level WARN --output-dir={output_dir} ./src/{notebook}.ipynb"
def jupyter_to_python(notebook, build_dir):
    """Convert a notebook to a python script"""
    return f"jupyter nbconvert --log-level WARN --to python ./src/{notebook}.ipynb --output _{notebook}.py --output-dir {build_dir}"
def jupyter_clear_output(notebook):
    return f"jupyter nbconvert --log-level WARN --ClearOutputPreprocessor.enabled=True --ClearMetadataPreprocessor.enabled=True --inplace ./src/{notebook}.ipynb"
# fmt: on


def copy_file(origin_path, destination_path, mkdir=True):
    """Create a Python action for copying a file."""

    def _copy_file():
        origin = Path(origin_path)
        dest = Path(destination_path)
        if mkdir:
            dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(origin, dest)

    return _copy_file


##################################
## Begin rest of PyDoit tasks here
##################################


def task_config():
    """Create empty directories for data and output if they don't exist"""
    return {
        "actions": ["python ./src/settings.py"],
        "targets": [DATA_DIR, OUTPUT_DIR],
        "file_dep": ["./src/settings.py"],
    }


def task_pull_fomc_dates():
    """Parse scheduled FOMC meeting dates from the Internet Appendix PDF"""
    return {
        "actions": [
            "python src/settings.py",
            "python src/pull_fomc_dates.py",
        ],
        "targets": [DATA_DIR / "fomc_dates.parquet"],
        "file_dep": [
            "./src/settings.py",
            "./src/pull_fomc_dates.py",
            "./references/ThePreFOMCAnnouncementDriftInternetAppendix_Lucca_Moench_2015.pdf",
        ],
    }


def task_pull_CRSP_index():
    """Pull daily S&P 500 index returns from CRSP on WRDS"""
    return {
        "actions": [
            "python src/settings.py",
            "python src/pull_CRSP_index.py",
        ],
        "targets": [DATA_DIR / "CRSP_DSP500.parquet"],
        "file_dep": [
            "./src/settings.py",
            "./src/pull_CRSP_index.py",
        ],
        "verbosity": 2,  # Print everything immediately. This is important in
        # case WRDS asks for credentials.
    }


def task_pull_ken_french():
    """Pull the daily risk-free rate from Ken French's data library"""
    return {
        "actions": [
            "python src/settings.py",
            "python src/pull_ken_french.py",
        ],
        "targets": [DATA_DIR / "ken_french_rf.parquet"],
        "file_dep": [
            "./src/settings.py",
            "./src/pull_ken_french.py",
        ],
    }


def task_test_pulled_data():
    """Test the saved data files, rerunning when a file or its test changes"""
    tests = {
        "test_pull_CRSP_index": "CRSP_DSP500.parquet",
        "test_pull_ken_french": "ken_french_rf.parquet",
    }
    for test, data_file in tests.items():
        yield {
            "name": test,
            "actions": [f"python -m pytest src/{test}.py"],
            "file_dep": [f"./src/{test}.py", DATA_DIR / data_file],
            "verbosity": 2,
        }


def task_pull_CRSP_stock():
    """Pull CRSP data from WRDS and save to disk"""

    return {
        "actions": [
            "python src/settings.py",
            "python src/pull_CRSP_stock.py",
        ],
        "targets": [
            Path(DATA_DIR) / file
            for file in [
                ## src/pull_CRSP_stock.py
                "CRSP_MSF_INDEX_INPUTS.parquet",
                "CRSP_MSIX.parquet",
            ]
        ],
        "file_dep": [
            "./src/settings.py",
            "./src/pull_CRSP_stock.py",
        ],
        "verbosity": 2,  # Print everything immediately. This is important in
        # case WRDS asks for credentials.
    }


def task_pull_SP500_constituents():
    """Pull SP500 constituents from WRDS and save to disk"""
    return {
        "actions": [
            "python src/settings.py",
            "python src/pull_SP500_constituents.py",
        ],
        "targets": [DATA_DIR / "df_sp500_constituents.parquet"],
        "file_dep": [
            "./src/settings.py",
            "./src/pull_SP500_constituents.py",
        ],
        "verbosity": 2,  # Print everything immediately. This is important in
        # case WRDS asks for credentials.
    }


def task_calc_SP500_index_approximations():
    """Calculate SP500 index approximations"""
    return {
        "actions": ["python src/calc_SP500_index.py"],
        "targets": [DATA_DIR / "sp500_index_approximations.parquet"],
        "file_dep": ["./src/calc_SP500_index.py"],
    }


notebook_tasks = {
    "01_wrds_python_package.ipynb": {
        "file_dep": [],
        "targets": [],
    },
    "02_CRSP_market_index.ipynb": {
        "file_dep": [],
        "targets": [],
    },
    "03_SP500_constituents_and_index.ipynb": {
        "file_dep": [
            "./src/pull_SP500_constituents.py",
            "./src/pull_CRSP_stock.py",
            "./src/calc_SP500_index.py",
        ],
        "targets": [],
    },
    "05_basics_of_SQL.ipynb": {
        "file_dep": [],
        "targets": [],
    },
}


def task_convert_notebooks_to_scripts():
    """Convert notebooks to script form to detect changes to source code rather
    than to the notebook's metadata.
    """
    build_dir = Path(OUTPUT_DIR)

    for notebook in notebook_tasks.keys():
        notebook_name = notebook.split(".")[0]
        yield {
            "name": notebook,
            "actions": [
                jupyter_clear_output(notebook_name),
                jupyter_to_python(notebook_name, build_dir),
            ],
            "file_dep": [Path("./src") / notebook],
            "targets": [OUTPUT_DIR / f"_{notebook_name}.py"],
            "clean": True,
            "verbosity": 0,
        }


# fmt: off
def task_run_notebooks():
    """Preps the notebooks for presentation format.
    Execute notebooks if the script version of it has been changed.
    """
    for notebook in notebook_tasks.keys():
        notebook_name = notebook.split(".")[0]
        yield {
            "name": notebook,
            "actions": [
                """python -c "import sys; from datetime import datetime; print(f'Start """ + notebook + """: {datetime.now()}', file=sys.stderr)" """,
                jupyter_execute_notebook(notebook_name),
                jupyter_to_html(notebook_name),
                copy_file(
                    Path("./src") / f"{notebook_name}.ipynb",
                    OUTPUT_DIR / f"{notebook_name}.ipynb",
                    mkdir=True,
                ),
                jupyter_clear_output(notebook_name),
                """python -c "import sys; from datetime import datetime; print(f'End """ + notebook + """: {datetime.now()}', file=sys.stderr)" """,
            ],
            "file_dep": [
                OUTPUT_DIR / f"_{notebook_name}.py",
                *notebook_tasks[notebook]["file_dep"],
            ],
            "targets": [
                OUTPUT_DIR / f"{notebook_name}.html",
                OUTPUT_DIR / f"{notebook_name}.ipynb",
                *notebook_tasks[notebook]["targets"],
            ],
            "clean": True,
        }
# fmt: on

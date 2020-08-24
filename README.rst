Analysis of Portuguese radios' repetitiveness
========

Code and data used for analyzing the repetitiveness of 4 Portuguese radios
https://ruitsilva.com/pt/post/repetitividade_radios/
(in Portuguese).


Dependencies
------------

`poetry` dependency management tool: https://python-poetry.org/

pyenv and virtualenv

Installation
------------

Clone repo

cd into project dir

Create a virtualenv for the project and activate it

    pyenv install 3.7.6

    pyenv virtualenv 3.7.6 analysis_pt_radios

    pyenv activate analysis_pt_radios

Install package with

    poetry install


Run
---

`cd` into the main folder

    cd radio_repeat

In the `./data` folder we have:

- `all_data.csv` csv file with the songs played by 4 radio stations
  during the Aug 10 - Aug 16 week. The data was already cleaned using
  the `clean_data.py` script

- `{radio}_{day}_08_2020.csv` csv file with the songs played by
  `radio` during `day`. Extracted using the scrapers.

Run

    python analysis.py


The plots will be saved as figures in the current directory. Other
results may be shown on the terminal.

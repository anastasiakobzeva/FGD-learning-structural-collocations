# Acquiring Constraints on FGDs with Structural Collocations

Data and code repository for "Acquiring Constraints on Filler-Gap Dependencies with Structural Collocations: Assessing a Computational Learning Model of Island-Insensitivity in Norwegian" (submitted to *Language Acquisition*).

The work reported in the paper consisted of three parts: 
1. Parsing the annotated nob-child corpus to extract FGD paths
2. Implementing the modeled learner in Python
3. Analyzing the modeling results alongside human AJTs
This repository is structured accordingly.

## Corpus parsing

Here you can find scripts for processing annotated corpus data in tiger-XML format.
- script for extracting FGDs paths from LFG's f-structure (`find_f_labels.py`, to be run from Python interpreter)
In the `examples` folder, you can find:
- example of raw data in tiger-XML (input to `find_f_labels.py`)
- example output file with extracted FGDs (output of `find_f_labels.py`)

## Learner implementation

Here you can find input and output data for the learning algorithm
- wh-FGDs paths extracted from the nob-child, with 14% of the data manually checked (`output_wh_corrected_oct23.xlsx`)
- RC-FGDs paths extracted from the nob-child, with 22% of the data manually checked (`output_rc_corrected_oct23.xlsx`)
- python script with learner functions such as creating frequency distribution, calculating probability etc.  (`learner_functions.py`)
- Jupyter notebooks with learner implementations (4 notebooks, one for each n-gram*dependency combination)

## Results visualization

- data analysis and visualisation in R Markdown
- all figures reported in the paper
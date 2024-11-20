# Learning Constraints on FGDs with Structural Collocations

Data and code repository for "Acquiring Constraints on Filler-Gap Dependencies with Structural Collocations: Assessing a Computational Learning Model of Island-Insensitivity in Norwegian" (submitted to *Language Acquisition*).

The work reported in the paper consisted of three parts: 
1. Parsing the annotated nob-child corpus to extract FGD paths
2. Implementing the modeled learner in Python
3. Analyzing the modeling results alongside human AJTs
This repository is structured accordingly.

## Corpus parsing

Here you can find scripts for processing annotated corpus data in tiger-XML format.
- script for extracting FGDs paths from LFG's f-structure (to be run from Python interpreter)
- script for converting c-structure into nltk-tree
- example of raw data in tiger-XML format that can be used for testing FGD-extraction
- example output file with extracted FGDs

## Learner implementation

Here you can find input and output data for the learning algorithm
- wh-FGDs paths extracted from the nob-child, with ... % of the data manually checked (`output_wh_corrected_oct23.xlsx`)
- RC-FGDs paths extracted from the nob-child, with ... % of the data manually checked (`output_rc_corrected_oct23.xlsx`)
- python script with learner functions such as creating frequency distribution, calculating probability etc.  (`learner_functions.py`)

## Results visualization
- data analysis and vizualisation in R Markdown
- all figures reported in the paper
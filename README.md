# Learning Constraints on FGDs with Structural Collocations
Data and code repository for "Acquiring Constraints on Filler-Gap Dependencies with Structural Collocations: Assessing a Computational Learning Model of Island-insensitivity in Norwegian".

**This is work in progress**

The repository contains the following folders:
1. data: input and output data for the learning algorithm
- wh-FGDs paths extracted from the nob-child, with ... % of the data manually checked (output_wh_corrected_oct23.xlsx)
- RC-FGDs paths extracted from the nob-child, with ... % of the data manually checked (output_rc_corrected_oct23.xlsx)
- example of raw data in tiger-XML format that can be used for testing FGD-extraction
- example output file with extracted FGDs

2. FGD-extraction: scripts for processing data in tiger-XML format and extracting FGDs paths from the f-structure
- script for extracting FGDs paths from LFG's f-structure (to be run from Python interpreter)
- 

3. learner-algorithm 
- python script with learner functions such as creating frequency distribution, calculating probability etc.  (learner_functions.py)
- 4 versions of the learner algorithm with data analysis as jupyter notebooks (ngrams $\times$ FGD type, where ngrams: bigrams, trigrams and FGD type: RC-FGDs, wh-FGDs)
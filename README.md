# AIBG - Analysis of Insuline use and Blood Glucose
## Motivation
It's important to have a good data analysis framework that fits a diabetic and their endo's needs when it comes to blood sugar analysis. This is what AIBG is meant to be.

## What's happening right now
The project is being overhauled in order to separate report creation and data analysis and filtering. Initially it'll support only the CSV files that [Diaguard](https://github.com/Faltenreich/Diaguard) exports, but there'll be support for future additions.

## Source for calculating HbA1c
The HbA1c estimative depends on the estimated average glucose (mg/dL) from the last three months, as described in:
Nathan DM, Kuenen J, Borg R, Zheng H, Schoenfeld D, Heine RJ (2008). **"Translating the A1C assay into estimated average glucose values"**. *Diabetes Care*. 31 (8): 1473–78.

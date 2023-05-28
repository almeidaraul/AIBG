<p align="center">
  <a href="" rel="noopener">
 <img width=200px height=200px src="img/glikoz_logo.png" alt="Glikoz logo"></a>
</p>

<h1 align="center">Glikoz</h1>

<div align="center">

  [![Status](https://img.shields.io/badge/status-active-success.svg)]() 
  [![GitHub Issues](https://img.shields.io/github/issues/almeidaraul/glikoz)](https://github.com/almeidaraul/glikoz/issues)
  [![GitHub Pull Requests](https://img.shields.io/github/issues-pr/almeidaraul/glikoz)](https://github.com/almeidaraul/glikoz/pulls)
  [![License](https://img.shields.io/badge/license-MIT-blue.svg)](/LICENSE)

</div>

---

<p align="center"> Glucose and insulin use data analysis for diabetes therapy
    <br> 
</p>

## 📝 Table of Contents
- [About](#about)
- [Getting Started](#getting_started)
- [Usage](#usage)

## 🧐 About <a name = "about"></a>
**Glikoz** · _γλικοζ_ (/ɣli'koz/): a glucose and insulin use data analysis tool to assist the treatment of diabetes. Currently it is built around information exported from the [Diaguard](https://github.com/Faltenreich/Diaguard) app as backup CSVs.

## 🏁 Getting Started <a name = "getting_started"></a>
These instructions will get you a copy of the project up and running on your local machine for development and testing purposes.

### Prerequisites
**Glikoz** is built using Python3. Install dependencies from `src/requirements.txt`:

```bash
pip3 install -r requirements.txt
```

### Installing
Install **glikoz** with pip so it can be used from anywhere in your machine:

```bash
pip3 install -e .
```

And then use its modules in your own program:
```python
from glikoz import DiaguardCSVParser

csv = open("diaguard_export.csv", 'r')
parser = DiaguardCSVParser()
df = parser.parse_csv(csv)

print(df.describe())
```

## 🎈 Usage <a name="usage"></a>
Using **glikoz** is as simple as instantiating a `ReportCreator` object with some input CSV (exported from Diaguard) and creating a report with it:

```python
import sys
from glikoz import DiaguardCSVParser, DataFrameHandler, PDFReportCreator

# parse a CSV into a pandas DataFrame
parser = DiaguardCSVParser()
csv_source = sys.stdin
df = parser.parse_csv(csv_source)
df_handler = DataFrameHandler(df)
# initialize report creator
report_creator = PDFReportCreator(df_handler)
report_creator.fill_report()

# create report and save it to report.pdf
output = open("report.pdf", "wb")
report_creator.create_report(target=output)
```

You can also run the `get_report` script with the input coming from STDIN, e.g.,
```bash
cat diaguard_export.csv | python3 get_report --format pdf  # reports to output.pdf
```
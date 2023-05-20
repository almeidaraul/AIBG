from .base_reporter import Reporter


class RawReporter(Reporter):
    """Reporter for pure text reports"""

    def __init__(self, explorer):
        super().__init__(explorer)

    def report(self):
        """Print report to STDOUT"""
        report = super().get_values()
        print("# Statistics")
        print("## Last 3 months")
        print(f"HbA1c: {report['hba1c']}")
        print("## Last 15 days")
        print("In/below/above range:",
              report['in_range'], '/', report['below_range'], '/',
              report['above_range'])
        print("## Last 5 days")
        print(f"Total entries: {report['total_entries']}",
              f"{report['entries_per_day']} per day")
        print(f"Fast insulin: {report['mean_fast_per_day']} +-",
              f"{report['std_fast_per_day']} per day")
        print("### Glucose per hour")
        print("#### Hours")
        for h in report['mean_glucose_per_hour']['hour']:
            print(h)
        print("#### Mean glucose")
        for g in report['mean_glucose_per_hour']['mean_glucose']:
            print(g)
        print("#### Std error")
        for s in report['mean_glucose_per_hour']['std_error']:
            print(s)
        table = report['table']
        print("### Entries")
        print("#### Date")
        for d in table['Date']:
            date, time = d.split(' ')
            date = date[5:].replace('-', '/')
            time = time[:-3]
            print(date, time)
        print("#### Glucose")
        for g in table['Glucose']:
            print(g if g > 0 else '')
        print("#### Bolus")
        for b in table['Bolus']:
            print(b if b > 0 else '')
        print("#### Correction")
        for c in table['Correction']:
            print(c if c > 0 else '')
        print("#### Basal")
        for b in table['Basal']:
            print(b if b > 0 else '')
        print("#### Meal")
        for m in table['Meal']:
            print(m)
        print("#### Carbohydrates")
        for c in table['Carbohydrates']:
            print(c if c > 0 else '')
        print("---")

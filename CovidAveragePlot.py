#!/usr/bin/env python

import argparse
import json

from covidtracking import CovidTracking
import plotly.graph_objects as go
from plotly.subplots import make_subplots

state_hash = {
    "AL": "Alabama",
    "AK": "Alaska",
    "AS": "American Samoa",
    "AZ": "Arizona",
    "AR": "Arkansas",
    "CA": "California",
    "CO": "Colorado",
    "CT": "Connecticut",
    "DE": "Delaware",
    "DC": "District Of Columbia",
    "FM": "Federated States Of Micronesia",
    "FL": "Florida",
    "GA": "Georgia",
    "GU": "Guam",
    "HI": "Hawaii",
    "ID": "Idaho",
    "IL": "Illinois",
    "IN": "Indiana",
    "IA": "Iowa",
    "KS": "Kansas",
    "KY": "Kentucky",
    "LA": "Louisiana",
    "ME": "Maine",
    "MH": "Marshall Islands",
    "MD": "Maryland",
    "MA": "Massachusetts",
    "MI": "Michigan",
    "MN": "Minnesota",
    "MS": "Mississippi",
    "MO": "Missouri",
    "MT": "Montana",
    "NE": "Nebraska",
    "NV": "Nevada",
    "NH": "New Hampshire",
    "NJ": "New Jersey",
    "NM": "New Mexico",
    "NY": "New York",
    "NC": "North Carolina",
    "ND": "North Dakota",
    "MP": "Northern Mariana Islands",
    "OH": "Ohio",
    "OK": "Oklahoma",
    "OR": "Oregon",
    "PW": "Palau",
    "PA": "Pennsylvania",
    "PR": "Puerto Rico",
    "RI": "Rhode Island",
    "SC": "South Carolina",
    "SD": "South Dakota",
    "TN": "Tennessee",
    "TX": "Texas",
    "UT": "Utah",
    "VT": "Vermont",
    "VI": "Virgin Islands",
    "VA": "Virginia",
    "WA": "Washington",
    "WV": "West Virginia",
    "WI": "Wisconsin",
    "WY": "Wyoming"
}

state_population = '''
Alabama,4903185
Alaska,731545
Arizona,7278717
Arkansas,3017804
California,39512223
Colorado,5758736
Connecticut,3565287
Delaware,973764
District of Columbia,705749
Florida,21477737
Georgia,10617423
Hawaii,1415872
Idaho,1787065
Illinois,12671821
Indiana,6732219
Iowa,3155070
Kansas,2913314
Kentucky,4467673
Louisiana,4648794
Maine,1344212
Maryland,6045680
Massachusetts,6892503
Michigan,9986857
Minnesota,5639632
Mississippi,2976149
Missouri,6137428
Montana,1068778
Nebraska,1934408
Nevada,3080156
New Hampshire,1359711
New Jersey,8882190
New Mexico,2096829
New York,19453561
North Carolina,10488084
North Dakota,762062
Ohio,11689100
Oklahoma,3956971
Oregon,4217737
Pennsylvania,12801989
Rhode Island,1059361
South Carolina,5148714
South Dakota,884659
Tennessee,6829174
Texas,28995881
Utah,3205958
Vermont,623989
Virginia,8535519
Washington,7614893
West Virginia,1792147
Wisconsin,5822434
Wyoming,578759
Puerto Rico,3193694
'''


def get_state_population():
    pop_map = {}
    for line in state_population.split('\n'):
        if line:
            name, population = line.split(',')
            pop_map[str(name).lower()] = int(population)
    return pop_map


def fetch_data(file=None, state=None):
    if file is None:
        return CovidTracking().states_daily(state)
    else:
        return json.loads(open(file).read())


def show_data(x, cases, avg_cases, pcts, avg_pcts, state, state_name, population_in_million):
    # stacked charts
    fig = make_subplots(rows=2, cols=1,
                        subplot_titles=("Daily Positive Cases", "Daily Positive Test Percentage"),
                        specs=[[{"secondary_y": True}], [{"secondary_y": True}]])

    # Total cases
    fig.add_trace(go.Scatter(x=x, y=cases, mode='lines+markers',
                             name='Total New Cases',
                             line=dict(color='orange', width=2)),
                  row=1, col=1)
    # Cases Per Population
    fig.add_trace(go.Scatter(x=x, y=[x / population_in_million for x in avg_cases], mode='markers',
                             name='Rolling Avg Per Million',
                             line=dict(color='firebrick', width=4, dash='dot')),
                  row=1, col=1,
                  secondary_y=True)

    # Positive percentage
    fig.add_trace(go.Scatter(x=x, y=pcts, mode='lines+markers',
                             name='Positive Test Percentage',
                             line=dict(color='orange', width=2)),
                  row=2, col=1)
    # Percentage Per Population
    fig.add_trace(go.Scatter(x=x, y=avg_pcts, mode='markers',
                             name='Rolling Avg Percentage',
                             line=dict(color='firebrick', width=4, dash='dot')),
                  row=2, col=1)

    # Edit the layout
    fig.update_yaxes(title_text='Number of Cases', showgrid=False, secondary_y=False, row=1, col=1)
    fig.update_yaxes(title_text='Rolling Number Per 1M', showgrid=True, secondary_y=True, row=1, col=1)
    fig.update_yaxes(title_text='Percentage of Positive', showgrid=False, secondary_y=False, row=2, col=1)
    fig.update_layout(title_text='{} state (pop. {:.2f}M) Covid Trend'.format(state_name, population_in_million))

    # output
    fig.write_html(state + '.html', auto_open=True)


def process_data(data, number_rolling_day, number_day_shown):
    date = []
    pos_cases, total_cases, pos_pct = [], [], []
    avg_pos_cases, avg_pos_pct = [], []
    # get all columns we need
    for daily in data:
        date.insert(0, daily.get('date'))
        # get data for the day
        posInc = daily.get('positiveIncrease', 0)
        totalInc = daily.get('totalTestResultsIncrease', 0)
        pos_cases.insert(0, posInc)
        total_cases.insert(0, totalInc)
        pos_pct.insert(0, posInc / totalInc * 100 if totalInc != 0 else 0)
    # calculate rolling average
    sum_pos = 0
    sum_tot = 0
    for i in range(len(date)):
        sum_pos += pos_cases[i]
        sum_tot += total_cases[i]
        if i < number_rolling_day - 1:
            avg_pos_cases.append(0)
            avg_pos_pct.append(0)
        elif i == number_rolling_day - 1:
            avg_pos_cases.append(sum_pos / number_rolling_day)
            avg_pos_pct.append(sum_pos / sum_tot * 100 if sum_tot != 0 else 0)
        else:
            sum_pos -= pos_cases[i - number_rolling_day]
            avg_pos_cases.append(sum_pos / number_rolling_day)
            sum_tot -= total_cases[i - number_rolling_day]
            avg_pos_pct.append(sum_pos / sum_tot * 100 if sum_tot != 0 else 0)
    # fix date format
    for i in range(len(date)):
        start = str(date[i])
        date[i] = start[:4] + "-" + start[4:6] + "-" + start[6:]
    # return results
    start = 0 - number_day_shown
    return date[start:], pos_cases[start:], avg_pos_cases[start:], pos_pct[start:], avg_pos_pct[start:]


def main():
    # command-line help
    parser = argparse.ArgumentParser(description='Plot the 7-day rolling average chart (daily new cases and '
                                                 'positive test percentage) for a state.',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('states', nargs='*', default=['WA'],
                        help="two-letter abbreviated state names")
    parser.add_argument('-shown', type=int, default=90,
                        help='number of days to be shown')
    parser.add_argument('-rolling', type=int, default=7,
                        help='number of days to be averaged')
    args = parser.parse_args()

    # input parameters
    states = args.states
    rolling = args.rolling
    shown = args.shown

    # pre-process
    name_hash = {v.lower(): k for k, v in state_hash.items()}
    state_pop_map = get_state_population()
    plot_chart = True
    if len(states) == 1 and states[0] == 'all':
        states = [name_hash[s] for s in state_pop_map]
        plot_chart = False

    # do the things
    lines = []
    for s in states:
        state = s.upper()
        state_name = state_hash[state] if state in state_hash else state
        if state_name.lower() not in state_pop_map:
            raise Exception("cannot find population for state: " + state_name)
        popInMillion = state_pop_map[state_name.lower()] / 1000000.0

        data = fetch_data(state=state)
        dates, new_cases, avg_cases, pos_pcts, avg_pcts = process_data(data=data,
                                                                       number_rolling_day=rolling,
                                                                       number_day_shown=shown)
        if plot_chart:
            show_data(x=dates,
                      cases=new_cases, avg_cases=avg_cases,
                      pcts=pos_pcts, avg_pcts=avg_pcts,
                      state=state, state_name=state_name, population_in_million=popInMillion)
        else:
            line = '{},{},{:.2f},{:.2f}'.format(dates[shown - 1],
                                                state_hash[state],
                                                avg_cases[shown - 1] / popInMillion,
                                                avg_pcts[shown - 1])
            print(line)
            lines.append(line)

    # save file if necessary
    if not plot_chart:
        with open('states.csv', 'w') as f:
            f.write('{},{},{},{}\n'.format('date', 'state', 'daily_positive_cases_in_million', 'daily_positive_rate'))
            for line in lines:
                f.write(line + "\n")


if __name__ == '__main__':
    main()

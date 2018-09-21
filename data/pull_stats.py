# Import a few libraries.
from bs4 import BeautifulSoup as bs
import html5lib, requests, time, os
import pandas as pd
from scipy.stats.stats import pearsonr


# Set the year
year = '2016'


# Pointers to the webpages for all the teams
response = requests.get("http://www.cfbstats.com/" + year + "/team/index.html")
soup = bs(response.content, "html5lib")
anchors = soup.findAll("a")
team_anchors = [a for a in anchors if '/' + year + '/team/' in a.attrs['href']]


# Get the fields by examining one particular team
response = requests.get("http://www.cfbstats.com/" + year + "/team/518/index.html")
soup = bs(response.content, "html5lib")

stat_names = soup.findAll("td", {"class": "statistic-name"})

stat_names = [d.text for d in stat_names]


def cfbStatsField_to_fields(s):
    if s == 'Time of Possession / Game':
        return [["TEAM Time of Possession"], ["OPP Time of Possession"]]
    elif s == 'Scoring:  Games - Points':
        #print('here')
        return [["TEAM Total Points"], ["OPP Total Points"]]
    else:
        cat,fields = s.split(": ")
        fields = fields.split(" - ")
        # fields = [[["TEAM " + cat + " " + field], ["OPP " + cat + " " + field]]  for field in fields]
        team_fields = ["TEAM " + cat + " " + field for field in fields]
        # ["TEAM Field Goals Attempts", "TEAM Field Goals Made"]
        opp_fields = ["OPP " + cat + " " + field for field in fields]
        # ["TEAM Field Goals Attempts", "TEAM Field Goals Made"]
        team_fields.extend(opp_fields)
        team_fields = [[x] for x in team_fields]
        # [["TEAM Field Goals Attempts"], ["TEAM Field Goals Made"], ..., ["OPP Field Goals Made"]]
        return team_fields


# for each stat like "Field Goals: Attempts - Made"
# [[["TEAM Field Goals Attempts"], ["TEAM Field Goals Made"], ..., ["OPP Field Goals Made"]], ... ]
myfields = [cfbStatsField_to_fields(s) for s in stat_names]

# myfields = ["TEAM Field Goals Attempts", "TEAM Field Goals Made", ..., "OPP Field Goals Made", ... ]
myfields = [item[0] for sublist in myfields for item in sublist]

# special names
myfields = [f.replace("Returns Returns", "Returns") for f in myfields]
myfields = [f.replace("Conversions Conversion", "Conversion") for f in myfields]
myfields = [f.replace("Conversions Conversions", "Conversion") for f in myfields]


# head = [["Team", "ID", "Wins", "Losses", "TEAM Field Goals Attempts", "TEAM Field Goals Made", ..., "OPP Field Goals Made", ... ]
head = ['Team', 'ID', 'Wins', 'Losses']
head.extend(myfields)


myfields = list(head)
myfields = [' '.join(name.split()) for name in myfields]

for name in myfields:
    ' '.join(name.split())

#this is a table with the stat names as headers
df = pd.DataFrame(columns = myfields)

# Processes the rows in the Team Statistics table for each team
def process_row(row):
    data = row.findAll('td')
    cfbStatsField = data[0].text
    d = data[1:]
    if cfbStatsField == 'Scoring:  Games - Points':
        games_and_points = d[0].text.split(" - ")
        games = games_and_points[0]
        points = games_and_points[1]
        opponents_points = d[1].text.split(" - ")[1]
        return [points, opponents_points]
    else:
        d = [dd.text.split(" - ") for dd in d]
        d = [item for sublist in d for item in sublist]
        return d


# Adds a team to the main data frame
def add_team(idx, team_anchor):
    team_name = team_anchor.text
    href = team_anchor.attrs['href']
    team_id = href.split('/')[3]
    response = requests.get("http://www.cfbstats.com/" + href)
    soup = bs(response.content, "html5lib")
    wl = soup.find('table', {"class":"team-record"}).findAll('td')[1].text.split('-')
    wins = wl[0]
    losses = wl[1]
    (wins,losses)
    head = [team_name, team_id, wins, losses]

    more_data = soup.find("table", {"class": "team-statistics"})
    rows = more_data.contents[3].findAll('tr')
    more_data = [process_row(row) for row in rows[1:]]
    more_data = [item for sublist in more_data for item in sublist]
    head.extend(more_data)
    df.loc[idx] = head


# Do it!
# Takes a minute or so.
for i,ta in enumerate(team_anchors):
    add_team(i,ta)

# Save the still fairly raw data to a CSV.
df.to_csv('CFB' + year + '_raw.csv')
#
#
#
# # A little function to convert the various formats to raw numbers
# def entry_to_num(s):
#     try:
#         n = s
#         if s[-1] == '%':
#             return float(n.split('%')[0])/100.0
#         if ',' in n:
#             n = n.replace(',','')
#         if ':' in n:
#             x = n.split(':')
#             return 60*float(x[0]) + float(x[1])
#         if '.' in n:
#             return float(n)
#         else:
#             return int(n)
#     except:
#         return s
#
#
#
# # Add some stats that are combos of the stats so far
# df = pd.read_csv('CFB' + year + '_raw.csv')
# del df['ID']
# df = df.iloc[:,:110]
# df = df.applymap(entry_to_num)
# df.columns = [' '.join(name.split()) for name in df.columns]
# df.insert(4, 'WL%', df['Wins']/(df['Wins'] + df['Losses']))
# df.insert(5, 'Turnover margin',
#     (df['OPP Fumbles Lost'] - df['TEAM Fumbles Lost']) +
#         (df['OPP Passing Interceptions'] - df['TEAM Passing Interceptions'])
# )
# df.insert(6, 'TEAM Passing Yards per Attempt',
#     df['TEAM Passing Yards']/df['TEAM Passing Attempts']
# )
# df.insert(7, 'OPP Passing Yards per Attempt',
#     df['OPP Passing Yards']/df['OPP Passing Attempts']
# )
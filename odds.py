import itertools
from bs4 import BeautifulSoup as bs
import requests
import json
import time
from datetime import datetime
from datetime import timedelta
import sys

if len(sys.argv) == 3:
    date1=sys.argv[1]
    date2 = sys.argv[2]
else:
    date1="2022-08-10"
    date2="2022-08-09"

mainLink="https://oddslogs.com"
sleepSeconds = 0.1
file = open("myfile.txt", "w", encoding="utf-8")
logfile = open("runlog.txt", "w", encoding="utf-8")


rowStr = ""
def addStr(str):
    global rowStr
    for s in str:
        if rowStr == "":
            rowStr += s
        else:
            rowStr += ";" + s


def writeLine():
    global rowStr
    file.write(rowStr + "\n")
    rowStr = ""


def split(str, character):
    if str is not None:
        return str.split(character)
    else:
        return ("", "")

try:

    dt1 = datetime.strptime(date1, "%Y-%m-%d")
    dt2 = datetime.strptime(date2, "%Y-%m-%d")


    #header
    addStr(("Date", "League", "MatchTime", "Team1", "Team2", "Weather_Temperature", "Weather_Condition",
           "Weather_wind_speed", "Weather_pressure", "Weather_humidity", "Minute", "Score", "1", "X", "2", "1X", "12", "X2",
           "HCap1", "HC1", "HCap2", "HC2", "Total", "O", "U", "Attacks1", "Attacks2", "Dangerous_Attacks1",
           "Dangerous_Attacks2", "Possession1", "Possession2", "Shots_on_target1", "Shots_on_target2", "Shots_off_target1",
           "Shots_off_target2", "Corners1", "Corners2", "Yellow_cards1", "Yellow_cards2", "Red_Cards1", "Red_Cards2",
           "Penalties1", "Penalties2"))
    writeLine()

    currentDt=dt1
    while currentDt >= dt2:

        currentDtStr = currentDt.strftime("%Y-%m-%d")

        dateLink = mainLink + "/date/" + currentDtStr
        html = requests.get(dateLink)
        soup = bs(html.text, "lxml")

        pageIndex = 0
        while True:
            pageIndex += 1

            # tarih
            dt = soup.findAll("span", {"class", "btn btn-sm"})[0].text

            # maçlar
            results = soup.findAll("a", {"class", "match__event"})
            index = 0
            for match in results:
                index += 1
                link = match["href"]
                matchHtml = requests.get("https://oddslogs.com" + link)
                matchSoup = bs(matchHtml.text, "lxml")

                # ana bilgiler
                if len(matchSoup.findAll("h2", {"class", "d-inline"})) > 0:
                    league = matchSoup.findAll("h2", {"class", "d-inline"})[0].text.replace("\t", "").replace("\n", "")
                    matchTime = matchSoup.findAll("span", {"class", "view-date text-end text-wrap"})[0].text.replace("\t", "").replace("\n", "")
                    team1 = matchSoup.findAll("h4", {"class", "py-1"})[0].text.replace("\t", "").replace("\n", "")
                    team2 = matchSoup.findAll("h4", {"class", "py-1"})[1].text.replace("\t", "").replace("\n", "")

                    l="date: " + currentDtStr + ", page: " + str(pageIndex)+ ", " + str(index) + "/" + str(len(results)) + " " + team1 + "-" + team2
                    print(l)
                    logfile.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S")+" - "+l+"\n")

                    #hava durumu
                    weather_list=[""]*5
                    if len(matchSoup.findAll("span", {"class", "meteo"})) > 0:
                        weather_list=[span.text.replace("\t", "").replace("\n","").strip() for span in matchSoup.findAll("span", {"class", "meteo"})]

                    # dakika bazında bilgiler
                    table = matchSoup.findAll("table", {"class", "table table__inplay table-hover"})[0]
                    tbody = table.find("tbody")
                    for row in tbody.findAll("tr"):
                        addStr([dt, league, matchTime, team1, team2]+weather_list+[row.find("th").text])

                        statsList = [""]*18
                        for cell in row.findAll("td"):
                            # detay istatistik
                            stats = cell.find("div", {"class", "stats"})
                            if stats is not None and stats["data-stat"] != "null":
                                statsjson = json.loads(stats["data-stat"])
                                statsList = list(itertools.chain(*[split(statsjson[item], '|') for item in ("A", "D", "P", "SO", "S", "C", "Y", "R", "PE")]))
                            else:
                                # kolon bilgisi
                                cellStr = cell.text.replace("\t", "").replace("\n", "").strip()
                                addStr((cellStr,))

                        addStr(statsList)
                        writeLine()

                    time.sleep(sleepSeconds)
                else:
                    l="hata:içerik alınamadı - date: " + currentDtStr + ", page: " + str(pageIndex) + ", " + str(index) + "/" + str(len(results)) + " https://oddslogs.com" + link
                    print(l)
                    logfile.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S")+" - " + l+"\n")


            if soup.findAll("li", {"class" : "page-item active"})[0].findNextSibling("li") is None:
                break
            nextPage = soup.findAll("li", {"class" : "page-item active"})[0].findNextSibling("li").find("a")["href"]
            html = requests.get(dateLink+nextPage)
            soup = bs(html.text, "lxml")

        currentDt -= timedelta(days=1)

except Exception as e:
    logfile.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S")+" - hata:"+str(e))
    raise e
finally:
    file.close()
    logfile.close()
    print("finished")

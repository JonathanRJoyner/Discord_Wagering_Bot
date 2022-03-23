from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from dateutil import parser
from datetime import date, timedelta
import time


def upcoming():
    """Runs the scrape, formats the data, and returns matches as a list of tuples."""

    upcoming = scrape_upcoming(
        ["basketball/nba", "hockey/nhl", "soccer/england-premier-league"]
    )
    parsed = match_parse(upcoming)

    matches = []
    for item in parsed:
        match = UpcomingMatch(item)
        match = match.match()
        matches.append(match)

    return matches


def scrape_upcoming(paths: list):
    """Gets the upcoming matches given a list of paths to scrape."""

    driver = webdriver.Chrome()

    upcoming = []
    for path in paths:
        driver.get(f"https://www.bovada.lv/sports/{path}")
        try:
            wait = WebDriverWait(driver, 10)
            wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "bucket__title-button"))
            )
            time.sleep(1)
        except:
            pass

        s = sport(path)
        l = league(path)
        html = driver.page_source
        output = (s, l, html)
        upcoming.append(output)

    return upcoming


def sport(path: str):
    '''Takes the url path and gets the sport.'''

    sport = path.split("/")[0]
    sport = sport.capitalize()
    return sport


def league(path: str):
    '''Takes the url path and gets the league. If the league is 1 word it is uppercase, otherwise it is titled.'''

    league = path.split("/")[-1]
    league = league.replace("-", " ")

    if " " not in league:
        league = league.upper()

    else:
        league = league.title()

    return league


def matches(html):
    '''Takes the scraped html for upcoming matches and makes a soup object.'''

    soup = BeautifulSoup(html, "html.parser")
    matches = soup.find_all("section", "coupon-content more-info")
    return matches

def match_parse(upcoming):
    '''Takes matches from the scrape_upcoming function and outputs the sport, league, and match html.'''

    output = []
    for item in upcoming:
        m = matches(item[2])
        for match in m:
            match = (item[0], item[1], match)
            output.append(match)

    return output

class UpcomingMatch:
    '''This class represents and individual upcoming match. Each method gathers one piece of match information.
        The match method outputs all data for the match.'''

    def __init__(self, tup):
        self.sport = tup[0]
        self.league = tup[1]
        self.soup = tup[2]

    def draw(self):
        """determines whether a draw is possible in the matchup."""

        try:
            draw = self.soup.find("span", "draw-name").text
            return draw

        except AttributeError:
            return None

    def gametime(self):
        """finds the gametime for each matchup."""

        try:
            gametime = self.soup.find("span", "period hidden-xs").text

            try:
                gametime = parser.parse(gametime)
                gametime = gametime.strftime("%Y-%m-%d %H:%M:%S")

            # this catches any live matches and sets the gametime to None
            except parser.ParserError:
                gametime = None

        # this catches errors with the gametime not existing.
        except AttributeError:
            gametime = None
        return gametime

    def matchup(self):
        """finds the teams involved in each matchup."""

        teams = self.soup.find_all("span", "name")
        matchup = [teams[0].text, teams[1].text]
        return matchup

    def favorite(self):
        """This captures the favored team in a matchup. Currently this information is not used but will be in the future."""

        try:
            favorite = self.soup.find("h4", "competitor-name favorite").text
        except AttributeError:
            favorite = None

        return favorite

    @staticmethod
    def even(bets):
        """Catches any even bets and turns them into an integer value."""

        output = []
        for bet in bets:
            if bet == " EVEN ":
                bet = 100

            output.append(bet)

        return output

    def win_bets(self):
        """Captures the winning bet amounts for each matchup. If a draw is possible it captures the odds for the draw."""

        if self.draw() == "Draw":
            bet = self.soup.find_all("sp-three-way-vertical", "market-type")

            # bet[1] is used to capture the winning bets. use '[0]' or '[2]' to capture other types of bets.
            try:
                bet = bet[1].find_all("span", "bet-price")
                bets = [bet[0].text, bet[1].text, bet[2].text]
                bets = self.even(bets)
                bet = [int(bets[0]), int(bets[1]), int(bets[2])]

            # this catches any issues with the bets not existing.
            except IndexError:
                bet = [None, None, None]

        else:
            bet = self.soup.find_all("sp-two-way-vertical", "market-type")

            try:
                bet = bet[1].find_all("span", "bet-price")
                bets = [bet[0].text, bet[1].text, None]
                bets = self.even(bets)
                bet = [int(bets[0]), int(bets[1]), None]

            # this catches any issues with the bets not existing.
            except IndexError:
                bet = [None, None, None]

        return bet

    def match(self):
        """This gathers all of the data from the match and returns a type containing all of the match information."""

        matchup = self.matchup()
        bet = self.win_bets()

        try:
            data = (
                self.sport,
                self.league,
                self.gametime(),
                matchup[0],
                matchup[1],
                bet[0],
                bet[1],
                bet[2],
                None,
            )
        except IndexError:
            pass
        return data


def yesterday():
    '''Gets yesterdays date'''
    return date.today() - timedelta(days=1)


def scrape_results():
    '''Scrapes the results given the sport.'''

    sports = ["soccer", "hockey", "basketball"]

    search_date = yesterday()

    driver = webdriver.Chrome()

    results = []
    for sport in sports:
        driver.get(f"https://scores.bovada.lv/en/{sport}/events?date={search_date}")

        time.sleep(20)

        html = driver.page_source
        results.append(html)

    return results


def r_matches(html):
    '''Takes the scraped match results html and makes a soup of each match.'''

    soup = BeautifulSoup(html, "html.parser")
    matches = soup.find_all("div", "event__container")
    return matches


def match_results(matches):
    '''Takes the list of matches from r_matches function and creates a result output 
        using other functions to get match information.'''

    results = []
    date = yesterday().strftime("%Y-%m-%d")

    for match in matches:
        status = results_status(match)
        matchup = result_matchup(match)
        winner = result_winner(match)

        output = (str(date), matchup[0], matchup[1], winner, status)
        results.append(output)

    return results


def results_status(match):
    '''Takes an individual match soup and returns the status. Status is "Canc." if none is found.'''

    try:
        status = match.find("span", "status--name").text

    except AttributeError:
        status = "Canc."

    return status


def result_matchup(match):
    '''Takes an individual match soup and returns the teams involved in the match.'''

    team_list = []
    teams = match.find_all("a", "link")
    for team in teams:
        team = team.text
        team_list.append(team)
    return team_list


def result_winner(match):
    '''Takes an individual match soup and returns the winner. Checks if the match was cancelled if no winner is found.
        If the match wasn't cancelled it returns "Draw".'''

    try:
        winner = match.find("a", "link winner").text

    except AttributeError:
        if results_status(match) == "Canc.":
            winner = "Canc."
        else:
            winner = "Draw"

    return winner


def results():
    '''Scrapes results, parses, and returns match results as a list of tuples.'''

    results = scrape_results()
    r = []
    for item in results:
        matches = r_matches(item)
        output = match_results(matches)

        r.extend(output)

    return r

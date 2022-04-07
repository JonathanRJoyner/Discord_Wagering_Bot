from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
import chromedriver_autoinstaller
from selenium import webdriver
from bs4 import BeautifulSoup
from dateutil import parser
import datetime
import time

chromedriver_autoinstaller.install()

options = webdriver.ChromeOptions()
options.add_argument('--no-sandbox')
options.add_argument('--headless')
options.add_argument('--disable-gpu')

class UpcomingMatch:
    '''This class represents the matches scraped from a leagues page, it takes string path of the league.'''

    def __init__(self, path):
        self.path = path
        self.html = self.scrape()

    def scrape(self):
        """Gets the upcoming matches given a list of paths to scrape."""

        driver = webdriver.Chrome(options=options)

        driver.get(f"https://www.bovada.lv/sports/{self.path}")
        try:
            wait = WebDriverWait(driver, 10)
            wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "bucket__title-button"))
            )
            time.sleep(1)

        except:
            pass

        html = driver.page_source

        return html

    def sport(self):
        '''Takes the url path and gets the sport.'''

        sport = self.path.split("/")[0]
        sport = sport.capitalize()
        return sport

    def league(self):
        '''Takes the url path and gets the league. If the league is 1 word it is uppercase, otherwise it is titled.'''

        league = self.path.split("/")[-1]
        league = league.replace("-", " ")

        if " " not in league:
            league = league.upper()

        else:
            league = league.title()

        return league

    def matches(self):
        '''Takes the scraped html for upcoming matches and makes a soup object.'''

        soup = BeautifulSoup(self.html, "html.parser")
        matches = soup.find_all("section", "coupon-content more-info")
        return matches

    def upcoming(self):
        """This gathers all of the data from the match and returns a type containing all of the match information."""
        output = []

        for match in self.matches():
            bet = UpcomingMatch.win_bets(match)
            teams = UpcomingMatch.teams(match)
            
            mdt = UpcomingMatch.match_datetime(match)

            try:
                match_date = mdt.strftime('%Y-%m-%d')
                match_time = mdt.strftime('%H:%M')
            except AttributeError:
                pass


            try:
                data = (
                    self.sport(),
                    self.league(),
                    match_date,
                    match_time,
                    teams[0],
                    teams[1],
                    bet[0],
                    bet[1],
                    bet[2],
                    None,
                )
                output.append(data)
            except IndexError:
                pass
            except UnboundLocalError:
                pass

        return output

    @staticmethod
    def match_datetime(match):
        """finds the gametime for each matchup."""

        try:
            mdt = match.find("span", "period hidden-xs").text

            try:
                mdt = parser.parse(mdt)
                return mdt

            # this catches any live matches and sets the gametime to None
            except parser.ParserError:
                pass

        # this catches errors with the gametime not existing.
        except AttributeError:
            pass    

    @staticmethod
    def teams(match):
        """finds the teams involved in each matchup."""

        teams = match.find_all("span", "name")
        matchup = [teams[0].text, teams[1].text]
        return matchup

    @staticmethod
    def favorite(match):
        """This captures the favored team in a matchup. Currently this information is not used but will be in the future."""

        try:
            favorite = match.find("h4", "competitor-name favorite").text
        except AttributeError:
            favorite = None

        return favorite

    @staticmethod
    def draw(match):
        """determines whether a draw is possible in the matchup."""

        try:
            draw = match.find("span", "draw-name").text
            return draw

        except AttributeError:
            return None

    @staticmethod
    def win_bets(match):
        """Captures the winning betting lines for each match. If a draw is possible it captures the odds for the draw."""

        if UpcomingMatch.draw(match) == "Draw":
            bet = match.find_all("sp-three-way-vertical", "market-type")

            # bet[1] is used to capture the winning bets. use '[0]' or '[2]' to capture other types of bets.
            try:
                bet = bet[1].find_all("span", "bet-price")
                bets = [bet[0].text, bet[1].text, bet[2].text]
                bets = UpcomingMatch.even(bets)
                bet = [int(bets[0]), int(bets[1]), int(bets[2])]

            # this catches any issues with the bets not existing.
            except IndexError:
                bet = [None, None, None]

        else:
            bet = match.find_all("sp-two-way-vertical", "market-type")

            try:
                bet = bet[1].find_all("span", "bet-price")
                bets = [bet[0].text, bet[1].text, None]
                bets = UpcomingMatch.even(bets)
                bet = [int(bets[0]), int(bets[1]), None]

            # this catches any issues with the bets not existing.
            except IndexError:
                bet = [None, None, None]

        return bet

    @staticmethod
    def even(bets):
        """Catches any even bets and turns them into an integer value."""

        output = []
        for bet in bets:
            if bet == " EVEN ":
                bet = 100

            output.append(bet)

        return output

class MatchResult:
    '''This class represents and individual match result. Each method gathers one piece of match information.
        Takes soup object.'''

    def __init__(self, sport, match_date):
        self.sport = sport
        self.date = match_date
        self.html = self.scrape()
         
    def scrape(self):
        '''Scrapes the results given the sport.'''

        driver = webdriver.Chrome(options=options)
        driver.get(f"https://scores.bovada.lv/en/{self.sport}/events?date={self.date}")

        time.sleep(20)

        html = driver.page_source

        return html
    
    def soup(self):
        return BeautifulSoup(self.html, 'html.parser')

    def match_date(self):
        try:
            match_date = self.soup().find('span', 'date').text
            match_date = datetime.datetime.strptime(match_date, '%d.%m.%Y').strftime('%Y-%m-%d')
            return match_date

        except AttributeError:
            pass
    
    def matches(self):
        '''Takes the scraped match results html and makes a soup of each match.'''

        matches = self.soup().find_all("div", "event__container")
        return matches

    def results(self):
        '''Takes the list of matches and returns the gamedate, teams, winner, and status as a tuple.'''

        results = []

        match_date = self.match_date()

        for match in self.matches():
            status = MatchResult.status(match)
            if status == "Unfinished":
                pass

            elif status == " Canc.":
                winner = "Canc."

            else:
                teams = MatchResult.teams(match)
                winner = MatchResult.winner(match)
            
            output = (str(match_date), teams[0], teams[1], winner)
            results.append(output)

        return results

    @staticmethod
    def winner(match):
        '''Takes an individual match and returns the winner. Checks if the match was cancelled if no winner is found.
            If the match wasn't cancelled and there is no winner, it returns "Draw".'''

        try:
            winner = match.find("a", "link winner").text
            winner = MatchResult.swap_names(winner)

        except AttributeError:
                winner = "Draw"

        return winner

    @staticmethod
    def status(match):
        '''Takes an individual match and returns the status. Returns "Unfinished" if the match hasn't concluded.'''

        finished = set([' AOT', ' AW', ' Fin.', ' Fin pen.', ' fin', ' Canc.', ' Fin ext.'])

        status = match.find("div", "event__cell flex flex--centered event__cell--status").text

        if status in finished:
            return status
        
        else:
            return 'Unfinished'        

    @staticmethod
    def teams(match):
        '''Takes an individual match and returns the teams involved in the match.'''
        teams = match.find_all("a", "link")
        team_list = []

        for team in teams:
            team = team.text
            team = MatchResult.swap_names(team)
            team_list.append(team)

        return team_list

    @staticmethod
    def swap_names(team):
        swap_names = {
            'Los Angeles Clippers':'L.A. Clippers', 
            'Belleville Senators':'Binghamton Senators'
        }

        if team in swap_names:
            return swap_names.get(team)

        else:
            return team
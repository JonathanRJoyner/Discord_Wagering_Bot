import db
import time
import schedule
from datetime import datetime

upcoming_leagues = ['soccer/major-league-soccer/mls', 'soccer/england-premier-league', 'basketball/nba', 'hockey/nhl', 'hockey/united-states/ahl']

sports_results = ['soccer', 'basketball', 'hockey']

def upcoming():
  for league in upcoming_leagues:
    db.get_matches(league)
  print(f'{datetime.now()}: ran upcoming()')

def results():
  for sport in sports_results:
    db.get_results(sport)
  print(f'{datetime.now()}: ran results()')

def update_matches():
  db.replace_result_teams()
  db.update_winner()
  db.replace_winner()
  print(f'{datetime.now}: ran update_matches()')

def update_users():
  db.update_payout()
  db.pay_users()
  print(f'{datetime.now()}: ran update_users()')

def test():
  print(datetime.now())

schedule.every().hour.do(upcoming)
schedule.every().day.at("09:00").do(results)
schedule.every().day.at("09:05").do(update_matches)
schedule.every().day.at("09:10").do(update_users)
schedule.every().second.do(test)

while True:
  schedule.run_pending()
  time.sleep(1)

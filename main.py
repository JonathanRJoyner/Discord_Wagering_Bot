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
    update_matches()
    update_users()
  print(f'{datetime.now()}: ran results()')

def update_matches():
  db.replace_result_teams()
  db.update_winner()
  db.replace_winner()
  print(f'{datetime.now()}: ran update_matches()')

def update_users():
  db.update_payout()
  db.pay_users()
  db.increase_all_user_amounts(1000)
  print(f'{datetime.now()}: ran update_users()')

schedule.every().hour.do(upcoming)
schedule.every(3).hours.do(results)

while True:
  schedule.run_pending()
  time.sleep(1)

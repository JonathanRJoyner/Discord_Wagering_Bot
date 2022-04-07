import db
import time
import schedule
from datetime import datetime, timedelta

upcoming_leagues = ['soccer/major-league-soccer/mls', 'soccer/england-premier-league', 'basketball/nba', 'hockey/nhl', 'hockey/united-states/ahl', 'esports/dota-2']

sports_results = ['soccer', 'basketball', 'hockey', 'dota2']


def upcoming():
  for league in upcoming_leagues:
    db.get_matches(league)
  print(f'{datetime.now()}: ran upcoming()')

def results():
  match_date = (datetime.now() - timedelta(hours = 1)).date()

  for sport in sports_results:
    db.get_results(sport, match_date)
  update_matches()
  update_users()
  print(f'{datetime.now()}: ran results()')

def update_matches():
  db.update_winner()
  db.replace_winner()
  print(f'{datetime.now()}: ran update_matches()')

def update_users():
  db.update_payout()
  db.pay_users()
  print(f'{datetime.now()}: ran update_users()')

schedule.every().hour.do(upcoming)
schedule.every().hour.do(results)
schedule.every().day.do(db.increase_all_user_amounts)

if __name__=="__main__":
  upcoming()

while True:
  schedule.run_pending()
  time.sleep(1)
import schedule
import db
import time
from datetime import datetime

def update():
    db.get_matches()
    db.get_results()
    db.replace_result_teams()
    db.update_results()
    db.replace_winner()
    db.update_payout()
    db.pay_users()
    print(datetime.now())

schedule.every(3).hours.do(update)

while True:
    schedule.run_pending()
    time.sleep(1)

import sqlite3
import scrape


#create a connection to the bets database
con = sqlite3.connect("bets.db")
cur = con.cursor()

#create necessary tables if the tables to not exist
cur.execute(
    """CREATE TABLE IF NOT EXISTS matches
                (sport, league, gamedate, gametime, team1, team2, bet1, bet2, draw, winner,
                PRIMARY KEY(gamedate, team1, team2))"""
)

cur.execute(
    """CREATE TABLE IF NOT EXISTS users
                (user, name, amount,
                PRIMARY KEY(user))"""
)

cur.execute(
    """CREATE TABLE IF NOT EXISTS user_bets
                (user, league, gamedate, team1, team2, team_choice, bet_amount, reward, payout, status)"""
)

cur.execute(
    """CREATE TABLE IF NOT EXISTS results
                (gamedate, team1, team2, winner, status,
                PRIMARY KEY(gamedate, team1, team2))"""
)


def get_matches(sport):
    '''Scrapes the upcoming matches and inserts them into the matches table.
        Replaces betting data if match already exists.'''

    upcoming = scrape.UpcomingMatch(sport).upcoming()

    upcoming = [item for item in upcoming if item[2] is not None]

    with con:
        cur.executemany(
            """INSERT OR REPLACE INTO matches (sport, league, gamedate, gametime, team1, team2, bet1, bet2, draw, winner) 
                            VALUES (?,?,?,?,?,?,?,?,?,?)""",
            upcoming,
        )
    
    #remove away/home goals betting line from NHL teams.
    cur.execute('''DELETE FROM matches 
                    WHERE team1 = "Away Goals"
                    OR team2 = "Home Goals"''')
    con.commit()


def get_results(sport, match_date):
    '''Scrapes results and inserts data into the results table.
        Deletes any results older than 2 days.'''

    results = scrape.MatchResult(sport, match_date).results()

    with con:
        cur.executemany(
            """INSERT OR IGNORE INTO results (gamedate, team1 ,team2, winner)
                            VALUES (?, ?, ?, ?)""",
            results,
        )

    cur.execute('''DELETE FROM results 
                    WHERE gamedate <= DATE("now","-2 days")''')
    con.commit()

def update_winner():
    '''Updates the matches table with the winner results if a winner exists.'''

    cur.execute(
        """UPDATE matches 
                    SET winner = (SELECT winner 
                                    FROM results
                                    WHERE (DATE(matches.gamedate) = DATE(results.gamedate)
                                            OR DATE(matches.gamedate, "+1 day") = DATE(results.gamedate))
                                    AND ( substr(matches.team1, 1, 5) IN( substr(results.team1, 1, 5), substr(results.team2, 1, 5)))
                                    AND ( substr(matches.team2, 1, 5) IN(substr(results.team1, 1, 5), substr(results.team2, 1, 5))))
                    WHERE winner IS NULL"""
    )
    con.commit()

def sports():
    '''Returns a list of sports from the matches table.'''
    
    data = cur.execute("""SELECT DISTINCT sport FROM matches""").fetchall()
    return [item[0] for item in data]


def leagues(sport):
    '''Takes a sport and returns a list of leagues in the matches table.'''

    data = cur.execute(
        """SELECT DISTINCT league FROM matches WHERE sport = ?""", (sport,)
    ).fetchall()
    return [item[0] for item in data]


def matches(league):
    '''Takes a league and returns a list of matches from the matches table.'''

    data = cur.execute(
        """SELECT * FROM matches WHERE league = ?
                        AND DATETIME(gamedate||gametime) > DATETIME('now',  'localtime') 
                        AND bet1 IS NOT NULL
                        AND bet2 IS NOT NULL
                        AND winner IS NULL""",
        (league,),
    ).fetchall()
    return [item for item in data]


def bets(match):
    '''Takes a match and returns the bets from the matches table.'''

    match = match.split(" | ")[0]
    match = match.split(" vs. ")
    team1 = match[0]
    team2 = match[1]

    data = cur.execute(
        """SELECT * FROM matches WHERE team1 = ?
                        AND team2 = ?
                        AND DATETIME(gamedate||gametime) >= DATETIME('now', 'localtime')
                        AND winner IS NULL""",
        (team1, team2),
    ).fetchall()

    data = data[0]
    bet1 = f"{data[4]} | {data[6]}"
    bet2 = f"{data[5]} | {data[7]}"

    if data[8] is not None:
        bet3 = f"Draw | {data[8]}"
        return [bet1, bet2, bet3]

    else:
        return [bet1, bet2]


def user_lookup(user):
    '''Returns the user details given id and name. 
        If the user does not exist, registers user with 1000 points.'''

    data = cur.execute("""SELECT * FROM users WHERE user = ?""", (user[0],)).fetchall()

    if len(data) == 0:
        cur.execute(
            """INSERT INTO users (user, name, amount)
                        VALUES (?, ?, 1000)""",
            (user[0], user[1]),
        )
        con.commit()
        return [(user[0], user[1], 1000)]

    elif user[1] != data[0][1]:
        cur.execute("""UPDATE users SET name = ? WHERE user = ?""", (user[1], user[0]))
        cur.commit()
        return [(user[0], user[1], data[2])]

    else:
        return data

def unpaid_bets_lookup(user):
    '''Takes a user id and returns all unpaid bets for that user.'''
    bets = cur.execute('''SELECT * FROM user_bets
                            WHERE user = ?
                            AND status IS NULL''', (user,)).fetchall()

    return bets

def user_amount(user_id):
    '''Takes a user id and returns the user amount.'''

    amount = cur.execute(
        """SELECT amount FROM users WHERE user = ?""", (user_id,)
    ).fetchall()[0][0]

    return amount


def user_bet(data):
    '''Inserts a bet into the user_bets table with the data given from the wager interaction.
        Removes the amount wagered from the users amount.'''

    user = data[0]
    amount = user_amount(user)
    new_amount = amount - data[-4]

    cur.execute(
        """INSERT INTO user_bets (user, league, gamedate, team1, team2, team_choice, bet_amount, reward, payout, status)
                    VALUES(?,?,?,?,?,?,?,?,?,?)""",
        data,
    )

    cur.execute(
        """UPDATE users SET amount = ?
                    WHERE user = ?""",
        (new_amount, user),
    )

    con.commit()

def replace_winner():
    '''The winner of a match could have a different name based on the results table.
        This changes the name to the original name used in the matches table.'''
    
    cur.execute('''UPDATE matches
                        SET winner = CASE
                                        WHEN (substr(team1, 1, 5) = substr(winner, 1, 5))
                                        THEN team1
                                        WHEN (substr(team2, 1, 5) = substr(winner, 1, 5))
                                        THEN team2
                                        ELSE winner
                                     END''')
    con.commit()

def update_payout():
    '''Updates the payout amount in player_bets table. If the team_choice team is a winner, 
        payout is the bet_amount + reward. If the match is cancelled, the bet_amount is returned.
        If there is no winner, the payout is unchanged. Otherwise, the payout is 0.'''

    cur.execute(
        """UPDATE user_bets
                    SET payout = CASE 
                                    WHEN (SELECT winner FROM matches
                                        WHERE DATE(matches.gamedate) = DATE(user_bets.gamedate)
                                        AND matches.team1 = user_bets.team1) = user_bets.team_choice
                                    THEN bet_amount + reward
                                    WHEN (SELECT winner FROM matches
                                        WHERE DATE(matches.gamedate) = DATE(user_bets.gamedate)
                                        AND matches.team1 = user_bets.team1) = " Canc."
                                    THEN bet_amount
                                    WHEN (SELECT winner FROM matches
                                        WHERE DATE(matches.gamedate) = DATE(user_bets.gamedate)
                                        AND matches.team1 = user_bets.team1) IS NULL
                                    THEN NULL
                                    ELSE 0 
                                 END"""
    )
    con.commit()


def pay_users():
    """Adds the payout amount in user_bets to the users amount. Changes status to PAID"""

    cur.execute(
        """UPDATE users
                    SET amount = CASE 
                                    WHEN (SELECT sum(payout) FROM user_bets
                                        WHERE users.user = user_bets.user
                                        AND status IS NULL) IS NOT NULL
                                    THEN (SELECT sum(payout) FROM user_bets
                                        WHERE users.user = user_bets.user
                                        AND status IS NULL) + amount
                                    ELSE amount
                                 END"""
    )

    cur.execute(
        """UPDATE user_bets
                    SET status = CASE
                                    WHEN payout IS NOT NULL
                                    THEN "PAID"
                                    ELSE NULL
                                 END"""
    )

    con.commit()

def increase_all_user_amounts():
    '''Adds 1000 to all users in the users table.'''

    cur.execute('''UPDATE users
                    SET amount = amount + ?''', (1000,))

    con.commit()

def top_10_users():

    top_users = cur.execute(
        '''SELECT name, amount FROM users
            ORDER BY amount DESC
            LIMIT 10;'''
        ).fetchall()

    return top_users
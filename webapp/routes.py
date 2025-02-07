from flask import render_template, render_template_string, g, request
from markupsafe import Markup, escape
from webapp import app
import sqlite3, datetime, pprint # type: ignore

DATABASE = 'RA.db'

def make_dicts(cursor, row):
    return dict((cursor.description[idx][0], value)
                for idx, value in enumerate(row))

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    #db.row_factory = sqlite3.Row
    db.row_factory = make_dicts
    return db

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def safereplace(value, repllist):
    safe_value = str(escape(value))
    
    for item in repllist:
        safe_value = safe_value.replace(item[0], item[1])

    return Markup(safe_value)

def titlebadges(title):
    return safereplace(title, [["~Prototype~", '<span class="badge bg-primary">Prototype</span>'], ["~Hack~", '<span class="badge bg-primary">Hack</span>'], ["~Demo~", '<span class="badge bg-primary">Demo</span>'], ["~Homebrew~", '<span class="badge bg-primary">Homebrew</span>']])

def get_want_to_play_games(username = None):
    query = "SELECT uw.GameID, uw.GameTitle, uw.ConsoleID, uw.ImageIcon, u.User, g.ID FROM userwantstoplay uw INNER JOIN users u ON uw.UserID = u.ID LEFT JOIN games g on uw.GameID = g.ID"
    args = []
    if username != None:
        query += " WHERE u.User = ?"
        args.append(username)
    #UserID INTEGER, GameID INTEGER, GameTitle TEXT, ConsoleID INTEGER, ImageIcon TEXT
    wtpg = query_db(query, args)
    #pprint.pprint(wtpg, indent=4)
    wtpgdone = {}
    for item in wtpg:
        if item["GameID"] in wtpgdone:
            wtpgdone[item["GameID"]]["Users"].append(item["User"])
        else:
            wtpgdone[item["GameID"]] = {"ID": item["ID"], "Title": titlebadges(item["GameTitle"]) , "ConsoleID": item["ConsoleID"], "ImageIcon": item["ImageIcon"], "Users": [item["User"]]}
    wtpgdone = sorted(wtpgdone.values(), key=lambda item: (-len(item.get("Users", [])), item.get("Title", "").startswith("<span"), item.get("Title", "")))
    return wtpgdone

def get_mastered_games():
    #mastered = query_db("SELECT g.ID, g.Title, g.ImageIcon, u.User FROM games g INNER JOIN users u ON uw.UserID = u.ID LEFT JOIN games g on uw.GameID = g.ID;")
    mastered = query_db("SELECT g.Title, g.ID, g.ImageIcon, u.User FROM usergames ug INNER JOIN users u ON ug.UserID = u.ID LEFT JOIN games g ON ug.GameID = g.ID WHERE HighestAwardKind = 'mastered';")
    mastereddone = {}
    for item in mastered:
        if item["ID"] in mastereddone:
            mastereddone[item["ID"]]["Users"].append(item["User"])
        else:
            mastereddone[item["ID"]] = {"ID": item["ID"], "Title": titlebadges(item["Title"]), "ImageIcon": item["ImageIcon"], "Users": [item["User"]]}
    mastereddone = sorted(mastereddone.values(), key=lambda item: (-len(item.get("Users", [])), item.get("Title", "").startswith("<span"), item.get("Title", "")))
    return mastereddone

def get_set_requests():
    #UserID INTEGER, GameID INTEGER, GameTitle TEXT, ConsoleID INTEGER, ImageIcon TEXT
    setrequests = query_db("SELECT sr.GameID, sr.GameTitle, sr.ConsoleID, sr.ImageIcon, u.User, g.ID FROM setrequests sr INNER JOIN users u ON sr.UserID = u.ID LEFT JOIN games g on sr.GameID = g.ID;")
    #pprint.pprint(wtpg, indent=4)
    setrequestsdone = {}
    for item in setrequests:
        if item["GameID"] in setrequestsdone:
            setrequestsdone[item["GameID"]]["Users"].append(item["User"])
        else:
            setrequestsdone[item["GameID"]] = {"ID": item["ID"], "Title": titlebadges(item["GameTitle"]) , "ConsoleID": item["ConsoleID"], "ImageIcon": item["ImageIcon"], "Users": [item["User"]]}
    setrequestsdone = sorted(setrequestsdone.values(), key=lambda item: (-len(item.get("Users", [])), item.get("Title", "").startswith("<span"), item.get("Title", "")))
    return setrequestsdone

def get_user_leaderboards(username = None):
    query = "SELECT ulb.GameID, ulb.FormattedScore, ulb.Rank, ulb.DateUpdated, g.Title, lb.Title, lb.Description, lb.RankAsc, lb.Format, u.User FROM userleaderboards ulb INNER JOIN users u ON ulb.UserID = u.ID LEFT JOIN leaderboards lb ON ulb.EntryID = lb.ID LEFT JOIN games g on lb.GameID = g.ID"
    args = []
    if username != None:
        query += " WHERE u.User = ?"
        args.append(username)
    query += " ORDER BY lb.ID"
    leaderboards = query_db(query, args)
    return leaderboards

def get_latest_masteries(username = None):
    query = "SELECT ug.UserID, ug.GameID, ug.HighestAwardKind, ug.HighestAwardDate, u.User, u.UserPic, g.Title, g.ImageIcon FROM usergames ug INNER JOIN users u ON ug.UserID = u.ID LEFT JOIN games g ON ug.GameID = g.ID WHERE ug.HighestAwardKind = 'mastered'"
    args = []
    if username != None:
        query += " AND u.User = ?"
        args.append(username)
    query += " ORDER BY ug.HighestAwardDate DESC"
    masteries = query_db(query, args)
    for item in masteries:
        item["Users"] = [item["User"]]
    return masteries

def pointsgraph(username = None):
    now = datetime.datetime.now()
    start_of_today = datetime.datetime(now.year, now.month, now.day)
    seven_days_ago = (start_of_today - datetime.timedelta(days=6))

    seven_days_ago_ts = int(seven_days_ago.timestamp())
    now_ts = int(now.timestamp())

    args = [seven_days_ago_ts, now_ts]
    query = """
WITH RECURSIVE date_range(day) AS (
    SELECT DATE('now', '-6 days') -- Start from 7 days ago (inclusive of today)
    UNION ALL
    SELECT DATE(day, '+1 day')
    FROM date_range
    WHERE day < DATE('now') -- Include up to today
),
daily_scores AS (
    SELECT 
        DATE(ua.DateEarnedHardcore, 'unixepoch') AS day,
        SUM(a.Points) AS daily_total
    FROM 
        userachievements ua
        JOIN achievements a ON ua.GameID = a.GameID AND ua.AchievementID = a.ID
        JOIN users u ON ua.UserID = u.ID
    WHERE 
        DateEarnedHardcore >= ? AND DateEarnedHardcore <= ?
        {username_condition}
    GROUP BY 
        DATE(DateEarnedHardcore, 'unixepoch')
)
SELECT 
    dr.day,
    COALESCE(ds.daily_total, 0) AS daily_total,
    SUM(COALESCE(ds.daily_total, 0)) OVER (ORDER BY dr.day) AS cumulative_score
FROM 
    date_range dr
LEFT JOIN 
    daily_scores ds ON dr.day = ds.day
ORDER BY 
    dr.day"""

    if username:
        username_condition = "AND u.User = ?"
        args.append(username)
    else:
        username_condition = ""
    
    query = query.format(username_condition=username_condition)

    graphdata = query_db(query, args)
    day = []
    daily = []
    cumulative = []
    for item in graphdata:
        day.append(item["day"])
        daily.append(str(item["daily_total"]))
        cumulative.append(str(item["cumulative_score"]))
    day = '", "'.join(day)
    daily = ", ".join(daily)
    cumulative = ", ".join(cumulative)
    return {"day": day, "daily": daily, "cumulative": cumulative}

def activity_feed(type = "combined", username = None):
    # 'Type': 'achievement' or 'leaderboard'
    # 'User': Username
    # 'aTitle': Achievement/leaderboard title
    # 'Description': Achievement/leaderboard description
    # 'Icon1': Game icon in both cases
    # 'Icon2': Achievement icon for Achievements... uh, idk, user profile pic for leaderboards?
    # 'gTitle': Game name
    # 'ID': Game ID
    # 'DateEarned': Date Earned
    # 'FormattedScore': Leaderboard score, None for achievements
    # 'Rank': Global leaderboard rank, None for achievements
    # 'LocalRank': Local (rawf instance) leaderboard rank, None for achievements
    args=[]
    username_condition = ""
    if username != None:
        args = [username]
    if type == "achievements":
        query = """SELECT
  u.User,
  a.Title AS aTitle,
  a.Description,
  g.ImageIcon AS Icon1,
  a.BadgeName AS Icon2,
  g.Title AS gTitle,
  g.ID,
  ua.DateEarned
FROM
  userachievements ua
  INNER JOIN achievements a ON a.ID = ua.AchievementID
  INNER JOIN users u ON u.ID = ua.UserID
  INNER JOIN games g ON g.ID = ua.GameID
{username_condition}
ORDER BY ua.DateEarned DESC LIMIT 50;"""
        if username:
            username_condition = "WHERE u.User = ?"
        query = query.format(username_condition=username_condition)
        resp = query_db(query, args=args)
        for item in resp:
            item["Type"] = "achievement"
            item["gTitle"] = titlebadges(item["gTitle"])
            item["DateEarnedts"] = item["DateEarned"]
            item["DateEarned"] = datetime.datetime.fromtimestamp(item["DateEarned"]).strftime("%Y-%m-%d %H:%M:%S")
            item['FormattedScore'] = None
            item['Rank'] = None
            item['LocalRank'] = None
        return resp
    elif type == "leaderboards":
        query = """SELECT 
  u.User,
  lb.Title AS aTitle,
  lb.Description,
  ulb.GameID,
  g.ImageIcon AS Icon1,
  u.UserPic AS Icon2,
  g.Title AS gTitle,
  g.ID,
  ulb.DateUpdated AS DateEarned,
  ulb.FormattedScore, 
  ulb.Rank,     
  lb.RankAsc, 
  lb.Format
FROM
  userleaderboards ulb 
  INNER JOIN users u ON ulb.UserID = u.ID 
  LEFT JOIN leaderboards lb ON ulb.EntryID = lb.ID 
  LEFT JOIN games g on lb.GameID = g.ID 
{username_condition}
ORDER BY ulb.DateUpdated DESC LIMIT 50;"""
        if username:
            username_condition = "WHERE u.User = ?"
        query = query.format(username_condition=username_condition)
        resp = query_db(query, args=args)
        for item in resp:
            item["Type"] = "leaderboard"
            item["gTitle"] = titlebadges(item["gTitle"])
            item["DateEarnedts"] = item["DateEarned"]
            item["DateEarned"] = datetime.datetime.fromtimestamp(item["DateEarned"]).strftime("%Y-%m-%d %H:%M:%S")
        return resp
    elif type == "combined":
        resp1 = activity_feed("achievements", username)
        resp2 = activity_feed("leaderboards", username)
        #Combine results here
        return sorted(resp1 + resp2, key=lambda x: x["DateEarnedts"], reverse=True)[:50]
    else:
        return None


@app.route('/')
@app.route('/index')
def index():
    sqlusers = query_db('select * from users ORDER BY TotalPoints DESC')
    achievements = activity_feed("combined")
    wtpg = get_want_to_play_games()
    pg = pointsgraph()
    mastered = get_mastered_games()
    srq = get_set_requests()
    masteries = get_latest_masteries()
    cstyles = {"widget_table": {"class": "scrollable-table table-260 border rounded"},
               "widget_hunters": {"class": "scrollable-table table-300 border rounded"},
               "widget_feed": {"class": "list-group list-group-flush scrollable-list border rounded"},
               "widget_graph": {"class": "chart-container border rounded", "style": "position: relative; height:260px; width:100%;"}}
    return render_template('index.html.j2', Title='Home', users=sqlusers, achievements=achievements, wtpg=wtpg, pointsgraph=pg, mastered=mastered, srq=srq, masteries=masteries, cstyles=cstyles)

@app.route('/user/<username>')
def userpage(username):
    user = query_db("select u.*, g.Title as gTitle from users u LEFT JOIN games g ON u.LastGameID = g.ID WHERE User = ?;", args = [str(username)], one=True)
    usergames = query_db("SELECT g.ID, g.Title, g.ConsoleName, g.ConsoleID, g.ImageIcon, g.NumAchievements, ug.NumAwardedHardcore FROM usergames ug INNER JOIN games g ON g.ID = ug.GameID WHERE UserID = ? ORDER BY MostRecentAwardedDate DESC;", args = [str(user["ID"])])
    lb = get_user_leaderboards(username)
    for game in usergames:
        game["NumHardcoreUnlocksp"] = int((len(query_db("SELECT AchievementID FROM userachievements WHERE UserID = ? AND GameID = ?", args=[int(user["ID"]), int(game["ID"])])) / int(game["NumAchievements"])) * 100)
        game["Title"] = titlebadges(game["Title"])
        game["HasLeaderboards"] = any(item["GameID"] == int(game["ID"]) for item in lb)
    wtpg = get_want_to_play_games(username)
    pg = pointsgraph(username)
    feed = activity_feed(type="combined", username=username)
    cstyles = {"widget_table": {"class": "scrollable-table table-260 border rounded"},
               "widget_graph": {"class": "chart-container border rounded", "style": "position: relative; height:260px; width:100%;"},
               "widget_feed": {"class": "list-group list-group-flush scrollable-list border rounded"}}
    #pprint.pprint(usergames, indent=4)
    return render_template('user.html.j2', Title=str(username) + ' userpage', user=user, usergames=usergames, wtpg=wtpg, pointsgraph = pg, leaderboards = lb, feed=feed, cstyles = cstyles)

@app.route('/games')
def allgamespage():
    games = {item["ID"]: item for item in query_db("SELECT * FROM games ORDER BY Title")}
    usergames = query_db("SELECT ug.GameID, u.User from usergames ug JOIN users u ON ug.UserID = u.ID")
    for item in usergames:
        if "Players" in games[item["GameID"]]:
            games[item["GameID"]]["Players"].append(item["User"])
        else:
            games[item["GameID"]]["Players"] = [item["User"]]
    games = games.values()
    for item in games:
        item["Title"] = titlebadges(item["Title"])
    return render_template('games.html.j2', Title='All games', games = games)


@app.route('/game/<gameid>')
def gamepage(gameid):
    user = []
    userachievements = []
    username = request.args.get('u', None)
    game = query_db("SELECT * FROM games WHERE ID = ?;", args=[int(gameid)], one=True)
    game["Titleb"] = titlebadges(game["Title"])
    gameachievements = query_db("SELECT * FROM achievements WHERE GameID = ? ORDER BY DisplayOrder, ID;", args=[int(gameid)])
    if username:
        user = query_db("select ID, User, UserPic FROM users WHERE User = ?;", args = [str(username)], one=True)
        userachievements = query_db("SELECT AchievementID, DateEarnedHardcore FROM userachievements WHERE UserID = ? AND GameID = ?;", args = [int(user["ID"]), int(game["ID"])])
        userachievements = {item["AchievementID"]: item["DateEarnedHardcore"] for item in userachievements}
        for item in gameachievements:
            if item["ID"] in userachievements:
                item["Achieved"] = True
                item["AchievedDate"] = (datetime.datetime.fromtimestamp(userachievements[int(item["ID"])]).strftime("%Y-%m-%d %H:%M:%S"))
        gameachievements = sorted(gameachievements, key=lambda item: (-item.get("Achieved", False), item.get("DisplayOrder", "")))
    return render_template('game.html.j2', Title=str(game["Title"]), user=user, game=game, gameachievements=gameachievements)

@app.route('/widget/<widget>')
def popupwidget(widget):
    cstyles = {"widget_table": {"class": "scrollable-table border rounded"},
               "widget_graph": {"class": "chart-container border rounded", "style": "position: relative; height:100%; width:100%;"}}
    match widget:
        case "wtpg":
            data = get_want_to_play_games()
            swidget = "{% import 'widgets.html.j2' as widgets %}{{ widgets.widget_list_gamebyuser(data, cstyles.widget_table) }}"
        case "weeklypoints":
            data = pointsgraph()
            swidget = "{% import 'widgets.html.j2' as widgets %}<script src='https://cdn.jsdelivr.net/npm/chart.js'></script>{{ widgets.widget_pointsgraph(data, cstyles.widget_graph) }}"
        case "mastered":
            data = get_mastered_games()
            swidget = "{% import 'widgets.html.j2' as widgets %}{{ widgets.widget_list_gamebyuser(data, cstyles.widget_table) }}"
        case "srq":
            data = get_set_requests()
            swidget = "{% import 'widgets.html.j2' as widgets %}{{ widgets.widget_list_gamebyuser(data, cstyles.widget_table) }}"
    return render_template('popup.html.j2', widget=render_template_string(swidget, data=data, cstyles=cstyles))
# weeklypoints
# mastered
# srq


@app.route("/api/update", methods=["POST"])
def update_page():
    cstyles = {"widget_hunters": {"class": "scrollable-table table-300 border rounded"},
            "widget_feed": {"class": "list-group list-group-flush scrollable-list border rounded"}}
    type = request.get_json()
    type = type["type"]
    match type:
        case "hunters-all":
            sqlusers = query_db('select * from users ORDER BY TotalPoints DESC')
            return render_template_string("{% import 'widgets.html.j2' as widgets %}{{ widgets.widget_hunters(data, cstyles.widget_hunters) }}", data = sqlusers, cstyles=cstyles)
        case "hunters-week":
            sqlusers = query_db("""WITH current_week AS (
    SELECT 
        ua.UserID,
        u.User,
        u.UserPic,
        u.Permissions,
        ua.GameID,
        ua.AchievementID,
        a.Points,
        DateEarnedHardcore
    FROM 
        userachievements ua
    INNER JOIN achievements a ON ua.AchievementID = a.ID
    INNER JOIN users u ON ua.UserID = u.ID
    WHERE 
        DateEarnedHardcore >= UNIXEPOCH('now', 'weekday 0', '-6 days', 'start of day') AND
        DateEarnedHardcore < UNIXEPOCH('now', 'weekday 0', '+1 day', 'start of day')
)
SELECT 
    User,
    UserID,
    UserPic,
    Permissions,
    SUM(Points) AS TotalPoints,
    COUNT(DISTINCT GameID) AS UniqueGamesPlayed,
    COUNT(DISTINCT AchievementID) AS Achievements
FROM 
    current_week
GROUP BY 
    User, UserID, UserPic, Permissions
ORDER BY TotalPoints DESC;""")
            return render_template_string("{% import 'widgets.html.j2' as widgets %}{{ widgets.widget_hunters(data, cstyles.widget_hunters) }}", data = sqlusers, cstyles=cstyles)
        case "hunters-month":
            sqlusers = query_db("""WITH current_week AS (
    SELECT 
        ua.UserID,
        u.User,
        u.UserPic,
        u.Permissions,
        ua.GameID,
        ua.AchievementID,
        a.Points,
        DateEarnedHardcore
    FROM 
        userachievements ua
    INNER JOIN achievements a ON ua.AchievementID = a.ID
    INNER JOIN users u ON ua.UserID = u.ID
    WHERE 
        DateEarnedHardcore >= UNIXEPOCH('now', 'start of month') AND
        DateEarnedHardcore < UNIXEPOCH('now', 'start of month', '+1 month')
)
SELECT 
    User,
    UserID,
    UserPic,
    Permissions,
    SUM(Points) AS TotalPoints,
    COUNT(DISTINCT GameID) AS UniqueGamesPlayed,
    COUNT(DISTINCT AchievementID) AS Achievements
FROM 
    current_week
GROUP BY 
    User, UserID, UserPic, Permissions
ORDER BY TotalPoints DESC;""")
            return render_template_string("{% import 'widgets.html.j2' as widgets %}{{ widgets.widget_hunters(data, cstyles.widget_hunters) }}", data = sqlusers, cstyles=cstyles)
        case "feed-achievements":
            feed = activity_feed("achievements")
            return render_template_string("{% import 'widgets.html.j2' as widgets %}{{ widgets.widget_feed(data, cstyles.widget_feed) }}", data = feed, cstyles=cstyles)
        case "feed-leaderboards":
            feed = activity_feed("leaderboards")
            return render_template_string("{% import 'widgets.html.j2' as widgets %}{{ widgets.widget_feed(data, cstyles.widget_feed) }}", data = feed, cstyles=cstyles)
        case "feed-combined":
            feed = achievements = activity_feed("combined")
            return render_template_string("{% import 'widgets.html.j2' as widgets %}{{ widgets.widget_feed(data, cstyles.widget_feed) }}", data = feed, cstyles=cstyles)
        case _:
            return ""

@app.route('/what')
def what():
    return render_template('what.html.j2')

@app.route('/test')
def test():
    return render_template('test.html.j2')

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()
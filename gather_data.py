import sqlite3, requests_ratelimiter, pprint, datetime, time, schedule, os, dotenv, http.client, json # type: ignore
from requests.exceptions import ConnectionError
from RARequest import RARequest

def add_new_user(username):
    c = conn.cursor()
    print("Adding new user " + str(username) + " to database")
    RAUserProfile = RARequest.get("GetUserProfile", u = str(username))
    RAUserGames = RARequest.get("GetUserCompletionProgress", u = str(username))
    known_games = [game[0] for game in c.execute("SELECT ID FROM games").fetchall()]
    mastered_games = 0
    achievement_count = 0
    gameids = {}
    for game in RAUserGames["Results"]:
        if game["GameID"] not in known_games:
            add_new_game(game["GameID"])
        if "HighestAwardKind" in game and "mastered" in str(game["HighestAwardKind"]):
            mastered_games += 1
        #UserID INTEGER, GameID INTEGER, NumAwarded INTEGER, NumAwardedHardcore INTEGER, MostRecentAwardedDate INTEGER, HighestAwardKind TEXT, HighestAwardDate INTEGER
        c.execute("INSERT INTO usergames VALUES (?, ?, ?, ?, ?, ?, ?);",
                   [int(RAUserProfile["ID"]), 
                    int(game["GameID"]), 
                    int(game["NumAwarded"]), 
                    int(game["NumAwardedHardcore"]), 
                    int(time.mktime(datetime.datetime.strptime(game["MostRecentAwardedDate"], "%Y-%m-%dT%H:%M:%S+00:00").timetuple()) if game["MostRecentAwardedDate"] != None else 0), 
                    str(game["HighestAwardKind"]), 
                    int(time.mktime(datetime.datetime.strptime(game["HighestAwardDate"], "%Y-%m-%dT%H:%M:%S+00:00").timetuple()) if game["HighestAwardDate"] != None else 0)])
        RAProgress = RARequest.get("GetGameInfoAndUserProgress", u = str(username), g = str(game["GameID"]))
        for achievement in RAProgress["Achievements"].values():
            if "DateEarnedHardcore" in achievement or "DateEarned" in achievement:
                achievement_count += 1
                # (UserID INTEGER, GameID INTEGER, AchievementID INTEGER, DateEarnedHardcore INTEGER, DateEarned INTEGER)
                c.execute("INSERT INTO userachievements VALUES (?, ?, ?, ?, ?);", 
                          [int(RAUserProfile["ID"]), 
                           int(game["GameID"]), 
                           achievement["ID"],
                           int(time.mktime(datetime.datetime.strptime(achievement["DateEarnedHardcore"], "%Y-%m-%d %H:%M:%S").timetuple()) if "DateEarnedHardcore" in achievement else 0),
                           int(time.mktime(datetime.datetime.strptime(achievement["DateEarned"], "%Y-%m-%d %H:%M:%S").timetuple()) if "DateEarned" in achievement else 0)])
        gameids[game["GameID"]] = int(time.time())
    get_image(str(RAUserProfile["UserPic"]).split("/")[1], str(RAUserProfile["UserPic"]).split("/")[2])
    # ID INTEGER PRIMARY KEY NOT NULL, User TEXT, UserPic TEXT, MemberSince INTEGER, RichPresenceMsg TEXT, LastGameID INTEGER, ContribCount INTEGER, 
    # ContribYield INTEGER, TotalPoints INTEGER, TotalSoftcorePoints INTEGER, TotalTruePoints INTEGER, Games INTEGER, GamesMastered INTEGER, Achievements INTEGER,
    # Permissions INTEGER, Untracked INTEGER, UserWallActive INTEGER, Motto TEXT
    c.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);",
                [int(RAUserProfile["ID"]),
                str(RAUserProfile["User"]),
                str(RAUserProfile["UserPic"]), 
                int(time.time()),
                int(time.mktime(datetime.datetime.strptime(RAUserProfile["MemberSince"], "%Y-%m-%d %H:%M:%S").timetuple())), 
                str(RAUserProfile["RichPresenceMsg"]), 
                int(RAUserProfile["LastGameID"]), 
                int(RAUserProfile["ContribCount"]), 
                int(RAUserProfile["ContribYield"]), 
                int(RAUserProfile["TotalPoints"]), 
                int(RAUserProfile["TotalSoftcorePoints"]), 
                int(RAUserProfile["TotalTruePoints"]), 
                int(RAUserGames["Total"]),
                int(mastered_games),
                int(achievement_count),
                int(RAUserProfile["Permissions"]), 
                int(RAUserProfile["Untracked"]), 
                int(RAUserProfile["UserWallActive"]), 
                str(RAUserProfile["Motto"]),
                int(time.time())])
    get_user_wants_to_play(username)
    get_user_set_requests(username)
    get_user_leaderboards(username, gameids)
    conn.commit()
    print("Finished adding user " + str(username) + " to database")

def add_new_game(gameid):
    print("Querying game " + str(gameid))
    RAGame = RARequest.get("GetGameExtended", i = str(gameid))
    RAGamelb = RARequest.get("GetGameLeaderboards", i = str(gameid))
    get_image(str(RAGame["ImageIcon"]).split("/")[1], str(RAGame["ImageIcon"]).split("/")[2])
    get_image(str(RAGame["ImageTitle"]).split("/")[1], str(RAGame["ImageTitle"]).split("/")[2])
    get_image(str(RAGame["ImageIngame"]).split("/")[1], str(RAGame["ImageIngame"]).split("/")[2])
    get_image(str(RAGame["ImageBoxArt"]).split("/")[1], str(RAGame["ImageBoxArt"]).split("/")[2])
    # with open("debuggames.txt", "a+", encoding = "utf-8") as f:
    #     pprint.pprint(RAGame, f, indent = 4, sort_dicts = False)
    print("Adding new game " + str(RAGame["Title"]) + " to database")
    c = conn.cursor()
    c.execute("INSERT INTO games VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);",
              [RAGame["ID"],
               RAGame["Title"],
               RAGame["ConsoleID"],
               RAGame["ConsoleName"],
               RAGame["ForumTopicID"],
               RAGame["Flags"],
               RAGame["ImageIcon"],
               RAGame["ImageTitle"],
               RAGame["ImageIngame"],
               RAGame["ImageBoxArt"],
               RAGame["Publisher"],
               RAGame["Developer"],
               RAGame["Genre"],
               RAGame["Released"],
               RAGame["ReleasedAtGranularity"],
               RAGame["GuideURL"],
               int(time.mktime(datetime.datetime.strptime(RAGame["Updated"], "%Y-%m-%dT%H:%M:%S.000000Z").timetuple())),
               RAGame["ParentGameID"],
               RAGame["NumAchievements"]])
    for achievement in RAGame["Achievements"]:
        get_image("Badge", str(RAGame["Achievements"][achievement]["BadgeName"]))
        c.execute("INSERT INTO achievements VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);",
                  [RAGame["ID"],
                   RAGame["Achievements"][achievement]["ID"],
                   RAGame["Achievements"][achievement]["Title"],
                   RAGame["Achievements"][achievement]["Description"],
                   RAGame["Achievements"][achievement]["Points"],
                   RAGame["Achievements"][achievement]["TrueRatio"],
                   RAGame["Achievements"][achievement]["Author"],
                   RAGame["Achievements"][achievement]["DateModified"],
                   RAGame["Achievements"][achievement]["DateCreated"],
                   RAGame["Achievements"][achievement]["BadgeName"],
                   RAGame["Achievements"][achievement]["DisplayOrder"],
                   RAGame["Achievements"][achievement]["type"]])
    print("Added " + str(len(RAGame["Achievements"])) + " achievements for " + str(RAGame["Title"]) + " to database")
    #ID INTEGER PRIMARY KEY NOT NULL, GameID INTEGER, Title TEXT, Description TEXT, RankAsc INTEGER, Format TEXT
    for entry in RAGamelb["Results"]:
        c.execute("INSERT INTO leaderboards VALUES (?, ?, ?, ?, ?, ?);",
                  [int(entry["ID"]),
                   int(gameid),
                   str(entry["Title"]),
                   str(entry["Description"]),
                   int(entry["RankAsc"]),
                   str(entry["Format"])])
    print("Added " + str(len(RAGamelb["Results"])) + " leaderboards for " + str(RAGame["Title"]) + " to database")
    conn.commit()

def update_user(username):
    print("Fetching updates for " + str(username))
    updategames = {}
    c = conn.cursor()
    user = c.execute("SELECT ID, LastUpdate, UserPicLastUpdate from users WHERE User = '" + str(username) + "'").fetchone()
    userid = user[0]
    userlastupdate = user[1]
    userlastha = [aa for aa in c.execute("SELECT DateEarnedHardcore from userachievements WHERE UserID = '" + str(userid) + "' ORDER BY DateEarnedHardcore DESC LIMIT 1").fetchone()]
    userlastsa = [aa for aa in c.execute("SELECT DateEarned from userachievements WHERE UserID = '" + str(userid) + "' ORDER BY DateEarned DESC LIMIT 1").fetchone()]
    userlasta = max(userlastha[0], userlastsa[0])
    RAUserRecentAchievements = RARequest.get("GetUserRecentAchievements", u = str(username), m = "30")
    for item in RAUserRecentAchievements:
        date = int(time.mktime(datetime.datetime.strptime(item["Date"], "%Y-%m-%d %H:%M:%S").timetuple()))
        if date > userlasta:
            print("Adding new achievement " + str(item["Title"]) + " from " + str(item["GameTitle"]))
            if int(item["GameID"]) not in updategames:
                updategames[int(item["GameID"])] = int(date)
            record = c.execute("SELECT * FROM userachievements WHERE UserID = ? AND GameID = ? AND AchievementID = ?;", [int(userid), int(item["GameID"]), int(item["AchievementID"])]).fetchall()
            if record:
                if item["HardcoreMode"] == 0:
                    c.execute("UPDATE userachievements SET DateEarned = ? WHERE UserID = ? AND GameID = ? AND AchievementID = ?;", [int(date), int(userid), int(item["GameID"]), int(item["AchievementID"])])
                else:
                    c.execute("UPDATE userachievements SET DateEarnedHardcore = ? WHERE UserID = ? AND GameID = ? AND AchievementID = ?;", [int(date), int(userid), int(item["GameID"]), int(item["AchievementID"])])
            else:
                if item["HardcoreMode"] == 0:
                    c.execute("INSERT INTO userachievements VALUES (?, ?, ?, ?, ?);", 
                          [int(userid), 
                           int(item["GameID"]), 
                           int(item["AchievementID"]),
                           0,
                           int(date)])
                else:
                    c.execute("INSERT INTO userachievements VALUES (?, ?, ?, ?, ?);", 
                          [int(userid), 
                           int(item["GameID"]), 
                           int(item["AchievementID"]),
                           int(date),
                           int(date)])
    if updategames or int(time.time()) - userlastupdate > 24 * 60 * 60:
        print("Updating profile for " + str(username))
        games = [aa[0] for aa in c.execute("SELECT ID FROM games;").fetchall()]
        usergames = [aa for aa in c.execute("SELECT GameID, HighestAwardKind FROM usergames WHERE UserID = ?;", [int(userid)]).fetchall()]
        for game in updategames:
            if game not in games:
                add_new_game(int(game))
            RAProgress = RARequest.get("GetGameInfoAndUserProgress", u = str(username), g = str(game), a = "1")
            if any(lst[0] == game for lst in usergames) == False:
                c.execute("INSERT INTO usergames VALUES (?, ?, ?, ?, ?, ?, ?);",
                   [int(userid), 
                    int(game), 
                    int(RAProgress["NumAwardedToUser"]), 
                    int(RAProgress["NumAwardedToUserHardcore"]), 
                    int(updategames[game]), 
                    str(RAProgress["HighestAwardKind"]) if "HighestAwardKind" in RAProgress else str("asdf"),
                    int(time.mktime(datetime.datetime.strptime(RAProgress["HighestAwardDate"], "%Y-%m-%dT%H:%M:%S+00:00").timetuple())) if "HighestAwardDate" in RAProgress and RAProgress["HighestAwardDate"] != None else 0])
            else:
                #UserID INTEGER, GameID INTEGER, NumAwarded INTEGER, NumAwardedHardcore INTEGER, MostRecentAwardedDate INTEGER, HighestAwardKind TEXT, HighestAwardDate INTEGER
                c.execute("UPDATE usergames SET NumAwarded = ?, NumAwardedHardcore = ?, MostRecentAwardedDate = ?, HighestAwardKind = ?, HighestAwardDate = ? WHERE UserID = ? AND GameID = ?;",
                          [int(RAProgress["NumAwardedToUser"]),
                           int(RAProgress["NumAwardedToUserHardcore"]),
                           int(updategames[game]),
                           str(RAProgress["HighestAwardKind"]) if "HighestAwardKind" in RAProgress else str("asdf"),
                           int(time.mktime(datetime.datetime.strptime(RAProgress["HighestAwardDate"], "%Y-%m-%dT%H:%M:%S+00:00").timetuple())) if "HighestAwardDate" in RAProgress and RAProgress["HighestAwardDate"] != None else 0,
                           int(userid),
                           int(game)])
        mastered_games = 0
        achievement_count = len(c.execute("SELECT AchievementID FROM userachievements WHERE UserID = ?;", [int(userid)]).fetchall())
        usergames = [aa for aa in c.execute("SELECT GameID, HighestAwardKind FROM usergames WHERE UserID = ?;", [int(userid)]).fetchall()]
        for game in usergames:
            if "mastered" in str(game[1]):
                mastered_games += 1
        RAUserProfile = RARequest.get("GetUserProfile", u = str(username))
        # ID INTEGER PRIMARY KEY NOT NULL, User TEXT, UserPic TEXT, MemberSince INTEGER, RichPresenceMsg TEXT, LastGameID INTEGER, ContribCount INTEGER, 
        # ContribYield INTEGER, TotalPoints INTEGER, TotalSoftcorePoints INTEGER, TotalTruePoints INTEGER, Games INTEGER, GamesMastered INTEGER, Achievements INTEGER,
        # Permissions INTEGER, Untracked INTEGER, UserWallActive INTEGER, Motto TEXT
        c.execute("UPDATE users SET RichPresenceMsg = ?, LastGameID = ?, ContribCount = ?, ContribYield = ?, TotalPoints = ?, TotalSoftcorePoints = ?, TotalTruePoints = ?, Games = ?, GamesMastered = ?, Achievements = ?, Motto = ?, LastUpdate = ? WHERE ID = ?;",
                  [str(RAUserProfile["RichPresenceMsg"]),
                   int(RAUserProfile["LastGameID"]),
                   int(RAUserProfile["ContribCount"]),
                   int(RAUserProfile["ContribYield"]),
                   int(RAUserProfile["TotalPoints"]),
                   int(RAUserProfile["TotalSoftcorePoints"]),
                   int(RAUserProfile["TotalTruePoints"]),
                   int(len(usergames)),
                   int(mastered_games),
                   int(achievement_count),
                   str(RAUserProfile["Motto"]),
                   int(time.time()),
                   int(userid),])
        get_user_wants_to_play(username)
        get_user_set_requests(username)
        get_user_leaderboards(username, updategames)
        if int(time.time()) - user[2] > 24 * 60 * 60:
            print("Fetching new UserPic for " + str(RAUserProfile["User"]))
            get_image(str(RAUserProfile["UserPic"]).split("/")[1], str(RAUserProfile["UserPic"]).split("/")[2], force=True)
            c.execute("UPDATE users SET UserPicLastUpdate = ? WHERE ID = ?;",
                      [int(time.time()),
                       int(userid)])
    conn.commit()

def get_user_wants_to_play(username):
    print("Fetching want to play list for " + str(username))
    RAUserWantToPlayList = RARequest.get("GetUserWantToPlayList", u = str(username))
    #UserID INTEGER, GameID INTEGER, GameTitle TEXT, ConsoleID INTEGER, ImageIcon TEXT
    if "Results" in RAUserWantToPlayList:
        c = conn.cursor()
        userid = [aa for aa in c.execute("SELECT ID from users WHERE User = '" + str(username) + "'").fetchone()][0]
        usergames = [aa[0] for aa in c.execute("SELECT GameID FROM userwantstoplay WHERE UserID = ?;", [int(userid)]).fetchall()]
        for item in RAUserWantToPlayList["Results"]:
            if item["ID"] not in usergames:
                c.execute("INSERT INTO userwantstoplay VALUES (?, ?, ?, ?, ?);",
                        [int(userid),
                        int(item["ID"]),
                        str(item["Title"]),
                        int(item["ConsoleID"]),
                        str(item["ImageIcon"])])
                get_image(str(item["ImageIcon"]).split("/")[1], str(item["ImageIcon"]).split("/")[2])
            else:
                usergames.remove(item["ID"])
        for item in usergames:
            c.execute("DELETE FROM userwantstoplay WHERE UserID = ? AND GameID = ?;", [int(userid), int(item)])
        conn.commit()

def get_user_set_requests(username):
    print("Fetching set requests for " + str(username))
    RAUserSetRequests = RARequest.get("GetUserSetRequests", u = str(username))
    #UserID INTEGER, GameID INTEGER, GameTitle TEXT, ConsoleID INTEGER, ImageIcon TEXT
    # I dont know if it acts the same way as want to play response, so being cautious here
    if "RequestedSets" in RAUserSetRequests:
        c = conn.cursor()
        userid = [aa for aa in c.execute("SELECT ID from users WHERE User = '" + str(username) + "'").fetchone()][0]
        usergames = [aa[0] for aa in c.execute("SELECT GameID FROM setrequests WHERE UserID = ?;", [int(userid)]).fetchall()]
        for item in RAUserSetRequests["RequestedSets"]:
            if item["GameID"] not in usergames:
                c.execute("INSERT INTO setrequests VALUES (?, ?, ?, ?, ?);",
                        [int(userid),
                        int(item["GameID"]),
                        str(item["Title"]),
                        int(item["ConsoleID"]),
                        str(item["ImageIcon"])])
                get_image(str(item["ImageIcon"]).split("/")[1], str(item["ImageIcon"]).split("/")[2])
            else:
                usergames.remove(item["GameID"])
        for item in usergames:
            c.execute("DELETE FROM setrequests WHERE UserID = ? AND GameID = ?;", [int(userid), int(item)])
        conn.commit()

def get_user_leaderboards(username, gamelist = {}):
    print("Fetching leaderboards data for " + str(username))
    c = conn.cursor()
    user = c.execute("SELECT ID, LastUpdate from users WHERE User = '" + str(username) + "'").fetchone()
    userid = user[0]
    if gamelist == {}:
        RARecentlyPlayed = RARequest.get("GetUserRecentlyPlayedGames", u = str(username), c = "5")
        for item in RARecentlyPlayed:
            gamelist[item["GameID"]] = int(time.mktime(datetime.datetime.strptime(item["LastPlayed"], "%Y-%m-%d %H:%M:%S").timetuple()))
    for item in gamelist:
        RAUserGameLeaderboards = RARequest.get("GetUserGameLeaderboards", u = username, i = str(item))
        #UserID INTEGER, GameID INTEGER, EntryID INTEGER, Score INTEGER, FormattedScore TEXT, Rank INTEGER, DateUpdated INTEGER
        if "Results" in RAUserGameLeaderboards:
            for entry in RAUserGameLeaderboards["Results"]:
                record = c.execute("SELECT * FROM userleaderboards WHERE UserID = ? AND GameID = ? AND EntryID = ?;", [int(userid), int(item), int(entry["ID"])]).fetchall()
                if record:
                    c.execute("UPDATE userleaderboards SET Score = ?, FormattedScore = ?, Rank = ?, DateUpdated = ? WHERE UserID = ? AND GameID = ? AND EntryID = ?;",
                            [int(entry["UserEntry"]["Score"]),
                            str(entry["UserEntry"]["FormattedScore"]),
                            int(entry["UserEntry"]["Rank"]),
                            int(time.mktime(datetime.datetime.strptime(entry["UserEntry"]["DateUpdated"], "%Y-%m-%dT%H:%M:%S+00:00").timetuple())),
                            int(userid),
                            int(item),
                            int(entry["ID"])])
                else:
                    c.execute("INSERT INTO userleaderboards VALUES (?, ?, ?, ?, ?, ?, ?);",
                            [int(userid),
                            int(item),
                            int(entry["ID"]),
                            int(entry["UserEntry"]["Score"]),
                            str(entry["UserEntry"]["FormattedScore"]),
                            int(entry["UserEntry"]["Rank"]),
                            int(time.mktime(datetime.datetime.strptime(entry["UserEntry"]["DateUpdated"], "%Y-%m-%dT%H:%M:%S+00:00").timetuple()))])
    conn.commit()

def get_image(type, id, force = False):
    if type == "Badge":
        if os.path.isfile("webapp/static/img/Badge/" + str(id) + ".png") == False or force == True:
            img = requests_free.get("https://media.retroachievements.org/Badge/" + str(id) + ".png", stream=True)
            with open("webapp/static/img/Badge/" + str(id) + ".png", "wb") as f:
                for chunk in img:
                    f.write(chunk)
            img = requests_free.get("https://media.retroachievements.org/Badge/" + str(id) + "_lock.png", stream=True)
            with open("webapp/static/img/Badge/" + str(id) + "_lock.png", "wb") as f:
                for chunk in img:
                    f.write(chunk)
            pass
    else:
        if os.path.isfile("webapp/static/img/" + str(type) + "/" + str(id)) == False or force == True:
            img = requests_free.get("https://media.retroachievements.org/" + str(type) + "/" + str(id), stream=True)
            with open("webapp/static/img/" + str(type) + "/" + str(id), "wb") as f:
                for chunk in img:
                    f.write(chunk)

def update():
    print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ": update users started")
    c = conn.cursor()
    dbusers = [user[0] for user in c.execute("SELECT User from users").fetchall()]
    with open("users.txt", "r", encoding = "utf-8") as fileusers:
        fileusers = fileusers.readlines()
        for user in fileusers:
            if user.strip() not in dbusers:
                add_new_user(user.strip())
            else:
                update_user(user.strip())
    conn.commit()
    print(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ": update users finished")

requests_free = requests_ratelimiter.LimiterSession(per_second=500)
requests_free.headers.update({"User-Agent": "rawf/dev-2025.01.15 ( tepiloxtl@tepiloxtl.net )"})

config = {**dotenv.dotenv_values(".env"), **os.environ}
if "RAWF_INTERVAL" not in config:
    config["RAWF_INTERVAL"] = 10
if "RAWF_DBFILE" not in config:
    config["RAWF_DBFILE"] = "RA.db"

if os.path.isfile(config["RAWF_DBFILE"]) == False:
    print("Database not found, creating new database at " + str(config["RAWF_DBFILE"]))
    conn = sqlite3.connect("RA.db")
    c = conn.cursor()

    c.execute("CREATE TABLE users (ID INTEGER PRIMARY KEY NOT NULL, User TEXT, UserPic TEXT, UserPicLastUpdate INTEGER, MemberSince INTEGER, RichPresenceMsg TEXT, LastGameID INTEGER, ContribCount INTEGER, ContribYield INTEGER, TotalPoints INTEGER, TotalSoftcorePoints INTEGER, TotalTruePoints INTEGER, Games INTEGER, GamesMastered INTEGER, Achievements INTEGER, Permissions INTEGER, Untracked INTEGER, UserWallActive INTEGER, Motto TEXT, LastUpdate INTEGER);")
    c.execute("CREATE TABLE games (ID INTEGER PRIMARY KEY NOT NULL, Title TEXT, ConsoleID INTEGER, ConsoleName TEXT, ForumTopicID INTEGER, Flags INTEGER, ImageIcon TEXT, ImageTitle TEXT, ImageIngame TEXT, ImageBoxArt TEXT, Publisher TEXT, Developer TEXT, Genre TEXT, Released TEXT, ReleasedAtGranularity TEXT, GuideURL TEXT, Updated INTEGER, ParentGameID INTEGER, NumAchievements INTEGER);")
    c.execute("CREATE TABLE usergames (UserID INTEGER, GameID INTEGER, NumAwarded INTEGER, NumAwardedHardcore INTEGER, MostRecentAwardedDate INTEGER, HighestAwardKind TEXT, HighestAwardDate INTEGER)")
    c.execute("CREATE TABLE achievements (GameID INTEGER, ID INTEGER, Title TEXT, Description TEXT, Points INTEGER, TrueRatio REAL, Author TEXT, DateModified INTEGER, DateCreated INTEGER, BadgeName INTEGER, DisplayOrder INTEGER, type TEXT);")
    c.execute("CREATE TABLE userachievements (UserID INTEGER, GameID INTEGER, AchievementID INTEGER, DateEarnedHardcore INTEGER, DateEarned INTEGER);")
    c.execute("CREATE TABLE leaderboards (ID INTEGER PRIMARY KEY NOT NULL, GameID INTEGER, Title TEXT, Description TEXT, RankAsc INTEGER, Format TEXT)")
    c.execute("CREATE TABLE userleaderboards (UserID INTEGER, GameID INTEGER, EntryID INTEGER, Score INTEGER, FormattedScore TEXT, Rank INTEGER, DateUpdated INTEGER)")
    c.execute("CREATE TABLE userwantstoplay (UserID INTEGER, GameID INTEGER, GameTitle TEXT, ConsoleID INTEGER, ImageIcon TEXT)")
    c.execute("CREATE TABLE setrequests (UserID INTEGER, GameID INTEGER, GameTitle TEXT, ConsoleID INTEGER, ImageIcon TEXT)")
    conn.commit()
    update()
    conn.close()

conn = sqlite3.connect(config["RAWF_DBFILE"])
RARequest = RARequest(str(config["RA_APIKEY"]))

for path in [os.path.join(os.getcwd(), 'webapp', 'static', 'img', 'Badge'), os.path.join(os.getcwd(), 'webapp', 'static', 'img', 'Images'), os.path.join(os.getcwd(), 'webapp', 'static', 'img', 'UserPic')]:
    if os.path.exists(path) == False:
        os.makedirs(path)

update()
schedule.every(int(config["RAWF_INTERVAL"])).minutes.at(":00").do(update)
while True:
    schedule.run_pending()
    time.sleep(1)
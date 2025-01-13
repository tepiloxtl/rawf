import sqlite3

conn = sqlite3.connect("RA.db")
c = conn.cursor()

c.execute("CREATE TABLE users (ID INTEGER PRIMARY KEY NOT NULL, User TEXT, UserPic TEXT, MemberSince INTEGER, RichPresenceMsg TEXT, LastGameID INTEGER, ContribCount INTEGER, ContribYield INTEGER, TotalPoints INTEGER, TotalSoftcorePoints INTEGER, TotalTruePoints INTEGER, Games INTEGER, GamesMastered INTEGER, Achievements INTEGER, Permissions INTEGER, Untracked INTEGER, UserWallActive INTEGER, Motto TEXT, LastUpdate INTEGER);")
c.execute("CREATE TABLE games (ID INTEGER PRIMARY KEY NOT NULL, Title TEXT, ConsoleID INTEGER, ConsoleName TEXT, ForumTopicID INTEGER, Flags INTEGER, ImageIcon TEXT, ImageTitle TEXT, ImageIngame TEXT, ImageBoxArt TEXT, Publisher TEXT, Developer TEXT, Genre TEXT, Released TEXT, ReleasedAtGranularity TEXT, GuideURL TEXT, Updated INTEGER, ParentGameID INTEGER, NumAchievements INTEGER);")
c.execute("CREATE TABLE usergames (UserID INTEGER, GameID INTEGER, NumAwarded INTEGER, NumAwardedHardcore INTEGER, MostRecentAwardedDate INTEGER, HighestAwardKind TEXT, HighestAwardDate INTEGER)")
c.execute("CREATE TABLE achievements (GameID INTEGER, ID INTEGER, Title TEXT, Description TEXT, Points INTEGER, TrueRatio REAL, Author TEXT, DateModified INTEGER, DateCreated INTEGER, BadgeName INTEGER, DisplayOrder INTEGER, type TEXT);")
c.execute("CREATE TABLE userachievements (UserID INTEGER, GameID INTEGER, AchievementID INTEGER, DateEarnedHardcore INTEGER, DateEarned INTEGER);")
c.execute("CREATE TABLE userwantstoplay (UserID INTEGER, GameID INTEGER, GameTitle TEXT, ConsoleID INTEGER, ImageIcon TEXT)")
c.execute("CREATE TABLE setrequests (UserID INTEGER, GameID INTEGER, GameTitle TEXT, ConsoleID INTEGER, ImageIcon TEXT)")
conn.commit()
conn.close()
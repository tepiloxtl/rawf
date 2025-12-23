import sqlite3
import json
from datetime import datetime
from collections import defaultdict, Counter

DB_PATH = 'RA.db'
TARGET_YEAR = 2025
OUTPUT_DIR = './wrapped_output'

class WrappedGenerator:
    def __init__(self, db_path, year):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.year = year
        self.start_ts = int(datetime(year, 1, 1).timestamp())
        self.end_ts = int(datetime(year, 12, 31, 23, 59, 59).timestamp())

    def get_users(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT ID, User, UserPic FROM users")
        return cursor.fetchall()

    def get_year_achievements(self, user_id):
        query = """
        SELECT 
            ua.DateEarned, ua.DateEarnedHardcore,
            a.ID as AchievementID, a.Title as AchTitle, a.Points, a.TrueRatio,
            g.ID as GameID, g.Title as GameTitle, g.ConsoleName, g.Genre, g.Released
        FROM userachievements ua
        JOIN achievements a ON ua.AchievementID = a.ID
        JOIN games g ON ua.GameID = g.ID
        WHERE ua.UserID = ?
        AND (
            (ua.DateEarned BETWEEN ? AND ?) OR 
            (ua.DateEarnedHardcore BETWEEN ? AND ?)
        )
        """
        
        cursor = self.conn.cursor()
        cursor.execute(query, (user_id, self.start_ts, self.end_ts, self.start_ts, self.end_ts))
        return cursor.fetchall()
    
    def get_year_games(self, user_id):
        query = """
        SELECT 
            g.ID,
            g.Title,
            g.ConsoleName,
            g.ImageIcon,
            g.Genre,
            ug.BeatenDate,
            ug.HighestAwardKind,
            ug.HighestAwardDate,
            
            -- 1. FIRST EVER: The oldest timestamp we can find for this game (History scope)
            MIN(
                COALESCE(ua.DateEarnedHardcore, ua.DateEarned)
            ) as date_started_ever,

            -- 2. LAST THIS YEAR: The newest timestamp specifically within the target year
            MAX(
                CASE 
                    WHEN COALESCE(ua.DateEarnedHardcore, ua.DateEarned) BETWEEN :start_ts AND :end_ts 
                    THEN COALESCE(ua.DateEarnedHardcore, ua.DateEarned)
                    ELSE NULL 
                END
            ) as last_played_this_year

        FROM userachievements ua
        JOIN games g ON ua.GameID = g.ID
        JOIN usergames ug ON ug.GameID = ua.GameID AND ug.UserID = ua.UserID
        WHERE 
            ua.UserID = :user_id
        GROUP BY 
            g.ID
        HAVING 
            -- 3. THE GATEKEEPER: Only return rows where the "Last This Year" calculation actually found something
            last_played_this_year IS NOT NULL
        ORDER BY 
            last_played_this_year DESC;"""
        
        cursor = self.conn.cursor()
        cursor.execute(query, {"start_ts": self.start_ts, "end_ts": self.end_ts, "user_id": user_id})
        return cursor.fetchall()

    def generate_for_user(self, user):
        user_id = user['ID']
        print(f"Processing {user['User']}...")

        achievements = self.get_year_achievements(user_id)
        # masteries = self.get_year_masteries(user_id)
        all_games = self.get_year_games(user_id)
        
        if not achievements:
            print(f"Skipping {user['User']} (No activity)")
            return None

        total_points = 0
        hourly_counts = [0] * 24
        genre_points = defaultdict(int)
        console_counts = defaultdict(int)
        dates_active = set()

        games_started = []
        games_beaten = []
        games_completed = []
        games_mastered = []

        for game in all_games:
            if game["date_started_ever"] >= self.start_ts:
                games_started.append({k: game[k] for k in game.keys()})
            if game["BeatenDate"] >= self.start_ts:
                games_beaten.append({k: game[k] for k in game.keys()})
            if game["HighestAwardKind"] == "completed":
                games_completed.append({k: game[k] for k in game.keys()})
            if game["HighestAwardKind"] == "mastered":
                games_mastered.append({k: game[k] for k in game.keys()})
        
        # Track Hardest/Rarest
        rarest_unlock = None
        max_ratio = -1

        for row in achievements:
            # Determine effective timestamp (Hardcore priority)
            ts = row['DateEarnedHardcore'] if row['DateEarnedHardcore'] else row['DateEarned']
            if not ts: continue
            
            # Points
            points = row['Points'] if row['Points'] else 0
            total_points += points
            
            # Temporal
            dt = datetime.fromtimestamp(ts)
            hourly_counts[dt.hour] += 1
            dates_active.add(dt.strftime("%Y-%m-%d"))
            
            # Genre & Console
            # Handle comma-separated genres
            genre_raw = row['Genre'] if row['Genre'] else "Unknown"
            primary_genre = genre_raw.split(',')[0].strip() 
            genre_points[primary_genre] += points
            
            console_counts[row['ConsoleName']] += 1
            
            # Rarest Logic
            ratio = row['TrueRatio'] if row['TrueRatio'] else 0
            if ratio > max_ratio:
                max_ratio = ratio
                rarest_unlock = {
                    "title": row['AchTitle'],
                    "game": row['GameTitle'],
                    "ratio": ratio,
                    "icon": ""
                }
        
        # Sort Genres
        sorted_genres = sorted(genre_points.items(), key=lambda x: x[1], reverse=True)
        top_genres = [{"name": k, "points": v} for k, v in sorted_genres[:5]]
        
        # Sort Consoles
        sorted_consoles = sorted(console_counts.items(), key=lambda x: x[1], reverse=True)
        top_consoles = [{"name": k, "count": v} for k, v in sorted_consoles[:3]]

        stats = {
            "meta": {
                "user": user['User'],
                "avatar": user['UserPic'],
                "generated_at": datetime.now().isoformat()
            },
            "summary": {
                "total_points": total_points,
                "total_achievements": len(achievements),
                "games_started": len(games_started),
                "games_completed": len(games_completed),
                "games_mastered": len(games_mastered),
                "completion_rate": round(((len(games_mastered) + len(games_completed)) / len(games_started) * 100), 1) if len(games_started) > 0 else 0,
                "active_days": len(dates_active)
            },
            "temporal": {
                "hourly_distribution": hourly_counts,
                "activity_dates": list(dates_active) 
            },
            "favorites": {
                "top_genres": top_genres,
                "top_consoles": top_consoles
            },
            "highlights": {
                "rarest_achievement": rarest_unlock
            },
            "games": {
                "started": games_started,
                "beaten": games_beaten,
                "completed": games_completed,
                "mastered": games_mastered
            }
        }

        return stats

    def generate_debug(self, user):
        user_id = user['ID']
        print(f"Processing {user['User']} debug...")

        achievements = self.get_year_achievements(user_id)

        if not achievements:
            print(f"Skipping {user['User']} (No activity)")
            return None
        debug_achievements = []
        for item in achievements:
            debug_achievements.append({k: item[k] for k in item.keys()})

        
        # masteries = self.get_year_masteries(user_id)
        # debug_masteries = []
        # for item in masteries:
        #     debug_masteries.append({k: item[k] for k in item.keys()})
        all_games = self.get_year_games(user_id)
        debug_all_games = []
        for item in all_games:
            debug_all_games.append({k: item[k] for k in item.keys()})


        with open(f"{OUTPUT_DIR}/debug/{user['User']}_achievements.json", 'w') as f:
            json.dump(debug_achievements, f, indent=2)
        # with open(f"{OUTPUT_DIR}/debug/{user['User']}_masteries.json", 'w') as f:
        #     json.dump(debug_masteries, f, indent=2)
        with open(f"{OUTPUT_DIR}/debug/{user['User']}_all_games.json", 'w') as f:
            json.dump(debug_all_games, f, indent=2)
        

    def run(self):
        users = self.get_users()
        all_stats = []

        for user in users:
            self.generate_debug(user)

            data = self.generate_for_user(user)
            if data:
                all_stats.append(data)
                # Write individual file
                filename = f"{OUTPUT_DIR}/{user['User']}_wrapped.json"
                with open(filename, 'w') as f:
                    json.dump(data, f, indent=2)

        #TODO: Group summaries
        print("Done!")

if __name__ == "__main__":
    import os
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR + "/debug")
        
    gen = WrappedGenerator(DB_PATH, TARGET_YEAR)
    gen.run()
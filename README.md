# RAWF - RetroAchievements with Friends
Please, forgive me for code crimes that might be commited in these files lol
## Installing and running (hopefully)
1. Clone the repo
2. Add your RA API key as `RA_APIKEY` either to your environment variables or into `.env` file
3. Add your group members usernames to users.txt, one user per line
4. (optional, recommended) Make a virtual environment
5. `python3 -m pip install requirements.txt`
6. (run once or when redoing the database) `python3 make_db.py`
To run the backend (retrieving data from API) run `python3 gather_data.py`
To run the frontend, run `flask run`. This will run werkzeug server at `127.0.0.1:5000`. Proxy it accordingly using a web server of your choice. It has ProxyFix already applied
TODO: Reconfigure to run with gunicorn or uWSGI
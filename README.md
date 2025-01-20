# RAWF - RetroAchievements with Friends
Simple webpage panel that tracks RetroAchievement progress for a group of players, in a small Python/Flask application

[Demo site](https://rawf.tepiloxtl.net)
## Installing and running (hopefully)
Python 3.11 or up required  
1. Clone the repo
2. Add your RA API key as `RA_APIKEY` either to your environment variables or into `.env` file
3. Add your group members usernames to users.txt, one user per line
4. (optional, recommended) Make a virtual environment
5. `python3 -m pip install -r requirements.txt`
6. (run once or when redoing the database) `python3 make_db.py`  
To run the backend (retrieving data from API) run `python3 gather_data.py`  
To run the frontend, run `python3 -m gunicorn -w 4 'webapp:app'`. This will run werkzeug server at `127.0.0.1:8000`. Proxy it accordingly using a web server of your choice. It has ProxyFix already applied (or use `flask run` to run development server on port 5000)

## Stuff
A lot has still to be done here, but I like how it stands for now in general. I still aim to better use bootstrap, with setting up a proper theme being my current objective for one of those weekends. Also handling of timezones is pretty... loose, but thats how it comes from the RA API. I only support "additive" user data changes, nothing really ever gets checked whether stuff changes or gets removed. So a big boi feature to add would be monitoring on data change, such as achievements being demoted/changed, game info changing, or user requesting achievments to be removed from their account. Other than that, I don't think there are any big outstanding issues? Please prove me wrong if thats not the case though lol.

By default I check with API every 10 minutes*, and there are ratelimits for API calls in place, so I think, I hope, I am being fair and not abuse the API

Database is SQLite, which I think is fair for such small application, but at the same time presents some limitations. Since the "backend" and "frontend" are two separate scripts, they can't both maintain write access to database. Hence, if I ever want to add some sort of configuration panel, that needs to be overcomed, either by some magic, or moving to actual DB engine...
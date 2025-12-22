import json, time, requests_ratelimiter
from requests.exceptions import ConnectionError, HTTPError
from json import JSONDecodeError

class RARequest:

    def __init__(self,
                 API_key = None,
                 username = None,
                 limit_per_second = 2,
                 user_agent = "RARequest Python library",
                 error_max_retries = 6,
                 error_retry_delay_sec = 10):

        self.API_key = API_key
        self.username = username
        self.limit_per_second = limit_per_second
        self.user_agent = user_agent
        self.error_max_retries = error_max_retries
        self.error_retry_delay_sec = error_retry_delay_sec

        if self.API_key == None:
            print("RetroAchievement API key needs to be provided")
            return None

        self.requests = requests_ratelimiter.LimiterSession(per_second=self.limit_per_second)
        self.requests.headers.update({"User-Agent": self.user_agent})
        self.requests_free = requests_ratelimiter.LimiterSession(per_second=500)
        self.requests_free.headers.update({"User-Agent": self.user_agent})

    def _test_connection(self):
        #make it raise exception I guess
        pass

    def _make_call(self, endpoint, **kwargs):
        kwargs["y"] = self.API_key
        print(endpoint + ": " + str(kwargs))
        attempt = 0
        while attempt < self.error_max_retries:
            try:
                r = self.requests.get("https://retroachievements.org/API/API_" + str(endpoint) + ".php", params=kwargs)
                #RA returns 422 in some responses, frankly probably correctly, but it trips here, so no catching http errors for now :(
                #r.raise_for_status()
                text = r.text
                json = r.json()
                return json
            except (ConnectionError, HTTPError, JSONDecodeError):
                attempt += 1
                if attempt >= self.error_max_retries:
                    raise
                print("Connection aborted, {}/{} retries, waiting {}s".format(str(attempt), str(self.error_max_retries), str(self.error_retry_delay_sec)))
                self.requests.close()
                time.sleep(self.error_retry_delay_sec)
                self.requests = requests_ratelimiter.LimiterSession(per_second=2)
                self.requests.headers.update({"User-Agent": "rawf/dev-2025.01.15 ( tepiloxtl@tepiloxtl.net )"})

    def get(self, endpoint, **kwargs):
        # Paginated response with proper counter/total count
        # Notably, having GetRecentGameAwards automatically unroll is a really bad idea, so I bumping it down to standard procedures
        if endpoint in ["GetUserCompletionProgress", "GetUserWantToPlayList", "GetUsersIFollow", "GetUsersFollowingMe", "GetGameLeaderboards", "GetLeaderboardEntries", "GetUserGameLeaderboards", "GetComments"]:
            apiresponse = self._make_call(endpoint, **kwargs)
            # API_GetUserWantToPlayList returns [] for users with no wants, which I find kind of weird? Investigate that later?
            if "Results" not in apiresponse:
                return []
            response = {"Total": apiresponse["Total"], "Results": []}
            more_entries = True
            o = 0
            count = apiresponse["Count"]
            while more_entries == True:
                if apiresponse["Results"] == []:
                    more_entries = False
                    continue
                for item in apiresponse["Results"]:
                    response["Results"].append(item)
                o = o + count
                kwargs["o"] = o
                apiresponse = self._make_call(endpoint, **kwargs)
            return response
        else:
            # Paginated response with legacy responses: GetUserRecentlyPlayedGames, GetGameList, GetAchievementUnlocks, GetTicketData
            # Non-paginated response
            # also GetRecentGameAwards
            return self._make_call(endpoint, **kwargs)
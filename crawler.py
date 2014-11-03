import urllib2
import json
import Queue
import time
import random

key = 'F6B38B6772012F11E1BB68FCF696140A'
getOwnedGames = 'http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key='
getFriendsList = 'http://api.steampowered.com/ISteamUser/GetFriendList/v0001/?key='
getSummaries = 'http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key='
queue = Queue.Queue()
user_set = []
user_owned_games = {}


def get_games(steamid):
    queue.put(steamid)
    counter = 0
    while not queue.empty() and counter < 50:
        current_user = str(queue.get())
        print current_user
        counter += 1
        summaries = json.loads(urllib2.urlopen(getSummaries + key + '&steamids=' + current_user + '&format=json').read())
        if summaries['response']['players'][0]['communityvisibilitystate'] == 3:
            owned_games = json.loads(urllib2.urlopen(getOwnedGames + key + '&steamid=' + current_user + '&format=json').read())
            user_owned_games[current_user] = owned_games
            friend_list = json.loads(urllib2.urlopen(getFriendsList + key + '&steamid=' + current_user + '&format=json').read())
            for friend in friend_list['friendslist']['friends']:
                friend_id = friend['steamid']
                if friend_id not in user_set:
                    queue.put(friend_id)
                    user_set.append(friend_id)
        time.sleep(random.randint(3, 5))


def main():
    get_games('76561198053212280')
    print user_owned_games.keys()

main()
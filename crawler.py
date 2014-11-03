import urllib2
import json
import Queue
import time
import random
from copy import deepcopy

key = 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
getOwnedGames = 'http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key='
getFriendsList = 'http://api.steampowered.com/ISteamUser/GetFriendList/v0001/?key='
getSummaries = 'http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key='
queue = Queue.Queue()
user_set = []
user_owned_games = {}


def get_games(steamid):
    queue.put(steamid)
    counter = 0
    while not queue.empty() and counter < 1:
        dictionary_file = open('dictionary.txt', 'a')
        queue_file = open('queue.txt', 'w')
        current_user = str(queue.get())
        print current_user, counter
        counter += 1
        summaries = json.loads(urllib2.urlopen(getSummaries + key + '&steamids=' + current_user + '&format=json').read())
        if summaries['response']['players'][0]['communityvisibilitystate'] == 3:
            owned_games = json.loads(urllib2.urlopen(getOwnedGames + key + '&steamid=' + current_user + '&include_played_free_games=1&format=json').read())
            user_owned_games[current_user] = owned_games
            dictionary_file.write(str(current_user) + str(owned_games) + '\n')
            dictionary_file.close()
            friend_list = json.loads(urllib2.urlopen(getFriendsList + key + '&steamid=' + current_user + '&format=json').read())
            for friend in friend_list['friendslist']['friends']:
                friend_id = friend['steamid']
                if friend_id not in user_set:
                    queue.put(friend_id)
                    user_set.append(friend_id)
        #while not temp_queue.empty():
         #   queue_file.write(temp_queue.get() + '\n')
        for elem in list(queue.queue):
            queue_file.write(str(elem) + '\n')
        queue_file.close()
        time.sleep(random.randint(3, 5))


def main():
    get_games('76561198053212280')

main()

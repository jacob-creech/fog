import urllib2
import json
import Queue
import time
import random

api_key = open('api_key.txt')
key = api_key.read()
api_key.close()
getOwnedGames = 'http://api.steampowered.com/IPlayerService/GetOwnedGames/v0001/?key='
getFriendsList = 'http://api.steampowered.com/ISteamUser/GetFriendList/v0001/?key='
getSummaries = 'http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key='
queue = Queue.Queue()
user_set = []
user_owned_games = {}


def get_games(steamid):
    queue.put(steamid)
    counter = len(user_set)
    while not queue.empty():
        dictionary_file = open('dictionary.txt', 'a')
        
        current_user = str(queue.get())
        print current_user, counter
        counter += 1
        try:
            summaries = json.loads(urllib2.urlopen(getSummaries + key + '&steamids=' + current_user + '&format=json', timeout = 10).read())
        except urllib2.URLError, e:
            print "URLError: ", e.reason
            counter -= 1
            queue.put(current_user)
            continue

        except urllib2.HTTPError, e:
            print "HTTPError: ", e.code
            counter -= 1
            queue.put(current_user)
            continue
        except e:
            print e
            counter -= 1
            queue.put(current_user)
            continue
        
        if summaries['response']['players'][0]['communityvisibilitystate'] == 3:
            try:
                owned_games = json.loads(urllib2.urlopen(getOwnedGames + key + '&steamid=' + current_user + '&include_played_free_games=1&format=json', timeout = 10).read())
            except urllib2.URLError, e:
                print "URLError: ", e.reason
                counter -= 1
                queue.put(current_user)
                continue
            except urllib2.HTTPError, e:
                print "HTTPError: ", e.code
                counter -= 1
                queue.put(current_user)
                continue
            except e:
                print e
                counter -= 1
                queue.put(current_user)
                continue
            
            user_owned_games[current_user] = owned_games
            dictionary_file.write(str(current_user) + ' ' + str(owned_games) + '\n')
            dictionary_file.close()

            try:
                friend_list = json.loads(urllib2.urlopen(getFriendsList + key + '&steamid=' + current_user + '&format=json', timeout = 10).read())
            except urllib2.URLError, e:
                print "URLError: ", e.reason
                counter -= 1
                queue.put(current_user)
                continue

            except urllib2.HTTPError, e:
                print "HTTPError: ", e.code
                counter -= 1
                queue.put(current_user)
                continue

            except e:
                print e
                counter -= 1
                queue.put(current_user)
                continue
            
            for friend in friend_list['friendslist']['friends']:
                friend_id = friend['steamid']
                if friend_id not in user_set:
                    queue.put(friend_id)
                    user_set.append(friend_id)
        #while not temp_queue.empty():
         #   queue_file.write(temp_queue.get() + '\n')
        queue_file = open('queue.txt', 'w')
        for elem in list(queue.queue):
            queue_file.write(str(elem) + '\n')
        queue_file.close()
        time.sleep(random.randint(1, 2))


def main():
    try:
        queue_file = open('queue.txt', 'r')
        for line in queue_file:
            queue.put(line[:17])
        queue_file.close()

        global user_set
        dict_file = open('dictionary.txt', 'r')
        for line in dict_file:
            user_set += [line[:17]]
        dict_file.close()
    except IOError, e:
        pass
    #seed is duplicated
    get_games('76561198129321156')

main()

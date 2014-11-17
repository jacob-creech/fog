import json
import re
import numpy

user_game_dict = {}

# user_averages[userid][appid][local_average]
user_averages = {}
# game_averages[appid][global_average]
game_averages = {}

def svd():
	global user_game_dict
	global user_averages
	global game_averages
	orig_matrix = []
	user_avg_keys = sorted(user_averages.keys())
	game_avg_keys = sorted(game_averages.keys())
	game_mapping = {}
	# Map each appid to an index
	for i, game in enumerate(game_avg_keys):
		game_mapping[game] = i
	# Default all values to Zero
	for i, user in enumerate(user_avg_keys):
		orig_matrix += [[]]
		for game in game_avg_keys:
			orig_matrix[i] += [0]
	# Maps previous ratings to matrix 
	for i, user in enumerate(user_avg_keys):
		gameids = user_averages[user].keys()
		for game in gameids:
			orig_matrix[i][game_mapping[game]] = user_averages[user][game]
	U, s, V = numpy.linalg.svd(orig_matrix, full_matrices=False)
	return orig_matrix

def global_average():
	global user_game_dict
	global user_averages
	global game_averages
	# game_user[appid][num_of_users]
	game_user = {}

	for user in user_game_dict:
		user_averages[user] = {}
	for user in user_game_dict:
		user_total_hours = 0
		game_hours = 0
		# for each game in the user's gamelist
		if 'games' in user_game_dict[user]['response']:
			# add up total hours of playtime that a user has first
			for game in user_game_dict[user]['response']['games']:
				# add up number of users per game
				game_user[game['appid']] = game_user.get(game['appid'], 0) + 1
				user_total_hours += game['playtime_forever']
			# Then get the local averages per game, per user
			for game in user_game_dict[user]['response']['games']:
				game_hours = game['playtime_forever']
				# Calculate local average
				if user_total_hours != 0:
					local_average = game_hours/float(user_total_hours)
					user_averages[user][game['appid']] = local_average
					# Add each local average to global total
					game_averages[game['appid']] = game_averages.get(game['appid'], 0) + local_average
	for appid in game_averages:
		game_averages[appid] /= game_user[appid]

	return game_averages

def main():
	global user_game_dict
	dict_file = open("dataset.txt", "r")
	count = 0
	for line in dict_file:
		line = re.sub('u', '', line)
		line = re.sub('\'', '\"', line)
		dataset = json.loads(line[18:])
		user_game_dict[line[:17]] = dataset
		if count == 5:
			break
		count+=1
	global_average()
	svd()
main()

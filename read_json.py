import json

data = []
for i, line in enumerate(open('meetups.json')):
	line = line.strip()
	if line.startswith('[{'):
		line = line[1:]
	if line.endswith('},'):
		line = line[:-1]
	if i % 1000 == 0:
		print('..',i)
	try:
		data.append(json.loads(line))
	except:
		print('fail at',i)
import json

dump = "dump.json"
local_exp = "local_exp.json"

members = []
players = []
servers = []

members_dump = "members.dump.json"
players_dump = "players.dump.json"
servers_dump = "servers.dump.json"

with open(dump, "r") as dfile:
    dump_data = json.load(dfile)

with open(local_exp, "r") as lfile:
    local_data = json.load(lfile)

for thing in dump_data:
    if thing.get('text') is not None and thing.get('text') == "member":
        members.append(thing)
    elif thing.get('text') is not None and thing.get('text') == "player":
        players.append(thing)
    elif thing.get('text') is not None and thing.get('text') == "server":
        servers.append(thing)

for member in members:
    for player in players:
        if player["id"] == member["player_id"]:
            member["player"] = player
            break
    for server in servers:
        if server["id"] == member["server_id"]:
            member["server"] = server
            break

for thing in local_data:
    found = False
    for member in members:
        if member["player"]["discord_id"] == thing["id"] and member["server"]["discord_id"] == thing["server_id"]:
            member["exp"] += thing["exp"]
            found = True
            break
    if not found:
        members.append({
            "player": {
                "discord_id": thing["id"]
            },
            "server": {
                "discord_id": thing["server_id"]
            },
            "exp": thing["exp"]
        })

with open(members_dump, "w") as mfile:
    json.dump(members, mfile, indent=4)


with open(players_dump, "w") as mfile:
    json.dump(players, mfile, indent=4)


with open(servers_dump, "w") as mfile:
    json.dump(servers, mfile, indent=4)

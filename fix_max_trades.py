import json

config_path = "/home/ec2-user/chacal_bot/config_chacal_aws.json"

with open(config_path, "r") as f:
    config = json.load(f)

config["max_open_trades"] = 9

with open(config_path, "w") as f:
    json.dump(config, f, indent=4)

print("max_open_trades actualizado a 9")

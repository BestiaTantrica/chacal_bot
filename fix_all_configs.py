import json

configs = [
    "/home/ec2-user/chacal_bot/user_data/config_chacal_aws.json",
    "/home/ec2-user/chacal_bot/user_data/config_backtest.json"
]

for config_path in configs:
    try:
        with open(config_path, "r") as f:
            config = json.load(f)
        config["max_open_trades"] = 9
        with open(config_path, "w") as f:
            json.dump(config, f, indent=4)
        print(f"OK: {config_path}")
    except Exception as e:
        print(f"ERROR {config_path}: {e}")

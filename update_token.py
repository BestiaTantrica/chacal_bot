
import json
import os

CONFIG_PATH = '/home/ec2-user/chacal_bot/user_data/config_chacal_aws.json'
NEW_TOKEN = '8073681433:AAFoLMLd1WRJmxwjx0OIPrAxDVW3KJKsghA'

try:
    with open(CONFIG_PATH, 'r') as f:
        data = json.load(f)
    
    data['telegram']['token'] = NEW_TOKEN
    
    with open(CONFIG_PATH, 'w') as f:
        json.dump(data, f, indent=4)
        
    print(f"SUCCESS: Token updated in {CONFIG_PATH}")
except Exception as e:
    print(f"ERROR: {str(e)}")
    exit(1)

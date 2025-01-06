from flask import Flask, request, send_from_directory, jsonify
import json
import os

app = Flask(__name__)

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/config.json')
def get_config():
    try:
        with open(CONFIG_PATH, 'r') as f:
            config = json.load(f)
        return jsonify(config)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/save-config', methods=['POST'])
def save_config():
    try:
        # Load existing config to preserve structure
        with open(CONFIG_PATH, 'r') as f:
            existing_config = json.load(f)
        
        # Get new config from request
        new_config = request.json
        
        # Update only the fields we handle in the frontend
        existing_config['user_profile'] = new_config['user_profile']
        existing_config['subreddits'] = new_config['subreddits']
        existing_config['scraping']['posts_limit'] = new_config['scraping']['posts_limit']
        existing_config['scraping']['comments_limit'] = new_config['scraping']['comments_limit']
        existing_config['scraping']['replies_limit'] = new_config['scraping']['replies_limit']
        existing_config['scraping']['comment_depth'] = new_config['scraping']['comment_depth']
        existing_config['scraping']['time_filter'] = new_config['scraping']['time_filter']
        existing_config['default_model'] = new_config['default_model']
        
        # Save updated config
        with open(CONFIG_PATH, 'w') as f:
            json.dump(existing_config, f, indent=4)
        
        return jsonify({'message': 'Configuration saved successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(port=5000, debug=True)

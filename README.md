## Setup

1. First you will need to generate gmail auth for the google account
1. Follow the google [quickstart guide](https://developers.google.com/gmail/api/quickstart/python) to generate a `credentials.json` file, and put this in `/data` also
1. `pip install google-auth-httplib2 google-auth-oauthlib`
1. Run the script `run_gmail_auth.py`
1. This will generate a `token.json` file in `/data`
1. Create a `credentials.py` file following the template of `credentials.example.py`
1. Run `docker compose up --build -d`
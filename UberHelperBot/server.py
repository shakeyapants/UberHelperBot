from flask import Flask, request
from uber_rides.auth import AuthorizationCodeGrant
import json
from models import db_session, User
import api_keys as keys

app = Flask(__name__)


@app.route('/')
def authorize():
    state = request.args.get('state')

    user = User.query.filter(User.uber_state == state).first()

    auth_flow = AuthorizationCodeGrant(
        keys.UBER_CLIENT_ID,
        {'request'},
        keys.UBER_CLIENT_SECRET,
        keys.UBER_REDIRECT_URL,
        state_token=state
    )

    session = auth_flow.get_session(request.url)
    credential = session.oauth2credential

    credential_data = {
        'client_id': credential.client_id,
        'redirect_url': credential.redirect_url,
        'access_token': credential.access_token,
        'expires_in_seconds': credential.expires_in_seconds,
        'scopes': list(credential.scopes),
        'grant_type': credential.grant_type,
        'client_secret': credential.client_secret,
        'refresh_token': credential.refresh_token,
    }

    user.uber_credentials = json.dumps(credential_data)
    user.uber_state = ''
    db_session.commit()
    return 'OK'


@app.errorhandler(500)
def internal_server_error(error):
    return 'Здесь ничего нет ;)'

if __name__ == '__main__':
    app.run()

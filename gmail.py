import httplib2
import ipdb
import os

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage


SCOPES = 'https://www.googleapis.com/auth/gmail.readonly'
CLIENT_SECRET_FILE = '.creds/secrets.json'
APPLICATION_NAME = 'booster'


def get_credentials():
    not os.path.exists('.creds') and os.makedirs('.creds')
    store = Storage('.creds/credentials.json')
    credentials = store.get()

    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = 'booster'

        credentials = tools.run_flow(flow, store)

    return credentials


def main():
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('gmail', 'v1', http=http)
    ipdb.set_trace()
    results = service.users().labels().list(userId='me').execute()
    labels = results.get('labels', [])

    if not labels:
        print('No labels found.')
    else:
        print('Labels:')

    for label in labels:
        print(label['name'])

main()

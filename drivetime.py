import json
import sqlite3
from collections import namedtuple
from google_drive_to_sqlite.cli import load_tokens
from google_drive_to_sqlite.utils import APIClient

# Google Authentication
tokens = load_tokens(auth='auth.json')
client = APIClient(**tokens)

# Get SQLite DB
con = sqlite3.connect('files.db')
cur = con.cursor()

# Get tables as named tuples
File = namedtuple("File", ["id", "name", "webViewLink"])
files = [File(*x) for x in cur.execute("select id, name, webViewLink from drive_files")]
User = namedtuple("User", ["permissionId", "displayName", "emailAddress"])
users = [User(*x) for x in cur.execute("select permissionId, displayName, emailAddress from drive_users")]
user_lookup = {user.permissionId: user for user in users}

# cur.execute("select * from lang where first_appeared=:year", {"year": 1972})

def get_permission_list(client, file_id, fields=None):
    file_url = "https://www.googleapis.com/drive/v3/files/{}/permissions".format(file_id)
    params = {}
    if fields is not None:
        params["fields"] = ",".join(fields)
    return client.get(
        file_url,
        params=params,
    ).json()

def get_permission(client, file_id, permission_id, fields=None):
    file_url = "https://www.googleapis.com/drive/v3/files/{}/permissions/{}".format(file_id, permission_id)
    params = {}
    if fields is not None:
        params["fields"] = ",".join(fields)
    return client.get(
        file_url,
        params=params,
    ).json()


# Get data
for file in files:
  permissions = get_permission_list(client, file.id)
  if 'error' in permissions:
    print (permissions, file)  # weird?!? -- some of the files aren't accessible to me? But I just got them...
  else:
    printed_file = False
    for permission in permissions['permissions']:
      permission_id = permission['id']
      user = user_lookup.get(permission_id, None)
      if not user:
        pass
        if not printed_file:
          print (file)
          printed_file = True
        print (permission) # There's a bunch of users who we don't know who has that Permission ID...
                             # Also domains, but they're probably mostly just "share with dxw"
      else:
        if not user.emailAddress.endswith('@dxw.com'):  # Do any contractors have @dxw.com email addresses?
          if not printed_file:
            print (file)
            printed_file = True
          print (user)

# print(files)

exit(1)

with open('files.json', 'r') as f:
    j = json.load(f)
print(j)

print(get_permission_list(client, "1kYHXE1HiFJE4VJPbHFSg-nNAFjX_yRizmFmEQl4wioo"))

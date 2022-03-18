import json
import sqlite3
from collections import namedtuple
from google_drive_to_sqlite.cli import load_tokens
from google_drive_to_sqlite.utils import APIClient

# This assumes that a basic database has been generated by running
# `google-drive-to-sqlite files files.db`

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

def reset_permissions_table():
  # there may be more columns that are useful:
  # https://developers.google.com/drive/api/v3/reference/permissions
  cur.execute("DROP TABLE IF EXISTS drive_permissions")
  cur.execute("""
    CREATE TABLE drive_permissions (
      id TEXT,
      type TEXT,
      kind TEXT,
      role TEXT,
      fileId TEXT,
      FOREIGN KEY (fileId) REFERENCES drive_files(id)
      FOREIGN KEY (id) REFERENCES drive_users(permissionId)
      PRIMARY KEY (id, fileId)
    )
    """)

def save_permission(**kwargs):
  cur.execute("""INSERT INTO drive_permissions
                 (id, type, kind, role, fileId)
                 VALUES
                 (:_id, :_type, :kind, :role, :fileId)
                 """, kwargs)

def get_permission_data(files):
  for file in files:
    permissions = get_permission_list(client, file.id)
    if 'error' in permissions:
      print (permissions, file)  # weird?!? -- some of the files aren't accessible to me? But I just got them...
    else:
      for permission in permissions['permissions']:
        save_permission(_id=permission['id'],
                        _type=permission['type'],
                        fileId=file.id,
                        **permission)

def create_view():
  # very optional
  cur.execute("DROP VIEW summary")
  cur.execute("""CREATE VIEW summary AS
  SELECT webViewLink, drive_files.name as filename, displayName, emailAddress FROM
  drive_users LEFT JOIN drive_permissions ON drive_users.permissionId=drive_permissions.id
              LEFT JOIN drive_files ON drive_permissions.fileID=drive_files.id
  WHERE emailAddress NOT LIKE "%dxw.com"
  GROUP BY name, displayName
  """)

create_view()
reset_permissions_table()
get_permission_data(files)

cur.execute("COMMIT")

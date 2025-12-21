from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

FOLDER_MIME_TYPE = "application/vnd.google-apps.folder"

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
SERVICE_ACCOUNT_FILE = "../service_account.json"

creds = Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)

def get_files(file_id, parent_path):
    count = 0
    service = build("drive", "v3", credentials=creds)

    results = service.files().list(
        q=f"'{file_id}' in parents and trashed = false",
        fields="files(id, name, mimeType)"
    ).execute()

    files = results.get("files", [])

    for file in files:
        if file["mimeType"] == FOLDER_MIME_TYPE:
            count += get_files(file["id"], file['name'] + "/" + parent_path)
        else:
            count += 1
            print(count)
            print(parent_path)
            print(f"Name: {file['name']}")
            print(f"ID: {file['id']}")
            print(f"Type: {file['mimeType']}")
            print("-" * 30)

    return count



if __name__ == "__main__":
    total_files = get_files("1VWtBJ4KClTf7v8ULab7VN-45QK-au0DO", "")
    print(total_files)
"""Placeholder data used to lay out the portals.

Nothing here touches the services yet - every screen renders from these
constants so the UI can be reviewed without a Drive connection, a Chroma
store or an embedding model.
"""

from constant.paths import BASE_DIR, CHROMA_STORE_DIR, INPUT_FILE_DIR, OUTPUT_FILE_DIR

# Mirrors the values currently hardcoded in the services.
COLLECTION_NAME = "my_knowledge_drive"
CHROMA_STORE_PATH = CHROMA_STORE_DIR
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
DRIVE_FOLDER_ID = "1VWtBJ4KClTf7v8ULab7VN-45QK-au0DO"
SERVICE_ACCOUNT_FILE = "C:/secrets/my_knowledge_drive_service_account.json"
RESULTS_PER_QUERY = 5

PATHS = {
    "Base directory": BASE_DIR,
    "Source files": INPUT_FILE_DIR,
    "Converted files": OUTPUT_FILE_DIR,
    "Chroma store": CHROMA_STORE_PATH,
}

STATS = {
    "embedded": "312",
    "source_files": "348",
    "converted_files": "312",
    "skipped_files": "36",
    "last_sync": "2h ago",
    "store_size": "48.2 MB",
}

DOCUMENTS = [
    ("1aB7xQfKm2LpZr9TnVdEs4YwHc0JgUiOe", "Docker\\Docker Commands Cheat Sheet", "image"),
    ("2cD8yRgLn3MqAs0UoWfFt5ZxId1KhVjPf", "Docker\\Docker General Notes", "doc"),
    ("3eF9zShMo4NrBt1VpXgGu6AyJe2LiWkQg", "Docker\\Installation Guides", "doc"),
    ("4gH0aTiNp5OsCu2WqYhHv7BzKf3MjXlRh", "Flutter\\Build\\Build", "doc"),
    ("5iJ1bUjOq6PtDv3XrZiIw8CaLg4NkYmSi", "Flutter\\App Icon\\Change Icon", "doc"),
    ("6kL2cVkPr7QuEw4YsAjJx9DbMh5OlZnTj", "Git\\Git Flow", "image"),
    ("7mN3dWlQs8RvFx5ZtBkKy0EcNi6PmAoUk", "Git\\Branch Rename", "doc"),
    ("8oP4eXmRt9SwGy6AuClLz1FdOj7QnBpVl", "Java\\Spring Boot Setup", "doc"),
    ("9qR5fYnSu0TxHz7BvDmMa2GePk8RoCqWm", "Java\\Spring Annotations", "doc"),
    ("0sT6gZoTv1UyIa8CwEnNb3HfQl9SpDrXn", "Java\\JPA, IOC, AOP, MVC", "doc"),
    ("1uV7hApUw2VzJb9DxFoOc4IgRm0TqEsYo", "Java\\Quartz\\Quartz", "doc"),
    ("2wX8iBqVx3WaKc0EyGpPd5JhSn1UrFtZp", "Java\\JavaMultiTreadingAndAsync\\ThreadExample1", "code"),
    ("3yZ9jCrWy4XbLd1FzHqQe6KiTo2VsGuAq", "Linux\\Linux General Notes", "doc"),
    ("4aB0kDsXz5YcMe2GaIrRf7LjUp3WtHvBr", "Linux\\SSH & SFTP\\SSH Tunnel", "doc"),
    ("5cD1lEtYa6ZdNf3HbJsSg8MkVq4XuIwCs", "Linux\\SSH & SFTP\\SSH with Private Key", "doc"),
    ("6eF2mFuZb7AeOg4IcKtTh9NlWr5YvJxDt", "Linux\\Firewall", "doc"),
    ("7gH3nGvAc8BfPh5JdLuUi0OmXs6ZwKyEu", "Linux\\Installations\\Install docker", "doc"),
    ("8iJ4oHwBd9CgQi6KeMvVj1PnYt7AxLzFv", "Linux\\Linux Path Cheatsheet", "image"),
    ("9kL5pIxCe0DhRj7LfNwWk2QoZu8ByMaGw", "Networking\\Networking", "doc"),
    ("0mN6qJyDf1EiSk8MgOxXl3RpAv9CzNbHx", "Networking\\8 Popular Network Protocols", "image"),
    ("1oP7rKzEg2FjTl9NhPyYm4SqBw0DaOcIy", "Networking\\OSI Layers and Protocols Example", "image"),
    ("2qR8sLaFh3GkUm0OiQzZn5TrCx1EbPdJz", "Nginx\\Nginx", "doc"),
    ("3sT9tMbGi4HlVn1PjRaAo6UsDy2FcQeKa", "Nginx\\Load Balancer", "doc"),
    ("4uV0uNcHj5ImWo2QkSbBp7VtEz3GdRfLb", "Nginx\\Proxy", "doc"),
    ("5wX1vOdIk6JnXp3RlTcCq8WuFa4HeSgMc", "Node.js\\Node.js", "doc"),
    ("6yZ2wPeJl7KoYq4SmUdDr9XvGb5IfThNd", "Node.js\\Node\\server", "code"),
    ("7aB3xQfKm8LpZr5TnVeEs0YwHc6JgUiOe", "Python\\Python Notes\\Async\\Asyncio", "doc"),
    ("8cD4yRgLn9MqAs6UoWfFt1ZxId7KhVjPf", "Python\\Python Notes\\Threading\\testThreading_1", "code"),
    ("9eF5zShMo0NrBt7VpXgGu2AyJe8LiWkQg", "Python\\Python Notes\\Pandas\\Pandas", "doc"),
    ("0gH6aTiNp1OsCu8WqYhHv3BzKf9MjXlRh", "Python\\VectorDB\\VectorDB Libraries Installation", "doc"),
    ("1iJ7bUjOq2PtDv9XrZiIw4CaLg0NkYmSi", "SQL\\Postgres", "doc"),
    ("2kL8cVkPr3QuEw0YsAjJx5DbMh1OlZnTj", "SQL\\MSSQL", "doc"),
    ("3mN9dWlQs4RvFx1ZtBkKy6EcNi2PmAoUk", "Redis\\Commands Cheat Sheet", "doc"),
    ("4oP0eXmRt5SwGy2AuClLz7FdOj3QnBpVl", "Security\\nmap\\nmap cheat sheet page1", "image"),
    ("5qR1fYnSu6TxHz3BvDmMa8GePk4RoCqWm", "Security\\Study Paths", "doc"),
    ("6sT2gZoTv7UyIa4CwEnNb9HfQl5SpDrXn", "VueJs\\Setup", "doc"),
    ("7uV3hApUw8VzJb5DxFoOc0IgRm6TqEsYo", "VueJs\\Vue Nonce-based CSP", "doc"),
    ("8wX4iBqVx9WaKc6EyGpPd1JhSn2UrFtZp", "Windows Commands\\Windows Commands", "doc"),
]

# Ordered by distance the way TextEmbedderService.query() returns them.
SEARCH_RESULTS = [
    {
        "id": "4aB0kDsXz5YcMe2GaIrRf7LjUp3WtHvBr",
        "label": "Linux\\SSH & SFTP\\SSH Tunnel",
        "kind": "doc",
        "distance": 0.2841,
        "modified": "2026-05-18 09:41",
        "snippet": "Local port forwarding: ssh -L 8080:localhost:80 user@host. Reverse tunnel "
                   "exposes a local service on the remote side with -R ...",
    },
    {
        "id": "5cD1lEtYa6ZdNf3HbJsSg8MkVq4XuIwCs",
        "label": "Linux\\SSH & SFTP\\SSH with Private Key",
        "kind": "doc",
        "distance": 0.3517,
        "modified": "2026-04-02 16:07",
        "snippet": "Generate the pair with ssh-keygen -t ed25519, copy the public half to "
                   "~/.ssh/authorized_keys and tighten permissions to 600 ...",
    },
    {
        "id": "6eF2mFuZb7AeOg4IcKtTh9NlWr5YvJxDt",
        "label": "Linux\\Firewall",
        "kind": "doc",
        "distance": 0.4880,
        "modified": "2026-03-27 11:22",
        "snippet": "firewall-cmd --add-port=22/tcp --permanent then reload. Check the active "
                   "zone before opening anything on a public interface ...",
    },
    {
        "id": "8iJ4oHwBd9CgQi6KeMvVj1PnYt7AxLzFv",
        "label": "Linux\\Linux Path Cheatsheet",
        "kind": "image",
        "distance": 0.6123,
        "modified": "2026-01-14 20:55",
        "snippet": "-----img start----- /etc holds configuration, /var holds variable state, "
                   "/opt holds optional add-on packages ----- img end -----",
    },
    {
        "id": "0mN6qJyDf1EiSk8MgOxXl3RpAv9CzNbHx",
        "label": "Networking\\8 Popular Network Protocols",
        "kind": "image",
        "distance": 0.7402,
        "modified": "2025-11-08 13:30",
        "snippet": "HTTP, HTTPS, FTP, SMTP, SSH, DNS, DHCP, TCP - what each one is for and "
                   "which OSI layer it sits on ...",
    },
]

SEARCH_HISTORY = [
    ("ssh tunnel port forwarding", "2 min ago", 5),
    ("spring boot annotations", "18 min ago", 5),
    ("docker compose volumes", "1 hour ago", 5),
    ("chroma persistent client", "Yesterday", 4),
    ("nginx reverse proxy config", "Yesterday", 5),
    ("pytesseract image to string", "2 days ago", 3),
    ("quartz scheduler tables", "2 days ago", 5),
    ("mammoth convert docx to html", "5 days ago", 2),
]

SYNC_SUMMARY = [
    ("Added", "6", "success"),
    ("Updated", "11", "info"),
    ("Removed", "2", "warning"),
    ("Unchanged", "293", "neutral"),
]

SYNC_LOG = [
    ("10:24:01", "INFO", "Syncing collection"),
    ("10:24:01", "INFO", "Start syncing files"),
    ("10:24:03", "INFO", "Converting (changed): resources\\files\\Docker\\Docker General Notes.docx"),
    ("10:24:06", "INFO", "Converting (changed): resources\\files\\Nginx\\Proxy.docx"),
    ("10:24:07", "INFO", "Skipping (unchanged): resources\\files\\SQL\\Postgres.docx"),
    ("10:24:09", "WARN", "Skip unknown file: resources\\files\\Format PC\\Tools\\rufus-4.1.exe"),
    ("10:24:12", "INFO", "File sync completed - converted: 17, skipped: 331"),
    ("10:24:13", "INFO", "Fetching Drive file ids"),
    ("10:24:21", "INFO", "Upserting 17 documents into my_knowledge_drive"),
    ("10:24:24", "INFO", "Deleting 2 documents no longer on Drive"),
    ("10:24:25", "DONE", "Sync completed - added: 6, updated: 11, removed: 2, unchanged: 293"),
]

RESET_LOG = [
    ("09:02:11", "INFO", "Reseting collection"),
    ("09:02:11", "WARN", "Clearing: resources\\converted_files"),
    ("09:02:14", "INFO", "Start converting files"),
    ("09:04:52", "INFO", "Total converted files: 348"),
    ("09:04:53", "WARN", "Deleting collection my_knowledge_drive"),
    ("09:04:55", "INFO", "Start embedding files"),
    ("09:07:38", "DONE", "Total embedded files: 312"),
]


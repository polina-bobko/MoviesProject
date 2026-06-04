# Movies Search CLI

A console application for searching films in the **Sakila** MySQL database, with search history stored in **MongoDB**.

---

## Features

- Search films by **keyword** — matches against title and description
- Search films by **genre and release year range** — with paginated results
- Save all search queries to **MongoDB**
- View **top 5 popular queries** by frequency or by most recent date

---

## Project Structure

```
MoviesProject/
├── db/
│   ├── __init__.py
│   ├── mongo_client.py     # MongoDB connection and query history
│   ├── mysql_client.py     # MySQL connection and film queries
│   └── sql_queries.py      # Raw SQL query strings
├── .env                    # Environment variables (not committed)
├── .gitignore
├── errors.py               # Custom exceptions
├── logger.py               # Logging setup and decorator
├── main.py                 # Entry point
├── requirements.txt
├── settings.py             # Loads config from .env
└── ui.py                   # Console menu and user interaction
```

---

## Requirements

- Python 3.10+
- MySQL with the [Sakila](https://dev.mysql.com/doc/sakila/en/) database
- MongoDB instance

---

## Installation

**1. Clone the repository and navigate to the project folder:**

```bash
git clone <repository-url>
cd MoviesProject
```

**2. Create and activate a virtual environment:**

```bash
python -m venv .venv

# macOS / Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

**3. Install dependencies:**

```bash
pip install -r requirements.txt
```

**4. Configure environment variables:**

Copy the example below into a `.env` file in the project root and fill in your credentials:

```env
# MySQL
DB_HOST=your_mysql_host
DB_PORT=3306
DB_USER=your_mysql_user
DB_PASSWORD=your_mysql_password
DB_NAME=sakila

# MongoDB
MONGO_URL=mongodb://user:password@host/?authSource=db
MONGO_DB=your_mongo_database
MONGO_COLLECTION=your_collection_name

# Pagination
DB_PAGE_SIZE=10
```

---

## Usage

```bash
python main.py
```

### Main menu

```
=== Main menu ===
  1: Search films
  2: Popular queries
  0: Exit
```

### Search films

| Option | Description |
|--------|-------------|
| 1 | Search by keyword (title or description) |
| 2 | Search by genre and year range |

Results are displayed **10 at a time**. After each page you will be asked whether to load the next 10.

### Popular queries

| Option | Description |
|--------|-------------|
| 1 | Last 5 unique queries by date |
| 2 | Top 5 most frequently used queries |

---

## Dependencies

| Package | Version |
|---------|---------|
| PyMySQL | 1.2.0 |
| pymongo | 4.17.0 |
| dnspython | 2.8.0 |
| python-dotenv | 1.2.2 |

---

## Logging

All application events and errors are written to `app.log` in the project root.

---

## Notes

- The `.env` file is listed in `.gitignore` and will not be committed to version control.
- The Sakila database contains films from **1990** only — this is expected for this demo dataset.
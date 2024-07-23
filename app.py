from flask import Flask, render_template, url_for, request, redirect
from bs4 import BeautifulSoup
import sqlite3
import requests

app = Flask(__name__)

def init_db():
    with sqlite3.connect('manga_updates.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS manga_updates(
                id INTEGER PRIMARY KEY,
                chapter TEXT,
                date TEXT
            )
        ''')
        conn.commit()

    print("DB created")

@app.route('/')
def home():
    init_db()
    print("Home route accessed.")
    with sqlite3.connect('manga_updates.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT chapter, date FROM manga_updates')
        manga_updates = cursor.fetchall()
    print(f"Fetched manga updates: {manga_updates}")
    return(render_template("index.html", manga_updates = manga_updates))

@app.route('/scrape', methods=['POST'])
def scrape_manga():
    r = requests.get("https://kingofshojo.com/manga/nano-machine/")

    #scrape the html and find the div that contains the chapter lists
    soup = BeautifulSoup(r.content, 'html.parser')
    target_div = soup.find('div', {'class' : 'eplister', 'id': 'chapterlist'})

    if target_div:
        # Clean up the text
        cleaned_text = target_div.text.strip().split('\n')
        cleaned_text = [line.strip() for line in cleaned_text if line.strip()]

        # Pair chapters and dates
        cleaned_data = [(cleaned_text[i], cleaned_text[i + 1]) for i in range(0, len(cleaned_text), 2)]

        # Update the database
        with sqlite3.connect('manga_updates.db') as conn:
            cursor = conn.cursor()
            for chapter, date in cleaned_data:
                cursor.execute('''
                    INSERT INTO manga_updates(chapter, date)
                    VALUES (?, ?)
                ''', (chapter, date))
            conn.commit()

    return redirect('/')

if __name__ == "__main__":
    init_db()
    app.debug(True)
    app.run()
from flask import Flask, render_template, url_for, request, redirect
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from pytz import timezone
from bs4 import BeautifulSoup
import sqlite3
import requests

app = Flask(__name__)
cst = timezone('America/Chicago')
# creates the database table to store the updates on the chapter of manga
def init_db():
    with sqlite3.connect('manga_list.db') as conn:
        cursor = conn.cursor()
        cursor.execute('PRAGMA foreign_keys = ON;')
       # Create manga_updates table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS manga_updates(
                id INTEGER PRIMARY KEY,
                chapter TEXT,
                date TEXT,
                manga_id INTEGER,
                FOREIGN KEY (manga_id) REFERENCES manga_list(id)
            )
        ''')
        
         # Create manga_list table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS manga_list(
                    id INTEGER PRIMARY KEY,
                    manga_name TEXT,
                    url_link TEXT,
                    image_link TEXT
            )
        ''')
        conn.commit()

#routes to home page of the website and displays the data stored in the manga-list
@app.route('/')
def home():
    init_db()
    with sqlite3.connect('manga_list.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT manga_name, image_link FROM manga_list')
        manga_lists = cursor.fetchall()
    return render_template("index.html", manga_lists=manga_lists)

@app.route('/add-manga', methods=['GET', 'POST'])
def add_manga():
    if request.method == 'POST':
        manga_name = request.form['manga_name']
        manga_link = request.form['manga_link']
        add_manga_to_db(manga_name, manga_link)
        scrape_manga(manga_name, manga_link)
        return redirect('/')
    return render_template("add-manga.html")

#routes to manga page and displays the data of the chapters in the manga-list
def nano(manga_name):
    init_db()
    with sqlite3.connect('manga_list.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM manga_list WHERE manga_name = ?', (manga_name,))
        result = cursor.fetchone()
        if result:
            manga_id = result[0]
            cursor.execute('SELECT chapter, date FROM manga_updates WHERE manga_id = ?', (manga_id,))
            manga_updates = cursor.fetchall()
        else:
            manga_updates = []

    return(render_template("manga_detail.html", manga_updates = manga_updates, manga_name=manga_name))

#scrapes the chapter's name and data from a given url and stores them in the database
def scrape_manga(manga_name, manga_link_scrape):
    init_db()
    r = requests.get(manga_link_scrape)

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
        with sqlite3.connect('manga_list.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id FROM manga_list WHERE manga_name = ?', (manga_name,))
            result = cursor.fetchone()
            if result:
                manga_id = result[0]
                for chapter, date in cleaned_data:
                    cursor.execute('''
                        INSERT INTO manga_updates(chapter, date, manga_id)
                        VALUES (?, ?, ?)
                    ''', (chapter, date, manga_id))
                conn.commit()


def add_manga_to_db(manga_name, url):
    r = requests.get(url)

    soup = BeautifulSoup(r.content, 'html.parser')
    target_div = soup.find('div', {'class': 'thumb'})
    if target_div:
        # Find the img tag within the div and get its src attribute
        img_tag = target_div.find('img')
        if img_tag:
            image_url = img_tag['src']
        else:
            image_url = None
    else:
        image_url = None
    with sqlite3.connect('manga_list.db') as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO manga_list (manga_name, url_link, image_link)
            VALUES (?,?,?)''', (manga_name, url, image_url))
        conn.commit()

@app.route('/remove-manga', methods=['POST'])
def remove_manga():
    manga_name = request.form['manga_name']
    print(f"Removing manga: {manga_name}") 
    with sqlite3.connect('manga_list.db') as conn:
        cursor = conn.cursor()
        cursor.execute(' DELETE FROM manga_list WHERE manga_name = ?', (manga_name,))
        conn.commit()
    return redirect('/')

@app.route('/manga/<manga_name>')
def manga_detail(manga_name):
    return nano(manga_name)


@app.route('/search')
def manga_search():
    searched_name = request.args.get('query')
    print("searched_name:", searched_name)
    with sqlite3.connect('manga_list.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT manga_name FROM manga_list WHERE manga_name = ?', (searched_name,))
        searched = cursor.fetchone()
        if searched != None:
            print(searched[0])
            return redirect(url_for('manga_detail', manga_name = searched[0]))
        else:
            return print("Manga not found")

#creating a function that would periodically run the scrape_manga function while retreving the names and links of the manga
#from the manga_list database

def periodic_scraper():
    with sqlite3.connect('manga_list.db') as conn:
        cursor = conn.cursor()
        cursor.execute(' SELECT manga_name, url_link FROM manga_list')
        list = cursor.fetchall()
    
    for name, link in list:
        scrape_manga(name, link)

# Scheduler setup
def setup_scheduler():
    scheduler = BackgroundScheduler(timezone=cst)
    scheduler.add_job(periodic_scraper, CronTrigger(hour=23, minute=0))
    scheduler.start()

if __name__ == "__main__":
    setup_scheduler()
    app.run()
    
    

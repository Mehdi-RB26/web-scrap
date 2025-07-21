# Fichier : scrap.py
import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient
from datetime import datetime
import re
import certifi
import os
from dotenv import load_dotenv

load_dotenv()
# --- 1. Configuration ---
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = "blog_moderateur" 
COLLECTION_NAME = "articles"
# --- 2. Connexion à MongoDB ---
# On utilise certifi pour les certificats SSL
try:
    # On passe les certificats de la librairie certifi à MongoClient
    ca = certifi.where()
    client = MongoClient(MONGO_URI, tlsCAFile=ca)
   
    # Ping pour vérifier la connexion
    client.admin.command('ping')
    db = client.get_default_database()
    collection = db[COLLECTION_NAME]
    print("Connexion à MongoDB réussie.")
except Exception as e:
    print(f"Erreur de connexion à MongoDB : {e}")
    exit()
 
def scrape_article(article_url):
    """
    Scrape les informations d'une seule page d'article.
    """
    print(f"Scraping de l'article : {article_url}")
    try:
        response = requests.get(article_url, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Erreur lors de la requête HTTP pour {article_url}: {e}")
        return None
 
    soup = BeautifulSoup(response.content, 'html.parser')
 
    # --- Extraction des données ---
    try:
        title = soup.find('h1', class_='entry-title').get_text(strip=True)
    except AttributeError:
        title = "Titre non trouvé"
 
    try:
        thumbnail_url = soup.find('figure', class_='article-hat-img').find('img')['src']
    except (AttributeError, KeyError):
        thumbnail_url = "URL de miniature non trouvée"
 
    try:
        # La catégorie est dans un 'span' avec la classe 'hat-link'
        tags = soup.select('ul.tags-list li a.post-tags')
        subcategories = [tag.get_text(strip=True) for tag in tags]
    except AttributeError:
        subcategories = ["Sous-catégorie non trouvée"]
 
    try:
        summary_div = soup.select_one('div[class*="col-12"]')
        summary = summary_div.find("p").get_text(strip=True) if summary_div else "Résumé non trouvé"
    except AttributeError:
        summary = "Résumé non trouvé"
 
    try:
        pub_date_str = soup.find('time', class_='entry-date')['datetime']
        pub_date = datetime.fromisoformat(pub_date_str).strftime('%Y-%m-%d')
    except (AttributeError, KeyError):
        pub_date = "Date non trouvée"
 
    try:
        author = soup.find('span', class_='byline').get_text(strip=True)
    except AttributeError:
        author = "Auteur non trouvé"
 
    content_div = soup.find('div', class_='entry-content')
    if content_div:
        # Nettoyage amélioré pour enlever les scripts, styles, etc.
        for unwanted_tag in content_div.find_all(['script', 'style']):
            unwanted_tag.decompose()
        content_text = ' '.join(content_div.get_text(separator=' ', strip=True).split())
    else:
        content_text = "Contenu non trouvé"
       
    images_dict = {}
    if content_div:
        for img in content_div.find_all('img'):
            img_url = img.get('src') or img.get('data-src')
            img_alt = img.get('alt', 'Image sans légende')
            if img_url:
                images_dict[img_url] = img_alt
   
    article_data = {
        'url': article_url,
        'title': title,
        'thumbnail_url': thumbnail_url,
        'subcategory': subcategories,
        'summary': summary,
        'publication_date': pub_date,
        'author': author,
        'content': content_text,
        'images': images_dict,
        'scraped_at': datetime.now()
    }
   
    return article_data
 
def save_to_mongodb(data):
    """
    Sauvegarde (ou met à jour) un document dans la collection MongoDB.
    """
    if not data:
        return
    try:
        collection.update_one(
            {'url': data['url']},
            {'$set': data},
            upsert=True
        )
        print(f"-> Article '{data.get('title', 'Sans titre')}' sauvegardé.")
    except Exception as e:
        print(f"Erreur lors de la sauvegarde MongoDB pour {data.get('url')}: {e}")
 
def main():
    """
    Fonction principale pour orchestrer le scraping via le flux RSS.
    """
    RSS_URL = "https://www.blogdumoderateur.com/feed/"
    print(f"Récupération des articles depuis le flux RSS : {RSS_URL}")
   
    try:
        response = requests.get(RSS_URL, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Impossible de charger le flux RSS : {e}")
        return
 
    # On utilise 'xml' comme parser car un flux RSS est du XML
    soup = BeautifulSoup(response.content, 'xml')
   
    # Dans un flux RSS, le lien est dans une balise <link> à l'intérieur d'un <item>
    urls_to_scrape = [item.link.text for item in soup.find_all('item')]
 
    if not urls_to_scrape:
        print("Aucun article trouvé dans le flux RSS. Le format a peut-être changé.")
        return
 
    print(f"{len(urls_to_scrape)} articles trouvés dans le flux RSS.")
 
    for url in urls_to_scrape:
        # Les flux RSS peuvent contenir des liens vers les commentaires, on les ignore.
        if '/feed' not in url:
            article_data = scrape_article(url)
            save_to_mongodb(article_data)
 
    print("\n--- Scraping terminé ---")
 
if __name__ == "__main__":
    main()
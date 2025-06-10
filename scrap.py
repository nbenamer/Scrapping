import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json

HEADERS = {
    'User-Agent': 'Mozilla/5.0'
}

def fetch_article_urls(page_url):
    try:
        response = requests.get(page_url, headers=HEADERS)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        main_tag = soup.find('main')
        articles = main_tag.find_all('article') if main_tag else []
        urls = []

        for article in articles:
            a_tag = article.find('a', href=True)
            if a_tag:
                urls.append(a_tag['href'])
        return urls
    except Exception as e:
        print(f"Erreur récupération URL page {page_url} : {e}")
        return []

def clean_text(text):
    return ' '.join(text.strip().split())

def extract_article_data(url):
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        main = soup.find('main') or soup

        # 1. Titre
        title_tag = main.find('h1')
        title = clean_text(title_tag.get_text()) if title_tag else None

        # 2. Image miniature principale
        thumbnail_meta = soup.find('meta', property='og:image')
        thumbnail_url = thumbnail_meta['content'] if thumbnail_meta else None

        # 3. Sous-catégorie
        tag_div = soup.find('div', class_='favtag')
        subcategory = clean_text(tag_div.get_text()) if tag_div else None

        # 4. Résumé (chapô)
        excerpt = None
        excerpt_div = soup.find('div', class_='chapo')
        if excerpt_div:
            excerpt = clean_text(excerpt_div.get_text())
        else:
            first_strong = soup.find('strong')
            if first_strong:
                excerpt = clean_text(first_strong.get_text())

        # 5. Date de publication
        date_meta = soup.find('meta', property='article:published_time')
        raw_date = date_meta['content'] if date_meta else None
        pub_date = None
        if raw_date:
            try:
                pub_date = datetime.fromisoformat(raw_date).strftime("%Y-%m-%d")
            except Exception:
                pub_date = raw_date[:10]

  # 6. Auteur
        author = None
        author_link = soup.find('a', href=lambda href: href and '/auteur/' in href)
        if author_link:
            author = clean_text(author_link.get_text())


        # 7. Contenu (bloc texte)
        content_div = soup.find('div', class_='entry-content')
        paragraphs = content_div.find_all(['p', 'h2', 'h3']) if content_div else []
        full_content = "\n\n".join([clean_text(p.get_text()) for p in paragraphs if p.get_text(strip=True)])

        # 8. Images avec légendes
        image_dict = {}
        if content_div:
            images = content_div.find_all('img')
            for idx, img in enumerate(images):
                img_url = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
                alt = img.get('alt') or img.get('title') or ''
                if img_url:
                    image_dict[f'image_{idx+1}'] = {
                        'url': img_url,
                        'alt': clean_text(alt)
                    }

        return {
            'url': url,
            'title': title,
            'thumbnail': thumbnail_url,
            'subcategory': subcategory,
            'excerpt': excerpt,
            'date': pub_date,
            'author': author,
            'content': full_content,
            'images': image_dict
        }

    except Exception as e:
        print(f"Erreur scraping article : {url}\n{e}")
        return None

# -------------------- EXÉCUTION --------------------

base_url = "https://www.blogdumoderateur.com/web/page/{}/"
all_article_urls = []

# Étape 1 : récupérer les URLs des articles des 5 premières pages
for page in range(1, 6):  # pages 1 à 5
    url = base_url.format(page)
    print(f"📄 Scraping page: {url}")
    article_urls = fetch_article_urls(url)
    all_article_urls.extend(article_urls)

# Supprimer les doublons
all_article_urls = list(set(all_article_urls))

# Étape 2 : scraper les articles
data = []
for url in all_article_urls:
    print(f"🔍 Scraping article: {url}")
    article_data = extract_article_data(url)
    if article_data:
        data.append(article_data)

# Étape 3 : export JSON
with open('articles.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

print(f"\n✅ {len(data)} articles exportés dans 'articles.json'")


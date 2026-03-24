import re
import requests
from bs4 import BeautifulSoup

def fetch_google_scholar_metrics(scholar_id):
    url = f"https://scholar.google.ca/citations?user={scholar_id}&hl=en"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Error fetching Google Scholar page: {response.status_code}")
            return None
    except Exception as e:
        print(f"Request failed: {e}")
        return None
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Google Scholar uses a table with class 'gsc_rsb_std' for indices
    metrics = soup.find_all('td', class_='gsc_rsb_std')
    
    if len(metrics) < 6:
        print("Could not find all expected metrics on the page.")
        return None
    
    # The metrics are usually: Citations (All, Since), h-index (All, Since), i10-index (All, Since)
    # index 0: Citations (All)
    # index 2: h-index (All)
    # index 4: i10-index (All)
    
    data = {
        "citations": metrics[0].text.strip(),
        "hindex": metrics[2].text.strip(),
        "i10index": metrics[4].text.strip()
    }
    return data

def update_index_html(data):
    file_path = "index.html"
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Avoid raw string backreference issues by using non-regex replacement or careful group handling
    patterns = [
        (r'(<span id="citation-count"[^>]*>)[^<]*(</span>)', data["citations"]),
        (r'(<span id="h-index"[^>]*>)[^<]*(</span>)', data["hindex"]),
        (r'(<span id="i10-index"[^>]*>)[^<]*(</span>)', data["i10index"]),
    ]
    
    for pattern, value in patterns:
        # Use a lambda for repl to avoid backreference interpretation of the value if it has numbers
        content = re.sub(pattern, lambda m: f"{m.group(1)}{value}{m.group(2)}", content)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Successfully updated index.html with latest metrics.")

if __name__ == "__main__":
    SCHOLAR_ID = "sLVsbB0AAAAJ"
    metrics = fetch_google_scholar_metrics(SCHOLAR_ID)
    if metrics:
        print(f"Fetched metrics: {metrics}")
        update_index_html(metrics)
    else:
        print("Failed to fetch metrics.")

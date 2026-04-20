import re
import requests
from bs4 import BeautifulSoup
import time
import random
import sys

def fetch_google_scholar_metrics(scholar_id):
    url = f"https://scholar.google.ca/citations?user={scholar_id}&hl=en"
    
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, Gecko) Chrome/120.0.0.0 Safari/537.36"
    ]
    
    for attempt in range(3):
        headers = {
            "User-Agent": random.choice(user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        
        try:
            print(f"Attempt {attempt + 1}: Fetching Google Scholar page...")
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                metrics = soup.find_all('td', class_='gsc_rsb_std')
                
                if len(metrics) >= 6:
                    data = {
                        "citations": metrics[0].text.strip(),
                        "hindex": metrics[2].text.strip(),
                        "i10index": metrics[4].text.strip(),
                        "source": "Google Scholar"
                    }
                    return data
                else:
                    print("Could not find all expected metrics on Google Scholar page.")
            elif response.status_code == 429:
                print("Google Scholar returned 429 (Too Many Requests). Waiting before retry...")
            else:
                print(f"Error fetching Google Scholar page: {response.status_code}")
                
        except Exception as e:
            print(f"Request failed: {e}")
        
        # Exponential backoff with jitter
        wait_time = (2 ** attempt) + random.random() * 2
        time.sleep(wait_time)
        
    return None

def fetch_semantic_scholar_metrics(author_id):
    print(f"Attempting fallback to Semantic Scholar for ID: {author_id}")
    url = f"https://api.semanticscholar.org/graph/v1/author/{author_id}?fields=citationCount,hIndex"
    
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            data = response.json()
            return {
                "citations": str(data.get("citationCount", "N/A")),
                "hindex": str(data.get("hIndex", "N/A")),
                "i10index": None, # Semantic Scholar doesn't provide i10 directly in basic author info
                "source": "Semantic Scholar"
            }
        else:
            print(f"Semantic Scholar API error: {response.status_code}")
    except Exception as e:
        print(f"Semantic Scholar request failed: {e}")
        
    return None

def update_index_html(data):
    file_path = "index.html"
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # If i10index is None (from fallback), try to preserve the old value
    if data["i10index"] is None:
        match = re.search(r'<span id="i10-index"[^>]*>([^<]*)</span>', content)
        data["i10index"] = match.group(1) if match else "N/A"

    patterns = [
        (r'(<span id="citation-count"[^>]*>)[^<]*(</span>)', data["citations"]),
        (r'(<span id="h-index"[^>]*>)[^<]*(</span>)', data["hindex"]),
        (r'(<span id="i10-index"[^>]*>)[^<]*(</span>)', data["i10index"]),
    ]
    
    for pattern, value in patterns:
        content = re.sub(pattern, lambda m: f"{m.group(1)}{value}{m.group(2)}", content)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Successfully updated index.html with latest metrics from {data['source']}.")

if __name__ == "__main__":
    SCHOLAR_ID = "sLVsbB0AAAAJ"
    SEMANTIC_ID = "144675661"
    
    metrics = fetch_google_scholar_metrics(SCHOLAR_ID)
    
    if not metrics:
        print("Google Scholar fetch failed. Falling back to Semantic Scholar...")
        metrics = fetch_semantic_scholar_metrics(SEMANTIC_ID)
        
    if metrics:
        print(f"Final metrics: {metrics}")
        update_index_html(metrics)
    else:
        print("Failed to fetch metrics from all sources. Exiting with error.")
        sys.exit(1)

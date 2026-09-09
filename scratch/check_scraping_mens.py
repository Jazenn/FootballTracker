import requests
from bs4 import BeautifulSoup

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def check_url(url, label):
    print(f"\nFetching {label} program from {url}...")
    try:
        r = requests.get(url, headers=headers, timeout=15)
        print(f"Status Code: {r.status_code}")
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            title = soup.find("title")
            print(f"Title: {title.text if title else 'None'}")
            
            # Print some match info if found
            blocks = soup.find_all(class_="Matchblock")
            print(f"Found {len(blocks)} Matchblocks")
            for b in blocks[:5]:
                wrapper = b.find(class_="Matchblock-wrapper")
                title_attr = wrapper.get("title") if wrapper else "No title"
                
                # Check metadata
                meta = b.find(class_="Matchblock-metadata")
                date_el = meta.find(class_="Matchblock-metadata--date") if meta else None
                time_el = meta.find(class_="Matchblock-metadata--time") if meta else None
                note_el = meta.find(class_="Matchblock-metadata--note") if meta else None
                
                date_str = date_el.text.strip() if date_el else "None"
                time_str = time_el.text.strip() if time_el else ""
                note_str = note_el.text.strip() if note_el else ""
                
                print(f"  - Match: {title_attr}")
                print(f"    Date: {date_str}, Time: {time_str}, Note: {note_str}")
        else:
            print("Failed to load page")
    except Exception as e:
        print(f"Error: {e}")

check_url("https://www.onsoranje.nl/teams/185189/programma", "Men's National Team")

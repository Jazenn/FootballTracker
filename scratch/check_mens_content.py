import requests
from bs4 import BeautifulSoup

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
r = requests.get("https://www.onsoranje.nl/teams/185189/programma", headers=headers, timeout=15)
soup = BeautifulSoup(r.text, "html.parser")

print("Dossier Menu Items:")
for item in soup.find_all(class_="DossierMenu-item"):
    print(f"- {item.text.strip()}")

content = soup.find(class_="Template-content")
if content:
    print("\nTemplate-content:")
    print(content.text.strip()[:1000])
else:
    print("\nNo Template-content class found")
    
# Let's search for "Matchblock"
print(f"\nNumber of Matchblocks: {len(soup.find_all(class_='Matchblock'))}")
print(f"Number of Matchevent-items: {len(soup.find_all(class_='Matchevent-item'))}")

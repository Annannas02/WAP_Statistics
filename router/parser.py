from bs4 import BeautifulSoup

def parse_device_info(html: str):
    soup = BeautifulSoup(html, 'html.parser')
    rows = soup.find_all('tr')
    results = []
    for row in rows:
        cols = row.find_all('td')
        if len(cols) >= 5:
            results.append({
                "hostname": cols[0].text.strip(),
                "ip": cols[1].text.strip(),
                "mac": cols[2].text.strip(),
                "status": cols[3].text.strip(),
                "duration": cols[4].text.strip(),
            })
    return results
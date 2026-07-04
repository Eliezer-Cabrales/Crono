import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta

def get_meeting_data():
    """
    Scrapes the JW meeting schedule website, using hierarchical DOM navigation 
    to pair assignment titles (h3) with their durations.
    """
    base_url = "https://www.jw.org/es/biblioteca/guia-actividades-reunion-testigos-jehova/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        # Calculate the Monday of the current week to use as a consistent reference
        now = datetime.now()
        monday = now - timedelta(days=now.weekday())

        # 1. Connect to the main page
        response = requests.get(base_url, headers=headers)
        if response.status_code != 200:
            return None
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 2. Get the link for the current workbook using the monday date
        current_month_workbook = get_mwb_storage_name(monday)
        current_workbook_link = None
        for link in soup.find_all('a', href=True):
            if current_month_workbook in link['href']:
                current_workbook_link = "https://www.jw.org" + link['href']
                break

        if not current_workbook_link:
            current_workbook_link = base_url

        # 3. Connect to the specific week
        workbook_response = requests.get(current_workbook_link, headers=headers)
        workbook_soup = BeautifulSoup(workbook_response.text, 'html.parser')

        week_link = None
        week_workbook_name = get_weekly_range_storage_name(monday)
        for link in workbook_soup.find_all('a', href=True):
            if week_workbook_name in link['href']:
                week_link = "https://www.jw.org" + link['href']
                break
        
        if not week_link:
            return None

        week_workbook_response = requests.get(week_link, headers=headers)
        week_soup = BeautifulSoup(week_workbook_response.text, 'html.parser')

        # 4. Extract assignments by looking for the preceding h3
        assignments = []
        time_pattern = re.compile(r'\((\d+)\s*mins?\.?\)')

        all_paragraphs = week_soup.find_all('p')
        
        for p in all_paragraphs:
            match = time_pattern.search(p.get_text())
            if match:
                duration = int(match.group(1))
                
                # Search for the nearest h3 in the DOM tree (going upwards)
                title_element = p.find_previous('h3')
                title = title_element.get_text().strip() if title_element else "Untitled assignment"
                
                # Avoid duplicates if the same h3 has multiple time paragraphs
                if not any(a['title'] == title for a in assignments):
                    assignments.append({
                        "title": title,
                        "duration_mins": duration
                    })

        return assignments

    except Exception as e:
        print(f"Scraping error: {e}")
        return None

def get_mwb_storage_name(reference_date):
    """
    Calculates the workbook name based on the provided reference date (Monday).
    """
    months_es = {1: "enero", 2: "febrero", 3: "marzo", 4: "abril", 
                 5: "mayo", 6: "junio", 7: "julio", 8: "agosto", 
                 9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"}
    
    month = reference_date.month
    year = reference_date.year
    
    # Logic: Odd months (1, 3...) are start of workbook, even months (2, 4...) are end.
    if month % 2 != 0:
        first_month = months_es[month]
        second_month = months_es[month + 1] if month < 12 else months_es[1]
    else:
        first_month = months_es[month - 1]
        second_month = months_es[month]
        
    return f"{first_month}-{second_month}-{year}-mwb"

def get_weekly_range_storage_name(monday):
    """
    Gets the weekly range format based on the Monday of the target week.
    """
    sunday = monday + timedelta(days=6)
    months_es = {1: "enero", 2: "febrero", 3: "marzo", 4: "abril", 
                 5: "mayo", 6: "junio", 7: "julio", 8: "agosto", 
                 9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre"}
    
    if monday.month == sunday.month:
        return f"{monday.day}-{sunday.day}-de-{months_es[monday.month]}"
    else:
        return f"{monday.day}-de-{months_es[monday.month]}-a-{sunday.day}-de-{months_es[sunday.month]}"

if __name__ == "__main__":
    data = get_meeting_data()
    if data:
        for item in data:
            print(f"- {item['title']}: {item['duration_mins']} min")
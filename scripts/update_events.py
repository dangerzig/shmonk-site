#!/usr/bin/env python3
"""
Fetch upcoming events for Dan Zigmond from various venues and update the Teaching page.

Usage:
    python scripts/update_events.py

This script fetches events from:
- Esalen Institute
- SF Dharma Collective
- (Add more sources as needed)

Then updates the teaching.html file between the EVENTS_START and EVENTS_END markers.
"""

import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path

# Configuration
TEACHING_PAGE = Path(__file__).parent.parent / "teaching.html"
EVENTS_START_MARKER = "<!-- EVENTS_START -->"
EVENTS_END_MARKER = "<!-- EVENTS_END -->"

def fetch_esalen_events():
    """Fetch Dan Zigmond's events from Esalen Institute."""
    events = []
    try:
        url = "https://www.esalen.org/faculty/dan-zigmond"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Look for workshop links - Esalen's structure may vary
        # This looks for links containing "workshops" in the href
        for link in soup.find_all('a', href=re.compile(r'/workshops/')):
            workshop_url = link.get('href')
            if not workshop_url.startswith('http'):
                workshop_url = f"https://www.esalen.org{workshop_url}"

            # Try to extract event details from the page
            title = link.get_text(strip=True)
            if title and 'dan' not in title.lower():  # Skip if it's just a name link
                # Look for date nearby
                parent = link.find_parent(['div', 'li', 'article'])
                date_text = ""
                if parent:
                    text = parent.get_text()
                    # Look for date patterns
                    date_match = re.search(r'(\w+ \d+[–-]\d+,? \d{4})', text)
                    if date_match:
                        date_text = date_match.group(1)

                events.append({
                    'title': title,
                    'date': date_text,
                    'location': 'Esalen Institute, Big Sur',
                    'url': workshop_url
                })
    except Exception as e:
        print(f"Error fetching Esalen events: {e}")

    return events

def fetch_sfdc_events():
    """Fetch Dan Zigmond's events from SF Dharma Collective.

    Note: SFDC uses Gatsby with client-side rendering, so we try multiple approaches:
    1. Fetch the page-data.json endpoints that Gatsby uses
    2. Fall back to searching the HTML if that fails

    SFDC events are always at 7pm and are hybrid (in-person and online).
    """
    events = []
    try:
        # Try Gatsby page-data endpoint first
        page_data_urls = [
            "https://sfdharmacollective.org/page-data/upcoming-events/page-data.json",
            "https://sfdharmacollective.org/page-data/events/page-data.json",
        ]

        for page_data_url in page_data_urls:
            try:
                response = requests.get(page_data_url, timeout=10)
                if response.status_code == 200:
                    import json
                    data = response.json()
                    # Search through the JSON for events mentioning Dan Zigmond
                    data_str = json.dumps(data).lower()
                    if 'zigmond' in data_str or 'dan' in data_str:
                        # Found potential match - parse the structure
                        # Gatsby stores data in result.data or result.pageContext
                        result = data.get('result', {})
                        page_data = result.get('data', {})

                        # Look for event-like structures
                        for key, value in page_data.items():
                            if isinstance(value, dict) and 'edges' in value:
                                for edge in value['edges']:
                                    node = edge.get('node', {})
                                    title = node.get('title', node.get('name', ''))
                                    if 'zigmond' in str(node).lower():
                                        event_url = node.get('url', node.get('slug', ''))
                                        if event_url and not event_url.startswith('http'):
                                            event_url = f"https://sfdharmacollective.org{event_url}"
                                        date_str = node.get('date', node.get('startDate', ''))
                                        if date_str:
                                            date_str = f"{date_str}, 7pm"
                                        events.append({
                                            'title': title or 'Event with Dan Zigmond',
                                            'date': date_str,
                                            'location': 'SF Dharma Collective, San Francisco · Hybrid (in-person and online)',
                                            'url': event_url or 'https://sfdharmacollective.org/upcoming-events'
                                        })
            except Exception as e:
                print(f"  Could not fetch {page_data_url}: {e}")
                continue

        # Fallback: try the HTML approach
        if not events:
            url = "https://sfdharmacollective.org/upcoming-events"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # Look for events mentioning Dan Zigmond
            page_text = soup.get_text().lower()
            if 'dan zigmond' in page_text or 'zigmond' in page_text:
                for event in soup.find_all(['article', 'div'], class_=re.compile(r'event')):
                    if 'zigmond' in event.get_text().lower():
                        title_elem = event.find(['h2', 'h3', 'h4', 'a'])
                        title = title_elem.get_text(strip=True) if title_elem else "Event"

                        link = event.find('a', href=True)
                        event_url = link['href'] if link else "https://sfdharmacollective.org/upcoming-events"
                        if not event_url.startswith('http'):
                            event_url = f"https://sfdharmacollective.org{event_url}"

                        events.append({
                            'title': title,
                            'date': '',  # Date would need parsing, but time is always 7pm
                            'location': 'SF Dharma Collective, San Francisco · Hybrid (in-person and online)',
                            'url': event_url
                        })
    except Exception as e:
        print(f"Error fetching SF Dharma Collective events: {e}")

    return events

def generate_events_html(events):
    """Generate HTML for the events list."""
    if not events:
        return '''        <p style="color: var(--color-text-light);">No upcoming events scheduled. Check back soon or <a href="http://eepurl.com/gOSn91" target="_blank" rel="noopener">join the mailing list</a> for updates.</p>'''

    html_parts = ['        <div class="services-list">']
    for event in events:
        date_location = []
        if event.get('date'):
            date_location.append(event['date'])
        if event.get('location'):
            date_location.append(event['location'])

        html_parts.append(f'''          <div style="padding: 1rem 0; border-bottom: 1px solid var(--color-border);">
            <strong>{event['title']}</strong><br>
            <span style="color: var(--color-text-light);">{' · '.join(date_location)}</span><br>
            <a href="{event['url']}" target="_blank" rel="noopener">Register →</a>
          </div>''')
    html_parts.append('        </div>')

    return '\n'.join(html_parts)

def update_teaching_page(events_html):
    """Update the teaching.html file with new events."""
    content = TEACHING_PAGE.read_text()

    # Find and replace content between markers
    pattern = f"{re.escape(EVENTS_START_MARKER)}.*?{re.escape(EVENTS_END_MARKER)}"
    replacement = f"{EVENTS_START_MARKER}\n{events_html}\n        {EVENTS_END_MARKER}"

    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

    if new_content != content:
        TEACHING_PAGE.write_text(new_content)
        print("Teaching page updated with new events.")
        return True
    else:
        print("No changes to teaching page.")
        return False

def main():
    print("Fetching events...")

    # Fetch from all sources
    all_events = []

    esalen_events = fetch_esalen_events()
    print(f"  Esalen: {len(esalen_events)} events")
    all_events.extend(esalen_events)

    sfdc_events = fetch_sfdc_events()
    print(f"  SF Dharma Collective: {len(sfdc_events)} events")
    all_events.extend(sfdc_events)

    # Remove duplicates and sort by date if possible
    # For now, just use as-is

    print(f"\nTotal events found: {len(all_events)}")
    for event in all_events:
        print(f"  - {event['title']}")

    # Generate HTML and update page
    events_html = generate_events_html(all_events)
    update_teaching_page(events_html)

    print("\nDone! Don't forget to commit and push changes.")

if __name__ == "__main__":
    main()

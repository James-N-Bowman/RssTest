from ast import Sub
import json
import urllib.request
from datetime import datetime
import re
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom


def fetch_json_data(api_url):
    """Fetch JSON data from API endpoint"""
    with urllib.request.urlopen(api_url) as response:
        return json.loads(response.read().decode())

def split_report_title(input_string):
    """
    Split a report string into ordinal/type and title components.
    
    Args:
        input_string: String like "58th Report - blah blah blah"
        
    Returns:
        tuple: (report_prefix, title) or ("", original_string) if invalid
    """
    # Define valid dividers: hyphen, en-dash, em-dash, colon
    # Using Unicode escape sequences to avoid encoding issues
    divider_pattern = r'\s*[-\u2013\u2014:]\s*'
    
    # Split on any of the valid dividers
    parts = re.split(divider_pattern, input_string, maxsplit=1)
    
    # Check if we got exactly 2 parts
    if len(parts) != 2:
        return ("", input_string)
    
    left_part = parts[0].strip()
    right_part = parts[1].strip()
    
    # Check if left part matches: ordinal number + "Report" or "Special Report"
    # Pattern: number + st/nd/rd/th + (optional whitespace) + "Special Report" or "Report"
    ordinal_pattern = r'^\d+(st|nd|rd|th)\s+(Special\s+)?Report$'
    
    if re.match(ordinal_pattern, left_part, re.IGNORECASE):
        return (left_part, right_part)
    else:
        return ("", input_string)

def create_rss_feed(feed_info, items):
    """
    Create RSS 2.0 feed from feed info and items
    
    feed_info: dict with keys: title, link, description, language (optional)
    items: list of dicts with keys: title, link, description, pubDate (ISO format), guid (optional)
    """
    # Create RSS root element
    rss = Element('rss', {
        'version': '2.0'#,
        #'xmlns:media': 'http://search.yahoo.com/mrss/'
    })
    channel = SubElement(rss, 'channel')
    
    # Add channel elements
    SubElement(channel, 'title').text = feed_info.get('title', 'RSS Feed')
    SubElement(channel, 'link').text = feed_info.get('link', '')
    SubElement(channel, 'description').text = feed_info.get('description', '')
    
    if 'language' in feed_info:
        SubElement(channel, 'language').text = feed_info['language']
    
    # Add last build date
    SubElement(channel, 'lastBuildDate').text = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
    
    # Add items
    for item_data in items:
        if item_data.get('committee'):
            if item_data.get('committee').get('house') == 'Lords':
                continue  # Skip items from House of Lords
            if item_data.get('committee').get('category'):
               if item_data.get('committee').get('category').get('name') != 'Select':
                   continue # Skip non-Select Committee items
        item = SubElement(channel, 'item')

        api_description = item_data.get('description', '')
        ordinal, title = split_report_title(api_description)
        committee = item_data.get('committee', dict())
        committee_name = committee.get('name','')

        rss_description = ordinal
        rss_description = rss_description.strip()
        
        SubElement(item, 'title').text = title
        SubElement(item, 'description').text = rss_description
        SubElement(item, 'author').text = committee_name
        
        image = SubElement(item, 'enclosure ')
        image.set('type', 'image/png')
        image.set('url', 'https://committees.parliament.uk/dist/opengraph-card.png')
        image.set('length', '123456')


        link_text = ''

        if item_data.get('additionalContentUrl', None) != None:
            link_text = item_data.get('additionalContentUrl', '')
        
        elif 'documents' in item_data and len(item_data['documents']) > 0:
            publication_id = item_data.get('id', None)
            document_id = item_data['documents'][0].get('documentId', None)
            if publication_id != None and document_id != None:
                link_text = f"https://committees.parliament.uk/publications/{publication_id}/documents/{document_id}/default/"
                                                
        SubElement(item, 'link').text = link_text
        
        # Parse and format pubDate
        if 'publicationStartDate' in item_data:
            try:
                # If pubDate is ISO format, convert to RFC 822
                pre_date_obj = item_data['publicationStartDate']+'Z'
                date_obj = datetime.fromisoformat(pre_date_obj)
                SubElement(item, 'pubDate').text = date_obj.strftime('%a, %d %b %Y %H:%M:%S GMT')
            except:
                SubElement(item, 'pubDate').text = item_data['publicationStartDate']
        
        # Add GUID (use link if not provided)
        guid_text = str(item_data.get('id'))
        SubElement(item, 'guid').text = guid_text
    
    return rss

def prettify_xml(elem):
    """Return a pretty-printed XML string"""
    rough_string = tostring(elem, encoding='unicode')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent='  ')

def generate_rss(api_url, output_file='docs/feed.xml'):
    """
    Main function to generate RSS feed
    
    Example JSON structure expected from API:
    {
        "items": [
            {
                "title": "Post Title",
                "link": "https://example.com/post1",
                "description": "Post description",
                "pubDate": "2024-01-15T10:00:00Z"
            }
        ]
    }
    """
    # Fetch data from API
    data = fetch_json_data(api_url)
    
    # Extract feed info and items
    feed_info = {
        "title": "House of Commons Select Committee Reports",
        "link": "https://committees.parliament.uk/publications/",
        "description": "Latest reports from House of Commons select committees"
    }
    
    items = data.get('items', [])
    
    # Create RSS feed
    rss = create_rss_feed(feed_info, items)
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(prettify_xml(rss))
    
    print(f"RSS feed generated: {output_file}")

if __name__ == '__main__':
    # Example usage - replace with your API endpoint
    API_URL = 'https://committees-api.parliament.uk/api/Publications?PublicationTypeIds=1&SortOrder=PublicationDateDescending&Skip=100'
    

    generate_rss(API_URL, 'docs/feed.xml')

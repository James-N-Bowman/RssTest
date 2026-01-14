import json
import urllib.request
from datetime import datetime
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

def fetch_json_data(api_url):
    """Fetch JSON data from API endpoint"""
    with urllib.request.urlopen(api_url) as response:
        return json.loads(response.read().decode())

def create_rss_feed(feed_info, items):
    """
    Create RSS 2.0 feed from feed info and items
    
    feed_info: dict with keys: title, link, description, language (optional)
    items: list of dicts with keys: title, link, description, pubDate (ISO format), guid (optional)
    """
    # Create RSS root element
    rss = Element('rss', version='2.0')
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
        item = SubElement(channel, 'item')
        SubElement(item, 'title').text = item_data.get('description', '')
        SubElement(item, 'link').text = item_data.get('additionalContentUrl', '')
        SubElement(item, 'description').text = item_data.get('actualDescription', '')
        
        # Parse and format pubDate
        if 'publicationStartDate' in item_data:
            try:
                # If pubDate is ISO format, convert to RFC 822
                pre_date_obj = item_data['publicationStartDate'].replace('T', '+00:00')
                date_obj = datetime.fromisoformat(pre_date_obj)
                SubElement(item, 'pubDate').text = date_obj.strftime('%a, %d %b %Y %H:%M:%S GMT')
            except:
                SubElement(item, 'pubDate').text = item_data['pubDate']
        
        # Add GUID (use link if not provided)
        guid_text = item_data.get('guid', item_data.get('additionalContentUrl', ''))
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
    API_URL = 'https://committees-api.parliament.uk/api/Publications?PublicationTypeIds=1&SortOrder=PublicationDateDescending&Take=4'
    

    generate_rss(API_URL, 'docs/feed.xml')

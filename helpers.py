import base64
from bs4 import BeautifulSoup
import re
from datetime import datetime
import pytz

def decode_base64_gmail(data):
    # Convert from Base64URL to Base64
    data = data.replace('-', '+').replace('_', '/')
    
    # Add padding if necessary
    missing_padding = len(data) % 4
    if missing_padding:
        data += '=' * (4 - missing_padding)
    
    # Decode the content   
    # Decode the content
    try:
        decoded_bytes = base64.b64decode(data)
        return decoded_bytes.decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"❌ Decoding failed: {e}")
    
    return ""

def is_html(text):
    soup = BeautifulSoup(text, "html.parser")
    return bool(soup.find())

def extract_text_from_html(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    return soup.get_text(separator=' ', strip=True)

def convert_to_jakarta_time(date_string):
    # Define the format of the Gmail API date string
    format_str = "%a, %d %b %Y %H:%M:%S %z"
    
    # Parse the string into a datetime object with UTC timezone
    utc_time = datetime.strptime(date_string, format_str)
    
    # Define Jakarta timezone (Asia/Jakarta is UTC+7)
    jakarta_timezone = pytz.timezone('Asia/Jakarta')
    
    # Convert UTC time to Jakarta time
    jakarta_time = utc_time.astimezone(jakarta_timezone)
    
    return jakarta_time.strftime("%m-%d-%Y")

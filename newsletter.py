from bs4 import BeautifulSoup
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import argparse
import datetime
import feedparser
import os
import requests
import smtplib
import hashlib
import csv
from dotenv import load_dotenv

def send_email(to_addr, content, subject, from_addr, mailgun_server, mailgun_password):
	# Create and configure the message
	message = MIMEMultipart()
	message['From'] = from_addr
	message['To'] = to_addr
	message['Subject'] = subject
	message.attach(MIMEText(content, 'html'))

	# Send the email
	with smtplib.SMTP(mailgun_server, 587) as server:
		server.starttls()
		server.login(from_addr, mailgun_password)
		server.send_message(message)

def unsub_link(email):
	string_to_hash = f'{{"email":"{email}"}}'
	hash_object = hashlib.sha256()
	# Update the hash object with the bytes of the input string
	hash_object.update(string_to_hash.encode())
	# Get the hexadecimal representation of the hash
	hash = hash_object.hexdigest()
	link = f'https://YOUR-WEBSITE.COM/unsubscribe/?e={hash}'
	return link

# Load environment variables
load_dotenv()

# Access credentials
subscribers_bearer_token = os.getenv('SUBSCRIBERS_BEARER_TOKEN')
mailgun_server = os.getenv('MAILGUN_SERVER')
mailgun_user = os.getenv('MAILGUN_USER')
mailgun_password = os.getenv('MAILGUN_PASSWORD')
from_name = os.getenv('FROM_NAME')
from_email = mailgun_user
from_addr = f'"{from_name}" <{from_email}>'

# Setup argument parser
parser = argparse.ArgumentParser(description='Send requests to API.')
parser.add_argument('--feed', type=str, required=True, help='RSS Feed URL')
parser.add_argument('--send', action='store_true', help='Use the production URL and send the emails')
parser.add_argument('--csv', type=str, help='Path to CSV file containing email addresses')
args = parser.parse_args()

# Fetch the latest feed
feed = feedparser.parse(args.feed)
if feed.bozo:
	print("Error parsing feed:", feed.bozo_exception)
	sys.exit(1)
if not feed.entries:
	print("No entries found in the feed.")
	sys.exit(1)

# Retrieve the latest post
latest_post = feed.entries[0]

# Read the HTML template
script_dir = os.path.dirname(os.path.realpath(__file__))
template_file_path = os.path.join(script_dir, 'templates', 'weekly-notes.html')
with open(template_file_path, 'r', encoding='utf-8') as file:
	html_template = file.read()

# Prepare content
current_date = datetime.datetime.now().strftime("%Y-%m-%d")
title = latest_post.title
content = latest_post.summary
soup = BeautifulSoup(content, 'html.parser')

p_style = "font-family: sans-serif; font-size: 16px; font-weight: normal; margin: 0; margin-bottom: 15px; margin-top:15px;"

# Find all <p> tags and apply the style
for p_tag in soup.find_all('p'):
	prev_sibling = p_tag.find_previous_sibling()
	if prev_sibling and prev_sibling.name == 'p':
		new_br_tag = soup.new_tag("br")
		p_tag.insert_before(new_br_tag)
	p_tag['style'] = p_style

# Resize images if they are wider than 400px
for img_tag in soup.find_all('img'):
	# Set the width to 100% to ensure full column width on all devices
	img_tag['style'] = "width: 100%; height: auto;"
	# Remove width and height attributes to prevent conflicts
	img_tag.attrs.pop('width', None)
	img_tag.attrs.pop('height', None)

# Update the content with modified HTML
content = str(soup)

# Replace placeholders in the template
email_content = html_template.replace("{{date}}", current_date)
email_content = email_content.replace("{{permalink}}", latest_post.link)
email_content = email_content.replace("{{title}}", title)
email_content = email_content.replace("{{content}}", content)

# Fetch email addresses
if args.csv:
	# Load email addresses from the CSV file
	email_addresses = []
	with open(args.csv, newline='') as csvfile:
		reader = csv.reader(csvfile)
		for row in reader:
			email_addresses.append(row[0])
else:
	# Determine the URL where to get the list of emails and authenticate with bearer token
	url = os.getenv('URL_FETCH_SUBSCRIBERS')
	if not args.send:
		url += '/dry-run'
	headers = { 'Authorization': f'Bearer {subscribers_bearer_token}' }
	response = requests.post(url, headers=headers)
	email_addresses = response.text.split(', ')

# Send emails
for to_addr in email_addresses:
	unsubscribe_link = unsub_link(to_addr)
	individual_content = email_content.replace("{{unsubscribe_link}}", unsubscribe_link)
	send_email(to_addr, individual_content, latest_post.title, from_addr, mailgun_server, mailgun_password)
	print(f"Email sent successfully to {to_addr}!")
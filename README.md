# Newsletter From RSS

A python script that picks up the latest post from an RSS feed to send it as an email newsletter.

The code finds the email addresses either from a subscription manager built with Node-RED (using an API) or from a CSV file. It generates the unsubscribe link with data from the server.

This would be a v1.0 if the script could work without fetching the addresses from the subscription manager.

## Assembly required

### Current way to fetch email addresses

By default, the script fetches email addresses from an API endpoint provided by a subscription manager:

```python
# Fetch email addresses
# Determine the URL where to get the list of emails and authenticate with bearer token
url = os.getenv('URL_FETCH_SUBSCRIBERS')
if not args.send:
    url += '/dry-run'
headers = { 'Authorization': f'Bearer {subscribers_bearer_token}' }
response = requests.post(url, headers=headers)
email_addresses = response.text.split(', ')
```

If you use Node-RED, you can import the file `nodered__subscription_manager_flow`.json and configure it to match your domain.

Alternatively, you can now load email addresses from a CSV file using the --csv argument.

###  Fetching email addresses from a CSV

If you prefer not to use the API, you can supply a CSV file containing the email addresses. The CSV file should have one email address per line.

Example of CSV usage:
```
# Load email addresses from a CSV file
email_addresses = []
with open(args.csv, newline='') as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
        email_addresses.append(row[0])
```

## Usage

Testing the email

`newsletter.py --feed https://WEBSITE.COM/feed`

Running the script without the `--send` argument will add `/dry-run` to the `url_fetch_subscribers` and expects to get a list of dummy emails that will be used for testing the resulting email.

Sending the email with API

`newsletter.py --feed https://WEBSITE.COM/feed --send`

Sending the email with CSV

`newsletter.py --feed https://WEBSITE.COM/feed --csv /path/to/emails.csv --send`

Remember to edit `example.env` to configure your settings.
## Templates

The `templates` directory has two examples on how to organise and format your email with html and a simple substitution logic.

Edit this line to change the template used:

`template_file_path = os.path.join(script_dir, 'templates', 'weekly-notes.html')`
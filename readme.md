# Zendesk Exporter

## Description
This project connects to the Zendesk API to retrieve tickets (and their comments), then exports the data to a CSV file. It:
- Uses environment variables instead of hard-coding credentials (for security)
- Handles pagination to fetch tickets in batches
- Fetches additional comments for each ticket, beyond the initial description
- Saves the final data to a timestamped CSV file

## Requirements
- **Python 3.8+**
- **Dependencies**:
  - [requests](https://pypi.org/project/requests/)
  - [pandas](https://pypi.org/project/pandas/)
  - [tqdm](https://pypi.org/project/tqdm/)

Install them with:
```bash
pip install requests pandas tqdm
```

Or, if you have a `requirements.txt` file:
```bash
pip install -r requirements.txt
```

## Setup
### Environment Variables
Your script relies on three environment variables for Zendesk credentials:

1. **ZENDESK_SUBDOMAIN**
   * The subdomain is the part **before** `.zendesk.com`
   * **Example:** If your Zendesk URL is `https://mycompany.zendesk.com`, then `mycompany` is the subdomain

2. **ZENDESK_EMAIL**
   * The email address associated with your Zendesk account

3. **ZENDESK_API_TOKEN**
   * The API token you generate from your Zendesk admin settings

### Setting Environment Variables
* **macOS/Linux (bash/zsh):**
```bash
export ZENDESK_SUBDOMAIN="mycompany"
export ZENDESK_EMAIL="my-email@example.com"
export ZENDESK_API_TOKEN="my-api-token"
python main.py
```

* **Windows (Command Prompt):**
```bash
set ZENDESK_SUBDOMAIN=mycompany
set ZENDESK_EMAIL=my-email@example.com
set ZENDESK_API_TOKEN=my-api-token
python main.py
```

* **Windows (PowerShell):**
```powershell
$env:ZENDESK_SUBDOMAIN="mycompany"
$env:ZENDESK_EMAIL="my-email@example.com"
$env:ZENDESK_API_TOKEN="my-api-token"
python main.py
```

## Usage
1. Install dependencies (see above)
2. Set your environment variables as shown
3. Run your script (for example, `python main.py`)
4. When prompted, enter the number of tickets to export or press Enter to export all

Once complete, the script will create a CSV file with the format:
```
zendesk_tickets_YYYYMMDD_HHMMSS.csv
```
This file will contain all ticket details and comments.

## Troubleshooting
* **Missing credentials**: If the script reports missing `ZENDESK_SUBDOMAIN`, `ZENDESK_EMAIL`, or `ZENDESK_API_TOKEN`, verify that you've set them correctly (see "Setting Environment Variables" above)
* **Rate limits**: Zendesk imposes rate limits; the script uses small `time.sleep` delays to avoid hitting them too quickly
* **Further help**: Refer to Zendesk's API documentation for more details on endpoints, parameters, and best practices
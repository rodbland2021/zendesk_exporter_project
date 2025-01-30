import os
import sys
import requests
import pandas as pd
import time
from datetime import datetime
from typing import List, Dict, Any
from tqdm import tqdm

class ZendeskExporter:
    def __init__(self, subdomain: str, email: str, api_token: str):
        """
        Initialize the ZendeskExporter with your credentials 
        (fetched from environment variables).
        """
        self.subdomain = subdomain
        self.credentials = (f"{email}/token", api_token)
        self.base_url = f"https://{subdomain}.zendesk.com/api/v2"

    def get_tickets(self, limit: int = None, start_time: str = None) -> List[Dict[Any, Any]]:
        """
        Retrieve tickets using pagination.
        
        Args:
            limit (int): Maximum number of tickets to retrieve (None for all).
            start_time (str): Optional ISO datetime string to get tickets 
                              after this time.
            
        Returns:
            List of ticket dictionaries.
        """
        all_tickets = []
        next_page = f"{self.base_url}/tickets.json?per_page=100"

        if start_time:
            next_page += f"&start_time={start_time}"

        with tqdm(desc="Fetching tickets", unit="tickets") as pbar:
            while next_page:
                response = requests.get(next_page, auth=self.credentials)
                
                if response.status_code != 200:
                    raise Exception(f"Failed to get tickets: {response.status_code}")
                    
                data = response.json()
                tickets_batch = data['tickets']
                
                # Update progress bar
                pbar.update(len(tickets_batch))
                
                all_tickets.extend(tickets_batch)
                
                # Check if we've reached the desired limit
                if limit and len(all_tickets) >= limit:
                    all_tickets = all_tickets[:limit]
                    break
                
                next_page = data['next_page']
                
                # Respect rate limits
                if next_page:
                    time.sleep(0.5)
                    
        return all_tickets

    def get_ticket_comments(self, ticket_id: int) -> List[Dict[Any, Any]]:
        """
        Get all comments for a specific ticket.
        
        Args:
            ticket_id (int): The ID of the Zendesk ticket.
        
        Returns:
            A list of comment dictionaries.
        """
        url = f"{self.base_url}/tickets/{ticket_id}/comments.json"
        response = requests.get(url, auth=self.credentials)
        
        if response.status_code != 200:
            print(f"Warning: Failed to get comments for ticket {ticket_id}")
            return []
            
        return response.json().get('comments', [])

    def get_tickets_with_comments(self, tickets: List[Dict[Any, Any]]) -> List[Dict[Any, Any]]:
        """
        Enrich ticket data with their comments.
        
        Args:
            tickets (List[Dict[Any, Any]]): The list of ticket dictionaries.
        
        Returns:
            A list of enriched ticket dictionaries, each including a field 
            for additional comments.
        """
        enriched_tickets = []
        
        print("\nFetching comments for each ticket...")
        for ticket in tqdm(tickets, desc="Fetching comments"):
            # Get comments for this ticket
            comments = self.get_ticket_comments(ticket['id'])
            
            # Skip the first comment if it duplicates the description
            additional_comments = comments[1:] if comments else []
            
            # Add comments to ticket data
            ticket_data = {
                'id': ticket['id'],
                'created_at': ticket['created_at'],
                'updated_at': ticket['updated_at'],
                'subject': ticket.get('subject', ''),
                'description': ticket.get('description', ''),
                'status': ticket.get('status', ''),
                'priority': ticket.get('priority', ''),
                'requester_id': ticket.get('requester_id', ''),
                'assignee_id': ticket.get('assignee_id', ''),
                'tags': ticket.get('tags', []),
                'comments': '\n---\n'.join([
                    f"Comment by {comment['author_id']} at {comment['created_at']}:\n{comment['body']}"
                    for comment in additional_comments
                ]) if additional_comments else ''
            }
            
            enriched_tickets.append(ticket_data)
            
            # Respect rate limits
            time.sleep(0.5)
            
        return enriched_tickets

    def export_to_csv(self, tickets: List[Dict[Any, Any]], filename: str = None) -> str:
        """
        Export tickets to a CSV file.
        
        Args:
            tickets (List[Dict[Any, Any]]): The list of ticket dictionaries 
                                            (potentially enriched with comments).
            filename (str): Name of the CSV file to create. If None, a 
                            time-stamped file name will be generated.
        
        Returns:
            The filename used for exporting.
        """
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"zendesk_tickets_{timestamp}.csv"
            
        df = pd.DataFrame(tickets)
        
        # Select important columns and rename them
        columns_to_export = {
            'id': 'Ticket ID',
            'created_at': 'Created Date',
            'updated_at': 'Last Updated',
            'subject': 'Subject',
            'description': 'Description',
            'status': 'Status',
            'priority': 'Priority',
            'requester_id': 'Requester ID',
            'assignee_id': 'Assignee ID',
            'tags': 'Tags',
            'comments': 'Additional Comments'
        }
        
        export_df = df[columns_to_export.keys()].rename(columns=columns_to_export)
        export_df.to_csv(filename, index=False, encoding='utf-8')
        
        return filename

def main():
    """
    Main function to run the Zendesk export process.
    It prompts for the number of tickets to export, fetches
    them from Zendesk, retrieves comments, and saves to CSV.
    """
    # Pull credentials from environment variables
    SUBDOMAIN = os.getenv("ZENDESK_SUBDOMAIN")
    EMAIL = os.getenv("ZENDESK_EMAIL")
    API_TOKEN = os.getenv("ZENDESK_API_TOKEN")
    
    # Check that all credentials are present
    if not all([SUBDOMAIN, EMAIL, API_TOKEN]):
        print("\nERROR: Missing Zendesk credentials. Please set these environment variables:\n"
              "  - ZENDESK_SUBDOMAIN\n"
              "  - ZENDESK_EMAIL\n"
              "  - ZENDESK_API_TOKEN\n")
        sys.exit(1)
    
    # Prompt user for how many tickets to export
    while True:
        try:
            user_input = input("How many tickets do you want to export? (press Enter for all tickets): ").strip()
            if user_input == "":
                limit = None
                break
            limit = int(user_input)
            if limit <= 0:
                print("Please enter a positive number.")
                continue
            break
        except ValueError:
            print("Please enter a valid number.")
    
    # Initialize the exporter
    exporter = ZendeskExporter(SUBDOMAIN, EMAIL, API_TOKEN)
    
    # Fetch tickets
    print("\nFetching tickets...")
    tickets = exporter.get_tickets(limit=limit)
    print(f"\nRetrieved {len(tickets)} tickets")

    # Enrich tickets with comments
    enriched_tickets = exporter.get_tickets_with_comments(tickets)

    # Export to CSV
    output_file = exporter.export_to_csv(enriched_tickets)
    print(f"\nTickets exported to: {output_file}")

if __name__ == "__main__":
    main()

import argparse
from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Execute GraphQL queries against CFBD API')
    parser.add_argument('--query', type=str, required=True, help='GraphQL query to execute')
    
    args = parser.parse_args()
    
    # Create transport around the CFBD GraphQL URL
    transport = AIOHTTPTransport(
        url="https://graphql.collegefootballdata.com/v1/graphql",
        headers={"Authorization": "Bearer 5aavtnwoq2REwn7hxzm3um9p3SonMPeDTEeVeC10ZoTe1T5y6+lmJgikKDlCpabD"}
    )
    
    # Create GraphQL client around this transport
    client = Client(transport=transport, fetch_schema_from_transport=True)
    
    # Execute the query from command line argument
    try:
        query = gql(args.query)
        result = client.execute(query)
        print("Query result:")
        print(result)
    except Exception as e:
        print(f"Error executing query: {e}")

if __name__ == "__main__":
    main()

import requests
import io
import pandas as pd

def authenticate(token: str, start_date: str, end_date: str) -> pd.DataFrame:
    """Fetch EN bulk data for a date range and return as DataFrame."""
    url = "https://us.engagingnetworks.app/ea-dataservice/export.service"
    querystring = {
        "token": token,
        "startDate": start_date,  # MMDDYYYY
        "endDate": end_date,      # MMDDYYYY
    }
    headers = {
        "Accept": "text/html; charset=UTF-8, text/xml; charset=UTF-8, text/csv; charset=UTF-8"
    }

    response = requests.get(url, headers=headers, params=querystring)
    response.raise_for_status()

    df = pd.read_csv(io.StringIO(response.text))
    return df

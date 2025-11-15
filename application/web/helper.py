import re
from typing import List


def extract_onions(s: str) -> List[str]:
    """
    Extract Onion v3 addresses from text.
    
    Extracts .onion URLs from the provided text using regex pattern matching.
    Supports URLs with or without protocol prefixes (http/https).
    Note: This function extracts potential onion addresses; validation for
    v3 format (56-character addresses) occurs downstream via is_valid_onion_url().
    
    Args:
        s: Text content to search for onion addresses
        
    Returns:
        List of extracted onion URLs (may include protocol prefix)
    """
    result = []
    print(s)
    # Extract .onion URLs - validation for v3 format happens downstream
    for m in re.finditer(r"(?:https?://)?(?:www)?(\S*?\.onion)\b", s, re.M | re.IGNORECASE):
        url = str(m.group(0))
        result.append(url)
    print(result)
    return result

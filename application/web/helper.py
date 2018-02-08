import re

def extract_onions(s):
    result = []
    print(s)
    for m in re.finditer(r'(?:https?://)?(?:www)?(\S*?\.onion)\b', s, re.M | re.IGNORECASE):
        url = str(m.group(0))
        if "'" in url:
            url = url[url.index("'")+1:]
        result.append(url)
    print(result)
    return result

def validate_onion(url):
    result = re.finditer(r'(?:https?://)?(?:www)?(\S*?\.onion)\b', url, re.M | re.IGNORECASE)
    if "'" in url:
        result = result[str(result).index("'") + 1:]
    print (result)
    if result:
        return False
    return True
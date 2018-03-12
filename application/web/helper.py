import re

def extract_onions(s):
    result = []
    print(s)
    for m in re.finditer(r'(?:https?://)?(?:www)?(\S*?\.onion)\b', s, re.M | re.IGNORECASE):
        url = str(m.group(0))
        url = url[len(url) - 22:]
        # if "'" in url:
        #     url = url[url.index("'")+1:]
        result.append(url)
    print(result)
    return result

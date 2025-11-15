"""
Application-wide constants.

This module defines all constant values used throughout the application,
including HTTP status codes, queue names, and other magic values.
"""

# HTTP Status Codes
HTTP_OK = 200
HTTP_CREATED = 201
HTTP_BAD_REQUEST = 400
HTTP_UNAUTHORIZED = 401
HTTP_FORBIDDEN = 403
HTTP_NOT_FOUND = 404
HTTP_METHOD_NOT_ALLOWED = 405
HTTP_INTERNAL_SERVER_ERROR = 500
HTTP_SERVICE_UNAVAILABLE = 503

# Queue Names
QUEUE_HIGH_PRIORITY = "high"
QUEUE_DEFAULT_PRIORITY = "default"
QUEUE_LOW_PRIORITY = "low"

# Redis Database Numbers (for reference, actual values in Settings)
REDIS_DB_PANEL = 0
REDIS_DB_APP = 1
REDIS_DB_DETECTOR = 2
REDIS_DB_CRAWLER = 3

# Pagination Defaults
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# Password Hashing
PASSWORD_HASH_METHOD = "pbkdf2:sha256"

# Crawling Constants
DEFAULT_CRAWL_DEPTH = 1
MAX_CRAWL_DEPTH = 5

# Document Status Codes
STATUS_PENDING = 0
STATUS_PROCESSING = 1
STATUS_COMPLETED = 2
STATUS_FAILED = 3

# File Extensions
ALLOWED_SEED_EXTENSIONS = {".txt", ".csv"}
ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif"}

# Spacy POS Tags
SPACY_TAG_MAP = {
    ".",
    ",",
    "-LRB-",
    "-RRB-",
    "``",
    '""',
    "''",
    ", #",
    "$",
    "#",
    "AFX",
    "CC",
    "CD",
    "DT",
    "EX",
    "FW",
    "HYPH",
    "IN",
    "JJ",
    "JJR",
    "JJS",
    "LS",
    "MD",
    "NIL",
    "NN",
    "NNP",
    "NNPS",
    "NNS",
    "PDT",
    "POS",
    "PRP",
    "PRP$",
    "RB",
    "RBR",
    "RBS",
    "RP",
    "SP",
    "SYM",
    "TO",
    "UH",
    "VB",
    "VBD",
    "VBG",
    "VBN",
    "VBP",
    "VBZ",
    "WDT",
    "WP",
    "WP$",
    "WRB",
    "ADD",
    "NFP",
    "GW",
    "XX",
    "BES",
    "HVS",
    "_SP",
}

# Regex Patterns
# Pattern for extracting Onion v3 addresses (56-character format only)
# This pattern extracts .onion domains; validation for v3 format occurs downstream
ONION_URL_PATTERN = r"(?:https?://)?(?:www)?(\S*?\.onion)\b"

# Timeouts (in seconds)
HTTP_REQUEST_TIMEOUT = 30
SCREENSHOT_TIMEOUT = 60
CRAWL_TIMEOUT = 300

# Job TTL (Time To Live) in seconds
JOB_TTL = 86400  # 24 hours
JOB_RESULT_TTL = 1  # 1 second

# Logging
LOG_FORMAT = "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
LOG_MAX_BYTES = 10000000  # 10MB
LOG_BACKUP_COUNT = 3

# Crawler Configuration
MAX_TRY_COUNT = 3
REQUEST_TIMEOUT = 5
CONNECTION_TIMEOUT = 25
FOLLOWLOCATION = True

# Splash Configuration
SPLASH_HOST = "splash"
SPLASH_PORT = 8050

# HTTP Status Code Descriptions
HTTP_STATUS_DESCRIPTIONS = {
    200: "OK",
    201: "The POST command was a success!",
    202: "Request for processing accepted but it may be disallowed when processing actually takes place.",
    203: (
        "The returned metainformation is not a definitive set of the object from a server with a copy of the "
        "object, but is from a private overlaid web."
    ),
    204: (
        "No information to send back from the server. Please stay in the same document view to allow input for "
        "scripts without changing the document at the same time."
    ),
    301: "The data requested has been assigned a new URI and the change is permanent.",
    302: (
        "The data requested actually resides under a different URL, however, the redirection may be altered on "
        "occasion as for 'Forward'."
    ),
    303: "You should try another network address.",
    304: (
        "The server did not send the document body since the document has not been modified since the date and "
        "time specified in If-Modified-Since field."
    ),
    400: "Either the request had bad syntax or is inherently impossible to be satisfied",
    401: "Retry the request with a suitable Authorization header.",
    402: "Retry the request with a suitable ChargeTo header.",
    403: "The request is for something forbidden and unfortunately, authorization will not help.",
    404: "Nothing that matches the URI was found by the server.",
    500: "Unexpected condition encountered by the server is preventing it from fulfilling the request.",
    501: "The server does not support the facility required.",
    502: (
        "The server cannot process the request due to a high load but the good news is that this is a temporary "
        "condition which maybe alleviated at other times!"
    ),
    503: (
        "The respose from the other service which the server tried to access did not return within a time that "
        "the gateway was prepared to wait."
    ),
}

# User Agent
DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 6.1; rv:45.0) Gecko/20100101 Firefox/45.0"

# HTTP Headers
DEFAULT_HTTP_HEADERS = ["Connection: close", "User-Agent: {user_agent}"]

# Retry Constants
MAX_RETRY_SENTINEL = 9999

# MongoDB Credentials (for backward compatibility - should use settings)
DEFAULT_MONGODB_USERNAME = "admin"
DEFAULT_MONGODB_PASSWORD = "123qwe"

# Spacy NLP Tags
SPACY_NNP_TAG = "NNP"
SPACY_NNPS_TAG = "NNPS"

# Captcha Constants
CAPTCHA_SESSION_KEY = "captcha_answer"
CAPTCHA_FORM_KEY = "captcha"
CAPTCHA_IMAGE_WIDTH = 200
CAPTCHA_CHAR_POOL = "qwertyuiopasdfghjklzxcvbnm1234567890"
CAPTCHA_DEFAULT_LENGTH = 4

# Captcha Error Messages
CAPTCHA_ERROR_MISSING = "Captcha validation is required"
CAPTCHA_ERROR_INVALID = "Invalid captcha. Please try again"
CAPTCHA_ERROR_EXPIRED = "Captcha has expired. Please refresh and try again"

localhost = False

if localhost:
	mongodb_uri = "mongodb://%s:%s@localhost:27017/crawler" % ("admin", "123qwe")
	tor_pool_url = "localhost"
	tor_pool_port = 9150
else:
	mongodb_uri = "mongodb://%s:%s@mongodb:27017/crawler" % ("admin", "123qwe")
	tor_pool_url = "torpool"
	tor_pool_port = 5566

splash_host = "splash"
splash_port = 8050

max_try_count   =   3
REQUEST_TIMEOUT = 5
CONNECTION_TIMEOUT = 25
FOLLOWLOCATION = True

SCR_PATH = "/app/files/screenshots/"


http_codes = {
		200    : "OK",
		201    : "The POST command was a success!",
		202    : "Request for processing accepted but it may be disallowed when processing actually takes place.",
		203    : "The returned metainformation is not a definitive set of the object from a" +
		         " server with a copy of the object, but is from a private overlaid web.",
		204    : "No information to send back from the server. Please stay in the same document"+
		         " view to allow input for scripts without changing the document at the same time.",
		400    : "Either the request had bad syntax or is inherently impossible to be satisfied",
		401    : "Retry the request with a suitable Authorization header.",
		402    : "Retry the request with a suitable ChargeTo header.",
		403    : "The request is for something forbidden and unfortunately, authorization will not help.",
		404    : "Nothing that matches the URI was found by the server.",
		500    : "Unexpected condition encountered by the server is preventing it from fulfilling"+
		         " the request.",
		501    : "The server does not support the facility required.",
		502    : "The server cannot process the request due to a high load but the"+
		         " good news is that this is a temporary condition which maybe alleviated at other times!",
		503    : "The respose from the other service which the server tried to access did not return"+
		         " within a time that the gateway was prepared to wait.",
		301    : "The data requested has been assigned a new URI and the change is permanent.",
		302    : "The data requested actually resides under a different URL, however, the redirection may be "+
		         "altered on occasion as for 'Forward'.",
		303    : "You should try another network address.",
		304    : "The server did not send the document body since the document has not been modified "+
		         "since the date and time specified in If-Modified-Since field."
}


#curl 'http://splash:8050/render.html?url=http://wallstyizjhkrvmj.onion/&proxy=socks://torpool:5566'
def get_splash_uri(url):
	return "http://%s:%d/render.png?url=%s&proxy=socks5://%s:%d" % \
		   (splash_host, splash_port, url, tor_pool_url, tor_pool_port)


def get_save_path(filename):
	return "%s%s.png" % (SCR_PATH, filename)

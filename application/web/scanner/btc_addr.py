import re

class CryptoAddrDetector:
    def __init__(self,text_to_find):
        self.text = text_to_find

    def bitcoin(self):
        try:
            _find = re.findall('[13][a-km-zA-HJ-NP-Z1-9]{25,34}', self.text)
            return _find
        except:
            return None

    def eth(self):
        try:
            _find = re.findall('0x[a-fA-F0-9]{40}', self.text)
            return _find
        except:
            return None

    def monero(self):
        try:
            _find = re.findall('4[0-9AB][1-9A-HJ-NP-Za-km-z]{93}', self.text)
            return _find
        except:
            return None

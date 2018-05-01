n_per_page = 20

redis_uri = 'redis://redis:6379'
mongodb_uri = "mongodb://%s:%s@mongodb:27017/crawler" % ("admin", "123qwe")

seed_upload_dir = "/application/files/seeds/"
scr_upload_dir = "/application/files/screenshots/"
spacy_server_url = "http://spacy:8000/dep/"


EXIF_PATH = "/application/files/exif/"

localhost = False

if localhost:
	mongodb_uri = "mongodb://%s:%s@localhost:27017/crawler" % ("admin", "123qwe")
	tor_pool_url = "localhost"
	tor_pool_port = 9150
	redis_uri = 'redis://localhost:6379'
else:
	mongodb_uri = "mongodb://%s:%s@mongodb:27017/crawler" % ("admin", "123qwe")
	tor_pool_url = "torpool"
	tor_pool_port = 5566
	redis_uri = 'redis://redis:6379'


def get_exif_save_path(filename, ext):
	return "%s%s%s" % (EXIF_PATH, filename, ext)


SPACY_TAG_MAP = {
    ".", #        {POS: PUNCT, "PunctType", # "peri"},
    ",", #        {POS: PUNCT, "PunctType", # "comm"},
    "-LRB-", #    {POS: PUNCT, "PunctType", # "brck", "PunctSide", # "ini"},
    "-RRB-", #    {POS: PUNCT, "PunctType", # "brck", "PunctSide", # "fin"},
    "``", #       {POS: PUNCT, "PunctType", # "quot", "PunctSide", # "ini"},
    "\"\"", #     {POS: PUNCT, "PunctType", # "quot", "PunctSide", # "fin"},
    "''", #       {POS: PUNCT, "PunctType", # "quot", "PunctSide", # "fin"},
    ", #", #        {POS: PUNCT},
    "$", #        {POS: SYM, "Other", # {"SymType", # "currency"}},
    "#", #        {POS: SYM, "Other", # {"SymType", # "numbersign"}},
    "AFX", #      {POS: ADJ,  "Hyph", # "yes"},
    "CC", #       {POS: CCONJ, "ConjType", # "coor"},
    "CD", #       {POS: NUM, "NumType", # "card"},
    "DT", #       {POS: DET},
    "EX", #       {POS: ADV, "AdvType", # "ex"},
    "FW", #       {POS: X, "Foreign", # "yes"},
    "HYPH", #     {POS: PUNCT, "PunctType", # "dash"},
    "IN", #       {POS: ADP},
    "JJ", #       {POS: ADJ, "Degree", # "pos"},
    "JJR", #      {POS: ADJ, "Degree", # "comp"},
    "JJS", #      {POS: ADJ, "Degree", # "sup"},
    "LS", #       {POS: PUNCT, "NumType", # "ord"},
    "MD", #       {POS: VERB, "VerbType", # "mod"},
    "NIL", #      {POS: ""},
    "NN", #       {POS: NOUN, "Number", # "sing"},
    "NNP", #      {POS: PROPN, "NounType", # "prop", "Number", # "sing"},
    "NNPS", #     {POS: PROPN, "NounType", # "prop", "Number", # "plur"},
    "NNS", #      {POS: NOUN, "Number", # "plur"},
    "PDT", #      {POS: ADJ, "AdjType", # "pdt", "PronType", # "prn"},
    "POS", #      {POS: PART, "Poss", # "yes"},
    "PRP", #      {POS: PRON, "PronType", # "prs"},
    "PRP$", #     {POS: ADJ, "PronType", # "prs", "Poss", # "yes"},
    "RB", #       {POS: ADV, "Degree", # "pos"},
    "RBR", #      {POS: ADV, "Degree", # "comp"},
    "RBS", #      {POS: ADV, "Degree", # "sup"},
    "RP", #       {POS: PART},
    "SP", #       {POS: SPACE},
    "SYM", #      {POS: SYM},
    "TO", #       {POS: PART, "PartType", # "inf", "VerbForm", # "inf"},
    "UH", #       {POS: INTJ},
    "VB", #       {POS: VERB, "VerbForm", # "inf"},
    "VBD", #      {POS: VERB, "VerbForm", # "fin", "Tense", # "past"},
    "VBG", #      {POS: VERB, "VerbForm", # "part", "Tense", # "pres", "Aspect", # "prog"},
    "VBN", #      {POS: VERB, "VerbForm", # "part", "Tense", # "past", "Aspect", # "perf"},
    "VBP", #      {POS: VERB, "VerbForm", # "fin", "Tense", # "pres"},
    "VBZ", #      {POS: VERB, "VerbForm", # "fin", "Tense", # "pres", "Number", # "sing", "Person", # 3},
    "WDT", #      {POS: ADJ, "PronType", # "int|rel"},
    "WP", #       {POS: NOUN, "PronType", # "int|rel"},
    "WP$", #      {POS: ADJ, "Poss", # "yes", "PronType", # "int|rel"},
    "WRB", #      {POS: ADV, "PronType", # "int|rel"},
    "ADD", #      {POS: X},
    "NFP", #      {POS: PUNCT},
    "GW", #       {POS: X},
    "XX", #       {POS: X},
    "BES",
    "HVS",
    "_SP",
}



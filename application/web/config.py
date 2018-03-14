n_per_page = 20

local_dev = False

if local_dev:

    redis_uri = 'redis://localhost:6379'
    mongodb_uri = "mongodb://localhost:27017"
else:
    redis_uri = 'redis://redis:6379'
    mongodb_uri = "mongodb://%s:%s@mongodb:27017/crawler" % ("admin", "54nn4n")

seed_upload_dir = "./seeds/"

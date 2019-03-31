# All time in seconds
ITEM_CRAWL_TIME = 600  # Monitor sleep time, if not using proxy, CRAWL_TIME > 1800 recommended.
CATE_CRAWL_TIME = 1800  # Category crawl sleep time, if not using proxy, CRAWL_TIME > 1800 recommended.
UPDATE_TIME = 100  # Find item updated before this time value
PROXY_CRAWL = 0  # 1: Use proxy pool 0: Use local ip 2: zhi ma ip
THREAD_NUM = 1  # Crawler thread, 1 equals loop
THREAD_SLEEP_TIME = 5  # Sleep time for using LOCAL ip
PROXY_POOL_IP = "115.159.190.214"  # Your redis server ip
DISCOUNT_LIMIT = 0.8  # Set alert mail discount
ALERT_EXT = "stock,promo,coupon" # Set alert mail with other item changed
PROXY_POOL = "http://127.0.0.1:5010" # proxy_pool server, must start with scheme
NOTICE_EMAIL = 1 # 1 to enable
Email_TIME = 10  # Send email sleep time
MAIL_SMTP = "" # exmaple: 127.0.0.1:25, or 127.0.0.1:465, leave empty to use settings in mailbox.txt
MAIL_SMTP_NEED_AUTH = 0 # 0 disabled, 1 enabled and will use the follow data as a valid auth user.
MAIL_SMTP_ACCOUNT = "" # will be used as email from, if leave empty, email may be reported as spam
MAIL_SMTP_PASSWORD = ""

#  send message to custom endpoint
# 1 to enabled. example: add http://127.0.0.1/{msg} to the column 'endpoint' of 'user' table, {msg} will be replace with 'subject' and 'content'.
# can also post data, open db and fill 'endpoint_data' with json data in user table.
NOTICE_ENDPOINT = 0 
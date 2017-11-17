from urllib.parse import urlparse

RSS_TYPES = ["application/rss+xml", "text/xml", "application/atom+xml", "application/x.atom+xml",
             "application/x-atom+xml", "application/xml"]


def get_domain(url):
    return urlparse(url).netloc


def validate_content_type(content_type):
    return any(x in content_type for x in RSS_TYPES)

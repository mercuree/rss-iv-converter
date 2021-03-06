
from flask import Flask
import requests
import requests_cache
from flask import request
from flask import abort
from flask import Response
from flask import render_template
from fake_useragent import UserAgent

from rss_iv_converter.helpers import get_domain, validate_content_type
from lxml import etree
from lxml.html import fromstring
from urllib.parse import quote_plus
import re
import html
import idna

requests_cache.install_cache(expire_after=300)

ua = UserAgent()

app = Flask(__name__)

lxml_parser = etree.XMLParser(
    recover=True, resolve_entities=False, strip_cdata=False
)


@app.route('/')
def main_page():
    return render_template('index.html')


@app.route('/rss', methods=['GET'])
def get_rss():
    url = request.args.get('url')
    rhash = request.args.get('tg_rhash')
    rss_request_headers = {'User-Agent': ua.chrome} if request.args.get('spoof_ua') is not None else None
    if not url or not rhash:
        return abort(400)

    # validate tg_rhash
    if rhash and not re.match(r'^[a-fA-F\d]+$', rhash):
        return 'Invalid tg_rhash. Please, check rhash value from instant view template'

    domain = get_domain(url)

    resp = requests.get(url, headers=rss_request_headers)

    if not validate_content_type(resp.headers.get('Content-Type')):
        return "RSS TYPE IS NOT VALID"

    doc = etree.XML(resp.content, lxml_parser)

    # Channel title should not be empty
    channel_empty_titles = doc.xpath('.//channel/title[count(text())=0]')
    for ctitle in channel_empty_titles:
        ctitle.text = domain

    items = doc.xpath('.//item')
    for item in items:
        link = item.find('link')
        description = item.find('description')
        author = item.find('author')
        if link is not None and link.text.startswith('http://t.me/iv') is False:
            if description is not None and description.text and len(description.text):
                description.text = fromstring(html.unescape(description.text)).text_content()
                description.text = description.text.strip()

            link.text = link.text.strip()

            # convert idna domains
            link_domain = get_domain(link.text)
            try:
                idna_domain = idna.encode(link_domain).decode('utf-8')
                if idna_domain != link_domain:
                    link.text = link.text.replace(link_domain, idna_domain, 1)
            except:
                pass

            if author is not None:
                author.text = link.text
            else:
                author = etree.Element('author')
                author.text = link.text
                item.append(author)

            link.text = "http://t.me/iv?url={url}&rhash={rhash}".format(
                url=quote_plus(link.text),
                rhash=rhash
            )

    try:
        output = etree.tostring(doc, method="c14n")
    except:
        output = etree.tostring(doc, encoding='unicode')
    rss_response = Response(output)
    rss_response.headers.set('Content-Type', 'application/rss+xml; charset=utf-8')

    return rss_response


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=80)

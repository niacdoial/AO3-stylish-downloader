import http.client  # for HTTPSConnection
import ssl   # to create context
import argparse
import re
from sys import stderr


def url_checker(url):
    if re.fullmatch('[0-9]+', url):
        website = 'archiveofourown.org'
        address = '/works/' + url
    else:
        if url[:8] == 'https://':
            url = url[8:]
        if url[:7] == 'http://':
            url = url[7:]
            print("Didn't want HTTPS? Too bad, you're getting it.", file=stderr)
        website = url.split('/')[0]
        address = url[len(website):]

    if website != 'archiveofourown.org' or address[:7] != '/works/':
        raise argparse.ArgumentTypeError("invalid input. must be an AO3 work. (like 'archiveofourown.org/works/12345678' or simply '12345678')")

    temp = re.fullmatch(r'(?P<final>/works/[0-9]+).*', address)
    if temp is None:
        raise argparse.ArgumentTypeError("invalid input. must be an AO3 work. (like 'archiveofourown.org/works/12345678' or simply '12345678')")
    else:
        address = temp.group('final')

    return address

"failed to connect. Please check the url syntax, and that it points to a valid, publicly available AO3 fic."

SSLC = ssl.create_default_context()
# create a ssl context to securely connect to ao3, using the https protocol

def getwebpage(address, switches='', base_site='archiveofourown.org'):
    ## first parse the URL (let's suppose it's done)
    #if url[:8] == 'https://':
    #    url = url[8:]
    #website = url.split('/')[0]
    #address = url[len(website):]
    # example : website = "(www.)archiveofourown.org", address = "/works/12345678"

    # then request the contentrs of the page
    conn = http.client.HTTPSConnection(base_site, context=SSLC)
    conn.connect()
    conn.request('GET', address+switches)
    page = conn.getresponse()

    # detect redirection (from AO3 only for now)
    if page.read(26) == b'<html><body>You are being ':
        rawdata = page.read()
        url = re.match(r'.*<a href="(?P<url>[\w\%\-\./:]*)(?P<switches>(\?.*)?)">', rawdata.decode())\
              .group('url')
        page.close()

        # parse the redirection URL, and go here
        if url[:8] == 'https://':
            url = url[8:]
        website = url.split('/')[0]
        address = url[len(website):]

        conn.request('GET', address+switches)
        page = conn.getresponse()
    #else:
        #print(page.read())

    return address, page

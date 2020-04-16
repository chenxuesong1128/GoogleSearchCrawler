#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Create by Meibenjin.
#
# Last updated: 2018-12-15
#
# google search results crawler

import sys
import os
import urllib.request
import urllib
import urllib.parse
import urllib.error
import socket
import time
import gzip
# import StringIO
from io import StringIO, BytesIO
import re
import random
import types
from dotenv import load_dotenv, find_dotenv
from bs4 import BeautifulSoup
import ssl
from tqdm import tqdm
# reload(sys)
# sys.setdefaultencoding('utf-8')

# Load config from .env file
# TODO: Error handling
try:
    load_dotenv(find_dotenv(usecwd=True))
    base_url = os.environ.get('BASE_URL')
    results_per_page = int(os.environ.get('RESULTS_PER_PAGE'))
except:
    print("ERROR: Make sure you have .env file with proper config")
    sys.exit(1)

user_agents = list()

# results from the search engine
# basically include url, title,content


class SearchResult:
    def __init__(self):
        self.url = ''
        self.title = ''
        self.content = ''
        self.location = ''

    def getURL(self):
        return self.url

    def setURL(self, url):
        self.url = url

    def getTitle(self):
        return self.title

    def getLocation(self):
        return self.location

    def setLocation(self, position):
        self.location =  position

    def setTitle(self, title):
        self.title = title

    def getContent(self):
        return self.content

    def setContent(self, content):
        self.content = content

    def printIt(self, prefix=''):
        print ('url\t->', self.url, '\n',
            'title\t->', self.title, '\n',
            # 'position\t->', self.position, '\n',
            # 'content\t->', self.content
               )

    def writeCSV(self, filename):
        query = urllib.parse.unquote(filename)
        query = query.split(':')[1]
        results = query.split(' ')
        site = results[0]
        key_word = '_'.join(results[1:])
        dir_path = 'results/%s'%site
        if os.path.exists(dir_path):
            pass
        else:
            os.makedirs(dir_path)
        file = open('%s/%sV1.tsv'%(dir_path, key_word), 'a')
        try:
            file.write(self.url + '\t')
            file.write(self.title + '\t')
            file.write(self.location + '\n')
            # file.write('content:' + self.content + '\n\n')
        except IOError as e:
            print ('file error:', e)
        finally:
            file.close()

    def writeFile(self, filename):
        file = open(filename, 'a')
        try:
            file.write('url:' + self.url + '\n')
            file.write('title:' + self.title + '\n')
            file.write('location:' + self.location + '\n\n')
            # file.write('content:' + self.content + '\n\n')
        except IOError as e:
            print ('file error:', e)
        finally:
            file.close()


class GoogleAPI:
    def __init__(self):
        timeout = 40
        socket.setdefaulttimeout(timeout)

    def randomSleep(self, type=None):
        if type == 'short':
            sleeptime = random.randint(30, 60)
        else:
            sleeptime = random.randint(600, 1000)
        time.sleep(sleeptime)

    def extractDomain(self, url):
        """Return string

        extract the domain of a url
        """
        domain = ''
        pattern = re.compile(r'http[s]?://([^/]+)/', re.U | re.M)
        url_match = pattern.search(url)
        if(url_match and url_match.lastindex > 0):
            domain = url_match.group(1)

        return domain

    def extractUrl(self, href):
        """ Return a string

        extract a url from a link
        """
        url = ''
        pattern = re.compile(r'(http[s]?://[^&]+)&', re.U | re.M)
        url_match = pattern.search(href)
        if(url_match and url_match.lastindex > 0):
            url = url_match.group(1)

        return url

    def extractSearchResults(self, html, query):
        """Return a list

        extract serach results list from downloaded html file
        """
        results = list()
        soup = BeautifulSoup(html, 'html.parser')
        div = soup.find('div', id='main')
        if (type(div) is type(None)):
            div = soup.find('div', id='center_col')
        if (type(div) == type(None)):
            div = soup.find('body')
        if (type(div) != type(None)):
            lis = div.findAll('a')
            if(len(lis) > 0):
                for link in lis:
                    if (type(link) == type(None)):
                        continue
                    
                    try:
                        url = link['href']
                    except:
                        continue

                    if url.find(".google") > 6:
                        continue
                    url = self.extractUrl(url)
                    if(url == ''):
                        continue
                    title = link.renderContents()
                    # title = link.contents[0].text
                    title = re.sub(r'<.+?>', '', title.decode())
                    try:
                        title, location = re.split('https://', title)
                    except:
                        title = title
                        location = ''
                    # position = link.contents[1].text
                    result = SearchResult()
                    result.setURL(url)
                    result.setTitle(title)
                    result.setLocation(location)
                    result.writeCSV(query)
                    result.printIt()
                    # span = link.find('div')
                    # if (type(span) != type(None)):
                    #     content = span.renderContents()
                    #     content = re.sub(r'<.+?>', '', content.decode())
                    #     result.setContent(content)
                    results.append(result)
        # return results
        return None

    def search(self, query, lang='en', num=results_per_page):
        """Return a list of lists

        search web
        @param query -> query key words
        @param lang -> language of search results
        @param num -> number of search results to return
        """
        search_results = list()
        query = urllib.parse.quote(query)
        is_end_page = False
        if(num % results_per_page == 0):
            pages = num / results_per_page
        else:
            pages = num / results_per_page + 1

        for p in tqdm(range(0, int(pages))):
            start = p * results_per_page
            url = '%s/search?hl=%s&num=%d&start=%s&q=%s' % (
                base_url, lang, results_per_page, start, query)
            retry = 3
            if is_end_page:
                break
            while(retry > 0):
                try:
                    request = urllib.request.Request(url)
                    length = len(user_agents)
                    index = random.randint(0, length-1)
                    user_agent = user_agents[index]
                    request.add_header('User-agent', user_agent)
                    request.add_header('connection', 'keep-alive')
                    request.add_header('Accept-Encoding', 'gzip')
                    request.add_header('referer', base_url)
                    context = ssl._create_unverified_context()
                    response = urllib.request.urlopen(request, context=context)
                    html = response.read()
                    if(response.headers.get('content-encoding', None) == 'gzip'):
                        html = gzip.GzipFile(
                            fileobj=BytesIO(html)).read()
                    html = html.decode('utf-8', 'ignore')
                    results = self.extractSearchResults(html, query)
                    # search_results.extend(results)
                    if html.find('In order to show you the most relevant results') != -1:
                        is_end_page = True
                        break
                    self.randomSleep('short')
                    break
                except urllib.error.URLError as e:
                    print ('url error:', e)
                    self.randomSleep()
                    retry = retry - 1
                    continue

                except Exception as e:
                    print ('error:', e)
                    retry = retry - 1
                    self.randomSleep()
                    continue
        return search_results


def load_user_agent():
    fp = open('./user_agents', 'r')

    line = fp.readline().strip('\n')
    while(line):
        user_agents.append(line)
        line = fp.readline().strip('\n')
    fp.close()


def crawler():
    # Load use agent string from file
    load_user_agent()

    # Create a GoogleAPI instance
    api = GoogleAPI()

    # set expect search results to be crawled
    expect_num = 500
    # if no parameters, read query keywords from file
    if(len(sys.argv) < 2):
        keywords = open('./keywords', 'r')
        sites = open('./sites_2.txt', 'r')
        for keyword in keywords.readlines():
            for site in sites.readlines():
                keyword = keyword.strip()
                site = site.strip()
                query = "site:%s %s"%(site, keyword)
                results = api.search(query, num=expect_num)
                # for r in results:
                #     r.printIt()
                #     r.writeCSV(query)
        keywords.close()
        sites.close()
    else:
        keyword = sys.argv[1]
        results = api.search(keyword, num=expect_num)
        for r in results:
            r.printIt()


if __name__ == '__main__':
    crawler()

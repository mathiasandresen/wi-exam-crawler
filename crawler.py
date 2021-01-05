from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser
import urllib.request
from datetime import datetime, timedelta
import time as Time
import requests
from bs4 import BeautifulSoup

from frontier import Frontier
from corpus import Corpus 

class Crawler:

    blacklist = []
    frontier: Frontier
    corpus: Corpus
    verbose: bool
    debug: bool
    corpuse_max_size: int
    robot_files = {}
    thread: int
    duplicate_identification: bool

    def __init__(self, seeds: list[str], corpus: Corpus, frontier: Frontier, corpuse_max_size = 5, duplicate_identification=False, thread=0, verbose = False, debug = False):
        self.verbose = verbose
        self.debug = debug
        self.corpuse_max_size = corpuse_max_size
        self.thread = thread
        self.duplicate_identification = duplicate_identification

        self.seeds = seeds
        self.frontier = frontier
        self.corpus = corpus

        for seed in seeds:
            self.frontier.add_url(seed)

        self.frontier.fill_back_queues()

    def start(self):
        while len(self.corpus.corpus) < self.corpuse_max_size:
            url, time, back_queue_index = self.frontier.extract_url()
            if (url is None):
                continue

            if self.verbose: self.thread_print("Going to crawl: " + url)

            now = datetime.now()

            if time > now:
                delay = (time - now).total_seconds()
                if self.verbose: self.thread_print("not allowed to crawl yet, waiting {} seconds".format(delay))
                Time.sleep(delay)

            title, res_url, crawl_delay = self.__crawl_url(url)
            if res_url is not None and title is not None:
                self.corpus.add((title, res_url))
                self.blacklist.append(res_url)

            delay_to_be_added = timedelta(seconds=crawl_delay) if ( crawl_delay is not None and crawl_delay != 0) else timedelta(seconds=5)
            self.frontier.update_back_queue(back_queue_index, (now + delay_to_be_added))
            
            self.thread_print("{} out of {}".format(len(self.corpus.corpus), self.corpuse_max_size))
        

    def __crawl_url(self, url) -> tuple[str, str, int]:
        if url in self.blacklist:
            return (None, None, None)

        try:
            can_fetch = True
            rp = self.robot_files.get(urlparse(url).hostname, None)

            if rp is None:            
                rp = RobotFileParser()
                rp.set_url(url)
                rp.read()
                self.robot_files[urlparse(url).hostname] = rp   
            
            can_fetch = rp.can_fetch("*", url)

            if not can_fetch:
                if self.verbose and self.debug: self.thread_print("Not allowed to crawl, adding url to blacklist: {}".format(url))
                self.blacklist.append(url)
                return (None, None, None)

            if not self.__is_html(url):
                if self.verbose and self.debug: self.thread_print("Not html document, adding url to blacklist: {}".format(url))
                self.blacklist.append(url)
                return (None, None, None)

            content = requests.get(url, timeout = 1)
            if self.verbose and self.debug: self.thread_print("Statuscode: {}".format(content.status_code))
            if content.status_code != 200:
                if self.verbose and self.debug: self.thread_print("Status not 200, returning")
                return (None, None, None)


        except:
            if self.verbose and self.debug: self.thread_print("An error happened, adding url to blacklist: {}".format(url))
            self.blacklist.append(url)
            return (None, None, None)

        parsed_content = BeautifulSoup(content.text, 'html.parser')
        
        links = parsed_content.findAll('a')
        links = filter(lambda x: x.has_attr('href'), links)
        self.__add_links_to_frontier(links)

        title_obj = parsed_content.find('title')

        title = title_obj.string if title_obj is not None else url

        crawl_delay = rp.crawl_delay("*") if rp.crawl_delay("*") is not None else 0

        return (title, url, crawl_delay)

        

    # Helper method
    def __add_links_to_frontier(self, links):
        for link in links:
            temp_blacklist = []
            found_url = str(link['href'])
            # Usage of blacklist doubles memory usage related to found urls, but makes it easier to keep track of visited sites
            if (found_url.startswith('http') or found_url.startswith('https')) and (found_url not in temp_blacklist) and (found_url not in self.blacklist):
                self.frontier.add_url(found_url)
                temp_blacklist.append(found_url)


    def thread_print(self, string):
        print("{}: {}".format(self.thread, string))

    def __is_html(self, url) -> bool:
        request = urllib.request.urlopen(url, timeout=1)
        return request.info().get_content_type() == "text/html"
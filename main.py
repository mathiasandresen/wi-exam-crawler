from datetime import datetime
from frontier import Frontier
from corpus import Corpus
from crawler import Crawler
import sys

VERBOSE = True
DEBUG = False

SEEDS = [
    "https://ekstrabladet.dk/",
    # 'https://www.aau.dk/',
    # 'https://www.w3schools.com/',
    # 'https://github.com/',
    # 'https://vbn.aau.dk/da/projects/search.html',
    # "https://github.com/cli/cli/releases/download/v1.4.0/gh_1.4.0_windows_amd64.msi",
]

CORPUS_SIZE = int(sys.argv[1]) if len(sys.argv) > 1 else 100

def main():

    corpus = Corpus(output="stack_without_dupes/result-{}.csv".format(CORPUS_SIZE))
    frontier = Frontier(corpus, 10, 8, duplicate_identification=True, verbose=VERBOSE, debug=DEBUG)
    
    crawler = Crawler(SEEDS, corpus, frontier, corpuse_max_size=CORPUS_SIZE, duplicate_identification=True, verbose=VERBOSE, debug=DEBUG)
    print("Starting at {}".format(datetime.now()))
    crawler.start()
    print("Done at {}".format(datetime.now()))

    # thread1 = threading.Thread(target=start_crawler_in_thread, args=[1, frontier, corpus])
    # thread2 = threading.Thread(target=start_crawler_in_thread, args=[2, frontier, corpus])
    # thread3 = threading.Thread(target=start_crawler_in_thread, args=[3, frontier, corpus])

    # thread1.start()
    # thread2.start()
    # thread3.start()



def start_crawler_in_thread(thread: int, frontier, corpus):
    crawler = Crawler(SEEDS, corpus, frontier, corpuse_max_size=50, verbose=VERBOSE, debug=DEBUG, thread=thread)
    crawler.start()

if __name__ == "__main__":
    main()
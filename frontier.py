from typing import TypeVar, Generic
from urllib.parse import urlparse
import heapq
from datetime import datetime, timedelta
import random
from corpus import Corpus

T = TypeVar('T')
class Queue(Generic[T]):
    items: list[T]
    is_stack: bool

    def __init__(self, is_stack=False) -> None:
        self.items = []
        self.is_stack = is_stack

    def extract_next(self) -> T:
        value = self.items.pop() if self.is_stack else self.items.pop(0)
        return value
        
    def insert(self, item: T) -> None:
        self.items.append(item)

    def contains(self, item: T) -> bool:
        return item in self.items

    def empty(self) -> bool:
        return len(self.items) <= 0
        
class Frontier:
    front_queues: list[Queue[str]] = []
    back_queues: list[Queue[str]] = []
    back_queue_heap = []
    back_queue_map = {}
    verbose: bool
    debug: bool
    duplicate_identification: bool
    choice_array: list[int] = []
    corpus: Corpus

    def __init__(self, corpus: Corpus, amount_of_front_queues: int, amount_of_back_queues: int, duplicate_identification=False, verbose = False, debug = False):
        self.verbose = verbose
        self.debug = debug
        self.corpus = corpus
        self.duplicate_identification = duplicate_identification
        # Create front queues
        for i in range(amount_of_front_queues):
            self.front_queues.append(Queue(is_stack=True))
            self.choice_array.extend([i] * (i + 1))
        # Create back queues
        for i in range(amount_of_back_queues):
            self.back_queues.append(Queue(is_stack=True))
            heapq.heappush(self.back_queue_heap, (datetime.now(), i))
    
    def add_url(self, url: str):
        queue_id = self.__prioritizer(url)
        should_be_added = True

        if self.duplicate_identification:
            if self.front_queues[queue_id].contains(url):
                should_be_added = False
                
        if should_be_added:
            self.front_queues[queue_id].insert(url)

    def extract_url(self) -> tuple[str, datetime, int]:
        if (len(self.back_queue_heap) == 0):
            print("Heap is empty, no url is extracted")
            return (None,None,None)

        (time, index) = heapq.heappop(self.back_queue_heap)
    
        if self.verbose and self.debug: print("Selecting from back queue {}".format(index))

        if self.back_queues[index].empty():
            self.__fill_back_queue(index)
            # If still empty try another queue
            if self.back_queues[index].empty():
                heapq.heappush(self.back_queue_heap, (datetime.now() + timedelta(seconds=5), index))
                if self.verbose and self.debug: print("Heap still empty, try another queue")
                return (None,None,None)

        return (self.back_queues[index].extract_next(), time, index)

    def update_back_queue(self, index, time):
        new_host = False
        if self.back_queues[index].empty():
            new_host = self.__fill_back_queue(index)

        if new_host:
            time = datetime.now()

        heapq.heappush(self.back_queue_heap, (time, index))

    def fill_back_queues(self):
        for index, _ in enumerate(self.back_queues):
            self.__fill_back_queue(index)


    def __prioritizer(self, url: str) -> int:
        if self.corpus.has_url(url):
            value = 0
        else:
            value = random.randrange(0, len(self.front_queues)) 

        return value

    def __front_queue_selector(self) -> int:
        rand = random.choice(self.choice_array)
        while self.front_queues[rand].empty():
            rand = random.choice(self.choice_array)
        return rand

    def __fill_back_queue(self, index: int) -> bool:
        front_queue_empty = True
        for front_queue in self.front_queues:
            if front_queue.empty() == False:
                front_queue_empty = False
                break
            
        if front_queue_empty:
            print("Front queues are empty, not filling up back queue")
            return

        new_host = False

        front_queue_index = self.__front_queue_selector()
        url = self.front_queues[front_queue_index].extract_next()

        if self.verbose and self.debug: print("found {} adding to back queue".format(url))

        if self.back_queue_map.get(urlparse(url).hostname, None) is None:
            self.back_queues[index].insert(url)
            self.back_queue_map[urlparse(url).hostname] = index
            new_host = True
        else:
            queue_index = self.back_queue_map[urlparse(url).hostname]
            self.back_queues[queue_index].insert(url)        

        if self.back_queues[index].empty():
            if self.verbose and self.debug: print("back queue {} still empty, running again".format(str(index)))
            self.__fill_back_queue(index)

        return new_host

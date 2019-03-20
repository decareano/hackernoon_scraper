from __future__ import (
    absolute_import,
    print_function,
)

from bs4 import (
    BeautifulSoup,
)

from multiprocessing import (
    Process,
    Queue,
)

import queue
import requests


class scraper:
    """Base class for a multiprocessing queue to scrap urls"""

    def __init__(self):
        self.queue = Queue()
        self.workers = []

        return self

    def put(self, name, url):
        # print("Putting (%s, %s) into %s queue" % (name, url, id(self.queue)))
        p = Process(target=self.batch, args=(self, ))
        self.workers.append(p)
        p.start()
        self.queue.put((name, url))

        return self

    def finish(self):
        # print("Finishing for %s" % self.__class__)

        # ask the workers to quit.
        # print("Asking workers for %s to quit" % self.__class__)
        for w in self.workers:
            self.queue.put(None)

        # # wait for workers to quit.
        # print("Joining workers for %s" % self.__class__)
        # for w in self.workers:
        #     print("w(%s) in %s joining..." % (w, self.__class__))
        #     w.join()

        return self

    def batch(self, *args):
        while True:
            if self.queue.empty():
                # it could be that this thread is fired before the queue has
                # been populated; that's ok because we just keep looping until
                # None is reached
                continue

            try:
                item = self.queue.get_nowait()

                if item is None:
                    break

                self.worker(item[0], item[1], *args)
            except queue.Empty:
                pass

        return self


class archive_scraper(scraper):
    """Scraps all the years of a hackernoon archive"""

    def __init__(self):
        super().__init__()
        self.years = year_scraper()

    def worker(self, name, url, *args):
        # print("Retrieving all the %s for %s..." % (name, url))

        page = requests.get(url)

        # raise an exception if page did not load
        page.raise_for_status()
        soup = BeautifulSoup(page.text, 'html.parser')

        for year in soup.select('div[class~=timebucket] a'):
            self.years.put(year.text, year.attrs['href'])

        # we're done queuing years, so request to finish
        self.years.finish()
        return self


class year_scraper(scraper):
    """Scraps all the months in a year of a hackernoon archive"""

    def __init__(self):
        super().__init__()

    def worker(self, name, url, *args):
        # print("Retrieving all the %s for %s..." % (name, url))

        page = requests.get(url)

        # raise an exception if page did not load
        page.raise_for_status()
        soup = BeautifulSoup(page.text, 'html.parser')

        months = {}
        for year in soup.select('div[class~=timebucket] a'):
            months[year.text] = year.attrs['href']

        print(months)
        return self
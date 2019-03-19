from __future__ import (
    absolute_import,
    print_function,
)

import multiprocessing
import requests
from bs4 import BeautifulSoup

url = 'https://hackernoon.com/archive'


def year_worker(input_queue):
    while True:
        year = input_queue.get()

        if year is None:
            break

        year, url = year
        print("Retrieving all the months for %s..." % year)

        page = requests.get(url)

        # raise an exception if page did not load
        page.raise_for_status()
        soup = BeautifulSoup(page.text, 'html.parser')

        months = {}
        for month in soup.select('div[class~=timebucket] a'):
            months[month.text] = month.attrs['href']

        print(months)


def main():
    print("Retrieving all the years...")
    page = requests.get(url)

    # raise an exception if page did not load
    page.raise_for_status()
    soup = BeautifulSoup(page.text, 'html.parser')

    input_queue = multiprocessing.Queue()
    workers = []

    for year in soup.select('div[class~=timebucket] a'):
        p = multiprocessing.Process(target=year_worker,
                                    args=(input_queue, ))
        workers.append(p)
        p.start()
        input_queue.put((year.text, year.attrs['href']))

    # ask the workers to quit.
    for w in workers:
        input_queue.put(None)

    # wait for workers to quit.
    for w in workers:
        w.join()


if __name__ == "__main__":
    main()

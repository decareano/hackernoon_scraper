#!/usr/bin/env python3

import argparse
import asyncio
import csv
import logging
import sys

import aiohttp
import bs4


logging.basicConfig(
    format="%(asctime)s %(levelname)s:%(name)s: %(message)s",
    level=logging.INFO,
    datefmt="%H:%M:%S",
    stream=sys.stderr,
)
logger = logging.getLogger("hackernoon")
logging.getLogger("chardet.charsetprober").disabled = True


articles = []
max_tags = []

async def fetch_html(url: str, session: aiohttp.ClientSession) -> str:
    """GET request wrapper to fetch page HTML.

    kwargs are passed to `session.request()`.
    """
    resp = await session.request(method="GET", url=url)
    resp.raise_for_status()
    html = await resp.text()
    return html


async def parse_and_queue(level: str, url: str, session: aiohttp.ClientSession,
                          q: asyncio.Queue) -> None:
    """Parses urls on a page to drill down into and queues them.

    e.g. Iterate over all the years in an archive page to then drill down into
    the months.
    """
    logger.info(f"Fetching url {url}")
    try:
        html = await fetch_html(url, session)
    except aiohttp.ClientError as e:
        status = getattr(e, "status", None)
        message = getattr(e, "message", None)
        logger.exception(f"aiohttp exception for {url} [{status}]: {message}")
        return None
    except Exception as e:
        status = getattr(e, "status", None)
        message = getattr(e, "message", None)
        logger.exception(f"Unknown exception for {url} [{status}]: {message}")
        return None

    soup = bs4.BeautifulSoup(html, 'html.parser')

    # opportunity here for object-oriented programming here
    new_level = None
    if level == "root":
        new_level = "year"
    elif level == "year":
        new_level = "month"
    elif level == "month":
        new_level = "day"
    elif level == "day":
        new_level = "article"

    if new_level is None and level != "article":
        return None

    if new_level != "article" and level != "article":
        found = set()
        for item in soup.select('div[class~=timebucket] a'):
            if new_level == "day":
                found.add(url)
            item_url = item.attrs['href']
            logger.debug(f"  Queueing {item.text} url {item_url}")
            if new_level != "year":
                await q.put((new_level, item_url, session))
            elif new_level == "year" and item.text == "2012":
                await q.put((new_level, item_url, session))

        # should really use classes
        if new_level == "day" and not found:
            # some months are not separated into days
            for item in soup.select('div[class~=postArticle-readMore] a'):
                item_url = item.attrs['href']
                if not item_url:
                    continue
                logger.debug(f"  [no days in month] Queuing {item.text} "
                             f"url {item_url}")
                await q.put(("article", item_url, session))

    elif new_level == "article":
        for article in soup.select('div[class~=postArticle-readMore] a'):
            item_url = item.attrs['href']
            if not item_url:
                continue
            logger.debug(f"  Queuing {item.text} url {item_url}")
            await q.put((new_level, item_url, session))

    elif level == "article":
        title = soup.select("div[class~=section-content] div h1")[0].text
        author = soup.select("div[class~=section-content] "
                             "div div div div a")[0].text
        date = soup.select("div[class~=section-content] "
                           "div div div div time")[0].attrs["datetime"]

        tags = []
        for tag in soup.select("ul[class~=tags] li"):
            tags.append(tag.text)
        max_tags.append(len(tags))
        articles.append((title, url, author, date, tags))


async def consume(level: str, q: asyncio.Queue) -> None:
    while True:
        l, url, session = await q.get()
        logger.debug(f"Consuming {url}")
        await parse_and_queue(l, url, session, q)
        q.task_done()


async def main(ncon: int) -> None:
    q = asyncio.Queue()
    async with aiohttp.ClientSession() as session:
        await q.put(("root", "https://hackernoon.com/archive", session))
        consumers = [asyncio.create_task(consume(n, q)) for n in range(ncon)]
        await q.join()
        for c in consumers:
            logger.info(f"Cancelling consumer <{id(c)}>")
            c.cancel()

    mt = max(max_tags)
    with open('output.csv', 'w') as f:
        csv_articles = csv.writer(f)
        tag_headers = [f"Tag {i+1}" for i in range(mt)]
        csv_articles.writerow(["Title", "Link", "Author",
                               "pubDate"] + tag_headers)
        for a in articles:
            logger.debug(a)
            row = list(a[:3])
            for t in a[4]:
                row.append(t)
            csv_articles.writerow(row)

if __name__ == "__main__":
    assert sys.version_info >= (3, 7), "Script requires Python 3.7+."

    parser = argparse.ArgumentParser()

    parser.add_argument("-c", "--ncon", type=int, default=10,
                        help="number of consumers in thread pool")
    parser.add_argument("-d", "--debug", action="store_true",
                        help="increase output verbosity")

    ns = parser.parse_args()

    if ns.debug:
        logger.setLevel(logging.DEBUG)

    asyncio.run(main(ns.ncon))

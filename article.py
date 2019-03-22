from __future__ import (
    absolute_import,
    print_function,
)

import asyncio

import aiohttp
import bs4


class article:

    def __init__(self, session, url):
        self.session = session
        self.url = url
        self.soup = None
        self.title = None
        self.author = None
        self.date = None
        self.tags = []

    def _get_one_tag(self, selector):
        """Return text from one tag.

        This will assert that we only get one tag which helps prevent us against
        silent data structure changes.

        """
        one_tag = self.soup.select(selector)

        # assert that we only have one tag
        assert len(one_tag) == 1

        return one_tag[0].text

    async def _get_page_data(self):
        """Initializes soup and downloads page data"""
        resp = await self.session.request(method="GET", url=self.url)

        # raise an exception if page did not load
        resp.raise_for_status()
        html = await resp.text()

        return html

    async def parse(self):
        data = await self._get_page_data()
        self.soup = bs4.BeautifulSoup(data, 'html.parser')

        # # just for debugging
        # with open("test.html") as f:
        #     soup = BeautifulSoup(f.read(), 'html.parser')

        self.title = self._get_one_tag("div[class~=section-content] div h1")

        self.author = self._get_one_tag("div[class~=section-content] "
                                        "div div div div a")

        self.date = self._get_one_tag("div[class~=section-content] "
                                      "div div div div time")

        for tag in self.soup.select("ul[class~=tags] li"):
            self.tags.append(tag.text)


async def main():
    url = 'https://hackernoon.com/3-steps-to-productive-habits-62ba6163d056'
    async with aiohttp.ClientSession() as session:
        a = article(session, url)
        await a.parse()

        print(a.title)
        print(a.author)
        print(a.date)
        print(a.tags)


if __name__ == "__main__":
    asyncio.run(main())

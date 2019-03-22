from __future__ import (
    absolute_import,
    print_function,
)

from scraper import (
    archive_scraper,
)

from scraper_pool import (
    scraper_pool
)

url = 'https://hackernoon.com/archive'


def main():
    spool = scraper_pool()
    years = archive_scraper(spool)

    years.put('archive', url)
    years.finish()


if __name__ == "__main__":
    main()

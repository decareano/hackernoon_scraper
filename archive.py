from __future__ import (
    absolute_import,
    print_function,
)

from scraper import (
    archive_scraper,
)

url = 'https://hackernoon.com/archive'


def main():
    years = archive_scraper()

    years.put('archive', url)
    years.finish()


if __name__ == "__main__":
    main()

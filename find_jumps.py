#!/usr/bin/env python

import logging

log = logging.getLogger(__name__)


def run():
    log.info("Hello, world!")

def main():
    """Initialize logging and run the script."""
    logging.basicConfig(format='%(asctime)s %(levelname)s--: %(message)s',
                        level=logging.DEBUG)
    run()

if __name__ == '__main__':
    main()
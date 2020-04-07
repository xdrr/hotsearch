import os, sys, requests, threading, logging, queue, copy, coloredlogs, time, json, signal
from datetime import datetime, timedelta
from splinter import Browser

class Search:
    _base_url = "https://www.hotwire.com/api/search/car/all"
    _api_key = "rds89xrxc4vywrtthjevarw3"
    _max_range = 28
    _max_threads = 5

    def __init__(self, criteria):

        self._results = queue.Queue()
        self._total_results = 0
        self._failures = []
        self._best_deal = {}
        self._car_info = {}

        self._locks = {
                'deal': threading.Lock(),
                'car_info': threading.Lock()
        }

        self._search_pool = self._proc_pool = []
        self._running = False

        self._criteria = criteria

        self._work_size = int(self._max_range / self._max_threads)

        self._log = logging.getLogger('Search')

        coloredlogs.install(
                logger=self._log,
                level='INFO',
        )

        signal.signal(signal.SIGINT, self.report_deal)

    def get_date(self, i):

        start = i * self._work_size
        end = start + self._work_size

        for offset in range(start, end):
            now = datetime.now()

            if now.hour > 10:
                d = timedelta(days=1)
                now = now + d

            day = now.day
            month = now.month
            year = now.year

            from_date = datetime(
                    year,
                    month,
                    day,
                    hour=10,
                    minute=0,
                    second=0,
                    microsecond=0
            )

            d = timedelta(days=offset)
            to_date = from_date + d

            yield (from_date, to_date)

    def report_deal(self, with_url=True, exit=True, *args):

        deal_ready = len(self._best_deal) != 0

        if deal_ready:
            result_code = self._best_deal['resultID']

            car_type = self._best_deal['vendorCategory'] + ' car'

            car_info = self._best_deal['carInfo']

            if car_info and car_info['carInfoId'] in self._car_info:
                car_info = self._car_info[car_info['carInfoId']]
                car_type = car_info['models']

            charges = self._best_deal['carSummaryOfCharges']

            currency = charges['localCurrencyCode']
            deal_total = charges['total']
            deal_rate = charges['dailyRate']

            rental_days = self._best_deal['rentalDays']

            self._log.critical(f'Best price: A {car_type} for ${deal_total} {currency} [{deal_rate} / day @ {rental_days} days] (result: {result_code})')

            if with_url:
                self._log.critical(f"Get this deal at: https://www.hotwire.com/checkout/#!/car/billing/{result_code}/?countryCode={self._criteria['country']}&currencyCode={currency}")

            if exit:
                self._running = False

    def begin(self):

        self._running = True

        self._log.debug(f'Starting up {self._max_threads} search workers')

        for i in range(self._max_threads):
            t = threading.Thread(
                target=self.do_search,
                args=[ i ],
            )

            self._search_pool.append(t)

            t.start()

        self._log.debug(f'Starting up {self._max_threads} processor workers')

        for i in range(self._max_threads):
            t = threading.Thread(
                    target=self.proc_search
            )

            self._proc_pool.append(t)

            t.start()

        # main loop

        while self._running:
            cur_results = self._results.qsize()
            cur_failures = len(self._failures)

            deal_ready = len(self._best_deal.keys()) != 0

            self._log.info(f'Status: [total results: {self._total_results}] [results pending: {cur_results}] [failures: {cur_failures}]')

            if deal_ready:
                self.report_deal(False, False)

            if len(self._search_pool) == 0 and len(self._proc_pool) == 0:
                self._running = False

                self.report_deal(False, False)
                break

            time.sleep(2)

        self._running = False

        [ x.join() for x in self._search_pool ]
        [ x.join() for x in self._proc_pool ]

    def proc_search(self):

        while self._running:

            res = self._results.get()

            self._total_results += 1

            if 'searchResults' in res and 'solution' in res['searchResults']:
                results = res['searchResults']['solution']

                cheapest = {}

                for x in results:
                    if 'carSummaryOfCharges' in cheapest and 'dailyRate' in cheapest['carSummaryOfCharges']:
                        if float(cheapest['carSummaryOfCharges']['dailyRate']) > float(x['carSummaryOfCharges']['dailyRate']):
                            cheapest = x
                    else:
                        cheapest = x

                if cheapest:
                    with self._locks['deal']:
                        if self._best_deal:
                            if float(self._best_deal['carSummaryOfCharges']['dailyRate']) > float(cheapest['carSummaryOfCharges']['dailyRate']):
                                self._best_deal = copy.copy(cheapest)
                        else:
                            self._best_deal = copy.copy(cheapest)

            if 'carInfoMetaData' in res and 'carInfo' in res['carInfoMetaData']:
                car_info = res['carInfoMetaData']['carInfo']

                with self._locks['car_info']:
                    for info in car_info:
                        self._car_info[info['carInfoId']] = info


    def do_search(self, i):

        while self._running:

            for from_date, to_date in self.get_date(i):

                if not self._running:
                    break

                ts = datetime.now().strftime('%s')

                params = {
                        'apikey': self._api_key,
                        'nwid': 'IR',
                        'siteID': 10557,
                        'siteIDtime': ts,
                        'string': 'siteID:10557,nwid:IR',
                        'timesStamp': ts,
                        'useCluster': 1,
                        'sig': self._criteria['sig'],
                }

                data = {
                        'clientInfo': {
                            'clientID': '7758241487852066344',
                            'customerID': '-1',
                            'countryCode': self._criteria['country'].lower(),
                            'latLong': '0,0',
                            'currencyCode': self._criteria['currency'].upper(),
                        },
                        'searchCriteria': {
                            'ageOfDriver': '25+',
                            'location': {
                                'originLocation': self._criteria['location'],
                                'originLocationName': self._criteria['location'],
                                'originLocationType': self._criteria['locationType'],
                                'destinationLocation': self._criteria['location'],
                                'destinationLocationName': self._criteria['location'],
                                'destinationLocationType': self._criteria['locationType'],
                            },
                            'startAndEndDate': {
                                'start': from_date.isoformat(),
                                'end': to_date.isoformat(),
                            },
                            'oneWay': self._criteria['oneWay']
                        },
                        'sortRequestType': 'LOWEST_PRICE',
                }

                r = requests.post(self._base_url, params=params, json=data)

                if r.status_code == 200:

                    self._log.debug(f"Good response: {r.url}")

                    self._results.put(r.json())
                else:

                    self._log.warning(f"Bad response [{r.status_code}]: {r.text}")

                    self._log.debug(f'Last error URL: {r.url}')

                    self._failures.append({
                        'url': self._base_url,
                        'params': params,
                        'body': data,
                        'status': r.status_code,
                        'msg': r.text
                    })


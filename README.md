# Hot Search

![Hot Search](logo.png)

Need to rent a car and want the absolute cheapest daily rate? Hot Search
is for you.

Hot Search finds the cheapeast possible rate price from the moment it's
launched, by enumerating rental search options; namely time periods.

Historical usage of Hotwire.com has shown that specific dates and
durations are significantly cheaper than others. Hence, by automatically
enumerating through these search parmaeters it's possible to find the
absolute cheapest car rental rate.

## Installation

Create a python virtual environment and install HotSearch requirements.

```
pip install -r requirements.txt
```

## Usage

Hot Search requires a valid signature from the Hotwire.com website. See [Caveats](#Caveats).

With a valid signature, launch Hot Search specifying your location and currency.

For example, to search for cheap rentals as San Jose Airport:

```
python hotsearch.py -c USD -x USD -l SJC -s <signature value>
```

The cheapest price will be output and slowly improved over time, as
better results are processed. The result value shown on the far right
of a result line, can be entered into the following URL to book a car
at the shown price.

```
https://www.hotwire.com/checkout/#!/car/billing/<RESULT VALUE>/?countryCode=us&currencyCode=USD
```

You may also stop the program (by pressing C-c) and a URL will be
displayed for you to follow through to checkout.

## Caveats

Currently, Hot Search requires a valid signature value to be specified so
that API requests may be performed to the Hotwire.com site.  The signature
value is either an anti-CSRF token or API signing checksum that rotates
every so often on the site. This means that Hot Search will only last
so long before a new signature must be obtained and Hot Search restarted
with ths new signature.

To obtain a signature, visit Hotwire.com and perform a search with the
browser console open. On the `Network` tab search for `sig`.  Find the
`/api/search/car/all` request and copy the value of `sig` in the request
paramters.  Use this value with the `-s` flag when starting Hot Search.

The highest priority improvement is to comprehend the generation of
the `sig` value so this can be performed in the Hot Search client
automatically.

## FAQ

**All I see is "Bad response [403]: Not Authorized"**

This means you've specified an invalid or expired signature value. Obtain a new value by following the process
described in [Caveats](#Caveats).

## LICENSE

See LICENSE.txt

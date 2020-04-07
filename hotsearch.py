import argparse
import search

def main(args):

    criteria = {
            'country': args.c,
            'currency': args.x,
            'location': args.l,
            'locationType': 'AIRPORT',
            'oneWay': args.o,
            'sig': args.s
    }

    search_engine = search.Search(criteria)

    search_engine.begin()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Hotwire car search')
    parser.add_argument('-l', type=str, required=True, help='Rental location')
    parser.add_argument('-o', type=bool, default=False, help='One way rental?')
    parser.add_argument('-c', type=str, required=True, help='Country (code)')
    parser.add_argument('-x', type=str, required=True, help='Currency (code)')
    parser.add_argument('-s', type=str, required=True, help='Signature (sig value from a recent search request)')

    args = parser.parse_args()

    main(args)

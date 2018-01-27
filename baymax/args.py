import argparse


def get_args():
    parser = argparse.ArgumentParser(description='Baymax arguments.')
    parser.add_argument('-t', '--token', metavar='token', type=str,
                        help='Telegram bot token', required=True)
    parser.add_argument('-to', '--timeout', metavar='timeout', type=int,
                        help='Telegram bot timeout', default=30)

    return parser.parse_args()

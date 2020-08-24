import os
import requests
import time
import bs4
import csv
from datetime import datetime
from datetime import timedelta
import re


ENDPOINT = 'https://radiocomercial.iol.pt/passou'


def scrape(out_dir):
    AVAILABLE_DAYS = [datetime.today() - timedelta(days=d) for d in range(7) ]

    all_songs = []
    dates = []
    for date in AVAILABLE_DAYS:
        print(f'Scraping: day {date}')
        day, month, year = date.day, date.month, date.year
        dates.append(f'{day:02d}_{month:02d}_{year:02d}')

        day_songs = []

        response = requests.post(url=ENDPOINT, data={'radio': 'comercial', 'day': f'{year:02d}-{month:02d}-{day:02d}', 'when': ''})
        html = bs4.BeautifulSoup(response.text, 'html.parser')
        music_info_divs = html.findAll('div', {'class': 'song'})

        for mi_div in music_info_divs:
            time = mi_div.find('div', {'class': 'timePlayed'}).text
            artist = mi_div.find('div', {'class': 'songArtist'}).text
            song = mi_div.find('div', {'class': 'songTitle'}).text

            song = re.sub(r'\s+', ' ', song)
            artist = re.sub(r'\s+', ' ', artist)
            time = re.sub(r'\s+', ' ', time)

            # found some weird examples of this occuring in the
            # data...
            # for example:
            # 12/08/2020 - 11:47 - liner daytime_08 (a minha filha vai delirar)
            # 11/08/2020 - 12:44 - liner daytime_07 (queria bilhetes)
            if 'liner daytime' in artist.lower():
                continue

            day_songs.append((time, song, artist))

        all_songs.append(day_songs)

    print('Writing to csv files')
    for date_idx, date in enumerate(dates):
        filename = os.path.join(out_dir, f'comercial_{date}.csv')
        with open(filename, 'w') as csvfile:
            writer = csv.writer(csvfile, delimiter='|', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            writer.writerows(all_songs[date_idx])


def main():
    import argparse

    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-o', '--out', type=str, default='./data/')
    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)

    scraper = scrape(args.out)


if __name__ == '__main__':
    main()

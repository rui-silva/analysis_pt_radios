import os
import requests
import time
import bs4
import csv
from datetime import datetime
from datetime import timedelta


ENDPOINT = 'https://cidade.iol.pt/passou'


def day_to_nums(day):
    if day == 'hoje':
        today = datetime.today()
        return today.day, today.month, today.year
    elif day == 'ontem':
        yesterday = datetime.today() - timedelta(days=1)
        return yesterday.day, yesterday.month, yesterday.year


def scrape(out_dir):
    AVAILABLE_DAYS = ['hoje', 'ontem']
    HOURS = range(0, 24)

    all_songs = []
    dates = []
    for day_str in AVAILABLE_DAYS:
        print(f'Scraping: day {day_str}')
        day, month, year = day_to_nums(day_str)
        dates.append(f'{day:02d}_{month:02d}_{year:02d}')

        day_songs = []
        for hour in HOURS:
            print(f'- Hour: {hour}')
            response = requests.get(url=ENDPOINT, params={'d': day_str, 'h': hour})
            html = bs4.BeautifulSoup(response.text, 'html.parser')
            music_info_lis = html.findAll('li', {'class': 'gereral-item'})

            for mi_li in music_info_lis:
                time = mi_li.find('div', {'class': 'passou-musica-hora'}).text
                artist = mi_li.find('span', {'class': ['top8artistname', 'passou-musica-artista']}).text
                song = mi_li.find('span', {'class': ['top8songname', 'passou-musica-title']}).text

                day_songs.append((time, song, artist))
                print((time, song, artist))

        all_songs.append(sorted(day_songs, key=lambda x: x[0]))

    print('Writing to csv files')
    for date_idx, date in enumerate(dates):
        filename = os.path.join(out_dir, f'cidadefm_{date}.csv')
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

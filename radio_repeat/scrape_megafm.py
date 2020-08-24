import os
import requests
import time
import bs4
import csv
from datetime import datetime
from datetime import timedelta
import random


ENDPOINT = 'https://megahits.sapo.pt/ajax/pesquisa/acaboudetocar.aspx'


def day_to_nums(day):
    if day == 'today':
        today = datetime.today()
        return today.day, today.month, today.year
    elif day == 'yesterday':
        yesterday = datetime.today() - timedelta(days=1)
        return yesterday.day, yesterday.month, yesterday.year


def scrape(out_dir):
    AVAILABLE_DAYS = ['today', 'yesterday']
    HOURS = range(0, 24)
    MINUTES = [0, 15, 30, 45, 55]

    all_songs = []
    dates = []
    for day_str in AVAILABLE_DAYS:
        print(f'Scraping: day {day_str}')
        day, month, year = day_to_nums(day_str)
        dates.append(f'{day:02d}_{month:02d}_{year:02d}')

        day_songs = set()
        for hour in HOURS:
            for minute in MINUTES:
                print(f'- Hour: {hour:02d} : Minute {minute:02d}')
                response = requests.post(url=ENDPOINT, data={'hora': hour, 'min': minute, 'dia': day_str, 'randval': random.random()})
                html = bs4.BeautifulSoup(response.text, 'html.parser')

                music_info_divs = html.findAll('div', {'class': 'ac-card1'})
                for mi_div in music_info_divs:
                    song = mi_div.find('div', {'class': 'ac-nomem1'}).text
                    artist = mi_div.find('div', {'class': 'ac-autor1'}).text
                    time = mi_div.find('td', {'class': 'ac-horas1'}).text

                    # This website has a very strange method for
                    # selecting the time range. It seems that for a
                    # given time x, it returns songs in the range
                    # [x - 15, x + 15]. Near the boundaries of the
                    # days it may end up giving songs from the
                    # previous/next day. Here we try to avoid that. 
                    song_time_hour = int(time[:2])
                    if hour == 0 and song_time_hour == 23:
                        continue
                    if hour == 23 and song_time_hour == 0:
                        continue
                    
                    day_songs.add((time, song, artist))

        all_songs.append(sorted(list(day_songs), key=lambda x: x[0]))

    print('Writing to csv files')
    for date_idx, date in enumerate(dates):
        filename = os.path.join(out_dir, f'megafm_{date}.csv')
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

import os
import requests
import time
import bs4
import csv
from datetime import datetime
from datetime import timedelta


ENDPOINT = 'https://rfm.sapo.pt/ajax/acaboudetocar/getlistmusic.aspx'


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

    all_songs = []
    dates = []
    for day_str in AVAILABLE_DAYS:
        print(f'Scraping: day {day_str}')
        day, month, year = day_to_nums(day_str)
        dates.append(f'{day:02d}_{month:02d}_{year:02d}')

        day_songs = []
        for hour in HOURS:
            print(f'- Hour: {hour}')
            response = requests.post(url=ENDPOINT, data={'hora': hour, 'dia': day_str, 'randval': 0.2})
            html = bs4.BeautifulSoup(response.text, 'html.parser')
            music_info_divs = html.findAll('div', {'class': 'musicInfo'})

            for mi_div in music_info_divs:
                time = mi_div.find('div', {'class': 'musicInfoTime'}).text
                artist = mi_div.find('div', {'class': 'musicInfoArtist'}).text
                song = mi_div.find('div', {'class': 'musicInfoName'}).text
                
                day_songs.append((time, song, artist))

        all_songs.append(day_songs)

    print('Writing to csv files')
    for date_idx, date in enumerate(dates):
        filename = os.path.join(out_dir, f'rfm_{date}.csv')
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

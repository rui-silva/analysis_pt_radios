import os
import glob
import pandas as pd
import csv
import re
import unidecode
import functools
import operator


RADIOS = ['rfm', 'comercial', 'megafm', 'cidadefm']


def date_from_filename(filename):
    matcher = re.match(r'[a-z]+_([0-9]+)_([0-9]+)_([0-9]+)', filename)
    day, month, year = matcher.group(1), matcher.group(2), matcher.group(3)

    return int(day), int(month), int(year)


def lowercase(df):
    df['song'] = df['song'].str.lower()
    df['artist'] = df['artist'].str.lower()
    return df


def clean_artist(df):
    # typos/inconsistencies detected manually
    df['artist'] = df['artist'].str.replace('xutos e pontapés', 'xutos & pontapés', regex=True)
    df['artist'] = df['artist'].str.replace('lil peep', 'lil pump')
    df['artist'] = df['artist'].str.replace('lil peep', 'lil pump')
    df['artist'] = df['artist'].str.replace('nial horan', 'niall horan')
    df['artist'] = df['artist'].str.replace('michele marrone', 'michele morrone')
    df['artist'] = df['artist'].str.replace('the cranberries', 'cranberries')
    df['artist'] = df['artist'].str.replace('elvis costelo', 'elvis costello')
    df['artist'] = df['artist'].str.replace('rag n bone man', 'ragnbone man')
    df['artist'] = df['artist'].str.replace('r\.e\.m', 'rem')

    df['artist'] = df['artist'].str.replace('diogo piã‡arra', 'diogo picarra', regex=True)
    df['artist'] = df['artist'].str.replace('diogo pi_arra', 'diogo picarra')

    # normalize the artist separations with &
    # - we found two bands that uses & in their name. so we repeat it.
    df['artist'] = df['artist'].str.replace('xutos & pontapés', 'xutos && pontapés', regex=True)
    df['artist'] = df['artist'].str.replace('years & years', 'years && years', regex=True)

    # - replace "feat.", "ft.", "x", "&", "x", "[+]" for &
    df['artist'] = df['artist'].str.replace(' feat(\.)? ', ' & ', regex=True)
    df['artist'] = df['artist'].str.replace(' ft(\.)? ', ' & ', regex=True)
    df['artist'] = df['artist'].str.replace(' \[\+\] ', ' & ', regex=True)
    # ' x ' needs to be processed before comma, because some artist names end in X
    df['artist'] = df['artist'].str.replace(' x ', ' & ', regex=True)
    df['artist'] = df['artist'].str.replace(' , ', ' & ', regex=True)
    df['artist'] = df['artist'].str.replace(', ', ' & ', regex=True)
    df['artist'] = df['artist'].str.replace(' / ', ' & ', regex=True)

    # remove extra symbols
    # - necessary since some statios use them, other dont
    df['artist'] = df['artist'].str.replace('\[.*\]', '', regex=True)
    df['artist'] = df['artist'].str.replace("'", '')
    df['artist'] = df['artist'].str.replace('\.', ' ')
    df['artist'] = df['artist'].str.replace('!', ' ')
    df['artist'] = df['artist'].str.replace('-', ' ')

    # further cleaning
    # - ascii only
    df['artist'] = df['artist'].apply(lambda x: unidecode.unidecode(x))
    # - sort artist names lexicographically
    df['artist'] = df['artist'].apply(lambda x: ' & '.join(sorted(x.split(' & '))))
    # - remove extra info in parenthesis
    df['artist'] = df['artist'].str.replace('\(.*\)', '', regex=True)
    # - remove unnecessary spaces
    df['artist'] = df['artist'].str.replace('\s+', ' ', regex=True)
    df['artist'] = df['artist'].str.strip()

    return df


def clean_songs(df):
    # typos/inconsistencies detected manually
    df['song'] = df['song'].str.replace('banana \(ft\. shaggy\) dj fle remix', 'banana')
    df['song'] = df['song'].str.replace('wonderfull', 'wonderful')

    # normalize songs
    # - remove extra symbols, extra info in (), make it ascii, and
    #   remove unecessary spaces
    df['song'] = df['song'].str.replace('\.\.\./\.\.\.', ' ')
    df['song'] = df['song'].str.replace('\.\.\.', ' ')
    df['song'] = df['song'].str.replace('\.', '')
    df['song'] = df['song'].str.replace('\?', ' ')
    df['song'] = df['song'].str.replace('!', ' ')
    df['song'] = df['song'].str.replace(',', '')
    df['song'] = df['song'].str.replace('-', ' ')
    df['song'] = df['song'].str.replace("'", '')
    df['song'] = df['song'].str.replace('`', '')
    df['song'] = df['song'].str.replace('\[.*\]', '', regex=True)
    df['song'] = df['song'].str.replace('\(.*\)', '', regex=True)

    df['song'] = df['song'].apply(lambda x: unidecode.unidecode(x))

    df['song'] = df['song'].str.replace('\s+', ' ', regex=True)
    df['song'] = df['song'].str.strip()
    return df


def clean_musics_with_multiple_artists(df):
    def selector_filter_by_song(df, song):
        return df['song'] == row.song

    def selector_filter_by_artist(df, artist):
        return df['artists_list'].apply(lambda x: artist in x)
    
    df['artists_list'] = df['artist'].apply(lambda x: x.split(' & '))

    for group_name, df_group in df.groupby('song'):
        for index, row in df_group.iterrows():
            row_artists = row.artists_list
            selector = functools.reduce(operator.or_, [selector_filter_by_artist(df_group, ra) for ra in row_artists])
            
            selected_artists = df_group['artists_list'][selector]
            longest_artists_list = max(selected_artists.tolist(), key=lambda x: len(x))
            final_artist_str = ' & '.join(sorted(longest_artists_list))

            df_selector = selector[selector].index
            df.loc[df_selector, 'artist'] = final_artist_str

    return df


def additional_manual_fixes(df):
    sel = (df['song'] == 'dilema') & (df['artist'] == 'kelly roland & nelly')
    df['song'][sel] = 'dilemma'
    df['artist'][sel] = 'kelly rowland & nelly'

    return df


def parse_radio_df(radio, in_dir, debug=False):
    print(f' - Parsing {radio}')
    paths = glob.glob(in_dir + f'{radio}_*.csv')
    frames = []
    for path in paths:
        filename = os.path.splitext(os.path.basename(path))[0]
        day, month, year = date_from_filename(filename)

        df = pd.read_csv(path, delimiter='|', names=['time', 'song', 'artist'])
        df['date'] = f'{year}-{month:02d}-{day:02d}'
        df['radio'] = radio
        frames.append(df)

    df = pd.concat(frames)
    if debug:
        df.sort_values(['song']).to_csv(filename + '_debug_sort_song.csv', index=False, sep='|')
        df.sort_values(['artist']).to_csv(filename + '_debug_sort_artist.csv', index=False, sep='|')

    return df


def clean(df):
    print(' - lowercasing')
    df = lowercase(df)
    print(' - cleaning songs')
    df = clean_songs(df)
    print(' - cleaning artists')
    df = clean_artist(df)
    print(' - normalizing songs with multiple artists')
    df = clean_musics_with_multiple_artists(df)

    return df


def main():
    import argparse

    parser = argparse.ArgumentParser(description='')
    parser.add_argument('-i', '--input', type=str, default='./data/')
    args = parser.parse_args()

    print('Parsing each radio...')
    df = [parse_radio_df(radio_name, args.input) for radio_name in RADIOS]
    df = pd.concat(df, ignore_index=True)

    print('Cleaning dataframe...')
    df = clean(df)
    df = additional_manual_fixes(df)

    df.to_csv('data/all_data.csv', index=False, sep='|')


if __name__ == '__main__':
    main()

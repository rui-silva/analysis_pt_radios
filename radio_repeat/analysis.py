import numpy as np
import pandas as pd
pd.set_option('display.max_rows', 200)
import matplotlib.pyplot as plt
import datetime as dt

RADIOS = ['cidadefm', 'comercial', 'megafm', 'rfm']
RADIO_NAME_MAP = {
    'rfm': 'RFM',
    'comercial': 'Comercial',
    'megafm': 'MegaFM',
    'cidadefm': 'CidadeFM'
}

def overlaps(df):
    """Outputs musics that played simultaneously"""
    print('\n\nOverlaps\n')

    df['dt_start'] = df['datetime']
    df['dt_end'] = 0
    for _, group in df.groupby(['radio']):
        dt_end = group.sort_values('datetime')['dt_start'].shift(-1)
        df.loc[group.index, 'dt_end'] = dt_end

    simultaneous = []
    for _, group in df.groupby(['song', 'artist']):
        group = group.sort_values('dt_start')
        group['merged'] = (group['dt_start'] >
                           group['dt_end'].shift()).cumsum()

        result = group.groupby('merged').agg(
            date=('date', 'first'),
            song=('song', 'first'),
            artist=('artist', 'first'),
            radios=('radio', lambda x: ' | '.join(x)),
            radios_count=('radio', 'count'),
            times=('time', lambda x: ' | '.join(x)))

        result = result[result.radios_count > 1]
        if len(result) > 0:
            simultaneous.append(result)

    if len(simultaneous) == 0:
        return pd.DataFrame()

    simultaneous = pd.concat(simultaneous).reset_index()
    print(simultaneous)
    print(f'Found: {len(simultaneous)}')

    print(
        simultaneous.groupby(['song',
                              'artist']).size().sort_values(ascending=False))

    print(simultaneous.groupby(['date']).size())
    return simultaneous


def count_daily_radio_repetitions(df, radio):
    """Count daily repetitions of songs
    
    Returns a pd.Series with the number of occurences of a given # of
    repetitions of a song, on a given day. Index is the # of
    repetitions, values are the number of occurrences.

    Example:
    1 2
    2 1
    3 4
    Corresponds to:
    - 2 songs that were played once
    - 1 song that was played twice
    - 4 songs that were played 3 times
    """

    radio_df = df[df['radio'] == radio]
    radio_counts = radio_df.groupby(['song', 'artist',
                                     'date']).agg(count=('time', 'count'))

    radio_counts = radio_counts.groupby('count').size().sort_index()
    radio_counts = radio_counts

    return radio_counts


def avg_daily_radio_repetitions(df, radio):
    """Computes the average daily repetitions of songs on a given radio

    Returns a scalar with the average number of times songs are played
    on a given station.
    """
    dates = df['date'].unique()

    # Compute avg daily repetitions
    counts = count_daily_radio_repetitions(df, radio)
    counts /= len(dates)

    # Compute the weighted average of weekly repetitions.
    times = counts.index.to_numpy()
    # - compute weights
    weights = (counts / counts.sum()).values
    daily_avg = times.dot(weights)

    return daily_avg


def daily_repetitions_stats(df):
    """Outputs avg daily repetitions for the radios"""
    print('\n\nDaily Stats\n')

    for radio_idx, radio in enumerate(RADIOS):
        avg = avg_daily_radio_repetitions(df, radio)
        print(f'{radio}: plays musics an avg of {avg:.1f} times per day')


def daily_repetitions_pie(df):
    """Generates pie chart of daily repetitions for the radios.
    """
    fig, axes = plt.subplots(
        nrows=2,
        ncols=2,
        squeeze=False,
        figsize=(12, 15),
        subplot_kw={},
        gridspec_kw={})
    axes = axes.ravel()

    dates = df['date'].unique()
    for radio_idx, radio in enumerate(RADIOS):
        ax = axes[radio_idx]

        radio_counts = count_daily_radio_repetitions(df, radio)
        radio_counts /= len(dates)

        others_5_9 = radio_counts[(radio_counts.index >= 5)
                                  & (radio_counts.index < 10)].sum()
        others_10p = radio_counts[(radio_counts.index >= 10)].sum()

        radio_counts_binned = radio_counts[:4]
        if not np.isclose(others_5_9, 0.0):
            radio_counts_binned = radio_counts_binned.append(
                pd.Series(others_5_9, index=['5-9']))
        if not np.isclose(others_10p, 0.0):
            radio_counts_binned = radio_counts_binned.append(
                pd.Series(others_10p, index=['10+']))

        ax.pie(
            radio_counts_binned.to_numpy(),
            labels=radio_counts_binned.index,
            autopct='%1.f%%',
            startangle=90,
            pctdistance=.9,
            explode=[.05] * len(radio_counts_binned),
            colors=[
                '#77DD76', '#BDE7BD', '#E7F1E8', '#FFD5D4', '#FFB6B3',
                '#FF6962'
            ])

        ax.set_title(RADIO_NAME_MAP[radio])

    plt.suptitle(
        'Quantas vezes passa uma música ao longo do dia? (média ao longo de 1 semana)'
    )
    plt.tight_layout()
    plt.savefig('daily_repetitions.png')


def count_week_radio_repetitions(df, radio):
    """Count repetitions of songs during the week days
    
    Returns a pd.Series with the number of days a given song is
    played, on a given week. Index is the # of days, values are the
    number of occurrences.

    Example:
    1 2
    2 1
    3 4
    Corresponds to:
    - 2 songs that were played on a single day
    - 1 song that was played in two days
    - 4 songs that were played in three days
    """
    radio_df = df[df['radio'] == radio]
    radio_counts = radio_df.groupby(
        ['song', 'artist']).agg(count=('date', lambda x: x.nunique()))
    radio_counts = radio_counts.groupby('count').size().sort_index()
    return radio_counts


def avg_week_radio_repetitions(df, radio):
    """Computes the average # of days a song is repeated, on a given radio

    Returns a scalar with the average number of days that songs are played
    on a given station.
    """

    # Count frequency of # of days that songs are repeated
    radio_counts = count_week_radio_repetitions(df, radio)

    # Compute weighted average
    times = radio_counts.index.to_numpy()
    weights = (radio_counts / radio_counts.sum()).values
    avg = times.dot(weights)
    return avg


def week_repetitions_stats(df):
    """Outputs avg # of days where songs are repeated"""
    print('\n\nWeek Stats\n')
    for radio_idx, radio in enumerate(RADIOS):
        avg = avg_week_radio_repetitions(df, radio)
        print(f'{radio}: plays musics an avg of {avg:.1f} days per week')


def week_repetitions_pie(df):
    """Generates pie chart of # of days where songs were repeated
    """
    fig, axes = plt.subplots(
        nrows=2,
        ncols=2,
        squeeze=False,
        figsize=(12, 15),
        subplot_kw={},
        gridspec_kw={})
    axes = axes.ravel()
    for radio_idx, radio in enumerate(RADIOS):
        ax = axes[radio_idx]

        radio_counts = count_week_radio_repetitions(df, radio)

        ax.pie(
            radio_counts.to_numpy(),
            labels=radio_counts.index,
            autopct='%1.f%%',
            startangle=90,
            pctdistance=.9,
            explode=[.05] * len(radio_counts),
            colors=[
                'cornflowerblue', 'sandybrown', 'yellowgreen', 'lightcoral',
                'palevioletred', 'peru', 'violet'
            ])

        ax.set_title(RADIO_NAME_MAP[radio])

    plt.suptitle('Em quantos dias da semana passa uma música?')
    plt.tight_layout()
    plt.savefig('weekly_repetitions.png')


def main():
    pd.set_option('display.max_rows', 500)
    df = pd.read_csv('./data/all_data.csv', delimiter='|')
    df['datetime'] = df[['date', 'time']].apply(
        lambda x: pd.to_datetime(
            f'{x.date} {x.time}', format='%Y/%m/%d %H:%M'),
        axis=1)
    df['date'] = pd.to_datetime(df['date'])

    df = df[(df['date'] >= dt.datetime(year=2020, month=8, day=10))
            & (df['date'] <= dt.datetime(year=2020, month=8, day=16))]

    daily_repetitions_stats(df)
    week_repetitions_stats(df)
    daily_repetitions_pie(df)
    week_repetitions_pie(df)
    overlaps(df)


if __name__ == '__main__':
    main()

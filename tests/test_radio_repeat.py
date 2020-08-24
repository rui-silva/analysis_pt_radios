from radio_repeat import __version__
import radio_repeat.analysis as rra
import pandas as pd
import numpy as np


def make_simple_radio_df(radio):
    return pd.DataFrame({
        'date':
        ['2020-08-10', '2020-08-10', '2020-08-10', '2020-08-11', '2020-08-11'],
        'song': ['S1', 'S1', 'S2', 'S1', 'S3'],
        'artist': ['A1', 'A1', 'A2', 'A1', 'A2'],
        'radio': [radio] * 5,
        'time': ['00:01', '00:02', '00:03', '00:04', '00:05']
    })


def _add_datetime_to_df(df):
    df['datetime'] = df[['date', 'time']].apply(lambda x: pd.to_datetime(
        f'{x.date} {x.time}', format='%Y/%m/%d %H:%M'),
                                                axis=1)
    df['date'] = pd.to_datetime(df['date'])

    return df


def test_single_overlap():
    df = pd.DataFrame({
        'date': ['2020-08-10', '2020-08-10', '2020-08-10', '2020-08-10'],
        'song': ['S1', 'S2', 'S1', 'S3'],
        'artist': ['A1', 'A1', 'A1', 'A2'],
        'radio': ['rfm', 'rfm', 'comercial', 'comercial'],
        'time': ['00:01', '00:04', '00:02', '00:05']
    })
    df = _add_datetime_to_df(df)

    result = rra.overlaps(df)
    assert len(result) == 1
    result = result.iloc[0]
    assert result['song'] == 'S1' and result['artist'] == 'A1'
    assert len(result['radios'].split(' | ')) == 2
    assert 'rfm' in result['radios'] and 'comercial' in result['radios']


def test_no_overlap():
    df = pd.DataFrame({
        'date': ['2020-08-10', '2020-08-10', '2020-08-10', '2020-08-10'],
        'song': ['S1', 'S2', 'S1', 'S3'],
        'artist': ['A1', 'A1', 'A1', 'A2'],
        'radio': ['rfm', 'rfm', 'comercial', 'comercial'],
        'time': ['00:01', '00:04', '00:05', '00:09']
    })
    df = _add_datetime_to_df(df)

    result = rra.overlaps(df)
    assert len(result) == 0


def test_overlap_but_on_different_day():
    df = pd.DataFrame({
        'date': ['2020-08-10', '2020-08-10', '2020-08-11', '2020-08-11'],
        'song': ['S1', 'S2', 'S1', 'S3'],
        'artist': ['A1', 'A1', 'A1', 'A2'],
        'radio': ['rfm', 'rfm', 'comercial', 'comercial'],
        'time': ['00:01', '00:04', '00:02', '00:05']
    })
    df = _add_datetime_to_df(df)

    result = rra.overlaps(df)
    assert len(result) == 0


def test_overlap_consecutive_days():
    df = pd.DataFrame({
        'date': ['2020-08-10', '2020-08-11', '2020-08-11', '2020-08-11'],
        'song': ['S1', 'S2', 'S1', 'S3'],
        'artist': ['A1', 'A1', 'A1', 'A2'],
        'radio': ['rfm', 'rfm', 'comercial', 'comercial'],
        'time': ['23:58', '00:03', '00:02', '00:07']
    })
    df = _add_datetime_to_df(df)

    result = rra.overlaps(df)
    assert len(result) == 1
    result = result.iloc[0]
    assert result['song'] == 'S1' and result['artist'] == 'A1'
    assert len(result['radios'].split(' | ')) == 2
    assert 'rfm' in result['radios'] and 'comercial' in result['radios']


def test_three_overlaps():
    df = pd.DataFrame({
        'date': [
            '2020-08-10', '2020-08-10', '2020-08-10', '2020-08-10',
            '2020-08-10', '2020-08-10'
        ],
        'song': ['S1', 'S2', 'S1', 'S3', 'S1', 'S5'],
        'artist': ['A1', 'A1', 'A1', 'A2', 'A1', 'A5'],
        'radio': ['rfm', 'rfm', 'comercial', 'comercial', 'megafm', 'megafm'],
        'time': ['15:38', '15:42', '15:39', '15:43', '15:41', '15:45']
    })
    df = _add_datetime_to_df(df)

    result = rra.overlaps(df)
    assert len(result) == 1
    result = result.iloc[0]
    assert result['song'] == 'S1' and result['artist'] == 'A1'
    assert len(result['radios'].split(' | ')) == 3
    assert sorted(
        result['radios'].split(' | ')) == ['comercial', 'megafm', 'rfm']


def test_multiple_overlaps():
    """
    Tests multiple overlaps, with unordered times, and a complex three-overlap.
    The three-overlap takes the form:
    [   ]
      [   ]
         [   ]
    That is, the first and last plays do not overlap directly, only through the middle play.
    """
    df = pd.DataFrame({
        'date': [
            '2020-08-10', '2020-08-10', '2020-08-10', '2020-08-10',
            '2020-08-10', '2020-08-10', '2020-08-10', '2020-08-10',
            '2020-08-10'
        ],
        'song': ['S1', 'S2', 'S3', 'S4', 'S2', 'S5', 'S3', 'S2', 'S5'],
        'artist': ['A1', 'A2', 'A3', 'A4', 'A2', 'A5', 'A3', 'A2', 'A5'],
        'radio': [
            'rfm', 'rfm', 'rfm', 'comercial', 'comercial', 'comercial',
            'megafm', 'megafm', 'megafm'
        ],
        'time': [
            '15:38', '15:42', '15:46', '15:37', '15:41', '15:45', '15:41',
            '15:37', '15:35'
        ]
    })
    df = _add_datetime_to_df(df)

    result = rra.overlaps(df)
    assert len(result) == 2

    first = result.iloc[0]
    assert first['song'] == 'S2' and first['artist'] == 'A2'
    assert len(first['radios'].split(' | ')) == 3
    assert sorted(
        first['radios'].split(' | ')) == ['comercial', 'megafm', 'rfm']

    second = result.iloc[1]
    assert second['song'] == 'S3' and second['artist'] == 'A3'
    assert len(second['radios'].split(' | ')) == 2
    assert sorted(second['radios'].split(' | ')) == ['megafm', 'rfm']


def test_count_daily_radio_repetitions():
    df = make_simple_radio_df('rfm')
    # Expected:
    # - day 1:
    #   - 1 rep: 1
    #   - 2 rep: 1
    # - day 2:
    #   - 1 rep: 2
    # => Counts: 1 rep: 3, 2reps: 1
    expected = pd.Series([3, 1], index=[1, 2])

    result = rra.count_daily_radio_repetitions(df, 'rfm')
    assert result.equals(expected)


def test_avg_daily_radio_repetitions():
    df = make_simple_radio_df('rfm')

    # Expected:
    # - day1: 2x S1 + 1x S2 => avg repetitions = 1.5
    # - day2: 1x S1 + 1x S3 => avg repetitions = 1
    # => daily avg = 1.25
    expected = 1.25

    result = rra.avg_daily_radio_repetitions(df, 'rfm')
    assert np.isclose(result, expected)


def test_count_day_radio_repetitions():
    df = make_simple_radio_df('rfm')
    expected = pd.Series([2, 1], index=[1, 2])
    result = rra.count_week_radio_repetitions(df, 'rfm')

    # Expected:
    # - 1 day:  2   => 2
    # - 2 days: 1  => 1

    assert result.equals(expected)


def test_avg_week_radio_repetitions():
    df = make_simple_radio_df('rfm')
    result = rra.avg_week_radio_repetitions(df, 'rfm')

    # Expected:
    # - played 1 day:  2
    # - played 2 days: 1
    # => (1x2 + 2x1) / 3
    expected = 4. / 3.

    assert np.isclose(result, expected)

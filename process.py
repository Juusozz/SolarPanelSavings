import pandas as pd
import streamlit as st
import datetime


def detect_separator(file, sample_size=1024):
    # Read a small part of the file to guess the separator
    content = file.read(sample_size)
    # Reset file read cursor to the start for later reading
    file.seek(0)
    # Count which delimiter is more prevalent
    semicolon_count = content.count(b';')
    comma_count = content.count(b',')
    # Determine the appropriate separator
    return ';' if semicolon_count > comma_count else ','

def process_dataframe(filepath, names, skiprows, sep, formats):
    sep = detect_separator(filepath)
    
    df = pd.read_csv(filepath, names=names, sep=sep, skiprows=skiprows, skip_blank_lines=True)
    df[names[1]] = df[names[1]].astype(str).str.replace(',', '.')

    df[names[1]] = pd.to_numeric(df[names[1]], errors='coerce')
    temp_date_columns = []
    for fmt in formats:
        temp_time = pd.to_datetime(df[names[0]], format=fmt, dayfirst=True, errors='coerce')
        temp_date_columns.append(temp_time)

    # Combine the results to find at least one valid parse per row
    combined_time = pd.concat(temp_date_columns, axis=1).bfill(axis=1).iloc[:, 0]

    if combined_time.isna().all():
        raise ValueError("None of the date formats matched the 'time' column data")

    df['time'] = combined_time
    
    df.set_index('time', inplace=True)
    return df
import pandas as pd
import streamlit as st
import datetime
import matplotlib.pyplot as plt

st.title("Lasketaan aurinkopaneelien tuottama säästö")



def process_dataframe(filepath, names, skiprows, sep, original_format):
    df = pd.read_csv(filepath, names=names, sep=sep, skiprows=skiprows, skip_blank_lines=True)
    df[names[1]] = df[names[1]].astype(str).str.replace(',', '.')

    df[names[1]] = pd.to_numeric(df[names[1]], errors='coerce')
    df['time'] = pd.to_datetime(df[names[0]], format=original_format, dayfirst=True)
    df.set_index('time', inplace=True)
    return df


# tuotettuCSV = st.file_uploader("Valitse tuotettu energia minuutin välein .csv tiedostona (muodossa AIKALEIMA;W)", type=['csv'])
tuotettuCSV = './data/tuotettu.csv'
# porssiCSV = st.file_uploader("Valitse pörssisähkön hinnan .csv tiedosto (muodossa AIKALEIMA;hinta (c/kWh))", type=['csv'])
porssiCSV = './data/porssi.csv'
# myytyCSV = st.file_uploader("Valitse myydyn sähkön .csv tiedosto (muodossa AIKALEIMA;kWh)", type=['csv'])
myytyCSV = './data/myyty.csv'
if tuotettuCSV is not None and porssiCSV is not None and myytyCSV is not None:
    df_produced = process_dataframe(tuotettuCSV, ['time', 'wats'], 3, ';', "%d/%m/%Y %H.%M")

    hourly_energy_watts = df_produced['wats'].resample('h').sum()
    hourly_totals_kwh = hourly_energy_watts / 60000

    df_market = process_dataframe(porssiCSV, ['time', 'c/kWh'], 1, ';', '%d.%m.%Y %H:%M')
    df_sold = process_dataframe(myytyCSV, ['time', 'kWh'], 1, ';', '%d.%m.%Y %H.%M')

    combined = pd.DataFrame()

    combined.index = df_sold.index
    combined['produced'] = (hourly_totals_kwh).round(3)
    # combined['bought'] = (df_bought['kWh']).round(2)
    combined['market'] = (df_market['c/kWh']).round(3)
    combined['sold'] = (df_sold['kWh']).round(3)
    combined.fillna(0, inplace=True)

    final = pd.DataFrame(index=combined.index)
    final['produced_kWh'] = combined['produced'].round(3)
    final['self_used_kWh'] = combined['produced'] - combined['sold']

    final['self_used_worth'] = final['self_used_kWh'] * combined['market'] + (5 * final['self_used_kWh']) + (0.6 * final['self_used_kWh'])
    final['self_used_worth_EUR'] = (final['self_used_worth'] / 100).round(3)
    final['sold_kWh'] = combined['sold'].round(3)

    final['revenue_from_energy_sold'] = (combined['sold'] * combined['market'] - (0.36 * combined['sold'])).round(3)
    final['revenue_from_energy_sold_EUR'] = (final['revenue_from_energy_sold'] / 100.0).round(3)


    # final['bought'] = combined['bought'].round(2)
    # final['market'] = combined['market'].round(3)
    final['total_savings_EUR'] = final['self_used_worth_EUR'] + final['revenue_from_energy_sold_EUR']

    total_day_savings = final['total_savings_EUR'].loc['2025-04-01'].sum().round(3)
    # st.write(final.loc['2025-04-01'])
    # print(f'Total savings 1.4.2025: {total_day_savings} eur')
    # print(f'Total produced 1.4.2025: {final['produced_kWh'].loc['2025-04-01'].sum().round(3)} kWh')


    # st.write(f'Total savings 1.4.2025: {total_day_savings} eur')
    # st.write(f'Total produced 1.4.2025: {final['produced_kWh'].loc['2025-04-01'].sum().round(3)} kWh')

    daily = final.resample('d').sum()
    st.write(daily)
    st.write(f'Säästö yhteensä kyseiseltä ajalta: {daily['total_savings_EUR'].sum().round(3)}')

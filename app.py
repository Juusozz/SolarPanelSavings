import pandas as pd
import streamlit as st
import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

st.title("Lasketaan aurinkopaneelien tuottama säästö")



def process_dataframe(filepath, names, skiprows, sep, formats):
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

try:
    tuotettuCSV = st.file_uploader("Valitse tuotettu energia (joko 1 tai 5 minuutin välein) .csv tiedostona (muodossa AIKALEIMA;W)", type=['csv'])
    # tuotettuCSV = './data/tuotettu.csv'
    with st.expander("Missä muodossa tiedoston täytyy olla?"):
        st.write("1. Avaa tiedosto Excelissä.")
        st.write("2. Poista kaikki sarakkeet aika ja watti -kenttien välistä")
        st.write("3. Tallenna tiedosto CSV (MS-DOS) (*.csv) muotoon")
        st.image("./format.png")
        st.write("Tiedoston pitäisi näyttää Notepadissä avattuna tältä:")
        st.image("./talta.png")
        st.write("Jos saat virheilmoituksen enkoodaamisesta, varmista, että tiedostosi on UTF-8 enkoodattu")
        st.image("./encode.png")
    porssiCSV = st.file_uploader("Valitse pörssisähkön hinnan .csv tiedosto (muodossa AIKALEIMA;hinta (c/kWh))", type=['csv'])
    # porssiCSV = './data/porssi.csv'
    myytyCSV = st.file_uploader("Valitse myydyn sähkön .csv tiedosto (muodossa AIKALEIMA;kWh)", type=['csv'])
    # myytyCSV = './data/myyty.csv'
    siirto = st.number_input("Sähkön siirto (c/kWh): ", min_value=0.0, max_value=None, step=0.01)

except UnicodeDecodeError:
    st.markdown("<span style='color: red; font-weight: bold;'>Tiedoston luku epäonnistui. Varmistathan, että tiedostosi ovat UTF-8 enkoodattuja</span>", unsafe_allow_html=True)

if st.button("Laske"):
    if tuotettuCSV is not None and porssiCSV is not None and myytyCSV is not None and siirto > 0:
        date_formats = ["%d/%m/%Y %H.%M", "%d/%m/%Y %H:%M", '%d.%m.%Y %H:%M', '%d.%m.%Y %H.%M', '%Y/%m/%d %H:%M', '%Y.%m.%d %H:%M', '%Y-%m-%d %H:%M', "%d/%m/%Y %H:%M:%S", "%d.%m.%Y %H:%M:%S", '%Y-%m-%d %H:%M:%S', "%d/%m/%Y %I:%M %p", "%d.%m.%Y %I:%M %p", '%d %m %Y %H:%M']

        df_produced = process_dataframe(tuotettuCSV, ['time', 'wats'], 3, ';', date_formats)


        hourly_energy_watts = df_produced['wats'].resample('h').sum()

        time_diff = df_produced.index.to_series().diff().dt.total_seconds().mode()[0]

        if time_diff == 60:
            hourly_totals_kwh = hourly_energy_watts / 60000
        elif time_diff == 300:
            hourly_totals_kwh = hourly_energy_watts / 12000

        df_market = process_dataframe(porssiCSV, ['time', 'c/kWh'], 1, ';', date_formats)
        df_sold = process_dataframe(myytyCSV, ['time', 'kWh'], 1, ';', date_formats)

        combined = pd.DataFrame()

        combined.index = df_sold.index
        combined['Tuotettu kWh'] = (hourly_totals_kwh).round(3)
        # combined['bought'] = (df_bought['kWh']).round(2)
        combined['Pörssisähkön hinta'] = (df_market['c/kWh']).round(3)
        combined['Myyty kWh'] = (df_sold['kWh']).round(3)
        combined.fillna(0, inplace=True)

        final = pd.DataFrame(index=combined.index)
        final['Tuotettu kWh'] = combined['Tuotettu kWh'].round(2)
        final['Itse käytetty kWh'] = combined['Tuotettu kWh'] - combined['Myyty kWh']

        final['Itse käytetyn arvo snt'] = final['Itse käytetty kWh'] * combined['Pörssisähkön hinta'] + (siirto * final['Itse käytetty kWh']) + (0.6 * final['Itse käytetty kWh'])
        final['Itse käytetyn sähkön arvo EUR'] = (final['Itse käytetyn arvo snt'] / 100).round(3)
        final['Myyty kWh'] = combined['Myyty kWh'].round(2)

        final['Tuotto myydystä sähköstä snt'] = (combined['Myyty kWh'] * combined['Pörssisähkön hinta'] - (0.36 * combined['Myyty kWh'])).round(3)
        final['Tuotto myydystä sähköstä EUR'] = (final['Tuotto myydystä sähköstä snt'] / 100.0).round(3)


        final['Säästö yhteensä EUR'] = final['Itse käytetyn sähkön arvo EUR'] + final['Tuotto myydystä sähköstä EUR']

        with st.expander("Data ennen laskelmia"):
            st.write("Tunneittain:")
            st.write(combined)
            st.write("Päivittäin:")
            paivittain = combined.resample('d').sum()
            paivittain = paivittain[paivittain['Tuotettu kWh'] > 0]
            st.write(paivittain[['Tuotettu kWh', 'Myyty kWh']])



        daily = final.resample('d').sum()
        daily = daily[daily['Tuotettu kWh'] > 0]
        st.write("Päiväkohtaiset tilastot:")

        columns_to_display = ['Tuotettu kWh', 'Itse käytetty kWh', 'Myyty kWh', 'Itse käytetyn sähkön arvo EUR', 'Tuotto myydystä sähköstä EUR', 'Säästö yhteensä EUR']
        selected_columns = daily[columns_to_display]
        st.write(selected_columns)

        st.write(f'Säästö yhteensä kyseiseltä ajalta: {daily['Säästö yhteensä EUR'].sum().round(3)} EUR')

        fig, ax = plt.subplots()

        ax.plot(daily['Säästö yhteensä EUR'], color="green")
        ax.set_title('Säästöt yhteensä EUR', fontsize=15, color='gray')
        ax.set_xlabel('Päivä', fontsize=12, color='gray')
        ax.set_ylabel('Säästöt (EUR)', fontsize=12, color='gray')
        ax.tick_params(axis='x', colors='gray')
        ax.tick_params(axis='y', colors='gray') 
        fig.patch.set_facecolor('black')
        ax.set_facecolor('black')
        ax.grid(True, which='both', color='gray', linestyle='-', linewidth=0.5)
        plt.xticks(rotation=45)
        ax.xaxis.set_major_locator(mdates.DayLocator())  # Ensure a tick for each day
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))

        st.pyplot(fig)
    else:
        st.write("Syötä ensin tarvittavat tiedot!")
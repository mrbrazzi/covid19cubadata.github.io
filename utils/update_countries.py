import csv
import json
from datetime import datetime
from pathlib import Path

import requests  # noqa We are just importing this to prove the dependency installed correctly

BASE_PATH = Path('.')


def change_date(dat):
    t = dat.split('-')
    m = t[1]
    if len(m) == 1:
        m = '0' + m
    return t[0] + '/' + m + '/' + t[2]


def get_oxford_index():
    now = datetime.now()
    indexes = requests.get(f'https://covidtrackerapi.bsg.ox.ac.uk/api/stringency/date-range/2020-1-27/{str(now.year)}-{str(now.month)}-{str(now.day)}').json()
    data = {'data': {}, 'countries': indexes['countries']}
    for day, countries in indexes['data'].items():
        data['data'][day] = {}
        for country in countries:
            print(day, country, countries[country]['stringency'])
            data['data'][day][country] = {'stringency': countries[country]['stringency'],
                                          'stringency_actual': countries[country]['stringency_actual']}
    with open(BASE_PATH / 'data' / 'oxford-indexes.json', 'w') as oxford_indexes:
        json.dump(data, oxford_indexes)
        oxford_indexes.close()
    return data


def get_json_info():
    countries = requests.get('https://pomber.github.io/covid19/timeseries.json').json()
    inf = {}
    back_inf = {}
    fecha = '2020-1-22'
    for c in countries:
        data = []
        deaths = []
        recovered = []
        started = False
        for day in countries[c]:
            if not started:
                if day['confirmed'] != 0:
                    started = True
                    data.append(day['confirmed'])
                    deaths.append(day['deaths'])
                    recovered.append(day['recovered'])
                    fecha = day["date"]
            else:
                data.append(day['confirmed'])
                deaths.append(day['deaths'])
                recovered.append(day['recovered'])
                fecha = day["date"]
        back_inf[c] = data
        inf[c] = {'confirmed': data, 'deaths': deaths, 'recovered': recovered}
    c = {"paises": back_inf, "paises_info": inf,
         "dia-actualizacion": change_date(fecha)}
    return c


def generate_csv():
    with open(BASE_PATH / 'data' / 'covid19-casos.csv', 'w') as f, \
            open(BASE_PATH / 'data' / 'covid19-cuba.json', 'r') as cuba:
        rows = [['caso', 'sexo', 'edad', 'pais', 'municipio', 'provincia',
                 'fecha_confirmacion', 'fecha_ingreso', 'tipo_contagio']]
        for day in cuba['casos']['dias'].values():
            if 'diagnosticados' not in day:
                continue
            for case in day['diagnosticados']:
                row = ['', case['sexo'], case['edad'], case['pais'], case['municipio_detección'], case['provincia_detección'], day['fecha']]
                if case['consulta_medico'] is not None:
                    row.append(case['consulta_medico'])
                else:
                    row.append('')
                if case['contagio'] == 'importado':
                    row.append('primario')
                elif case['contagio'] == 'introducido':
                    row.append('secundario')
                else:
                    row.append('desconocido')
                rows.append(row)
        w = csv.writer(f)
        w.writerows(rows)
        f.flush()
        f.close()


def main():
    indexes = get_oxford_index()
    print('Oxford Index generated')

    data = get_json_info()
    data['indexes'] = indexes
    with open(BASE_PATH / 'data' / 'paises-info-dias.json', 'w') as countries_info:
        json.dump(data, countries_info)
        countries_info.close()

    print(json.dumps(data, indent=2))

    generate_csv()
    print('CSV generated')


if __name__ == "__main__":
    main()

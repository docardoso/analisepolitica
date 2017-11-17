import sqlite3 as sql
from matplotlib import pyplot as pp

def filia(parlamentar):
    conn = sql.connect('py_politica.db')
    cursor = conn.cursor()
    res = set()

    filia = cursor.execute('''SELECT  data, sigla, uf
        FROM votacao NATURAL JOIN voto
        WHERE id_candidato = '{}' ORDER BY data'''.format(parlamentar)).fetchall()

    res.add(filia[0])

    for i, info in enumerate(filia [1:],1):
        if info[1] != filia[i-1][1]:
            res.add(filia[i+1])

    conn.close()
    return res


def N_filia(parlamentar):
    conn = sql.connect('py_politica.db')
    cursor = conn.cursor()
    count = 1


    filia = cursor.execute('''SELECT  data, sigla, uf
        FROM votacao NATURAL JOIN voto
        WHERE id_candidato = '{}' ORDER BY data, hora'''.format(parlamentar)).fetchall()


    for i, info in enumerate(filia [1:],1):
        if info[1] != filia[i-1][1]:
            count += 1

    conn.close()
    return count

def N_filia_partido(partido):
    conn = sql.connect('py_politica.db')
    cursor = conn.cursor()
    filia_parlamentar = 0

    parlamentares = cursor.execute('''SELECT DISTINCT id_candidato
        FROM voto NATURAL JOIN votacao
        WHERE sigla = '{}' '''.format(partido)).fetchall()


    for parlamentar in parlamentares:
        filia_parlamentar += N_filia(parlamentar[0])

    return filia_parlamentar

# Retorna o numero de parlamentares que foram filiados a cada partido em uma das casas durante um determinado perido de tempo
def get_bancadas(dataInicio, dataFim, casa):
    conn = sql.connect("py_politica.db")
    cursor = conn.cursor()

    bancada = dict()

    dataInicio = dataInicio.split('-')
    dataFim = dataFim.split('-')

    lista_bancada = cursor.execute('''select sigla, count(distinct voto.id_candidato) from voto
                                    join votacao join parlamentar
                                    where votacao.ano_mes_dia > "{}-{}-{}"
                                    and votacao.ano_mes_dia < "{}-{}-{}"
                                    and votacao.id_votacao=voto.id_votacao
                                    and voto.id_candidato=parlamentar.id_candidato
                                    and parlamentar.casa="{}"
                                    group by sigla'''.format(dataInicio[0], dataInicio[1], dataInicio[2], dataFim[0], dataFim[1], dataFim[2], casa)).fetchall()

    for i in lista_bancada:
        bancada[i[0]] = i[1]

    return bancada

def bar_graph(eixo_x, eixo_y):
    pp.bar(eixo_x, eixo_y)
    pp.show()

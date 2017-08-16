import sqlite3
import pickle
import requests as res

def get_info_deputados():
    dados = []
    for i in range(1,7):
        r = res.get("https://dadosabertos.camara.leg.br/api/v2/deputados?pagina={}&itens=100&ordem=ASC&ordenarPor=nome".format(i)).json()

        for deputado in r["dados"]:
            dados.append((deputado["id"], deputado["nome"], "CD"))
    return dados


def main():
    conn = sqlite3.connect("py_politica.db")
    cursor = conn.cursor()

    info = get_info_deputados()
    cursor.executemany("INSERT INTO Parlamentar VALUES (?, ?, ?)", info)    

    conn.commit()
    conn.close()

if __name__ == '__main__':
    main()
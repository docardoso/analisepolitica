from bs4 import BeautifulSoup
import requests
import sqlite3
import pickle

def get_agenda():
	datas = []

	for i in range(1,13):
		senado = requests.get('http://legis.senado.leg.br/dadosabertos/plenario/agenda/mes/2017{:02d}01'.format(i))
		xml_agenda = senado.text
		xml_agenda = BeautifulSoup(xml_agenda, "html.parser")

		for data in xml_agenda.find_all("data"):
			data = data.text
			if 'd' in data:
				continue

			datas.append(data)

	return datas

def get_votacoes(data):
	sen = set()
	part = set()
	data = "".join(data.split("-"))
	xml_votacao = requests.get('http://legis.senado.leg.br/dadosabertos/plenario/lista/votacao/{}'.format(data))
	xml_votacao = xml_votacao.text
	xml_votacao = BeautifulSoup(xml_votacao, "html.parser")

	
	for votacao in xml_votacao.find_all("votacao"):
		if votacao.find("secreta").text.strip() == 'S':
			continue

		for votos in votacao.find_all("votoparlamentar"):
			senador = votos.find("codigoparlamentar").text.strip()

			partido = votos.find('siglapartido').text.strip()
			nome = votos.find('nomeparlamentar').text.strip()
			# estado = votos.find('siglauf').text.strip()
			id_senador = (senador, nome)
	
			sen.add(id_senador)
			part.add(partido)

	return sen, part


def main():
	senadores = set()
	partidos = set()
	agenda = get_agenda()

	for data in sorted(agenda):
		s, p = get_votacoes(data)
		senadores = senadores.union(s)
		partidos = partidos.union(p)

	parlamentares = []
	for dado in senadores:
		parlamentares.append((dado[0], dado[1], "SF"))

	conn = sqlite3.connect("py_politica.db")
	cursor = conn.cursor()

	cursor.executemany("INSERT INTO parlamentar VALUES (?, ?, ?)", parlamentares)

	conn.commit()
	conn.close()

main()  
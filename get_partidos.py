from bs4 import BeautifulSoup
import requests as res
import pickle
import sqlite3

conn = sqlite3.connect('py_politica.db')
cursor = conn.cursor()


def get_agenda():

	datas = []
  
	for i in range(1,13):
		senado = res.get('http://legis.senado.leg.br/dadosabertos/plenario/agenda/mes/2017{:02d}01'.format(i))
		xml_agenda = senado.text
		xml_agenda = BeautifulSoup(xml_agenda, "html.parser")
  
		for data in xml_agenda.find_all("data"):
			
			data = data.text
			 
			if 'd' in data:
				continue
  
			datas.append(data)
  
	return datas

def insere_partido (data,partidos): 


	xml_votacao = res.get('http://legis.senado.leg.br/dadosabertos/plenario/lista/votacao/{}'.format(data))
	xml_votacao = xml_votacao.text
	xml_votacao = BeautifulSoup(xml_votacao, "html.parser")

	for votacao in xml_votacao.find_all("votacao"):

		if votacao.find("secreta").text.strip() == 'S':
			continue

			for votos in votacao.find_all("votoparlamentar"):

				partido = votos.find('siglapartido').text.strip()
				UF = votos.find('siglauf').text.strip()

				cursor.execute("""INSERT INTO partido (sigla, uf) Values (?,?)""", (partido,UF)) 


	r = res.get ("http://www.camara.leg.br/SitCamaraWS/Deputados.asmx/ObterDeputados")
	xml = BeautifulSoup(r.text,"html.parser")

	for deputado in xml.find_all("deputado"): 

		partido = deputado.find("partido").text.strip()
		UF = deputado.find("uf").text.strip()

		try:

			cursor.execute("""INSERT INTO partido (sigla, uf) Values (?,?)""",(partido,UF))

		except sqlite3.IntegrityError:

			continue

  
def main(): 

	agenda = get_agenda()
	partidos = []
	partidos_camara = []

	for data in sorted(agenda):

		data = data.replace('-',"")
		insere_partido(data, partidos)
			
	conn.commit()
	conn.close()

main()


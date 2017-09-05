from bs4 import BeautifulSoup
import requests
import sqlite3


def get_proposicoes_camara ():
	ano = 2017
	dados_propostas = [] 
	ListaProps = requests.get("http://www.camara.leg.br/SitCamaraWS/Proposicoes.asmx/ListarProposicoesVotadasEmPlenario?ano={}&tipo=".format(ano))
	ListaProps = ListaProps.text # XML aonde estão as informações
	ListaProps = BeautifulSoup(ListaProps, "html.parser")

	for info in ListaProps.find_all("proposicoes"):
		for proposicao in info.find_all("proposicao"):
			for dados in proposicao.find_all("nomeproposicao"):
				if "=>" in dados.text: # Verifica se houve uma mudança na proposta (Ex: PL que virou PEC) e pega o nome mais recente
					dados = dados.text.split(">")
					dados = dados[1].split()

				else:
					dados = dados.text.split()
 
				tipo = dados[0]
				numero, ano = dados[1].split("/")
				proposta = [numero, tipo, ano]
				if proposta in dados_propostas:
					continue
				else:
					dados_propostas.append([numero, tipo, ano]) 

			

	return dados_propostas


def get_agenda_senado():
	datas = []

	for i in range(1,13):
		senado = requests.get('http://legis.senado.leg.br/dadosabertos/plenario/agenda/mes/2017{:02d}01'.format(i))
		senado = senado.text
		senado = BeautifulSoup(senado, "html.parser")

		for data in senado.find_all("data"):
			data = data.text
			if 'd' in data:
				continue

			datas.append(data)

	return datas
	

def get_votos_camara(propostas): 	   
	votos = set()

	for proposta in propostas:
		votacoesLista = requests.get("http://www.camara.leg.br/SitCamaraWS/Proposicoes.asmx/ObterVotacaoProposicao?tipo={}&numero={}&ano={}".format(proposta[1], proposta[0], proposta[2]))
		votacoesLista = BeautifulSoup(votacoesLista.text, "html.parser")

		for votacao in votacoesLista.find_all("votacao"): 
			if votacao["data"].split("/")[2] == "2017":
				for voto in votacao.find_all("deputado"):
					if voto['idecadastro'] == '':
						continue

					if voto['voto'] == 'Sim':
						votos.add((voto["idecadastro"], votacao['codsessao'], 1))

					elif voto['voto'] == 'Não':
						votos.add((voto["idecadastro"], votacao['codsessao'], -1))

					else:
						votos.add((voto["idecadastro"], votacao['codsessao'], 0))
				
	return votos


def get_votos_senado(data):
	voto_senadores = set()
	data = data.replace("-","")
	xml_votacao = requests.get('http://legis.senado.leg.br/dadosabertos/plenario/lista/votacao/{}'.format(data))
	xml_votacao = xml_votacao.text
	xml_votacao = BeautifulSoup(xml_votacao, "html.parser")

	
	for votacao in xml_votacao.find_all("votacao"):
		if votacao.find("secreta").text.strip() == 'S':
			continue

		cod_sessao = votacao.find('codigosessaovotacao').text
		for votos in votacao.find_all("votoparlamentar"):
			senador = votos.find("codigoparlamentar").text.strip()
			if votos.find('voto').text.strip() == 'Sim':
				voto_senadores.add((senador, cod_sessao, 1))

			elif votos.find('voto').text.strip() == 'Não':
				voto_senadores.add((senador, cod_sessao, -1))

			else:
				voto_senadores.add((senador, cod_sessao, 0))

	return voto_senadores


def main():
	conn = sqlite3.connect("py_politica.db")
	cursor = conn.cursor()
	votos = set()

	agenda = get_agenda_senado()
	proposicoes = get_proposicoes_camara()

	voto_deputados = get_votos_camara(proposicoes)
	votos = votos.union(voto_deputados)

	for data in sorted(agenda):
		voto_senadores = get_votos_senado(data)
		votos = votos.union(voto_senadores)

	for voto in votos:
		cursor.execute('SELECT id FROM parlamentar WHERE id_API = {}'.format(voto[0]))
		cursor.execute("INSERT INTO voto(id_candidato, id_votacao, descricao) VALUES ({}, {}, {})".format(int(cursor.fetchone()[0]), voto[1], voto[2]))

	conn.commit()
	conn.close()

if __name__ == '__main__':
	main()
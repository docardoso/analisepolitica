import sqlite3 as sql

con = sql.connect('py_politica.db')
cursor = con.cursor()

cursor.execute('''
CREATE TABLE parlamentar( 
		id_candidato varchar primary key,
		nome varchar(50) not null,
		casa char(2) not null);''')

cursor.execute('''
CREATE TABLE proposicao( 
		id_proposicao varchar primary key,
		tipo varchar(10) not null,
		numero integer not null,
		ano integer not null,
		ementa varchar not null);''')

cursor.execute('''
CREATE TABLE votacao( 
		id_votacao varchar primary key,
		id_proposicao varchar not null,
		dataHoraInicio datetime not null,
		foreign key(id_proposicao) references proposicao(id_proposicao));''')

cursor.execute('''
CREATE TABLE votacao_secreta( 
		id_votacao varchar not null,
		placarSim integer not null,
		placarNao integer not null,
		placarAbs integer not null,
		primary key(id_votacao),
		foreign key(id_votacao) references votacao(id_votacao));''')

cursor.execute('''
CREATE TABLE voto( 
		id_candidato varchar not null,
		id_votacao varchar not null,
		sigla varchar not null,
		uf char(2) not null,
		descricao integer not null,
		primary key(id_candidato, id_votacao),
		foreign key (id_votacao) references votacao(id_votacao),
		foreign key (id_candidato) references parlamentar(id_candidato));''')

con.commit()
con.close()
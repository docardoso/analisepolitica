import sqlite3 as sql

con = sql.connect('py_politica.db')
cursor = con.cursor()

cursor.execute('''
CREATE TABLE parlamentar( 
		id_candidato varchar primary key,
		nome varchar(50) not null,
		casa char(2) not null);''')

cursor.execute('''
CREATE TABLE materia( 
		id_materia varchar primary key,
		tipo varchar null,
		autor varchar null,
		numero integer null,
		data_apresentacao date null,
		ementa varchar null,
		temas varchar null,
		apelido varchar null,
		status varchar null);''')

cursor.execute('''
CREATE TABLE votacao( 
		id_votacao varchar primary key,
		id_materia varchar null,
		dataHoraInicio datetime not null,
		foreign key(id_materia) references materia(id_materia));''')

cursor.execute('''
CREATE TABLE votacao_secreta( 
		id_votacao varchar not null,
		placarSim integer null,
		placarNao integer null,
		placarAbs integer null,
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
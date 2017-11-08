import sqlite3 as sql

con = sql.connect('py_politica.db')
cursor = con.cursor()

cursor.execute('''
CREATE TABLE parlamentar( 
		id_candidato integer primary key AUTOINCREMENT,
		id_API integer not null,
		nome varchar(50) not null,
		casa char(2) not null);''')

cursor.execute('''
CREATE TABLE votacao( 
		id_votacao integer primary key AUTOINCREMENT,
		id_API varchar not null,
		tipo varchar(10) not null,
		ano_mes_dia date not null);''')

cursor.execute('''
CREATE TABLE voto( 
		id_candidato integer not null,
		id_votacao varchar not null,
		sigla varchar not null,
		uf char(2) not null,
		descricao integer not null,
		primary key(id_candidato, id_votacao),
		foreign key (id_votacao) references votacao(id),
		foreign key (id_candidato) references parlamentar(id));''')

con.commit()
con.close()
BEGIN TRANSACTION;
CREATE TABLE books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                isbn TEXT,
                price REAL,
                etag TEXT
            );
INSERT INTO "books" VALUES(1,'Clean Code','Robert C. Martin','111',29.99,'10aa0c8af1bfcd65aa33cb95269133ec');
INSERT INTO "books" VALUES(2,'Clean Architecture','Robert C. Martin','222',34.99,'a15e7dadd0b58864451ca573487a3d36');
INSERT INTO "books" VALUES(3,'The Pragmatic Programmer','Andrew Hunt','333',39.99,'00c9eefa2f1ff85038a3b861dbc8419b');
INSERT INTO "books" VALUES(4,'1984','George Orwell','444',19.99,'31e3b5897ad5c8f2834a61c1ec8d6ad8');
INSERT INTO "books" VALUES(5,'Animal Farm','George Orwell','555',14.99,'eaf8c43fbb5633d1755848fdc362cea3');
INSERT INTO "books" VALUES(6,'Design Patterns','Erich Gamma','666',45.0,'24c24366e460cafc5a8a63edf61ad7f5');
INSERT INTO "books" VALUES(7,'Refactoring','Martin Fowler','777',40.0,'5643aa52c1a402c94e05c2b8da1ad56c');
INSERT INTO "books" VALUES(8,'Domain-Driven Design','Eric Evans','888',50.0,'9559073f488ed7908ea695b6e443967c');
INSERT INTO "books" VALUES(9,'Introduction to Algorithms','Thomas H. Cormen','999',60.0,'9d032d638c6ea381fa5898f25831a364');
INSERT INTO "books" VALUES(10,'Code Complete','Steve McConnell','101',35.0,'332798aef48749ad3740ac32b6d313c5');
INSERT INTO "books" VALUES(11,'The Mythical Man-Month','Frederick P. Brooks Jr.','102',25.0,'eb7d07cca659d7b735d9ce8e91aa42f8');
INSERT INTO "books" VALUES(12,'Head First Design Patterns','Eric Freeman','103',45.0,'b8b6849181552184cf999091a1f9f6d1');
INSERT INTO "books" VALUES(13,'Python Crash Course','Eric Matthes','104',30.0,'ffa111a9fdc03d82eceac776ba3fc9c0');
INSERT INTO "books" VALUES(14,'Fluent Python','Luciano Ramalho','105',42.0,'352d434021acb78309108c4035b0d7ad');
INSERT INTO "books" VALUES(15,'Grokking Algorithms','Aditya Bhargava','106',38.0,'379c500f3cadfc22ee10752d7b8a9afb');
INSERT INTO "books" VALUES(16,'Clean Agile','Robert C. Martin','107',28.0,'78992f60eca6a97f066022e4c38c1e81');
INSERT INTO "books" VALUES(17,'Structure and Interpretation of Computer Programs','Harold Abelson','108',55.0,'3ff3779d9e5052d99cf32dcea730ff3e');
INSERT INTO "books" VALUES(18,'Computer Systems: A Programmer''s Perspective','Randal E. Bryant','109',70.0,'d8ca5292fc9b39c7c12779b60a3e5598');
INSERT INTO "books" VALUES(19,'Operating System Concepts','Abraham Silberschatz','110',65.0,'233ee89a173bd8604a5862dbc05abc04');
INSERT INTO "books" VALUES(20,'Compilers: Principles, Techniques, and Tools','Alfred V. Aho','111',68.0,'cbd426e68de0108079859e951bd2be1b');
INSERT INTO "books" VALUES(21,'Homage to Catalonia','George Orwell','112',15.99,'b8edc6fe83f8eaa50730111aca4ae49d');
INSERT INTO "books" VALUES(22,'Down and Out in Paris and London','George Orwell','113',12.99,'96de18eeeb6873be479b425a9e84a86f');
INSERT INTO "books" VALUES(23,'Effective Java','Joshua Bloch','114',45.0,'2f82ba9edee8b0b455e21cf2bec3661c');
INSERT INTO "books" VALUES(24,'Java Concurrency in Practice','Brian Goetz','115',35.0,'f82bdac089403648705cbc98cdf88359');
INSERT INTO "books" VALUES(25,'Spring in Action','Craig Walls','116',40.0,'c2b3c1333fda66dceccdbc44679f7ce4');
DELETE FROM "sqlite_sequence";
INSERT INTO "sqlite_sequence" VALUES('books',25);
COMMIT;

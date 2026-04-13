-- Таблица пользователей
CREATE TABLE IF NOT EXISTS users (
    userID SERIAL PRIMARY KEY,
    fio VARCHAR(150) NOT NULL,
    phone VARCHAR(15) NOT NULL,
    login VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(100) NOT NULL,
    type VARCHAR(50) NOT NULL CHECK (type IN ('Менеджер', 'Мастер', 'Оператор', 'Заказчик'))
);

-- Таблица заявок
CREATE TABLE IF NOT EXISTS repair_requests (
    requestID SERIAL PRIMARY KEY,
    startDate DATE NOT NULL,
    homeTechType VARCHAR(100) NOT NULL,
    homeTechModel VARCHAR(150) NOT NULL,
    problemDescryption TEXT NOT NULL,
    requestStatus VARCHAR(50) NOT NULL CHECK (requestStatus IN ('Новая заявка', 'В процессе ремонта', 'Готова к выдаче', 'Ожидание запчастей')),
    completionDate DATE,
    repairParts TEXT,
    masterID INTEGER REFERENCES users(userID) ON DELETE SET NULL,
    clientID INTEGER NOT NULL REFERENCES users(userID) ON DELETE CASCADE
);

-- Таблица комментариев
CREATE TABLE IF NOT EXISTS comments (
    commentID SERIAL PRIMARY KEY,
    message TEXT NOT NULL,
    masterID INTEGER NOT NULL REFERENCES users(userID) ON DELETE CASCADE,
    requestID INTEGER NOT NULL REFERENCES repair_requests(requestID) ON DELETE CASCADE
);

-- Вставка данных (с экранированием русских букв через доллар-кавычки)
INSERT INTO users (userID, fio, phone, login, password, type) VALUES
(1, $$Трубин Никита Юрьевич$$, '89210563128', 'kasoo', 'root', 'Менеджер'),
(2, $$Мурашов Андрей Юрьевич$$, '89535078985', 'murashov123', 'qwerty', 'Мастер'),
(3, $$Степанов Андрей Викторович$$, '89210673849', 'test1', 'test1', 'Мастер'),
(4, $$Перина Анастасия Денисовна$$, '89990563748', 'perinaAD', '250519', 'Оператор'),
(5, $$Мажитова Ксения Сергеевна$$, '89994563847', 'krutiha1234567', '1234567890', 'Оператор'),
(6, $$Семенова Ясмина Марковна$$, '89994563847', 'login1', 'pass1', 'Мастер'),
(7, $$Баранова Эмилия Марковна$$, '89994563841', 'login2', 'pass2', 'Заказчик'),
(8, $$Егорова Алиса Платоновна$$, '89994563842', 'login3', 'pass3', 'Заказчик'),
(9, $$Титов Максим Иванович$$, '89994563843', 'login4', 'pass4', 'Заказчик'),
(10, $$Иванов Марк Максимович$$, '89994563844', 'login5', 'pass5', 'Мастер');

INSERT INTO repair_requests (requestID, startDate, homeTechType, homeTechModel, problemDescryption, requestStatus, completionDate, repairParts, masterID, clientID) VALUES
(1, '2023-06-06', $$Фен$$, $$Ладомир ТА112 белый$$, $$Перестал работать$$, 'В процессе ремонта', NULL, NULL, 2, 7),
(2, '2023-05-05', $$Тостер$$, $$Redmond RT-437 черный$$, $$Перестал работать$$, 'В процессе ремонта', NULL, NULL, 3, 7),
(3, '2022-07-07', $$Холодильник$$, $$Indesit DS 316 W белый$$, $$Не морозит одна из камер холодильника$$, 'Готова к выдаче', '2023-01-01', NULL, 2, 8),
(4, '2023-08-02', $$Стиральная машина$$, $$DEXP WM-F610NTMA/WW белый$$, $$Перестали работать многие режимы стирки$$, 'Новая заявка', NULL, NULL, NULL, 8),
(5, '2023-08-02', $$Мультиварка$$, $$Redmond RMC-M95 черный$$, $$Перестала включаться$$, 'Новая заявка', NULL, NULL, NULL, 9),
(6, '2023-08-02', $$Фен$$, $$Ладомир ТА113 чёрный$$, $$Перестал работать$$, 'Готова к выдаче', '2023-08-03', NULL, 2, 7),
(7, '2023-07-09', $$Холодильник$$, $$Indesit DS 314 W серый$$, $$Гудит, но не замораживает$$, 'Готова к выдаче', '2023-08-03', $$Мотор обдува морозильной камеры холодильника$$, 2, 8);

INSERT INTO comments (commentID, message, masterID, requestID) VALUES
(1, $$Интересная поломка$$, 2, 1),
(2, $$Очень странно, будем разбираться!$$, 3, 2),
(3, $$Скорее всего потребуется мотор обдува!$$, 2, 7),
(4, $$Интересная поломка$$, 2, 1),
(5, $$Очень странно, будем разбираться!$$, 3, 6);

-- Проверка
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM repair_requests;
SELECT COUNT(*) FROM comments;
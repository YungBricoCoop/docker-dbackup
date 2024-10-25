CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL
);

CREATE TABLE products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    price DECIMAL(10, 2) NOT NULL
);

CREATE TABLE orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    order_date DATE NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);

INSERT INTO users (username, email) VALUES
('alice', 'alice@example.com'),
('bob', 'bob@example.com'),
('charlie', 'charlie@example.com'),
('david', 'david@example.com'),
('eva', 'eva@example.com'),
('frank', 'frank@example.com'),
('grace', 'grace@example.com'),
('henry', 'henry@example.com'),
('irene', 'irene@example.com'),
('john', 'john@example.com');

INSERT INTO products (name, price) VALUES
('Laptop', 999.99),
('Smartphone', 599.99),
('Tablet', 299.99),
('Headphones', 89.99),
('Smartwatch', 199.99),
('Camera', 449.99),
('Printer', 149.99),
('Monitor', 249.99),
('Keyboard', 49.99),
('Mouse', 29.99);

INSERT INTO orders (user_id, product_id, quantity, order_date) VALUES
(1, 2, 1, '2024-10-15'),
(2, 3, 2, '2024-10-16'),
(3, 1, 1, '2024-10-17'),
(4, 5, 1, '2024-10-18'),
(5, 4, 2, '2024-10-19'),
(6, 6, 1, '2024-10-20'),
(7, 7, 3, '2024-10-21'),
(8, 8, 1, '2024-10-22'),
(9, 9, 2, '2024-10-23'),
(10, 10, 1, '2024-10-24');
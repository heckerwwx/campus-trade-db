import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'campus_trade.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    cursor.executescript('''
        DROP TABLE IF EXISTS orders;
        DROP TABLE IF EXISTS item;
        DROP TABLE IF EXISTS user;
        DROP VIEW IF EXISTS sold_items_view;
        DROP VIEW IF EXISTS unsold_items_view;

        CREATE TABLE user (
            user_id   TEXT PRIMARY KEY,
            user_name TEXT NOT NULL,
            phone     TEXT NOT NULL
        );

        CREATE TABLE item (
            item_id    TEXT PRIMARY KEY,
            item_name  TEXT NOT NULL,
            category   TEXT NOT NULL,
            price      REAL NOT NULL CHECK(price > 0),
            status     INTEGER NOT NULL DEFAULT 0 CHECK(status IN (0, 1)),
            seller_id  TEXT NOT NULL,
            list_date  TEXT NOT NULL,
            FOREIGN KEY (seller_id) REFERENCES user(user_id)
        );

        CREATE TABLE orders (
            order_id     TEXT PRIMARY KEY,
            item_id      TEXT NOT NULL UNIQUE,
            buyer_id     TEXT NOT NULL,
            order_date   TEXT NOT NULL,
            FOREIGN KEY (item_id) REFERENCES item(item_id),
            FOREIGN KEY (buyer_id) REFERENCES user(user_id)
        );

        INSERT INTO user (user_id, user_name, phone) VALUES
            ('u001', 'ZhangSan', '13800000001'),
            ('u002', 'LiSi',     '13800000002'),
            ('u003', 'WangWu',   '13800000003'),
            ('u004', 'ZhaoLiu',  '13800000004');

        INSERT INTO item (item_id, item_name, category, price, status, seller_id, list_date) VALUES
            ('i001', 'CalculusBook',    'Book',        20, 0, 'u001', '2024-03-15'),
            ('i002', 'DeskLamp',        'DailyGoods',  35, 1, 'u002', '2024-03-20'),
            ('i003', 'Microcontroller', 'Electronics', 80, 0, 'u001', '2024-04-01'),
            ('i004', 'Chair',           'Furniture',   50, 1, 'u003', '2024-04-05'),
            ('i005', 'WaterBottle',     'DailyGoods',  15, 0, 'u004', '2024-04-10');

        INSERT INTO orders (order_id, item_id, buyer_id, order_date) VALUES
            ('0001', 'i002', 'u001', '2024-05-01'),
            ('0002', 'i004', 'u002', '2024-05-03');

        CREATE VIEW sold_items_view AS
            SELECT i.item_id, i.item_name, i.category, i.price, o.buyer_id, o.order_date
            FROM item i JOIN orders o ON i.item_id = o.item_id
            WHERE i.status = 1;

        CREATE VIEW unsold_items_view AS
            SELECT item_id, item_name, category, price, seller_id, list_date
            FROM item
            WHERE status = 0;
    ''')

    conn.commit()
    conn.close()
    print("Database initialized successfully.")

if __name__ == '__main__':
    init_db()

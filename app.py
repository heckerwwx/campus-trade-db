import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from db import get_db, init_db

app = Flask(__name__)
app.secret_key = 'campus_trade_secret'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/users')
def users():
    conn = get_db()
    rows = conn.execute('SELECT * FROM user').fetchall()
    conn.close()
    return render_template('users.html', users=rows)

@app.route('/user/add', methods=['GET', 'POST'])
def user_add():
    if request.method == 'POST':
        user_id = request.form['user_id']
        user_name = request.form['user_name']
        phone = request.form['phone']
        conn = get_db()
        try:
            conn.execute(
                'INSERT INTO user (user_id, user_name, phone) VALUES (?, ?, ?)',
                (user_id, user_name, phone)
            )
            conn.commit()
            flash('用户注册成功！', 'success')
        except Exception as e:
            conn.rollback()
            flash(f'注册失败：{e}', 'error')
        finally:
            conn.close()
        return redirect(url_for('users'))
    return render_template('user_add.html')

@app.route('/items')
def items():
    conn = get_db()
    rows = conn.execute('''
        SELECT i.*, u.user_name AS seller_name
        FROM item i LEFT JOIN user u ON i.seller_id = u.user_id
        ORDER BY i.item_id
    ''').fetchall()
    conn.close()
    return render_template('items.html', items=rows)

@app.route('/user/delete/<user_id>', methods=['POST'])
def user_delete(user_id):
    conn = get_db()
    try:
        conn.execute('DELETE FROM user WHERE user_id = ?', (user_id,))
        conn.commit()
        flash('用户删除成功！', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'删除失败：{e}', 'error')
    finally:
        conn.close()
    return redirect(url_for('users'))

@app.route('/orders')
def orders():
    conn = get_db()
    rows = conn.execute('''
        SELECT o.*, i.item_name, u.user_name AS buyer_name
        FROM orders o
        LEFT JOIN item i ON o.item_id = i.item_id
        LEFT JOIN user u ON o.buyer_id = u.user_id
        ORDER BY o.order_id
    ''').fetchall()
    conn.close()
    return render_template('orders.html', orders=rows)

@app.route('/item/add', methods=['GET', 'POST'])
def item_add():
    if request.method == 'POST':
        item_id = request.form['item_id']
        item_name = request.form['item_name']
        category = request.form['category']
        price = float(request.form['price'])
        seller_id = request.form['seller_id']
        conn = get_db()
        try:
            from datetime import date
            today = date.today().isoformat()
            conn.execute(
                'INSERT INTO item (item_id, item_name, category, price, status, seller_id, list_date) VALUES (?, ?, ?, ?, 0, ?, ?)',
                (item_id, item_name, category, price, seller_id, today)
            )
            conn.commit()
            flash('商品添加成功！', 'success')
        except Exception as e:
            conn.rollback()
            flash(f'添加失败：{e}', 'error')
        finally:
            conn.close()
        return redirect(url_for('items'))
    conn = get_db()
    users = conn.execute('SELECT * FROM user').fetchall()
    conn.close()
    return render_template('item_add.html', users=users)

@app.route('/item/edit_price/<item_id>', methods=['GET', 'POST'])
def item_edit_price(item_id):
    conn = get_db()
    if request.method == 'POST':
        new_price = float(request.form['price'])
        try:
            conn.execute('UPDATE item SET price = ? WHERE item_id = ?', (new_price, item_id))
            conn.commit()
            flash('价格修改成功！', 'success')
        except Exception as e:
            conn.rollback()
            flash(f'修改失败：{e}', 'error')
        finally:
            conn.close()
        return redirect(url_for('items'))
    item = conn.execute('SELECT * FROM item WHERE item_id = ?', (item_id,)).fetchone()
    conn.close()
    return render_template('item_edit_price.html', item=item)

@app.route('/item/delete/<item_id>', methods=['POST'])
def item_delete(item_id):
    conn = get_db()
    try:
        item = conn.execute('SELECT * FROM item WHERE item_id = ?', (item_id,)).fetchone()
        if item and item['status'] == 0:
            conn.execute('DELETE FROM item WHERE item_id = ? AND status = 0', (item_id,))
            conn.commit()
            flash('商品删除成功！', 'success')
        else:
            flash('只能删除未售出的商品！', 'error')
    except Exception as e:
        conn.rollback()
        flash(f'删除失败：{e}', 'error')
    finally:
        conn.close()
    return redirect(url_for('items'))

@app.route('/purchase/<item_id>', methods=['GET', 'POST'])
def purchase(item_id):
    conn = get_db()
    if request.method == 'POST':
        buyer_id = request.form['buyer_id']
        try:
            item = conn.execute('SELECT * FROM item WHERE item_id = ?', (item_id,)).fetchone()
            if not item:
                flash('商品不存在！', 'error')
            elif item['status'] == 1:
                flash('该商品已售出，无法购买！', 'error')
            else:
                max_order = conn.execute('SELECT MAX(order_id) AS max_id FROM orders').fetchone()
                new_id = str(int(max_order['max_id'] or '0') + 1).zfill(4)
                from datetime import date
                today = date.today().isoformat()
                conn.execute(
                    'INSERT INTO orders (order_id, item_id, buyer_id, order_date) VALUES (?, ?, ?, ?)',
                    (new_id, item_id, buyer_id, today)
                )
                conn.execute('UPDATE item SET status = 1 WHERE item_id = ?', (item_id,))
                conn.commit()
                flash('购买成功！', 'success')
        except Exception as e:
            conn.rollback()
            flash(f'购买失败：{e}', 'error')
        finally:
            conn.close()
        return redirect(url_for('items'))
    item = conn.execute('SELECT * FROM item WHERE item_id = ?', (item_id,)).fetchone()
    users = conn.execute('SELECT * FROM user').fetchall()
    conn.close()
    return render_template('purchase.html', item=item, users=users)

@app.route('/query')
def query_index():
    return render_template('query.html')

@app.route('/query/unsold')
def query_unsold():
    conn = get_db()
    rows = conn.execute('SELECT * FROM item WHERE status = 0').fetchall()
    conn.close()
    return render_template('query_result.html', title='未售出商品', rows=rows,
                           columns=['item_id', 'item_name', 'category', 'price', 'status', 'seller_id'])

@app.route('/query/price_gt_30')
def query_price_gt_30():
    conn = get_db()
    rows = conn.execute('SELECT * FROM item WHERE price > 30').fetchall()
    conn.close()
    return render_template('query_result.html', title='价格大于30的商品', rows=rows,
                           columns=['item_id', 'item_name', 'category', 'price', 'status', 'seller_id'])

@app.route('/query/daily_goods')
def query_daily_goods():
    conn = get_db()
    rows = conn.execute("SELECT * FROM item WHERE category = 'DailyGoods'").fetchall()
    conn.close()
    return render_template('query_result.html', title='生活用品类商品', rows=rows,
                           columns=['item_id', 'item_name', 'category', 'price', 'status', 'seller_id'])

@app.route('/query/seller_u001')
def query_seller_u001():
    conn = get_db()
    rows = conn.execute("SELECT * FROM item WHERE seller_id = 'u001'").fetchall()
    conn.close()
    return render_template('query_result.html', title='u001发布的所有商品', rows=rows,
                           columns=['item_id', 'item_name', 'category', 'price', 'status', 'seller_id'])

@app.route('/query/join_sold_with_buyer')
def query_join_sold_with_buyer():
    conn = get_db()
    rows = conn.execute('''
        SELECT i.item_id, i.item_name, i.category, i.price, u.user_name AS buyer_name
        FROM item i
        JOIN orders o ON i.item_id = o.item_id
        JOIN user u ON o.buyer_id = u.user_id
        WHERE i.status = 1
    ''').fetchall()
    conn.close()
    return render_template('query_result.html', title='已售商品及买家姓名', rows=rows,
                           columns=['item_id', 'item_name', 'category', 'price', 'buyer_name'])

@app.route('/query/join_order_detail')
def query_join_order_detail():
    conn = get_db()
    rows = conn.execute('''
        SELECT o.order_id, i.item_name, u.user_name AS buyer_name, o.order_date
        FROM orders o
        JOIN item i ON o.item_id = i.item_id
        JOIN user u ON o.buyer_id = u.user_id
    ''').fetchall()
    conn.close()
    return render_template('query_result.html', title='订单详情（商品名+买家名+日期）', rows=rows,
                           columns=['order_id', 'item_name', 'buyer_name', 'order_date'])

@app.route('/query/join_u001_purchased')
def query_join_u001_purchased():
    conn = get_db()
    rows = conn.execute('''
        SELECT i.item_id, i.item_name, i.status,
               CASE WHEN o.order_id IS NOT NULL THEN '已购买' ELSE '未购买' END AS purchase_status
        FROM item i
        LEFT JOIN orders o ON i.item_id = o.item_id
        WHERE i.seller_id = 'u001'
    ''').fetchall()
    conn.close()
    return render_template('query_result.html', title='卖家u001的商品是否被购买', rows=rows,
                           columns=['item_id', 'item_name', 'status', 'purchase_status'])

@app.route('/aggregate')
def aggregate_index():
    conn = get_db()
    total = conn.execute('SELECT COUNT(*) AS cnt FROM item').fetchone()['cnt']
    by_category = conn.execute('SELECT category, COUNT(*) AS cnt FROM item GROUP BY category').fetchall()
    avg_price = conn.execute('SELECT AVG(price) AS avg_price FROM item').fetchone()['avg_price']
    top_seller = conn.execute('''
        SELECT u.user_id, u.user_name, COUNT(*) AS cnt
        FROM item i JOIN user u ON i.seller_id = u.user_id
        GROUP BY i.seller_id
        ORDER BY cnt DESC
        LIMIT 1
    ''').fetchone()
    conn.close()
    return render_template('aggregate.html', total=total, by_category=by_category,
                           avg_price=round(avg_price, 2) if avg_price else 0, top_seller=top_seller)

@app.route('/views')
def views_index():
    conn = get_db()
    sold = conn.execute('SELECT * FROM sold_items_view').fetchall()
    unsold = conn.execute('SELECT * FROM unsold_items_view').fetchall()
    conn.close()
    return render_template('views.html', sold=sold, unsold=unsold)

@app.route('/security')
def security():
    return render_template('security.html')

if __name__ == '__main__':
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'campus_trade.db')
    if not os.path.exists(db_path):
        init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)

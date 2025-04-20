import json
from flask import Flask, render_template_string, request, redirect

def format_order_for_printing(order_id, order, total):
    """Converte l'ordine in un formato leggibile per la stampa."""
    lines = []
    lines.append(f"Ordine n. {order_id}")
    lines.append("-" * 30)
    for item, qty in order.items():
        lines.append(f"{item} x{qty} - €{MENU[item] * qty:.2f}")
    lines.append("-" * 30)
    lines.append(f"Totale: €{total:.2f}")
    lines.append("\nGrazie per il tuo ordine!")
    return "\n".join(lines)

app = Flask(__name__)

MENU = {
    'HUBurger': 10.00,
    'Bacon Cheese': 10.00,
    'Piadina farcita': 5.00,
    'Patate Fritte': 3.00,
    'Acqua 0.5L': 1.00,
    'Coca-Cola': 3.00,
    'Birra': 4.00,
    'Spritz': 5.00,
    'Gin Lennon': 5.00,
    'Gin Tonic': 5.00
}

order_counter = 1  # Inizializza il contatore degli ordini
ORDERS_FILE = "orders.json"  # Nome del file JSON per salvare gli ordini

def save_order_to_file(order_id, order, total):
    """Salva l'ordine in un file JSON."""
    try:
        with open(ORDERS_FILE, "r") as file:
            orders = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        orders = []

    orders.append({
        "order_id": order_id,
        "order": order,
        "total": total
    })

    with open(ORDERS_FILE, "w") as file:
        json.dump(orders, file, indent=4)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>CL-HUB Menu</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f8f8f8;
            margin: 0;
            padding: 0;
            display: flex;
            flex-direction: column;
            height: 100vh;
        }
        .main-container {
            display: flex;
            flex: 1;
        }
        .menu-container, .order-summary-container {
            flex: 1;
            background-color: #fff;
            padding: 1.5em;
            border-radius: 8px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            overflow-y: auto;
            max-height: 100vh;
        }
        .header {
            text-align: center;
            margin-bottom: 2em;
        }
        .header img {
            max-height: 100px;
            margin-bottom: 0.5em;
        }
        .header h1 {
            margin: 0;
            font-size: 1.8em;
            color: #00293B;
        }
        h2, h3 {
            text-align: center;
            color: #006080;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 1em;
        }
        th, td {
            text-align: center;
            padding: 0.5em;
            border-bottom: 1px solid #ccc;
        }
        .quantity-control {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5em;
        }
        .quantity-control button {
            background-color: #006080;
            color: white;
            border: none;
            border-radius: 8px;
            width: 40px;
            height: 30px;
            font-size: 1em;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .quantity-control button:hover {
            background-color: #009DB8;
        }
        .quantity-control span {
            font-size: 1.2em;
            font-weight: bold;
            min-width: 30px;
            text-align: center;
            color: #00293B;
        }
        button {
            background-color: #006080;
            color: white;
            padding: 0.5em 1em;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 1em;
            margin: 0.5em;
        }
        button:hover {
            background-color: #009DB8;
        }
        .order-summary ul {
            list-style: none;
            padding: 0;
        }
        .order-summary li {
            padding: 0.3em 0;
            color: #00293B;
        }
        .order-summary h3 {
            color: #006080;
        }
        .footer {
            text-align: left;
            padding: 1em;
            background-color: #f0f0f0;
            color: #333;
            font-size: 0.9em;
            border-top: 1px solid #ccc;
        }
    </style>
    <script>
        const menu = {{ menu|tojson }};
        const order = {};

        function increaseQuantity(item) {
            const quantitySpan = document.getElementById(`quantity-${item}`);
            const inputField = document.getElementById(`input-${item}`);
            const summaryList = document.getElementById('order-summary-list');
            const totalElement = document.getElementById('order-total');

            let currentQuantity = parseInt(quantitySpan.textContent);
            currentQuantity++;
            quantitySpan.textContent = currentQuantity;
            inputField.value = currentQuantity;
            order[item] = currentQuantity;
            updateOrderSummary(summaryList, totalElement);
        }

        function decreaseQuantity(item) {
            const quantitySpan = document.getElementById(`quantity-${item}`);
            const inputField = document.getElementById(`input-${item}`);
            const summaryList = document.getElementById('order-summary-list');
            const totalElement = document.getElementById('order-total');

            let currentQuantity = parseInt(quantitySpan.textContent);
            if (currentQuantity > 0) {
                currentQuantity--;
                quantitySpan.textContent = currentQuantity;
                inputField.value = currentQuantity;
                if (currentQuantity > 0) {
                    order[item] = currentQuantity;
                } else {
                    delete order[item];
                }
                updateOrderSummary(summaryList, totalElement);
            }
        }

        function updateOrderSummary(summaryList, totalElement) {
            summaryList.innerHTML = '';
            let total = 0;
            for (const [key, qty] of Object.entries(order)) {
                const price = menu[key];
                total += price * qty;
                const listItem = document.createElement('li');
                listItem.textContent = `${key} x${qty} - €${(price * qty).toFixed(2)}`;
                summaryList.appendChild(listItem);
            }
            totalElement.textContent = `Totale: €${total.toFixed(2)}`;
        }

        function showConfirmation(orderId) {
            if (Object.keys(order).length === 0) {
                alert("Nessuna selezione effettuata. Aggiungi almeno un elemento all'ordine.");
                return false;
            }
            alert(`Ordine n. ${orderId} confermato, invio alla stampante`);
            return true;
        }
    </script>
</head>
<body>
    <div class="main-container">
        <div class="menu-container">
            <div class="header">
                <h1>CL-Hub Festa del Sangiovese</h1>
            </div>
            <form method="post" onsubmit="return showConfirmation({{ order_id }})">
                <table>
                    <tr>
                        <th>Elemento</th>
                        <th>Prezzo</th>
                        <th>Quantità</th>
                    </tr>
                    {% for item, price in menu.items() %}
                    <tr>
                        <td>{{ item }}</td>
                        <td>€{{ '%.2f' % price }}</td>
                        <td>
                            <div class="quantity-control">
                                <button type="button" onclick="decreaseQuantity('{{ item }}')">-</button>
                                <span id="quantity-{{ item }}">0</span>
                                <button type="button" onclick="increaseQuantity('{{ item }}')">+</button>
                            </div>
                            <input type="hidden" name="{{ item }}" id="input-{{ item }}" value="0">
                        </td>
                    </tr>
                    {% endfor %}
                </table>
                <div style="text-align: center;">
                    <button type="submit">Conferma</button>
                </div>
            </form>
        </div>
        <div class="order-summary-container">
            <div class="order-summary">
                <h2>Riepilogo Ordine</h2>
                <ul id="order-summary-list">
                    {% for item, qty in order.items() %}
                        <li>{{ item }} x{{ qty }} - €{{ '%.2f' % (menu[item] * qty) }}</li>
                    {% endfor %}
                </ul>
                <h3 id="order-total">Totale: €{{ '%.2f' % total }}</h3>
            </div>
        </div>
    </div>
    <div class="footer">
        <button onclick="window.location.href='/reset'">Azzera</button>
        <p style="font-size: 0.9em; color: #666; margin-top: 1em;">&copy; 2025 CL-Hub. Tutti i diritti riservati.</p>
    </div>
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def index():
    global order_counter
    order = {}
    total = 0.0
    display_order_id = order_counter

    if request.method == 'POST':
        temp_order = {}
        temp_total = 0.0

        if request.is_json:
            data = request.get_json()
            temp_order = data.get('order', {})
            temp_total = data.get('total', 0.0)
        else:
            for item in MENU:
                qty_str = request.form.get(item, '0')
                try:
                    qty = int(qty_str)
                    if qty > 0:
                        temp_order[item] = qty
                        temp_total += MENU[item] * qty
                except ValueError:
                    continue

        if temp_order:
            order_id = order_counter
            display_order_id = order_id
            order_counter += 1
            order = temp_order
            total = temp_total
            save_order_to_file(order_id, order, total)
            formatted_order = format_order_for_printing(order_id, order, total)
            print({"status": "debug", "formatted_order": formatted_order})
            order = {}
            total = 0.0

    return render_template_string(
        HTML_TEMPLATE,
        menu=MENU,
        order=order,
        total=total,
        order_id=display_order_id
    )

@app.route('/reset')
def reset_counter():
    global order_counter
    order_counter = 1
    return redirect('/')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))  # Usa la porta specificata da Render o 5000 come fallback
    app.run(host='0.0.0.0', port=port, debug=True)

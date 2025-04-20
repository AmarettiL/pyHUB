import json
from flask import Flask, render_template_string, request, redirect
from escpos.printer import Usb
from PIL import Image
import os

def crop_image(image_path, output_path):
    """Ritaglia i margini bianchi dall'immagine."""
    img = Image.open(image_path)
    img = img.convert("RGB")  # Assicurati che l'immagine sia in RGB
    bbox = img.getbbox()  # Ottieni i bordi non vuoti
    cropped_img = img.crop(bbox)  # Ritaglia l'immagine
    cropped_img.save(output_path)  # Salva l'immagine ritagliata

def send_to_printer(order_id, formatted_order):
    try:
        # Configura la stampante USB
        printer = Usb(0x0483, 0x5743)  # Sostituisci con il Vendor ID e Product ID

        # Stampa il logo
        logo_path = "static/BIANCO_cropped.png"
        img = Image.open(logo_path)
        printer.image(img)

        # Stampa la sezione del cibo
        printer.set(align='center', bold=True)
        printer.text(f"Ordine n. {order_id}\n")
        printer.set(align='left', bold=False)
        printer.text("CIBO:\n")
        printer.text(formatted_order['food'])
        printer.text("\n" * 3)  # Spazio prima del taglio
        printer.cut()
    
        # Stampa la sezione delle bevande
        printer.set(align='center', bold=True)
        printer.text(f"Ordine n. {order_id}\n")
        printer.set(align='left', bold=False)
        printer.text("BEVANDE:\n")
        printer.text(formatted_order['drink'])
        printer.text("\n" * 3)  # Spazio prima del taglio
        printer.cut()

        # Stampa lo scontrino di cortesia
        printer.set(align='center', bold=True, double_height=True, double_width=True)
        printer.text(f"Ordine n. {order_id}\n")
        printer.set(align='left', bold=False, double_height=False, double_width=False)
        printer.text("Scontrino di cortesia:\n")
        printer.text(formatted_order['courtesy'])
        printer.text("\n" * 3)  # Spazio prima del taglio
        printer.cut()

        print("Ordine inviato alla stampante con successo.")
    except Exception as e:
        print(f"Errore durante l'invio alla stampante: {e}")

def format_order_for_printing(order_id, order):
    """Converte l'ordine in un formato leggibile per la stampa."""
    food_lines = []
    drink_lines = []
    courtesy_lines = []

    # Separa cibo e bevande
    for item, qty in order.items():
        if item in FOOD:
            food_lines.append(f"{item} x{qty} - EUR {FOOD[item] * qty:.2f}")
        elif item in DRINK:
            drink_lines.append(f"{item} x{qty} - EUR {DRINK[item] * qty:.2f}")

    # Scontrino di cortesia (senza prezzi)
    courtesy_lines.append("-" * 30)
    courtesy_lines.append(f"Ordine n. {order_id}")
    courtesy_lines.append("-" * 30)
    for item, qty in order.items():
        courtesy_lines.append(f"{item} x{qty}")
    courtesy_lines.append("-" * 30)

    # Formatta le sezioni
    formatted_order = {
        'food': "\n".join(food_lines) + f"\nTotale Cibo: EUR {sum(FOOD[item] * qty for item, qty in order.items() if item in FOOD):.2f}\n",
        'drink': "\n".join(drink_lines) + f"\nTotale Bevande: EUR {sum(DRINK[item] * qty for item, qty in order.items() if item in DRINK):.2f}\n",
        'courtesy': "\n".join(courtesy_lines)
    }

    return formatted_order

app = Flask(__name__)

FOOD = {
    'HUBurger': 10.00,
    'Bacon Cheese': 10.00,
    'Piadina farcita': 5.00,
    'Patate Fritte': 3.00,
}

DRINK = {
    'Acqua 0.5L': 1.00,
    'Coca-Cola': 3.00,
    'Birra': 4.00,
    'Drink': 5.00
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
            for item in {**FOOD, **DRINK}:  # Unisci FOOD e DRINK
                qty_str = request.form.get(item, '0')
                try:
                    qty = int(qty_str)
                    if qty > 0:
                        temp_order[item] = qty
                        temp_total += (FOOD.get(item, 0) + DRINK.get(item, 0)) * qty
                except ValueError:
                    continue

        if temp_order:
            order_id = order_counter
            display_order_id = order_id
            order_counter += 1
            order = temp_order
            total = temp_total
            save_order_to_file(order_id, order, total)
            formatted_order = format_order_for_printing(order_id, order)
            print({"status": "debug", "formatted_order": formatted_order})

            # Invia l'ordine alla stampante USB
            send_to_printer(order_id, formatted_order)
            order = {}
            total = 0.0

    return render_template_string(
        HTML_TEMPLATE,
        menu={**FOOD, **DRINK},  # Unisci FOOD e DRINK per il menu
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

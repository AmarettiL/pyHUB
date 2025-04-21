import json
from flask import Flask, render_template_string, request, redirect
from escpos.printer import Usb
import os
from datetime import datetime

printFood = False
printDrink = False
ORDERS_FILE = os.path.join(os.path.dirname(__file__), "orders.json")


def send_to_printer_debug(order_id, formatted_order):
    """Simula l'invio alla stampante stampando nel log."""
    try:
        output = []

        # Simula la stampa della sezione del cibo, se presente
        if printFood:
            output.append(f"Ordine n. {order_id}")
            output.append("CIBO:")
            output.append(formatted_order['food'])
            output.append("-" * 30)

        # Simula la stampa della sezione delle bevande, se presente
        if printDrink:
            output.append(f"Ordine n. {order_id}")
            output.append("BEVANDE:")
            output.append(formatted_order['drink'])
            output.append("-" * 30)

        # Simula la stampa dello scontrino di cortesia
        if printFood or printDrink:
            output.append(f"Ordine n. {order_id}")
            output.append("Scontrino di cortesia:")
            output.append(formatted_order['courtesy'])
            output.append("-" * 30)

        # Stampa il risultato nel log
        print("\n".join(output))
        print("Simulazione completata: Ordine inviato al log con successo.")
    except Exception as e:
        print(f"Errore durante la simulazione della stampa: {e}")

def send_to_printer(order_id, formatted_order):
  try:
    # Configura la stampante USB
    printer = Usb(0x0483, 0x5743)

    # Stampa la sezione del cibo, se presente
    if printFood:
      printer.set(align='center', bold=True)
      printer.text(f"Ordine n. {order_id}\n")
      printer.set(align='left', bold=False)
      printer.text("CIBO:\n")
      printer.text(formatted_order['food'])
      printer.text("\n" * 3)  # Spazio prima del taglio
      printer.cut()

    # Stampa la sezione delle bevande, se presente
    if printDrink:
      printer.set(align='center', bold=True)
      printer.text(f"Ordine n. {order_id}\n")
      printer.set(align='left', bold=False)
      printer.text("BEVANDE:\n")
      printer.text(formatted_order['drink'])
      printer.text("\n" * 3)  # Spazio prima del taglio
      printer.cut()

    # Stampa lo scontrino di cortesia
    if printFood or printDrink:  # Stampa solo se c'è cibo o bevande
      # Stampa il logo
      logo_path = os.path.join(os.path.dirname(__file__), "static/LOGO.png")
      if os.path.exists(logo_path):
        printer.set(align='center')  # Centra il logo
        printer.image(logo_path)
        printer.text("\n")  # Aggiungi una riga vuota dopo il logo

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
  global printFood, printDrink  # Usa le variabili globali
  printFood = False
  printDrink = False

  food_lines = []
  drink_lines = []
  courtesy_lines = []

  # Separa cibo e bevande
  for item, qty in order.items():
    if item in FOOD:
      printFood = True
      food_lines.append(f"{item} x{qty}")  # Rimuovi i prezzi
    elif item in DRINK:
      printDrink = True
      drink_lines.append(f"{item} x{qty}")  # Rimuovi i prezzi

  # Scontrino di cortesia (con prezzi e totale)
  courtesy_lines.append("-" * 30)
  courtesy_lines.append(f"Ordine n. {order_id}")
  courtesy_lines.append("-" * 30)
  total_food = 0.0
  total_drink = 0.0
  for item, qty in order.items():
    if item in FOOD:
      courtesy_lines.append(f"{item} x{qty} - EUR {FOOD[item] * qty:.2f}")
      total_food += FOOD[item] * qty
    elif item in DRINK:
      courtesy_lines.append(f"{item} x{qty} - EUR {DRINK[item] * qty:.2f}")
      total_drink += DRINK[item] * qty
  courtesy_lines.append("-" * 30)
  courtesy_lines.append(f"Totale: EUR {total_food + total_drink:.2f}")
  courtesy_lines.append("-" * 30)

  # Formatta le sezioni
  formatted_order = {
    'food': "\n".join(food_lines),  # Rimuovi i totali
    'drink': "\n".join(drink_lines),  # Rimuovi i totali
    'courtesy': "\n".join(courtesy_lines)  # Aggiungi i totali
  }

  return formatted_order

app = Flask(__name__)

FOOD = {
  'HUB-Burger': 10.00,
  'Bacon Cheese': 10.00,
  'Chicken Burger': 10.00,
  'Veggie Burger': 10.00,
  'Piadina farcita': 5.00,
  'Piadina': 3.00,
  'Patate Fritte': 3.00,
  'Jalapenos': 3.00,
  'Olive': 3.00,
  'Speedy pollo': 3.00
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
      // Mostra un pop-up di conferma con due opzioni: Conferma o Annulla
      const userChoice = confirm(`Ordine n. ${orderId} confermato. Vuoi procedere con l'invio alla stampante?`);
      if (userChoice) {
        // L'utente ha scelto di confermare
        return true;
      } else {
        // L'utente ha scelto di annullare
        alert("Ordine annullato. Puoi modificarlo.");
        return false;
      }
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
        <form method="post" action="/">
          <button type="submit">Conferma</button>
        </form>
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
    <form method="post" action="/reset" style="display: inline;">
      <button type="submit">Azzera</button>
    </form>
    <p style="font-size: 0.9em; color: #666; margin-top: 1em;">&copy; 2025 CL-Hub. Tutti i diritti riservati.</p>
  </div>
</body>
</html>
'''

def render_menu(order=None, total=0.0):
  global order_counter
  return render_template_string(
    HTML_TEMPLATE,
    menu={**FOOD, **DRINK},  # Unisci FOOD e DRINK per il menu
    order=order or {},
    total=total,
    order_id=order_counter
  )

@app.route('/', methods=['GET'])
def index_get():
  return render_menu()

@app.route('/', methods=['POST'])
def index_post():
  global order_counter
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
    order_counter += 1
    save_order_to_file(order_id, temp_order, temp_total)
    formatted_order = format_order_for_printing(order_id, temp_order)
    print({"status": "debug", "formatted_order": formatted_order})

    # Invia l'ordine alla stampante USB
    send_to_printer(order_id, formatted_order)
    # send_to_printer_debug(order_id, formatted_order)

  # Reindirizza alla homepage dopo aver elaborato l'ordine
  return redirect('/')

@app.before_request
def log_request():
    print(f"Request endpoint: {request.endpoint}, Method: {request.method}, URL: {request.url}")

@app.route('/reset', methods=['POST'])
def reset_counter():
    global order_counter
    order_counter = 1
    print(f"Percorso del file ORDERS_FILE: {ORDERS_FILE}")
    print(f"Esiste il file ORDERS_FILE? {os.path.exists(ORDERS_FILE)}")
    # Salva una copia del file JSON con un timestamp
    if os.path.exists(ORDERS_FILE):
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = f"orders_{timestamp}.json"
            os.rename(ORDERS_FILE, backup_file)
            print(f"Backup creato: {backup_file}")
        except Exception as e:
            print(f"Errore durante il salvataggio del backup: {e}")
    else:
        print("Nessun file di ordini trovato da salvare come backup.")

    # Ripulisci il file JSON degli ordini
    try:
        with open(ORDERS_FILE, "w") as file:
            json.dump([], file)
            print("Ordini ripuliti con successo.")
    except Exception as e:
        print(f"Errore durante la pulizia degli ordini: {e}")

    return redirect('/')

if __name__ == '__main__':
  port = int(os.environ.get('PORT', 10000))  # Usa la porta specificata da Render o 5000 come fallback
  app.run(host='0.0.0.0', port=port, debug=True)

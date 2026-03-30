from http.server import HTTPServer, SimpleHTTPRequestHandler
import socket
import os
import json
from datetime import datetime
from urllib.parse import parse_qs, urlparse


class CustomHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests"""
        # Parse the URL to check for form submission
        parsed_url = urlparse(self.path)
        
        # Check if this is a form submission from reserva.html
        if parsed_url.path == '/reserva.html' and parsed_url.query:
            self.handle_reservation(parsed_url.query)
            return
        
        # Redirect root to index.html
        if self.path == '/':
            self.path = '/index.html'
        
        # Serve the requested file
        super().do_GET()

    def handle_reservation(self, query_string):
        """Handle reservation form submission"""
        # Parse the form data
        form_data = parse_qs(query_string)
        
        # Create orders folder if it doesn't exist
        if not os.path.exists('orders'):
            os.makedirs('orders')
            print("\n✓ Created 'orders' folder")
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"orders/order_{timestamp}.txt"
        
        # Prepare order summary
        order_summary = self.format_order(form_data)
        
        # Save to file
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(order_summary)
            print(f"\n✓ New order saved: {filename}")
        except Exception as e:
            print(f"\n✗ Error saving order: {e}")
        
        # Send confirmation page
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        confirmation_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Reserva Confirmada - Nova Arcadia</title>
            <meta charset="UTF-8">
            <link rel="stylesheet" href="https://www.w3schools.com/w3css/5/w3.css">
            <style>
                body {{ font-family: "Montserrat", sans-serif; }}
                .confirmation-box {{
                    max-width: 800px;
                    margin: 50px auto;
                    padding: 30px;
                    background: #f0f8ff;
                    border: 3px solid #2196F3;
                    border-radius: 10px;
                }}
                .success-icon {{
                    text-align: center;
                    font-size: 72px;
                    color: #4CAF50;
                }}
                pre {{
                    background: white;
                    padding: 15px;
                    border-radius: 5px;
                    border: 1px solid #ddd;
                    white-space: pre-wrap;
                }}
            </style>
        </head>
        <body>
            <div class="confirmation-box">
                <div class="success-icon">✓</div>
                <h1 style="text-align: center; color: #2196F3;">Reserva Confirmada!</h1>
                <p style="text-align: center; font-size: 18px;">
                    Obrigado pela sua reserva. Entraremos em contacto em breve.
                </p>
                <h3>Resumo da Sua Reserva:</h3>
                <pre>{order_summary}</pre>
                <div style="text-align: center; margin-top: 30px;">
                    <a href="index.html" class="w3-button w3-blue w3-large">Voltar à Página Principal</a>
                </div>
            </div>
        </body>
        </html>
        """
        self.wfile.write(confirmation_html.encode('utf-8'))

    def format_order(self, form_data):
        """Format order data into readable text"""
        lines = []
        lines.append("=" * 50)
        lines.append("NOVA ARCADIA - RESERVA DE T-SHIRTS")
        lines.append("=" * 50)
        lines.append(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        lines.append("")
        
        # Product prices
        precos = {
            'gustave': 39.99,
            'lune': 19.99,
            'maelle': 49.99,
            'sciel': 29.99
        }
        
        # Products ordered
        lines.append("PRODUTOS ENCOMENDADOS:")
        lines.append("-" * 50)
        total = 0
        
        products = ['gustave', 'lune', 'maelle', 'sciel']
        product_names = {
            'gustave': 'Gustave | Clair Obscur: Expedition 33',
            'lune': 'Lune | Clair Obscur: Expedition 33',
            'maelle': 'Maelle | Clair Obscur: Expedition 33',
            'sciel': 'Sciel | Clair Obscur: Expedition 33'
        }
        
        for product in products:
            qty_key = f'{product}_qty'
            if qty_key in form_data:
                qty = int(form_data[qty_key][0])
                if qty > 0:
                    # Get selected sizes
                    sizes = []
                    for size in ['s', 'm', 'l', 'xl']:
                        size_key = f'{product}_{size}'
                        if size_key in form_data:
                            sizes.append(size.upper())
                    
                    subtotal = qty * precos[product]
                    total += subtotal
                    
                    lines.append(f"{product_names[product]}")
                    lines.append(f"  Quantidade: {qty}")
                    lines.append(f"  Tamanhos: {', '.join(sizes) if sizes else 'Não especificado'}")
                    lines.append(f"  Preço unitário: {precos[product]:.2f}€")
                    lines.append(f"  Subtotal: {subtotal:.2f}€")
                    lines.append("")
        
        lines.append("-" * 50)
        lines.append(f"TOTAL: {total:.2f}€")
        lines.append("")
        
        # Contact information
        lines.append("DADOS DE CONTACTO:")
        lines.append("-" * 50)
        
        if 'nome' in form_data:
            lines.append(f"Nome: {form_data['nome'][0]}")
        if 'email' in form_data:
            lines.append(f"Email: {form_data['email'][0]}")
        if 'telefone' in form_data:
            lines.append(f"Telefone: {form_data['telefone'][0]}")
        if 'morada' in form_data:
            lines.append(f"Morada: {form_data['morada'][0]}")
        
        if 'observacoes' in form_data and form_data['observacoes'][0]:
            lines.append("")
            lines.append("OBSERVAÇÕES:")
            lines.append(form_data['observacoes'][0])
        
        lines.append("")
        lines.append("=" * 50)
        
        return "\n".join(lines)

    def do_POST(self):
        """Handle POST requests"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)

        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        response = f"Received POST data: {post_data.decode()}"
        self.wfile.write(response.encode())


def get_local_ip():
    """Get the local IP address"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "127.0.0.1"


def run_server(port=80):
    """Run the HTTP server"""
    # Bind to 0.0.0.0 to accept connections from any network interface
    server_address = ('0.0.0.0', port)
    httpd = HTTPServer(server_address, CustomHandler)

    local_ip = get_local_ip()

    print(f"Server starting on port {port}...")
    print(f"\nLocal access:")
    print(f"  http://localhost:{port}/index.html")
    print(f"  http://127.0.0.1:{port}/index.html")
    print(f"\nLocal network access:")
    print(f"  http://{local_ip}:{port}/index.html")
    print(f"\nFor custom domain access (http://nova-arcadia.com/index.html):")
    print(f"  1. Add this line to your hosts file:")
    print(f"     Windows: C:\\Windows\\System32\\drivers\\etc\\hosts")
    print(f"     Linux/Mac: /etc/hosts")
    print(f"     Add: {local_ip} nova-arcadia.com")
    print(f"  2. Other devices on your network should add the same line")
    print(f"  3. Access via: http://nova-arcadia.com/index.html")
    print(f"\nFor external access (from outside your network):")
    print(f"  1. Forward port {port} in your router settings")
    print(f"  2. Find your public IP at https://whatismyip.com")
    print(f"  3. Configure DNS or hosts file to point nova-arcadia.com to your public IP")
    print(f"\nMake sure index.html, reserva.html, and the images folder are in the same directory as this script!")
    print(f"\nOrders will be saved to the 'orders' folder")
    print(f"\nPress Ctrl+C to stop the server\n")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        httpd.shutdown()


if __name__ == '__main__':
    # Check if running with appropriate permissions for port 80
    try:
        run_server(port=80)
    except PermissionError:
        print("Port 80 requires administrator/root privileges.")
        print("Running on port 8000 instead...\n")
        run_server(port=8000)
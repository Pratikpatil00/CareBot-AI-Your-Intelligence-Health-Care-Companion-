import os
from backend.app import create_app
from waitress import serve

if __name__ == '__main__':
    app = create_app()
    port = int(os.getenv('PORT','5000'))
    print(f'CareBot frontend and API: http://localhost:{port}',flush=True)
    serve(app,host=os.getenv('HOST','127.0.0.1'),port=port,threads=8,max_request_body_size=10*1024*1024)

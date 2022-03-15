from waitress import serve
import main

# Serve the app using WSGI server
serve(main.app, host='0.0.0.0', port=8080)
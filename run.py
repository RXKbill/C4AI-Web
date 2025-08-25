import os
from dotenv import load_dotenv
from app import create_app, db
from app.models import User, RolePermission

# 加载环境变量
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

app = create_app(os.getenv('FLASK_CONFIG') or 'default')

@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, RolePermission=RolePermission)

if __name__ == '__main__':
    print("Starting Flask application...")
    print(f"Static folder: {app.static_folder}")
    print(f"Template folder: {app.template_folder}")
    print("Available routes:")
    for rule in app.url_map.iter_rules():
        print(f"  {rule.rule} -> {rule.endpoint}")
    print("\nServer will be available at: http://localhost:5000")
    app.run(host='0.0.0.0', port=8080, debug=True)
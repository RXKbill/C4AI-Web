import os
from flask import Flask, send_from_directory, render_template_string, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from config import config

db = SQLAlchemy()
jwt = JWTManager()

def create_app(config_name='default'):
    # 获取项目根目录
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # 调试信息
    print(f"Project root: {project_root}")
    print(f"Static folder path: {os.path.join(project_root, 'static')}")
    print(f"Template folder path: {os.path.join(project_root, 'templates')}")
    print(f"HTML folder path: {os.path.join(project_root, 'html')}")
    
    app = Flask(__name__, 
                static_folder=os.path.join(project_root, 'static'),
                template_folder=os.path.join(project_root, 'templates'))
    app.config.from_object(config[config_name])
    
    # 初始化扩展
    db.init_app(app)
    jwt.init_app(app)
    CORS(app)
    
    # 注册蓝图
    from .api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # 添加静态文件路由
    @app.route('/static/<path:filename>')
    def static_files(filename):
        return send_from_directory(app.static_folder, filename)
    
    # 提供 templates 目录下的静态模板文件（供前端直接加载片段）
    @app.route('/templates/<path:filename>')
    def template_files(filename):
        template_dir = os.path.join(project_root, 'templates')
        file_path = os.path.join(template_dir, filename)
        if os.path.exists(file_path):
            return send_file(file_path)
        else:
            html_folder = os.path.join(project_root, 'html')
            return send_file(os.path.join(html_folder, 'app-page_404.html'))
    
    # 添加前端页面路由
    @app.route('/')
    def index():
        html_folder = os.path.join(project_root, 'html')
        index_path = os.path.join(html_folder, 'app-auth-login.html')
        print(f"Serving index from: {index_path}")
        if os.path.exists(index_path):
            return send_file(index_path)
        else:
            return send_file(os.path.join(html_folder, 'app-page_404.html'))
    
    @app.route('/<path:page>')
    def serve_page(page):
        html_folder = os.path.join(project_root, 'html')
        
        # 处理各种前端页面
        if page.endswith('.html'):
            file_path = os.path.join(html_folder, page)
            if os.path.exists(file_path):
                return send_file(file_path)
            else:
                return send_file(os.path.join(html_folder, 'app-page_404.html'))
        elif not '.' in page:  # 没有扩展名的页面
            html_file = f'app-{page}.html'
            html_path = os.path.join(html_folder, html_file)
            if os.path.exists(html_path):
                return send_file(html_path)
            else:
                # 如果找不到对应的HTML文件，返回主页
                index_path = os.path.join(html_folder, 'app-index.html')
                if os.path.exists(index_path):
                    return send_file(index_path)
                else:
                    return send_file(os.path.join(html_folder, 'app-page_404.html'))
        else:
            # 尝试直接提供文件
            file_path = os.path.join(html_folder, page)
            if os.path.exists(file_path):
                return send_file(file_path)
            else:
                return send_file(os.path.join(html_folder, 'app-page_404.html'))
    
    return app 
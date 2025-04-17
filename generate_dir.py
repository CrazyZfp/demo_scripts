import os

# 你的目录结构定义
directory_structure = """
lottery/
├── app.py
├── config/
│   └── config.yaml
├── trading/
│   └── order_manager.py
├── binance/
│   ├── binance_ws.py
│   └── binance_rest.py
├── risk_control/
│   └── limiter.py
├── records/
│   └── trade_logger.py
├── strategy/
│   └── strategy_hook.py
├── templates/
│   ├── index.html
│   ├── config.html
│   └── records.html
├── static/
│   └── style.css
└── requirements.txt
"""

def parse_structure(structure_text):
    lines = structure_text.strip().split('\n')
    path_stack = []
    result_paths = []

    for i, line in enumerate(lines):
        if not line.strip():
            continue

        # 清除前缀符号
        stripped = line.lstrip('│├└─ ')
        indent_level = (len(line) - len(line.lstrip(' │'))) // 4

        # 更新路径栈
        if indent_level >= len(path_stack):
            path_stack.append(stripped)
        else:
            path_stack = path_stack[:indent_level]
            path_stack.append(stripped)

        # 如果是第一行，则设置为根目录
        if i == 0:
            root_dir = stripped.rstrip('/')  # 去掉结尾的斜杠
            continue  # 根目录不计入 result_paths

        # 加入路径列表
        rel_path = os.path.join(*path_stack)
        result_paths.append(rel_path)

    return root_dir, result_paths

def create_structure(root_dir, paths):
    for path in paths:
        full_path = os.path.join(root_dir, path)

        if '.' in os.path.basename(path):  # 文件
            dir_name = os.path.dirname(full_path)
            if dir_name:
                os.makedirs(dir_name, exist_ok=True)
            with open(full_path, 'w', encoding='utf-8') as f:
                pass
        else:  # 文件夹
            os.makedirs(full_path, exist_ok=True)

if __name__ == "__main__":
    root_dir, paths = parse_structure(directory_structure)
    create_structure(root_dir, paths)
    print(f"已在 ./{root_dir} 下生成完整目录结构。")

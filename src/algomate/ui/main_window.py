from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QStatusBar
from PyQt5.QtCore import Qt, QSettings

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = QSettings('Algomate', 'Algomate')
        self.init_ui()
        self.load_window_state()
    
    def init_ui(self):
        self.setWindowTitle('算法学习助手')
        
        # 主布局
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        
        # 左侧导航栏
        self.navigation = QWidget()
        nav_layout = QVBoxLayout(self.navigation)
        nav_layout.setAlignment(Qt.AlignTop)
        
        # 导航按钮
        self.nav_buttons = {
            '首页': QPushButton('首页'),
            '笔记': QPushButton('笔记'),
            '练习': QPushButton('练习'),
            '进度': QPushButton('进度'),
            '设置': QPushButton('设置')
        }
        
        for name, button in self.nav_buttons.items():
            button.setMinimumHeight(40)
            button.setStyleSheet('QPushButton { text-align: left; padding-left: 20px; }')
            nav_layout.addWidget(button)
        
        # 内容区域
        self.content_area = QWidget()
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_label = QLabel('请选择左侧导航项')
        self.content_label.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(self.content_label)
        
        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage('就绪')
        
        # 组装布局
        main_layout.addWidget(self.navigation, 1)
        main_layout.addWidget(self.content_area, 4)
        
        self.setCentralWidget(main_widget)
        
        # 连接信号
        for name, button in self.nav_buttons.items():
            button.clicked.connect(lambda checked, name=name: self.switch_content(name))
    
    def switch_content(self, page_name):
        # 清空内容区域
        while self.content_layout.count() > 0:
            widget = self.content_layout.takeAt(0).widget()
            if widget:
                widget.deleteLater()
        
        # 创建新的内容
        content_label = QLabel(f'当前页面: {page_name}')
        content_label.setAlignment(Qt.AlignCenter)
        self.content_layout.addWidget(content_label)
        
        # 更新状态栏
        self.status_bar.showMessage(f'已切换到{page_name}页面')
    
    def load_window_state(self):
        # 加载窗口大小和位置
        if self.settings.contains('window/geometry'):
            self.restoreGeometry(self.settings.value('window/geometry'))
        else:
            self.setGeometry(100, 100, 800, 600)
    
    def save_window_state(self):
        # 保存窗口大小和位置
        self.settings.setValue('window/geometry', self.saveGeometry())
    
    def closeEvent(self, event):
        # 关闭时保存窗口状态
        self.save_window_state()
        event.accept()

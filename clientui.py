import socket 
import re
import json
import hashlib
import threading
import time
import sys
import base64

from PyQt5.QtWidgets import QGridLayout, QFrame, QSizePolicy, QFileDialog, QInputDialog, QDialog,QDialogButtonBox, QComboBox, QHeaderView, QTableWidgetItem, QTableWidget, QLineEdit, QStackedWidget, QLabel, QHBoxLayout, QVBoxLayout, QWidget, QMessageBox, QApplication, QPushButton, QTabWidget, QTextEdit
from PyQt5.QtCore import QMetaObject, Qt, Q_ARG, pyqtSlot, QSize
from PyQt5.QtGui import QIcon, QPixmap

'''when a user adds a product, it gets added to his self.products_for_sale, when a user buys their product the serer should send the seller the quantity bought '''


class ClientWindow(QWidget):

    def __init__(self):
        super().__init__()
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.bind(("0.0.0.0", 0))
        self.receive_thread = threading.Thread(target=self.receive_thread_func, daemon=True)
        self.points = 0
        self.all_products = []
        self.products_for_sale = []
        self.bought_products = []
        self.sold_products = []
        self.username = None
        self.active_peers = {}
        self.peer_to_widget = {}
        self.following = {}
        self.image_path = None
        self.preffered_currency = "USD"
        self.preffered_currency_multiplier = 1
        self.sent_add_req = False
        
        
        try:
           self.client_socket.connect(("localhost", 1235))
        except ConnectionRefusedError:
           QMessageBox.critical(self, "Connection Failed", "The server is unavailable. Please try again later.")
           sys.exit()
           
        self.receive_thread.start()  # Start the receiving thread after initializing the window
        self.msg_count = 0
        self.p2p_reply_recieved = threading.Event()
        self.p2p_req_reply_recieved = threading.Event()
        self.target_ip = ''
        self.target_port = ''
        self.initialize_UI()
        
    def initialize_UI(self):
        self.setWindowTitle("AUBoutique")
        self.setGeometry(0, 40, 1920, 980)
        self.setStyleSheet("background-color: white;")

        # Create the main layout and a stacked widget
        self.main_layout = QVBoxLayout(self)
        self.stacked_widget = QStackedWidget()
        
        # Create and add the login page to the stacked widget
        self.log_page = self.create_log_page()
        self.stacked_widget.addWidget(self.log_page)

        # Create and add the registration page to the stacked widget
        self.reg_page = self.create_registration_page()
        self.stacked_widget.addWidget(self.reg_page)

        # Create the dashboard page,shown after login
        self.dashboard_page = self.create_dashboard_page()
        self.stacked_widget.addWidget(self.dashboard_page)

        # Set the stacked widget as the main layout widget
        self.main_layout.addWidget(self.stacked_widget)

    # def create_log_reg_page(self):
    #     log_reg_page = QWidget()
    #     log_reg_page_layout = QVBoxLayout()

    #     welcome = QLabel(" Welcome to AUBoutique - Login or Register")
    #     welcome.setStyleSheet("font-size: 56px; font-weight: bold;padding-bottom: 50px;")
    #     welcome.setAlignment(Qt.AlignHCenter)
    #     spacer = QSpacerItem(0, 10, QSizePolicy.Minimum, QSizePolicy.Expanding)
    #     log_reg_page_layout.addItem(spacer)
    #     log_reg_page_layout.addWidget(welcome)

    #     spacer = QSpacerItem(0, 10, QSizePolicy.Minimum, QSizePolicy.Expanding)
    #     log_reg_page_layout.addItem(spacer)
        
    #     log_button = QPushButton("Login", clicked = lambda:self.stacked_widget.setCurrentWidget(self.log_page))
    #     log_button.setStyleSheet("""
    #         QPushButton {background-color: #4CAF50; color: white; font-size: 18px; padding: 10px 20px; border: none; border-radius: 5px;}
    #         QPushButton:hover { background-color: #45a049;}
    #         QPushButton:pressed {background-color: #387a36;}
    #     """)
    #     log_button.setFixedSize(400, 50)

    #     reg_button = QPushButton("Register", clicked = lambda: self.stacked_widget.setCurrentWidget(self.reg_page))
    #     reg_button.setStyleSheet("""
    #         QPushButton {background-color: #4CAF50; color: white; font-size: 18px; padding: 10px 20px; border: none; border-radius: 5px;}
    #         QPushButton:hover { background-color: #45a049;}
    #         QPushButton:pressed {background-color: #387a36;}
    #     """)
    #     reg_button.setFixedSize(400, 50)

    #     container = QWidget()
    #     con_layout = QVBoxLayout(container)
        
    #     con_layout.addWidget(log_button)
    #     con_layout.setAlignment(log_button, Qt.AlignHCenter)
    #     con_layout.addWidget(reg_button)
    #     con_layout.setAlignment(reg_button, Qt.AlignHCenter)
    #     con_layout.addStretch()
        
        
        
    #     log_reg_page_layout.addWidget(container)
    #     spacer = QSpacerItem(0, 10, QSizePolicy.Minimum, QSizePolicy.Expanding)
    #     log_reg_page_layout.addItem(spacer)


    #     log_reg_page.setLayout(log_reg_page_layout)
        
    #     return log_reg_page

    def create_registration_page(self):
        reg_page = QWidget()
        reg_layout = QVBoxLayout()
        reg_layout.addStretch()
    
        welcome = QLabel(" Welcome to AUBoutique - Register")
        welcome.setStyleSheet("font-size: 56px; font-weight: bold; padding-bottom: 50px;")
        welcome.setAlignment(Qt.AlignCenter)
        reg_layout.addWidget(welcome)
        
        reg_form = QWidget()
        reg_form_layout = QVBoxLayout()
        
        (name_layout, self.name_reg_input) = self.create_text_input_box("Name: ", "John Doe", password=False)
        reg_form_layout.addLayout(name_layout)
        
        (mail_layout, self.mail_reg_input) = self.create_text_input_box("Email: ", "example@mail.aub.edu", password=False)
        reg_form_layout.addLayout(mail_layout)
        
        (username_layout, self.username_reg_input) = self.create_text_input_box("Username: ", "user123", password=False)
        reg_form_layout.addLayout(username_layout)
        
        (password_layout, self.password_reg_input) = self.create_text_input_box("Password: ", "Password123", password=True)
        reg_form_layout.addLayout(password_layout)
        
        self.name_reg_input.returnPressed.connect(self.mail_reg_input.setFocus)
        self.mail_reg_input.returnPressed.connect(self.username_reg_input.setFocus)
        self.username_reg_input.returnPressed.connect(self.password_reg_input.setFocus)

        
        reg_form.setLayout(reg_form_layout)
        
        
        reg_layout.addStretch()
        reg_layout.addWidget(reg_form, alignment = Qt.AlignHCenter)
        reg_layout.addStretch()
        
        #adding reg button
        reg_button = QPushButton("Register", clicked=lambda: self.handle_reg())
        reg_button.setStyleSheet("""
        QPushButton {
            background-color: #007BFF;  
            color: white;
            font-size: 20px;
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
        }
        QPushButton:hover {
            background-color: #0056b3;
        }
        QPushButton:pressed {
            background-color: #003d80;
        }
        """)
        reg_button.setFixedSize(400, 50)
        
        self.password_reg_input.returnPressed.connect(reg_button.click)
        
        #adding alr have acc msg
        msg = QLabel("Already have an account?")
        msg.setStyleSheet('''
                          bachground-color = transparent;
                          font-size = 18px;
                          ''')
        msg.setFixedHeight(30)
        
    
        #adding log button
        log_button = QPushButton("Log in", clicked=lambda: (self.stacked_widget.setCurrentWidget(self.log_page), self.username_log_input.clear(), self.password_log_input.clear() ))
        log_button.setStyleSheet("""
        QPushButton {
            color: #007BFF;
            background-color: transparent;
            font-size: 18px;
            border: none;
        }
        QPushButton:hover {
            color: #0056b3;  
        }
        QPushButton:pressed {
            color: #003d80;  
        }
        """)
        log_button.setFixedSize(400, 25)
        log_button.setCursor(Qt.PointingHandCursor)
        
        reg_layout.addStretch()
        reg_layout.addWidget(reg_button, alignment = Qt.AlignHCenter)
        reg_layout.addWidget(msg, alignment = Qt.AlignHCenter)
        reg_layout.addWidget(log_button, alignment = Qt.AlignHCenter)
        reg_layout.addStretch()
        
        reg_page.setLayout(reg_layout)
        return reg_page



    def create_log_page(self):
        log_page = QWidget()
        log_layout = QVBoxLayout()
        log_layout.addStretch()
    
        welcome = QLabel(" Welcome to AUBoutique - Login")
        welcome.setStyleSheet("font-size: 56px; font-weight: bold; padding-bottom: 50px;")
        welcome.setAlignment(Qt.AlignCenter)
        log_layout.addWidget(welcome)
        log_layout.addStretch()
        
        log_form = QWidget()
        log_form_layout = QVBoxLayout()
    
        (username_layout, self.username_log_input) = self.create_text_input_box("Username: ", "user123", password=False)
        log_form_layout.addLayout(username_layout)
       
        (password_layout, self.password_log_input) = self.create_text_input_box("Password: ", "Password123", password=True)
        log_form_layout.addLayout(password_layout)
        
        self.username_log_input.returnPressed.connect(self.password_log_input.setFocus)
        
        
        log_form.setLayout(log_form_layout)
        
        container = QWidget()
        container_layout = QHBoxLayout()
        container_layout.addWidget(log_form, alignment = Qt.AlignVCenter)
        container.setLayout(container_layout)
        
        log_layout.addWidget(container, alignment = Qt.AlignHCenter)
        log_layout.addStretch()
        
        login_button = QPushButton("Login", clicked=lambda: self.handle_log())
        login_button.setCursor(Qt.PointingHandCursor)
        login_button.setStyleSheet("""
        QPushButton {
            background-color: #007BFF; 
            color: white;
            font-size: 20px;
            padding: 10px 20px;
            border: none;
            border-radius: 5px;
        }
        QPushButton:hover {
            background-color: #0056b3; 
        }
        QPushButton:pressed {
            background-color: #003d80;
        }
        """)
        login_button.setFixedSize(400, 50)
                    
        msg = QLabel("Don't have an account? Create one for free now!")
        msg.setStyleSheet('''
                          bachground-color = transparent;
                          font-size = 18px;
                          ''')
        msg.setFixedHeight(30)
        
        self.password_log_input.returnPressed.connect(login_button.click)
        
                          
        reg_button = QPushButton("Sign up", clicked=lambda: (self.stacked_widget.setCurrentWidget(self.reg_page), self.username_log_input.clear(), self.password_log_input.clear() ))
        reg_button.setStyleSheet("""
        QPushButton {
            color: #007BFF;
            background-color: transparent;
            font-size: 18px;
            border: none;
        }
        QPushButton:hover {
            color: #0056b3;  
        }
        QPushButton:pressed {
            color: #003d80;  
        }
        """)
        reg_button.setFixedSize(400, 25)
        reg_button.setCursor(Qt.PointingHandCursor)
        
        
        log_layout.addWidget(login_button, alignment=Qt.AlignHCenter)
        log_layout.addWidget(msg, alignment=Qt.AlignHCenter)
        log_layout.addWidget(reg_button, alignment=Qt.AlignHCenter)
        log_layout.addStretch()
        
        log_page.setLayout(log_layout)
    
        return log_page

    
    
    def create_dashboard_page(self):
        dashboard_page = QWidget()
        dashboard_layout = QVBoxLayout()
    
        # Create the QTabWidget
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
        QTabWidget::pane {
            border: 1px solid #C0C0C0;
            background: #F7F7F7;
        }
        QTabBar::tab {
            min-width: 100px;
            background: white;
            color: black; 
            border: 1px solid #C0C0C0;
            padding: 6px 10px; 
            font-size: 14px;
            font-family: Arial, sans-serif; 
        }
        QTabBar::tab:hover {
            background: white; 
            color: black;
            border: 3px solid #0056B3;
        }
        QTabBar::tab:selected {
            background: #0056B3; 
            color: white; 
            font-weight: bold;
        }
        """)
        
        # Create header layout with more padding
        header_lay = QHBoxLayout()
        header_lay.setContentsMargins(20, 15, 20, 15)
        header_lay.setSpacing(20)  # Add space between elements
    
        # User name and points section
        user_info_layout = QHBoxLayout()
        self.name = QLabel()
        self.name.setStyleSheet('''
            font-Size: 24px;
            font-weight: bold;
            margin-right: 20px;
        ''')
        
        self.points_label = QLabel()
        self.points_label.setText(f"BlissPoints: {int(self.points)}")
        self.points_label.setStyleSheet('''
            font-size: 20px;
            font-weight: bold;
            color: black;
            background-color: transparent;
            padding: 10px 20px;
            margin: 0 20px;
        ''')
        self.points_label.setFixedSize(300,40)
        user_info_layout.addWidget(self.name)
        user_info_layout.addWidget(self.points_label)
        header_lay.addLayout(user_info_layout)
        
        # Add stretching space
        header_lay.addStretch()
        
        # Currency dropdown with improved styling
        self.currency_dropdown = QComboBox()
        self.currency_dropdown.setStyleSheet("""
            QComboBox {
                font-size: 16px;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 5px;
                background: white;
            }
            QComboBox::drop-down {
                border: none;
                padding-right: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #666;
                margin-right: 10px;
            }
            QComboBox:hover {
                border-color: #0056B3;
            }
        """)
        self.currency_dropdown.setFixedSize(200, 40)
        self.currencies = ["USD","EUR","LBP","GBP","JPY","AUD","CAD","CHF","CNY","SEK","NZD","MXN","SGD","HKD","NOK","KRW","TRY","INR","RUB","BRL","ZAR"]
        self.currency_dropdown.addItems(self.currencies)
        self.currency_dropdown.currentIndexChanged.connect(self.on_currency_change)
        header_lay.addWidget(self.currency_dropdown)
    
        # Add logout button
        logout_button = QPushButton("Logout")
        logout_button.setStyleSheet("""
            QPushButton {
                background-color: #DC3545;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #C82333;
            }
            QPushButton:pressed {
                background-color: #BD2130;
            }
        """)
        logout_button.clicked.connect(self.logout_user_ok)
        header_lay.addWidget(logout_button)
    
        # Add header to main layout
        dashboard_layout.addLayout(header_lay)
        
        # Add divider line
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setFrameShadow(QFrame.Sunken)
        divider.setStyleSheet("""
            QFrame {
                border: none;
                background-color: #ddd;
                height: 1px;
                margin: 0 20px;
            }
        """)
        dashboard_layout.addWidget(divider)
        
        # Create tabs with their content
        display_items_tab = self.create_display_tab()
        add_item_tab = self.create_add_tab()
        users_tab = self.create_users_tab()
        my_products_tab = self.create_my_products_tab()
        chat_tab = self.create_chat_tab()
        
        
        # Add icons and tabs to the QTabWidget
        self.tabs.addTab(display_items_tab, QIcon("display_icon.png"), "Display Items")
        self.tabs.addTab(add_item_tab, QIcon("add_icon.png"), "Add Item")
        self.tabs.addTab(users_tab, "Users")
        self.tabs.addTab(my_products_tab, "My Products")
        self.tabs.addTab(chat_tab, QIcon("add_icon.png"), "Chat")
        
    
        # Add the tabs widget
        dashboard_layout.addWidget(self.tabs)
    
        # Set background color for the dashboard
        dashboard_page.setStyleSheet("background-color: #F0F0F0;")
        dashboard_page.setLayout(dashboard_layout)
        return dashboard_page
    
    def on_currency_change(self):
        selected_currency = self.currency_dropdown.currentText()
        if selected_currency == "Lebanese Pound (LBP)":
            selected_currency = "LBP"  # Match with the server format if needed
        self.send_req({"action": "change_currency", "currency": selected_currency})
        

            
    
    def create_display_tab(self):
        display_tab = QWidget()
        display_tab_layout = QVBoxLayout()
        
        # Search bar and button setup
        search_container_layout = QHBoxLayout()
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search")
        self.search_bar.setStyleSheet("font-size: 18px; padding: 10px; border: 2px solid #007BFF; border-radius: 5px;")
        self.search_bar.setFixedSize(500, 50)
        
        search_button = QPushButton(clicked=lambda: self.update_product_table_request(self.search_bar.text())) 
        search_button.setFixedSize(50, 50)
        search_button.setCursor(Qt.PointingHandCursor)
        # Set icon
        search_button.setIcon(QIcon("search icon.png"))
        
        search_button.setStyleSheet("""
            QPushButton {background-color: transparent;}
            QPushButton:hover { background-color: transparent; }
            QPushButton:pressed { background-color: transparent; }
        """)
        search_button.setIconSize(QSize(20, 20))
        
        self.search_bar.returnPressed.connect(search_button.click) # if we press enter it also performs searching

        
        search_container_layout.addWidget(self.search_bar, Qt.AlignLeft)
        search_container_layout.addWidget(search_button, Qt.AlignLeft)
        search_container_layout.addStretch()
        
        display_tab_layout.addLayout(search_container_layout, Qt.AlignLeft)
        self.display_label = QLabel("Displaying all products.")
        
        # Style the QLabel
        self.display_label.setStyleSheet("""
            QLabel {
                color: gray; 
                font-size: 14px; 
                font-weight: italic; 
                background-color: transparent; 
                border-radius: 10px; 
                padding: 2px; 
            }
        """)
        self.display_label.setFixedHeight(25)

        display_tab_layout.addWidget(self.display_label, Qt.AlignLeft)
        
        
        
        # Create the QTableWidget
        self.table = QTableWidget(self)
        self.table.setRowCount(0)
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(["Item", "Owner", "Price", "Quantity", "Rating", "Description", "Image"])
        self.table.setSelectionMode(QTableWidget.NoSelection)
        self.table.verticalHeader().setVisible(False)
        
        # Set row height and column widths
        self.table.setColumnWidth(0, 150)  
        self.table.setColumnWidth(1, 120)  
        self.table.setColumnWidth(2, 120) 
        self.table.setColumnWidth(3, 150)  
        self.table.setColumnWidth(4, 200)  
        self.table.setColumnWidth(5, 150)  
        
        #enable scrolling
        self.table.setVerticalScrollMode(QTableWidget.ScrollPerPixel)
        self.table.setHorizontalScrollMode(QTableWidget.ScrollPerPixel)
        self.table.setSizeAdjustPolicy(QTableWidget.AdjustToContents)
        
        #set scroll bar policies
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        #table takes available space
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.table.setSizePolicy(sizePolicy)
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Fixed)
        v_header = self.table.verticalHeader()
        v_header.setSectionResizeMode(QHeaderView.Fixed)
        
        self.table.setColumnWidth(5, 300)
        
        display_tab_layout.addWidget(self.table)
        display_tab.setLayout(display_tab_layout)
        
        # Connect the click event to retrieve the product ID
        self.table.cellClicked.connect(self.on_cell_click)
        
        return display_tab
    
    def upload_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Image", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if file_path:
            print(f"Selected file: {file_path}")
            self.image_path = file_path  # can now send this to server
    
    def create_add_tab(self):
        add_item_tab = QWidget()
        add_item_layout = QVBoxLayout()
        
        add_item_layout = QVBoxLayout()
        add_item_layout.addStretch()
        
        (product_name_layout, self.product_name_input) = self.create_text_input_box("Product name: ", "eg. Laptop", password=False)
        add_item_layout.addLayout(product_name_layout)
        
        (product_description_layout, self.product_description_input) = self.create_text_input_box("Description: ", "eg. New 16GB Ramp", password=False)
        add_item_layout.addLayout(product_description_layout)
        
        (product_price_layout, self.product_price_input) = self.create_text_input_box("Price: ", "eg. 299", password=False)
        add_item_layout.addLayout(product_price_layout)
        
        (product_quantity_layout, self.product_quantity_input) = self.create_text_input_box("Quantity: ", "eg. 3", password=False)
        add_item_layout.addLayout(product_quantity_layout)
        
        upload_button = QPushButton("Upload photo", clicked = lambda: self.upload_image())
        add_item_layout.addWidget(upload_button, Qt.AlignHCenter)
        
        self.product_name_input.returnPressed.connect(self.product_description_input.setFocus)
        self.product_description_input.returnPressed.connect(self.product_price_input.setFocus)
        self.product_price_input.returnPressed.connect(self.product_quantity_input.setFocus)
        # self.product_quantity_input.returnPressed.connect(self.image_input.setFocus)
        
        
        
        
        add_button = QPushButton("Add Product", clicked=lambda: 
                                 self.add_product(self.product_name_input, self.product_price_input, self.product_description_input, self.product_quantity_input, self.image_path)) 
            
        add_button.setStyleSheet("""
            QPushButton {
                background-color: #0078d7;
                color: white;
                font-size: 14px;
                border: none;
                border-radius: 5px;
                padding: 8px 12px;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
            QPushButton:pressed {
                background-color: #004578;
            }
        """)
        add_item_layout.addWidget(add_button)
        add_button.setCursor(Qt.PointingHandCursor)
        
        add_item_layout.addStretch()
        
        container_layout = QHBoxLayout()
        container_layout.addLayout(add_item_layout, Qt.AlignHCenter)
        add_item_tab.setLayout(container_layout)

        return add_item_tab
    
    
    def create_users_tab(self):
        '''Create a tab that displays all users with follow buttons'''
        users_tab = QWidget()
        users_layout = QVBoxLayout()
    
        # Title
        title = QLabel("Users")
        title.setStyleSheet("font-size: 32px; font-weight: bold;")

        
        # Refresh Button
        refresh_button = QPushButton("", clicked = lambda: self.send_req({"action": "show_users"}))
        refresh_button.setStyleSheet("""
            QPushButton {background-color: transparent;}
        """)
        refresh_button.setIcon(QIcon("refresh.png"))
        refresh_button.setCursor(Qt.PointingHandCursor)
        refresh_button.setFixedSize(25,25)
        refresh_button.setIconSize(QSize(25,25))
        
        container = QHBoxLayout()
        container.addWidget(title, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        container.addWidget(refresh_button, alignment=Qt.AlignLeft | Qt.AlignVCenter)
        container.addStretch()

        users_layout.addLayout(container)
    
        # Table to display users
        self.users_table = QTableWidget()
        self.users_table.setRowCount(0)
        self.users_table.setColumnCount(1)  # Single column for username and follow button
        self.users_table.setHorizontalHeaderLabels(["Username"])
        self.users_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.users_table.verticalHeader().setVisible(False)
        self.users_table.horizontalHeader().setVisible(False)
        self.users_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.users_table.setSelectionMode(QTableWidget.NoSelection)
        self.users_table.setFocusPolicy(Qt.NoFocus)
        
        #enable scrolling
        self.users_table.setVerticalScrollMode(QTableWidget.ScrollPerPixel)
        self.users_table.setHorizontalScrollMode(QTableWidget.ScrollPerPixel)
        self.users_table.setSizeAdjustPolicy(QTableWidget.AdjustToContents)
        
        #set scroll bar policies
        self.users_table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.users_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        #table takes available space
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.users_table.setSizePolicy(sizePolicy)
    
        users_layout.addWidget(self.users_table)

    
        users_tab.setLayout(users_layout)
        return users_tab    
    
    
    def create_chat_tab(self):
        # Initialize the layout and UI components
        chat_tab = QWidget()
        chat_tab_layout = QVBoxLayout()
        chat_tab_layout.addStretch()
        chat_tab_layout.setSpacing(10)  # Add spacing between components
        chat_tab_layout.setContentsMargins(15, 15, 15, 15)  # Add margins around the layout
    
        # Dropdown for selecting the peer
        self.peer_selector = QComboBox(self)
        self.peer_selector.setStyleSheet("""
            QComboBox {
                background-color: #ffffff;
                color: #333;
                font-size: 14px;
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 4px;
            }
            QComboBox:focus {
                border-color: #0078d7;
            }
        """)
        self.peer_selector.setFixedSize(500, 25)
        self.peer_selector.addItem("Select a peer...")  # Default placeholder
    
        self.peer_selector.currentIndexChanged.connect(self.switch_chat_widget)  # Connect signal, passes index of selected to func
        chat_tab_layout.addWidget(self.peer_selector)
    
        self.stacked_chat_widget = QStackedWidget()  # Stacked widget to select the chat with peer
        chat_tab_layout.addWidget(self.stacked_chat_widget)
    
        # Create the default chat widget with a message
        default_chat_widget = QWidget()
        default_chat_layout = QVBoxLayout()
        default_chat_display = QTextEdit(self)
        default_chat_display.setReadOnly(True)  # Make it read-only
        default_chat_display.setStyleSheet("""
            QTextEdit {
                background-color: #f7f7f7;
                color: #333;
                font-size: 14px;
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 8px;
            }
        """)
        default_chat_display.setText("Please select a peer to start chatting.")  # Default message
        default_chat_display.setFixedSize(500, 600)
        default_chat_layout.addWidget(default_chat_display)
        default_chat_widget.setLayout(default_chat_layout)
    
        # Add the default chat widget to the stacked widget (it will be the first widget)
        self.stacked_chat_widget.addWidget(default_chat_widget)
        self.peer_to_widget["Select a peer..."] = default_chat_widget
    
        # Message input field
        self.message_input = QLineEdit(self)
        self.message_input.setPlaceholderText("Type your message here...")
        self.message_input.setStyleSheet("""
            QLineEdit {
                background-color: #ffffff;
                color: #333;
                font-size: 14px;
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 8px;
            }
            QLineEdit:focus {
                border-color: #0078d7;
            }
        """)
        chat_tab_layout.addWidget(self.message_input)
        self.message_input.setFixedSize(500, 50)
    
        # Send button
        send_button = QPushButton("Send")
        send_button.setStyleSheet("""
            QPushButton {
                background-color: #0078d7;
                color: white;
                font-size: 14px;
                border: none;
                border-radius: 5px;
                padding: 8px 12px;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
            QPushButton:pressed {
                background-color: #004578;
            }
        """)
        send_button.setFixedSize(500, 50)
        send_button.clicked.connect(self.send_message_to_selected_peer)
        self.message_input.returnPressed.connect(send_button.click) # if we press enter it sends msg
        
        chat_tab_layout.addWidget(send_button)
    
        chat_tab_layout.addStretch()
        
        # Set layout and return the tab
        chat_tab.setLayout(chat_tab_layout)
    
        return chat_tab
    
    @pyqtSlot(int)
    def update_dashboard_points(self, points):
        self.points = points
        self.points_label.setText(f"BlissPoints: {int(self.points)}")
        
    def create_my_products_tab(self):
        my_product_tab = QTabWidget()
        my_product_layout = QVBoxLayout()
        
        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #C0C0C0;
                background: #F7F7F7;
            }
            QTabBar::tab {
                min-width: 100px;
                background: white;
                color: black; 
                border: 1px solid #C0C0C0;
                padding: 6px 10px; 
                font-size: 14px;
                font-family: Arial, sans-serif; 
            }
            QTabBar::tab:hover {
                background: white; 
                color: black;
                border: 3px solid #0056B3;
            }
            QTabBar::tab:selected {
                background: #0056B3; 
                color: white; 
                font-weight: bold;
            }
        """)
        for_sale_tab = self.create_for_sale_tab()
        sold_tab = self.create_sold_tab()
        bought_products_tab = self.create_bought_product_tab()
        
        tabs.addTab(for_sale_tab, QIcon("for sale.png"), "For Sale")
        tabs.addTab(sold_tab, QIcon("sold.png"), "Sold")
        tabs.addTab(bought_products_tab, QIcon("my purshases.png"), "my purshases")
        my_product_layout.addWidget(tabs)
        
        # Connect tab change to a function
        tabs.currentChanged.connect(self.on_tab_pressed)
        
       
        
        my_product_tab.setLayout(my_product_layout)
        
        return my_product_tab
    
    def on_tab_pressed(self, index):
        if index == 0:  # Tab 1 pressed
            self.refresh_for_sale_button.click()
        elif index == 1:  # Tab 2 pressed
            self.refresh_sold_button.click()
        elif index == 2:  # Tab 3 pressed
            self.refresh_bought_button.click()
    
    
    def create_bought_product_tab(self):
       tab = QWidget()
       tab_layout = QVBoxLayout()
       
       self.refresh_bought_button = QPushButton("Refresh")
       
       # Refresh Button
       self.refresh_bought_button= QPushButton("", clicked = lambda: self.send_req({"action": "show_users"}))
       self.refresh_bought_button.setStyleSheet("""
           QPushButton {background-color: transparent;}
       """)
       self.refresh_bought_button.setIcon(QIcon("refresh.png"))
       self.refresh_bought_button.setCursor(Qt.PointingHandCursor)
       self.refresh_bought_button.setFixedSize(25,25)
       self.refresh_bought_button.setIconSize(QSize(25,25))
       
       # Connect the button's pressed signal to a function
       self.refresh_bought_button.clicked.connect(self.refresh_bought_prod)
       
       tab_layout.addWidget(self.refresh_bought_button)
       
       # Create the QTableWidget
       self.bought_products_table = QTableWidget(self)
       self.bought_products_table.setRowCount(0)
       self.bought_products_table.setColumnCount(6)
       self.bought_products_table.setHorizontalHeaderLabels(["Item", "Price", "Quantity bought","Description", "ID", "Image"])
       self.bought_products_table.setSelectionMode(QTableWidget.NoSelection)
       self.bought_products_table.verticalHeader().setVisible(False)
       
       #fix headerss
       header = self.bought_products_table.horizontalHeader()
       header.setSectionResizeMode(QHeaderView.Fixed)
     
       header.setStyleSheet("QHeaderView::section { background-color: #4a97e9; color: white; font-weight: bold; font-size: 14px; border: 1px solid #C0C0C0;}")
       v_header = self.bought_products_table.verticalHeader()
       v_header.setSectionResizeMode(QHeaderView.Fixed)
     
       
       # Set row height and column widths
       self.bought_products_table.setRowHeight(0, 80)
       self.bought_products_table.setColumnWidth(0, 150)  
       self.bought_products_table.setColumnWidth(1, 120)  
       self.bought_products_table.setColumnWidth(2, 150) 
       self.bought_products_table.setColumnWidth(3, 150)  
       self.bought_products_table.setColumnWidth(4, 100)  
       self.bought_products_table.setColumnWidth(5, 150)  
       
       
       # enable scrolling
       self.bought_products_table.setVerticalScrollMode(QTableWidget.ScrollPerPixel)
       self.bought_products_table.setHorizontalScrollMode(QTableWidget.ScrollPerPixel)
       self.bought_products_table.setSizeAdjustPolicy(QTableWidget.AdjustToContents)
       
       #scroll bar policies
       self.bought_products_table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
       self.bought_products_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
       
       #table takes up available space
       sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
       self.bought_products_table.setSizePolicy(sizePolicy)
       
       tab_layout.addWidget(self.bought_products_table)
       tab.setLayout(tab_layout)
       
       # Connect the click event to retrieve the product ID
       self.bought_products_table.cellClicked.connect(self.on_cell_click_rate)
       
       return tab


    def create_for_sale_tab(self):
        tab = QWidget()
        tab_layout = QVBoxLayout()
        
        self.refresh_for_sale_button = QPushButton("Refresh")
        self.refresh_for_sale_button.setStyleSheet("""
            QPushButton {background-color: transparent;}
        """)
        self.refresh_for_sale_button.setIcon(QIcon("refresh.png"))
        self.refresh_for_sale_button.setCursor(Qt.PointingHandCursor)
        self.refresh_for_sale_button.setFixedSize(25,25)
        self.refresh_for_sale_button.setIconSize(QSize(25,25))
        
        # Refresh Button
        self.refresh_for_sale_button = QPushButton("", clicked = lambda: self.send_req({"action": "show_users"}))
        self.refresh_for_sale_button.setStyleSheet("""
            QPushButton {background-color: transparent;}
        """)
        self.refresh_for_sale_button.setIcon(QIcon("refresh.png"))
        self.refresh_for_sale_button.setCursor(Qt.PointingHandCursor)
        self.refresh_for_sale_button.setFixedSize(25,25)
        self.refresh_for_sale_button.setIconSize(QSize(25,25))
        
        # Connect the button's pressed signal to a function
        self.refresh_for_sale_button.clicked.connect(self.refresh_my_products)
        
        tab_layout.addWidget(self.refresh_for_sale_button)
        
        
        # Create the QTableWidget
        self.for_sale_table = QTableWidget(self)
        self.for_sale_table.setRowCount(0)
        self.for_sale_table.setColumnCount(8)
        self.for_sale_table.setHorizontalHeaderLabels(["Item", "Price", "Quantity Left", "Rating", "Description", "blah",  "Image", "Bump (200pts)"])
        self.for_sale_table.setSelectionMode(QTableWidget.NoSelection)
        self.for_sale_table.verticalHeader().setVisible(False)
        
        # enable scrolling
        self.for_sale_table.setVerticalScrollMode(QTableWidget.ScrollPerPixel)
        self.for_sale_table.setHorizontalScrollMode(QTableWidget.ScrollPerPixel)
        self.for_sale_table.setSizeAdjustPolicy(QTableWidget.AdjustToContents)
        
        #scroll bar policies
        self.for_sale_table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.for_sale_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        #table takes up available space
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.for_sale_table.setSizePolicy(sizePolicy)
        
        #fix headerss
        header = self.for_sale_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Fixed)
        header.setStyleSheet("QHeaderView::section { background-color: #4a97e9; color: white; font-weight: bold; font-size: 14px; border: 1px solid #C0C0C0;}")
        v_header = self.for_sale_table.verticalHeader()
        v_header.setSectionResizeMode(QHeaderView.Fixed)
        
        self.for_sale_table.setColumnWidth(5, 300)
        
        # Set row height and column widths
        self.for_sale_table.setRowHeight(0, 80)
        self.for_sale_table.setColumnWidth(0, 150)  
        self.for_sale_table.setColumnWidth(1, 120)  
        self.for_sale_table.setColumnWidth(2, 150) 
        self.for_sale_table.setColumnWidth(3, 120)  
        self.for_sale_table.setColumnWidth(4, 150)  
        self.for_sale_table.setColumnWidth(5, 50)  
        self.for_sale_table.setColumnWidth(6, 150) 
        self.for_sale_table.setColumnWidth(7, 150)
        
        tab_layout.addWidget(self.for_sale_table)
        tab.setLayout(tab_layout)
        
        return tab
    
    
    def create_sold_tab(self):
        tab = QWidget()
        tab_layout = QVBoxLayout()
        
        self.refresh_sold_button = QPushButton("Refresh")
        
        # Refresh Button
        self.refresh_sold_button = QPushButton("", clicked = lambda: self.send_req({"action": "show_users"}))
        self.refresh_sold_button.setStyleSheet("""
            QPushButton {background-color: transparent;}
        """)
        self.refresh_sold_button.setIcon(QIcon("refresh.png"))
        self.refresh_sold_button.setCursor(Qt.PointingHandCursor)
        self.refresh_sold_button.setFixedSize(25,25)
        self.refresh_sold_button.setIconSize(QSize(25,25))
        
        # Connect the button's pressed signal to a function
        self.refresh_sold_button.clicked.connect(self.refresh_sold_products)
        
        tab_layout.addWidget(self.refresh_sold_button)
        
        # Create the QTableWidget
        self.sold_table = QTableWidget(self)
        self.sold_table.setRowCount(0)
        self.sold_table.setColumnCount(4)
        self.sold_table.setSelectionMode(QTableWidget.NoSelection)
        self.sold_table.verticalHeader().setVisible(False)
        self.sold_table.setHorizontalHeaderLabels(["Item", "Buyer", "Price of 1", "Quantity Sold",])
        #fix headerss
        header = self.sold_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Fixed)
        header.setStyleSheet("QHeaderView::section { background-color: #4a97e9; color: white; font-weight: bold; font-size: 14px; border: 1px solid #C0C0C0;}")
        v_header = self.sold_table.verticalHeader()
        v_header.setSectionResizeMode(QHeaderView.Fixed)
        
        # Set row height and column widths
        self.sold_table.setRowHeight(0, 80)
        self.sold_table.setColumnWidth(0, 150)  
        self.sold_table.setColumnWidth(1, 120)  
        self.sold_table.setColumnWidth(2, 120) 
        self.sold_table.setColumnWidth(3, 150)   
        
        
        # enable scrolling
        self.sold_table.setVerticalScrollMode(QTableWidget.ScrollPerPixel)
        self.sold_table.setHorizontalScrollMode(QTableWidget.ScrollPerPixel)
        self.sold_table.setSizeAdjustPolicy(QTableWidget.AdjustToContents)
        
        #scroll bar policies
        self.sold_table.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.sold_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        #table takes up available space
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.sold_table.setSizePolicy(sizePolicy)
 
        
        tab_layout.addWidget(self.sold_table)
        tab.setLayout(tab_layout)
        
        return tab
        

    def refresh_my_products(self):
        self.send_req({"action" : "my_products"})
        
    def refresh_sold_products(self):
        self.send_req({"action" : "sold_prod"})
        
    def refresh_bought_prod(self):
        self.send_req({"action" : "my_purchases"})
        
    
    def add_product(self, name, price, description, quantity, image_path,):
        # Read the image file
        with open(self.image_path, "rb") as image_file:
            encoded_image = base64.b64encode(image_file.read()).decode('utf-8')
        
        #fomulate the add request
        req = {"action" : "add" , "name" : str(name.text()), 
              "price" : self.preffered_currency_multiplier * float(str(price.text())),
              "image" : encoded_image,
              "description" : str(description.text()), 
              "quantity" : int(str(quantity.text()))
              }
        #clear the text boxes
        name.clear()
        price.clear()
        description.clear()
        quantity.clear()
        self.image_path = None
        
        
        
        #send the request
        self.send_req({"action" : "sending_add"})
        time.sleep(1)
        self.send_req(req) 
        self.sent_add_req = True
    
    def create_text_input_box(self, text, placeholder, password = False):
        name_label = QLabel(text)
        name_label.setStyleSheet("font-size: 18px; padding-bottom: 0px")
        
        input_text = QLineEdit()
        input_text.clear()
        input_text.setPlaceholderText(placeholder)
        input_text.setStyleSheet("font-size: 18px; padding: 10px; border: 2px solid black; border-radius: 5px;")
        input_text.setFixedSize(500, 50)
        if password:
            input_text.setEchoMode(QLineEdit.Password) 
            
        layout = QVBoxLayout()
        layout.addWidget(name_label)
        layout.addWidget(input_text)
        
        return (layout, input_text)
    
        
    
    def handle_log(self):
        
        username = self.username_log_input.text()  # Get username input text
        password = self.password_log_input.text()  # Get password input text
        
        if self.validate_string(username):
            if self.validate_password(password):
                # Send login details to the server
                req = {"action" : "login", "user" : username, "password" : self.hash_password(password)}
                self.username = username
                self.name.setText(self.username)
                self.send_req(req)
            else:
                QMessageBox.critical(self, "Invalid Password", "Password must be at least 8 characters long and include at least one uppercase letter.")
        else:
            QMessageBox.critical(self, "Invalid Username", "Username cannot be empty or consist only of spaces.")
            
    
        

    def handle_reg(self):
        name = self.name_reg_input.text().strip() # Get name input text
        mail = self.mail_reg_input.text().strip() # Get name input text
        username = self.username_reg_input.text().strip() # Get username input text
        password = self.password_reg_input.text() # Get password input text
        
        # Debug prints 
        print(f"Name: '{name}'") 
        print(f"Mail: '{mail}'") 
        print(f"Username: '{username}'") 
        print(f"Password: '{password}'")
        
        if self.validate_reg_info(name, mail, username, password):
            req = {"action" : "reg", "name": name, "mail": mail, "username" : username, "password" : self.hash_password(password)}
            self.send_req(req)
            
            
    def initiate_p2p(self, username, status):
        if status==0:
            self.show_message(f"{username} is not online!")
            return
            
        req_p2p_info = {"action" : "p2p_info", "username" : username}
        self.send_req(req_p2p_info)
        
        
        if not self.p2p_reply_recieved.wait(timeout=10):  # Add timeout to avoid indefinite wait
            self.show_message("P2P info request timed out.")
            self.p2p_reply_recieved.clear()
            return
        if self.target_ip == "offline":
            self.show_message(f"{username} is not online!")
            self.p2p_reply_recieved.clear()
            return

        self.p2p_reply_recieved.clear()
        
        
        self.send_req({"action" : "p2p_req", "username" : username})
        if not self.p2p_req_reply_recieved.wait(timeout=10):  # wait to get confirmation of p2p req or declination# wait to get confirmation of p2p req or declination
            print("P2P request timed out or was declined.")
            return 
        # try:
        self.p2p_req_reply_recieved.clear()
        
        peer_info = {"ip": self.target_ip, "port": self.target_port, "username": username}
        self.active_peers[username] = peer_info

        # self.tabs.setCurrentIndex(3)
        self.add_peer_to_selector(username)
        threading.Thread(target=self.message_listener_thread, args=(username,)).start()
        print("recieving on port", self.udp_socket.getsockname()[1], "sending on port", self.target_port)
            
        # except Exception as e:
        #     print(f"Error connecting to peer: {e}")
            
        
    def message_listener_thread(self, peer_username):
        peer_info = self.active_peers[peer_username]
        peer_ip, peer_port = peer_info["ip"], peer_info["port"]
    
        while True:
            # try:
                message, addr = self.udp_socket.recvfrom(1024)
                print("message recieved from ", peer_username)
                if addr[0] == peer_ip and addr[1] == peer_port:
                    decoded_message = message.decode()
                    message = peer_username + " ", decoded_message
                    self.append_message_to_chat(peer_username, message)
            # except Exception as e:
            #     print(f"Error in listener for {peer_username}: {e}")
            #     break
            
    def send_message_to_selected_peer(self):
        selected_peer = self.peer_selector.currentText()
        if selected_peer == "Select a peer...":
            self.show_message("Please select a peer to send a message.")
            return
    
        if selected_peer not in self.active_peers:
            self.show_message(f"Peer {selected_peer} is no longer available.")
            return
    
        peer_info = self.active_peers[selected_peer]
        target_ip = peer_info["ip"]
        target_port = peer_info["port"]
    
        message = self.message_input.text().strip()
        if message:
            self.send_msg_udp(selected_peer, message, target_ip, target_port)
            
    def send_msg_udp(self,username, message, target_ip, target_port):
        print('sending message to', username, " ", message)
        self.append_message_to_chat(username, message, sender = True)
        # if message.lower() == "exit":
        #     print("Exiting chat.")
        #     break
        self.udp_socket.sendto((message).encode(), (target_ip, target_port))
        self.message_input.clear()
            
            
    def add_peer_to_selector(self, peer_username):
        """Adds a peer to the dropdown and creates a chat widget for them."""
        if peer_username not in self.peer_to_widget:
            self.peer_selector.addItem(peer_username)
            
            #create widget to addto stackedchatWidget
            chat_with_peer = QWidget()
            layout = QVBoxLayout()
            chat_display = QTextEdit(self) 
            chat_display.setReadOnly(True)  # Make chat display read-only
            chat_display.setStyleSheet("""
                QTextEdit {
                    background-color: #f7f7f7;
                    color: #333;
                    font-size: 14px;
                    border: 1px solid #ccc;
                    border-radius: 5px;
                    padding: 8px;
                }
            """)
            chat_display.setFixedSize(500, 600)
            layout.addWidget(chat_display)
            chat_with_peer.setLayout(layout)
            
            self.stacked_chat_widget.addWidget(chat_with_peer)
            
            #map the peer username to the respective chat box
            self.peer_to_widget[peer_username] = chat_with_peer
            
    
    def switch_chat_widget(self, index):
        """Switches the stacked widget to the selected user's chat. also to default"""
        username = self.peer_selector.itemText(index)
        chat_widget = self.peer_to_widget.get(username, None)
        if chat_widget:
            self.stacked_chat_widget.setCurrentWidget(chat_widget)
        
    
            
    def append_message_to_chat(self, peer_username, message, sender = False):
        """Appends a message to the respective peer's chat widget."""
        chat_widget = self.peer_to_widget[peer_username]
        if chat_widget:
            chat_display = chat_widget.findChild(QTextEdit)
            if chat_display:
                if not sender: # if user received msg
                    chat_display.append(f"{peer_username}: {message[1]}")
                else: # if user sent msg
                    chat_display.append(f"You: {message}")
            
    
    def remove_peer_from_selector(self, peer_username):
        index = self.peer_selector.findText(peer_username)
        if index != -1:
            self.peer_selector.removeItem(index)
            
    
        
    
    def view_prod_of_user(self, username):
        self.send_req({"action" : "display_user", "username" : username})
        
    
            
            
    def follow_user(self, username, button):
        """Handle follow button click."""
        req = {"action": "follow", "followed_username": username}
        self.send_req(req)
    
        # Update button state
        container_layout = button.parent().layout()
        if container_layout:
            # Remove the "Follow" button
            container_layout.removeWidget(button)
            button.deleteLater()  # Clean up the old button
    
            # Create a new "Following" button
            following_button = QPushButton("Following")
            following_button.setFixedSize(90, 30)
            following_button.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white; 
                    font-size: 12px; 
                    border: none; 
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
                QPushButton:pressed {
                    background-color: #387a36;
                }
            """)
            following_button.clicked.connect(lambda _, u=username, btn=following_button: self.unfollow_user(u, btn))
    
            # Add the new "Following" button to the layout
            container_layout.addWidget(following_button)
    
            # Add the user to the following dictionary
            self.following[username] = 1
            
            
    def unfollow_user(self, username, button):
        req = {"action": "unfollow", "unfollowed_username": username}
        self.send_req(req)
    
        # Update button state
        container_layout = button.parent().layout()
        if container_layout:
            # Remove the "Follow" button
            container_layout.removeWidget(button)
            button.deleteLater()  # Clean up the old button
    
            # Create a new "Following" button
            follow_button = QPushButton("Follow")
            follow_button.setFixedSize(90, 30)
            follow_button.setStyleSheet("""
                QPushButton {
                    background-color: #DD3D21;
                    color: white; 
                    font-size: 12px; 
                    border: none; 
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #E94225;
                }
                QPushButton:pressed {
                    background-color: #F64729;
                }
            """)
            follow_button.clicked.connect(lambda _, u=username, btn=follow_button: self.follow_user(u, btn))
    
            # Add the new "Following" button to the layout
            container_layout.addWidget(follow_button)
    
            # remove user from following dictionary
            del self.following[username]
            
            
    def buy_product(self, product_id, dialog, row):
        print("in buy")
       
        quantity_item = self.table.item(row, 3)
        quantity_available = int(quantity_item.text())  # Get the available quantity as an integer
        
        # Get quantity from the user (using a dialog box with the available quantity as the max value)
        quantity_bought, ok = QInputDialog.getInt(self, 
                                                  "Quantity", 
                                                  f"Enter the quantity you want to buy (Max: {quantity_available}):", 
                                                  1, 1, quantity_available, 1)
        if ok and quantity_bought <= quantity_available:
            print(f"Buying product with ID: {product_id}, Quantity: {quantity_bought}")

            new_quantity = quantity_available - quantity_bought
            self.table.item(row, 3).setText(str(new_quantity))  # Update the quantity in the table

            buy_request = {
                'action': 'buy',  
                'ID': product_id, 
                'quantity_bought': quantity_bought  
            }
            self.send_req(buy_request)  # Sends the buy request to the server

        else:
            print("Invalid quantity or quantity exceeds available stock.")
           
        dialog.accept()
    


        
    #COMMUNICATION WITH SERVER USING JSON
    @pyqtSlot(dict) # for thread safe requests
    def send_req(self, req):
        if not self.sent_add_req:
            try:
                request = ''
                request = json.dumps(req) + '\n' #to act as delimiter so server knows when it ends
                self.client_socket.send(request.encode())
                print("Request sent:", req)
            except (socket.error, json.JSONDecodeError) as e:
                print(f"Error sending request: {e}")
                self.show_message("Failed to send request. Please try again.")
        
    
    def validate_string(self, typed_string):
         '''Checks if string entered meets conditions'''
         if len(typed_string)==0:
             return False
         else:
             return True
            
    def hash_password(self, password): 
        '''encrypts the password for user safety'''
        hash_object = hashlib.sha256()
        hash_object.update(password.encode('utf-8'))
        return hash_object.hexdigest()
    
    
    def validate_password(self, password):
        '''Checks if password meets conditions'''
        if len(password) >= 8 and any(c.isupper() for c in password): # at least one upper and more than 8
            return True
        else:
            return False
        
    
    def validate_mail(self, email):
        '''Check if email is valid in aub email format'''
      
        if len(email) != 0:
            if re.match(r"[^@]+@mail\.aub\.edu$", email): #regex to validate
                return True

        QMessageBox.critical(self, "Invalid Password", "Password must be at least 8 characters long and include at least one uppercase letter.")
        return False
        
        
        
    def validate_reg_info(self, name, mail, username, password):
        if self.validate_string(name):
            if self.validate_mail(mail):
                if self.validate_string(username):
                    if self.validate_password(password):
                        return True
                    else:
                        QMessageBox.critical(self, "Invalid Password", "Password must be at least 8 characters long and include at least one uppercase letter.")
                        return False
                else:
                    QMessageBox.critical(self, "Invalid Username", "Username cannot be empty or consist only of spaces.")
                    return False
            else:
                QMessageBox.critical(self, "Invalid Mail Format", "Mail has to be an AUB Mail")
                return False
        else:
            QMessageBox.critical(self, "Invalid Name", "Name cannot be empty or consist only of spaces.")
            return False
        
        
        
    @pyqtSlot(tuple)
    def build_product_table(self, tup):
        '''Displays products for sale that were received from the server, or shows an error message if no products.'''
        print("building table")
        username = tup[1] #extract second component of tuple if it exists
        print(username)
        search_term = self.search_bar.text()
        if len(username) > 0:
            self.display_label.setText(f"Displaying products of '{username}'.")
        elif len(search_term) == 0:
            self.display_label.setText("Displaying all products.")
        else:
            self.display_label.setText(f"Displaying search results for '{search_term}'.")
        
        #clear search barz  
        self.search_bar.clear()

        # Clear existing contents in the table before adding new data
        self.table.clearContents()  
        #reset the row count to 0
        self.table.setRowCount(0)  
        #extract the actual list from the tup
        product_list = tup[0]  
        
        #handle empty product lists
        if product_list == "No products found matching your search." or product_list == "No products for sale at the moment.":
            self.show_message(product_list)
            return
    
        # set row count for the number of products
        self.table.setRowCount(len(product_list))
    
        # set the header labels and style
        self.table.setHorizontalHeaderLabels(["Item", "Owner", "Price", "Quantity", "Rating", "Description", "Image"])
        header = self.table.horizontalHeader()
        header.setStyleSheet("QHeaderView::section { background-color: #4a97e9; color: white; font-weight: bold; font-size: 14px; border: 1px solid #C0C0C0;}")

    
        # populate table with product data
        for row, product in enumerate(product_list):
            # Add data to columns with rows
            self.table.setItem(row, 0, self.create_uneditable_item(product["item"]))
            self.table.setItem(row, 1, self.create_uneditable_item(product["owner"]))
            self.table.setItem(row, 2, self.create_uneditable_item(f"{float(self.preffered_currency_multiplier * product['price']):.2f}"))
            self.table.setItem(row, 3, self.create_uneditable_item(product["quantity"]))
            self.table.setItem(row, 4, self.create_uneditable_item(self.convert_rating_to_stars(product["rating"])))
            
            self.table.setItem(row, 5, self.create_uneditable_item(product["description"]))

            self.table.setItem(row, 7, self.create_uneditable_item(product["ID"]))
    
            self.table.setColumnHidden(7, True)  # Hide the product ID column
    
            # Add image to the last column
            image_label = QLabel()
            pixmap = QPixmap(product["image_path"]).scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            image_label.setPixmap(pixmap)
            
            container_widget = QWidget()
            layout = QHBoxLayout()
            layout.addWidget(image_label)
            layout.setAlignment(Qt.AlignCenter)  # Align the label to the center
            layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
            container_widget.setLayout(layout)
            
            self.table.setCellWidget(row, 6, container_widget)
    
            self.table.setRowHeight(row, 80)  # Adjust the height of each row
        

        
        
    @pyqtSlot(list)
    def populate_users_table(self, users):
        self.users_table.setRowCount(0)
        self.users_table.setColumnCount(1)  # Single column for username and follow button
        self.users_table.setHorizontalHeaderLabels(["Username"])
        self.users_table.horizontalHeader().setStretchLastSection(True)  # Ensure column stretches
        self.users_table.verticalHeader().setVisible(False)  # Hide row numbers
        self.users_table.setStyleSheet("""
            QTableWidget {
                font-size: 14px;
                background-color: #f9f9f9;
                border: 1px solid #ccc;
            }
            QHeaderView::section {
                background-color: #0078d7;
                color: white;
                font-size: 14px;
                padding: 4px;
            }
        """)
    
        for i, (username, status) in enumerate(users):
            self.users_table.insertRow(i)
    
            # Create a container for username and follow button
            container_widget = QWidget()
            container_layout = QHBoxLayout(container_widget)
            container_layout.setContentsMargins(5, 5, 5, 5)  # Add padding inside container
            container_layout.setSpacing(10)  # Add spacing between elements
    
            # Username label
            username_label = QLabel(f"{username} {'(Online)' if status == 1 else '(Offline)'}")
            username_label.setStyleSheet("""
                QLabel {
                    font-size: 16px;
                    padding: 5px;
                    color: #333;
                }
            """)
            container_layout.addWidget(username_label, alignment=Qt.AlignVCenter)
            
            # Message button
            view_button = QPushButton("View Products")
            view_button.setFixedSize(90, 30)
            view_button.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    border: none;
                    color: white;
                    font-size: 12px;
                    padding: 4px 2px;
                    text-align: center;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
                QPushButton:pressed {
                    background-color: #2e7031;
                }
            """)
            view_button.clicked.connect(lambda _, u=username: self.view_prod_of_user(u))
            container_layout.addWidget(view_button)
            
            # Message button
            msg_button = QPushButton("Message")
            msg_button.setFixedSize(90, 30)
            msg_button.setStyleSheet("""
                QPushButton {
                    background-color: #0078d7;
                    color: white;
                    font-size: 12px;
                    border: none;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #005a9e;
                }
                QPushButton:pressed {
                    background-color: #004578;
                }
            """)
            msg_button.clicked.connect(lambda _, u=username, s=status: self.initiate_p2p(u, s))
            container_layout.addWidget(msg_button)
    
            # Follow button
            follow_button = QPushButton("Follow")
            follow_button.setFixedSize(90, 30)
            follow_button.setStyleSheet("""
                QPushButton {
                    background-color: #DD3D21;
                    color: white; 
                    font-size: 12px; 
                    border: none; 
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #E94225;
                }
                QPushButton:pressed {
                    background-color: #F64729;
                }
            """)
            follow_button.clicked.connect(lambda _, u=username, btn=follow_button: self.follow_user(u, btn))
            
            following_button = QPushButton("Following")
            following_button.setFixedSize(90, 30)
            following_button.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    border: none;
                    color: white;
                    font-size: 12px;
                    padding: 4px 2px;
                    text-align: center;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
                QPushButton:pressed {
                    background-color: #2e7031;
                }
            """)
            following_button.clicked.connect(lambda _, u=username, btn=following_button: self.unfollow_user(u, btn))
            if username in self.following:
                print("following", username)
                container_layout.addWidget(following_button)
            else:
                print("not following", username)
                container_layout.addWidget(follow_button)
    
            # Add container to the table
            self.users_table.setCellWidget(i, 0, container_widget)
    
        # Adjust row height for consistent spacing
        for row in range(self.users_table.rowCount()):
            self.users_table.setRowHeight(row, 50)
            
    @pyqtSlot(tuple)
    def update_my_products(self, product_list):
        """handles showing the products of the user"""
        #for debugging onlu
        
        print("building my products table")
        # Clear old content if any
        self.for_sale_table.clearContents() 
        self.for_sale_table.setRowCount(0)  #rows set to 0
        product_list = product_list[0] #because we passed it as a tuple
        
        # Handle empty product lists or error messages
        if not product_list:
            return
    
        # Set row count for the number of products
        self.for_sale_table.setRowCount(len(product_list))
    
        # Populate for_sale_table with product data
        for row, product in enumerate(product_list):
            # Add data to columns with rows
            self.for_sale_table.setItem(row, 0, self.create_uneditable_item(product["item"]))
            self.for_sale_table.setItem(row, 1, self.create_uneditable_item(f"{float(self.preffered_currency_multiplier * product['price']):.2f}"))
            self.for_sale_table.setItem(row, 2, self.create_uneditable_item(product["quantity"]))
            self.for_sale_table.setItem(row, 3, self.create_uneditable_item(self.convert_rating_to_stars(product["rating"])))
            self.for_sale_table.setItem(row, 4, self.create_uneditable_item(product["description"]))
    
            # Create a better styled bump button
            bump_button = QPushButton("Bump to Top")
            bump_button.setStyleSheet('''
                QPushButton {
                    background-color: #0078d7;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 5px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #005a9e;
                }
                QPushButton:pressed {
                    background-color: #004578;
                }
                QPushButton:disabled {
                    background-color: #cccccc;
                }
            ''')
            
            bump_button.setEnabled(self.points >= 200)
            bump_button.clicked.connect(lambda checked, ID=product["ID"]: self.bump_listing(ID))
            bump_button.setFixedSize(100, 50)
            
            # Create container for button to center it
            button_container = QWidget()
            button_layout = QHBoxLayout(button_container)
            button_layout.addWidget(bump_button, alignment=Qt.AlignCenter)
            self.for_sale_table.setCellWidget(row, 7, button_container)
    
            # Hide the owner column
            self.for_sale_table.setColumnHidden(5, True)
    
            # Add image to the last column
            image_label = QLabel()
            pixmap = QPixmap(product["image_path"]).scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            image_label.setPixmap(pixmap)
            
            container_widget = QWidget()
            layout = QHBoxLayout()
            layout.addWidget(image_label)
            layout.setAlignment(Qt.AlignCenter)  # Align the label to the center
            layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
            container_widget.setLayout(layout)
            self.for_sale_table.setCellWidget(row, 6, container_widget)
    
            self.for_sale_table.setRowHeight(row, 80)  # Adjust the height of each row
        
    @pyqtSlot(tuple)   
    def update_sold_products(self, product_list):
        self.sold_table.clearContents()
        self.sold_table.setRowCount(0)  #rows set to 0
        product_list = product_list[0] #because we passed it as a tuple
        
        if not product_list:
            # self.show_message("You haven't sold any products yet :(")
            return
        
        self.sold_table.setRowCount(len(product_list))

    
        # Populate sold_table with product data
        for row, product in enumerate(product_list):
            # Add data to columns with rows
            self.sold_table.setItem(row, 0, self.create_uneditable_item(product["product"]))
            self.sold_table.setItem(row, 1, self.create_uneditable_item(product["buyer"]))
            self.sold_table.setItem(row, 2, self.create_uneditable_item(f"{float(self.preffered_currency_multiplier * product['price']):.2f}"))
            self.sold_table.setItem(row, 3, self.create_uneditable_item(product["quantity_bought"]))
    
            self.sold_table.setRowHeight(row, 80)  # Adjust the height of each row
        
        # Connect the click event to retrieve the product ID
        # self.sold_table.cellClicked.connect(self.on_cell_click)
        
    
    @pyqtSlot(tuple)
    def update_products_I_bought(self, product_list):
        """handles showing the products of the user"""
        #for debugging onlu
        print("building bought products table")
        # Clear old content if any
        self.bought_products_table.clearContents() 
        self.bought_products_table.setRowCount(0)  #rows set to 0
        product_list = product_list[0] #because we passed it as a tuple
        
        # Handle empty product lists or error messages
        if not product_list:
            # self.show_message("You haven't bought any products yet :(")
            return
    
        # Set row count for the number of products
        self.bought_products_table.setRowCount(len(product_list))
    
        # Populate for_sale_table with product data
        for row, product in enumerate(product_list):
            # Add data to columns with rows
            self.bought_products_table.setItem(row, 0, self.create_uneditable_item(product["item"]))
            self.bought_products_table.setItem(row, 1, self.create_uneditable_item(f"{float(self.preffered_currency_multiplier * product['price']):.2f}"))
           
            self.bought_products_table.setItem(row, 2, self.create_uneditable_item(product["quantity_bought"]))
            self.bought_products_table.setItem(row, 3, self.create_uneditable_item(product["description"]))
            self.bought_products_table.setItem(row, 4, self.create_uneditable_item(product["ID"]))
            
            self.bought_products_table.setColumnHidden(4, True)  # Hide the product ID column
            
            # Add image to the last column
            image_label = QLabel()
            pixmap = QPixmap(product["image"]).scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            image_label.setPixmap(pixmap)
            
            container_widget = QWidget()
            layout = QHBoxLayout()
            layout.addWidget(image_label)
            layout.setAlignment(Qt.AlignCenter)  # Align the label to the center
            layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
            container_widget.setLayout(layout)
            self.bought_products_table.setCellWidget(row, 5, container_widget)
    
            self.bought_products_table.setRowHeight(row, 80)  # Adjust the height of each row
        
        
    def on_cell_click_rate(self, row, column):
        table = self.sender()  # Get the sender (the table)
        if column == 5:  # image column
            image_label = self.table.cellWidget(row, column)
            pixmap = image_label.pixmap()  #retrieve the image from the label
            self.show_large_image(pixmap)
        else:

            # Retrieve the product ID from the correct column (column 6)
            product_id_item = table.item(row, 4)  # Column 6 stores the product ID
            if product_id_item:
                product_id = product_id_item.text()
                print(f"Product ID: {product_id} was clicked")
                self.show_product_id_rating(product_id)
                
            else:
                print("No product ID found")
                
    def show_product_id_rating(self, product_id):
       '''Show a small dialog displaying the product ID.'''
       dialog = QDialog(self)  # Create a new dialog window
       dialog.setWindowTitle("Product rating")
       dialog.resize(300, 200) 
    
       # Create a label to display the product ID
       label = QLabel(f"Product ID: {product_id}", dialog)
       
       # Create a layout and add the label
       layout = QVBoxLayout()
       layout.addWidget(label)
       
       
       rate_button = QPushButton("rate your product", dialog)
       
       rate_button.setStyleSheet("background-color: green; color: white; font-size: 14px; padding: 10px;")
       
      
       rate_button.clicked.connect(lambda: self.show_rating_dialog(product_id))
      
      
       layout.addWidget(rate_button)
       
       # Add a button to close the dialog
       button = QDialogButtonBox(QDialogButtonBox.Ok, parent=dialog)
       button.accepted.connect(dialog.accept)
       layout.addWidget(button)
    
       dialog.setLayout(layout)
       dialog.exec_()

        

    def on_cell_click(self, row, column):
        print()
        table = self.sender()  # Get the sender (the table)
        if column == 6:  # image column
            image_label = self.table.cellWidget(row, column)
            pixmap = image_label.pixmap()  #retrieve the image from the label
            self.show_large_image(pixmap)  #call a function to display the image in a larger format
        else:
            # Retrieve the product ID from the correct column (column 6)
            product_id_item = table.item(row, 7) 
            product_name = table.item(row,0).text()
            if product_id_item:
                product_id = product_id_item.text()
                print(f"Product ID: {product_id} was clicked, in main")
                self.show_product_id_dialog(product_id, product_name, row)
                
            else:
                print("No product ID found")
                
    
    def show_large_image(self, pixmap):
        '''Display a larger version of the image in a dialog'''
        dialog = QDialog(self)  # Create a dialog to display the large image
        dialog.setWindowTitle("Large Image")  # Set the dialog title
        dialog.setFixedSize(500, 500)  # Set the dialog size

        # Create a label inside the dialog to hold the image
        label = QLabel(dialog)
        label.setPixmap(pixmap.scaled(500, 500, Qt.KeepAspectRatio))  # Scale the image to fit the dialog
        label.setAlignment(Qt.AlignCenter)  # Center the image in the dialog

        # Create a button box for dialog controls (optional)
        button_box = QDialogButtonBox(QDialogButtonBox.Close, parent=dialog)
        
        # Make sure the dialog closes properly when the close button is clicked
        button_box.rejected.connect(dialog.accept)  # Use accept() to close the dialog

        # Add the label and button box to the dialog's layout
        layout = QVBoxLayout(dialog)
        layout.addWidget(label)
        layout.addWidget(button_box)

        # Use exec_() to show the dialog and run the event loop
        dialog.exec_()  # Starts the event loop and waits for the dialog to close
            
            
    def show_product_id_dialog(self, product_id, product_name, row):
        '''Show a small dialog displaying the product ID.'''
        dialog = QDialog(self)  # Create a new dialog window
        dialog.setWindowTitle("Product ID")
        dialog.resize(300, 200) 

        # Create a label to display the product ID
        label = QLabel(f"Product: {product_name}", dialog)
        
        # Create a layout and add the label
        layout = QVBoxLayout()
        layout.addWidget(label)
        
        
        buy_button = QPushButton("Buy Now", dialog)
        # add_to_cart_button = QPushButton("Add to Cart", dialog)
        buy_button.setStyleSheet("background-color: green; color: white; font-size: 14px; padding: 10px;")
        # add_to_cart_button.setStyleSheet("background-color: green; color: white; font-size: 14px; padding: 10px;")
       
        buy_button.clicked.connect(lambda: self.buy_product(product_id, dialog, row))
        # add_to_cart_button.clicked.connect(lambda: self.add_to_cart(product_id, dialog))
       
        layout.addWidget(buy_button)
        # layout.addWidget(add_to_cart_button)
        
        # Add a button to close the dialog
        button = QDialogButtonBox(QDialogButtonBox.Ok, parent=dialog)
        button.accepted.connect(dialog.accept)
        layout.addWidget(button)

        dialog.setLayout(layout)
        dialog.exec_()
        
        
    def create_uneditable_item(self, text):
        text = str(text)
        item = QTableWidgetItem(text)            
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # Make the item uneditable
        item.setTextAlignment(Qt.AlignCenter)
        return item
    
    
    def closeEvent(self, event):    
    
        self.logout_user()  # Call the logout function
        event.accept()  # Close the application
    
    
            
    
            
    def logout_user_ok(self):
        if self.username:
            self.send_req({"action": "log_out", "username": self.username})
        self.client_socket.close()
        self.udp_socket.close()
        self.points = 0
        self.all_products.clear()
        self.products_for_sale.clear()
        self.bought_products.clear()
        self.sold_products.clear()
        self.username = None
        self.active_peers.clear()
        self.peer_to_widget.clear()
        self.following.clear()
        self.image_path = None
        self.preffered_currency = "USD"
        self.preffered_currency_multiplier = 1
        self.sent_add_req = False
        
        self.stacked_widget.setCurrentWidget(self.log_page)
        self.close()  # Close the window
            
    def logout_user(self):
        try:
            # Notify the server
            if self.username:
                self.send_req({"action": "log_out", "username": self.username})
            # if self.target_ip and self.target_port:
            #     self.send_msg_udp("self.udp_socketClosing_Close_conn_with_peer", self.udp_socket, self.target_ip, self.target_port)
                
            # Close sockets
            self.client_socket.close()
            self.udp_socket.close()
            
            print("Logged out successfully.")
        except Exception as e:
            print(f"Error during logout: {e}")
            

            
            
    def show_rating_dialog(self, product_id):
            dialog = QDialog(self)
            dialog.setWindowTitle("Rate Product")
            dialog.resize(300, 150)
            
            # Create a layout to display the stars
            layout = QVBoxLayout()
            rating_label = QLabel("Rate this product:")
            layout.addWidget(rating_label)

            # Create a horizontal layout for the stars
            stars_layout = QHBoxLayout()
            self.stars_buttons = []  # Store the buttons for the stars
            self.selected_rating = 0  # Initially, no rating is selected

            # Create the star buttons
            for i in range(1, 6):
                star_button = QPushButton("★")  # Using star character for the visual effect
                star_button.setObjectName(f"star_{i}")
                star_button.setFixedSize(50, 50)
                star_button.setStyleSheet("font-size: 30px;")
                star_button.setProperty("rating", i)  # Associate the numeric rating with the button
                star_button.clicked.connect(self.on_star_clicked)
                self.stars_buttons.append(star_button)
                stars_layout.addWidget(star_button)

            layout.addLayout(stars_layout)

            # Add Submit button
            submit_button = QPushButton("Submit Rating")
            submit_button.clicked.connect(lambda: self.submit_rating(product_id,self.selected_rating))
            layout.addWidget(submit_button)

            dialog.setLayout(layout)
            dialog.exec_()
            
            
    def on_star_clicked(self):
            """Called when a star button is clicked. It sets the rating based on the button clicked."""
            clicked_button = self.sender()
            self.selected_rating = clicked_button.property("rating")
            self.update_star_display()

    def update_star_display(self):
            """Updates the display of the stars based on the selected rating."""
            for i, button in enumerate(self.stars_buttons):
                if i < self.selected_rating:
                    button.setStyleSheet("font-size: 30px; color: gold;")  # Gold color for selected stars
                else:
                    button.setStyleSheet("font-size: 30px; color: grey;")  # Grey color for unselected stars

    def submit_rating(self, product_id,rating):
            """Sends the selected rating to the server."""
            if rating > 0:
                req = {
                    "action": "rate",
                    "product_id": product_id,
                    "rate": rating
                }     
                self.send_req(req)
            else:
              print("you must rate this product ")
              
    
    def convert_rating_to_stars(self, rating):
        if rating == "unrated":
               return "Unrated"
        try:
           full_stars = int(rating)  # Convert the rating to an integer
           return "★" * full_stars + "☆" * (5 - full_stars)  # Fill up to 5 stars
        except ValueError:
            return "Unrated"
              
    def bump_listing(self, product_id):
        if self.points >= 200:
            reply = QMessageBox.question(
                self, 
                "Confirm Bump",
                "Would you like to bump this listing to the top for 200 points?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.points = self.points - 200
                self.points_label.setText(f"BlissPoints: {self.points}")
                self.send_req({
                    "action": "bump_listing",
                    "product_id": product_id
                })
        else:
            self.show_message("You need 200 points to bump a listing.")

    
    @pyqtSlot(str)
    def show_message(self, message):
        msg = QMessageBox()
        msg.setWindowTitle("Message from server")
        msg.setText(message)
        msg.setIcon(QMessageBox.Information)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
        
    @pyqtSlot()
    def show_log_page(self):
        self.stacked_widget.setCurrentWidget(self.log_page)
        
    
    @pyqtSlot()
    def show_dashboard(self):
        self.stacked_widget.setCurrentWidget(self.dashboard_page)
    
    @pyqtSlot(str)
    def update_product_table_request(self, search_term):
        self.send_req({"action" : "show_matching", "search_term" : search_term})
     
    @pyqtSlot(dict)
    def handle_server_p2p_req_message(self, request):
        requester = request["from_user"]
        self.target_ip = request["init_ip"]
        self.target_port = request["init_port"]
        reply = QMessageBox.question(self, "P2P Chat Request", f"{requester} wants to start a chat. Accept?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.send_req({"action" : "p2p_confirmation", "requester" : requester, "response" : 'accept'})
            # self.tabs.setCurrentIndex(3)
            peer_info = {"ip": self.target_ip, "port": self.target_port, "username": requester}
            self.active_peers[requester] = peer_info
            self.add_peer_to_selector(requester)
            threading.Thread(target=self.message_listener_thread, args=(requester,)).start()
            print("recieving on port", self.udp_socket.getsockname()[1], "sending on port", self.target_port)
            
        else:
            self.send_req({"action" : "p2p_confirmation", "response" : 'decline'})
        
            
    @pyqtSlot()
    def send_udp_info(self):
        local_ip = socket.gethostbyname(socket.gethostname())  # Get local IP
        local_port = self.udp_socket.getsockname()[1] # and udp port
        registration_message = {
        "action": "send_udp_info",
        "username": self.username,
        "ip": local_ip,
        "port": local_port  
        }
        self.send_req(registration_message)  # send info to server
        
        
    
    def receive_thread_func(self):
        """Thread to handle receiving messages from the server."""
        buffer = ''
        while True:
            try:
                # Receive data and add to buffer
                data = self.client_socket.recv(1024).decode()
                if not data:
                    print("Connection closed by server")
                    break
                    
                buffer += data
                
                # Process complete messages
                while '\n' in buffer:
                    message, buffer = buffer.split('\n', 1)
                    try:
                        reply = json.loads(message)
                        action = reply["action"]
                        print("Received reply", reply)
                
                        if action == "login":
                            msg = reply["msg"]
                            if msg == "Login Successfull!":
                                # Call show_message on the main thread
                                QMetaObject.invokeMethod(self, "show_dashboard", Qt.QueuedConnection)
                                QMetaObject.invokeMethod(self, "send_udp_info", Qt.QueuedConnection)
                                
                            else:
                                # Show the error message using show_message on the main thread
                                QMetaObject.invokeMethod(self, "show_message", Qt.QueuedConnection, Q_ARG(str, msg))
                                
                        if action == "reg":
                            msg = reply["msg"]
                            if msg == "Account created. Please log in with your new account.":
                                # Call show_message on the main thread
                                QMetaObject.invokeMethod(self, "show_message", Qt.QueuedConnection, Q_ARG(str, msg))
                                QMetaObject.invokeMethod(self, "show_log_page", Qt.QueuedConnection)
                            else:
                                # Show the error message using show_message on the main thread
                                QMetaObject.invokeMethod(self, "show_message", Qt.QueuedConnection, Q_ARG(str, msg))
                                
                       
                        elif action=="display_user":
                            username = reply["username"]
                            self.all_products = reply["content"].copy()
                            QMetaObject.invokeMethod(self, "build_product_table", Qt.QueuedConnection, Q_ARG(tuple, (self.all_products,username)))
                            print(username, "in recieve")
                            self.tabs.setCurrentIndex(0)
            
                        # elif action == "get_msgs" and reply["new"]:
                        #     self.msg_count = 0
                        #     print(reply["content"])
                        
                        # elif action == "new_message":
                        #     self.msg_count += 1
            
                            
                        elif action == "show_matching":
                            '''displays matching products'''
                            self.all_products = reply["content"].copy()
                            QMetaObject.invokeMethod(self, "build_product_table", Qt.QueuedConnection, Q_ARG(tuple, (self.all_products,'')))
                                
                        elif action == "buy":
                            #show confirmation msg on main thread
                            QMetaObject.invokeMethod(self, "show_message", Qt.QueuedConnection, Q_ARG(str, reply["message"]))
                            QMetaObject.invokeMethod(self, "update_dashboard_points", Qt.QueuedConnection, Q_ARG(int, self.points + int(reply["points"])))
                            
                            
                        elif action == "message":
                            QMetaObject.invokeMethod(self, "show_message", Qt.QueuedConnection, Q_ARG(str, reply['message']))
                        elif action == "add":
                            self.sent_add_req = False
                            QMetaObject.invokeMethod(self, "show_message", Qt.QueuedConnection, Q_ARG(str, reply['message']))
                        
                        elif action == "p2p_info":
                            self.target_ip = reply["ip"]
                            self.target_port = reply["port"]
                            self.p2p_reply_recieved.set()
                            
                        elif action == "p2p_req":
                            QMetaObject.invokeMethod(self, "handle_server_p2p_req_message", Qt.QueuedConnection, Q_ARG(dict, reply))
                        
                        elif action == "p2p_conf":
                            response = reply["response"]
                            if response == "accepted":
                                self.p2p_req_reply_recieved.set()
                                QMetaObject.invokeMethod(self, "show_message", Qt.QueuedConnection, Q_ARG(str, "Message request accepted"))
                            else:
                                QMetaObject.invokeMethod(self, "show_message", Qt.QueuedConnection, Q_ARG(str, "Message request declined"))
                            
                        elif action == "show_users":
                            users = reply["users"]
                            QMetaObject.invokeMethod(self, "populate_users_table", Qt.QueuedConnection, Q_ARG(list, users))
                                
                        elif action == "your_info":
                            self.following = reply["following"].copy()
                            self.all_products = reply["all_products"].copy()
                            QMetaObject.invokeMethod(self, "build_product_table", Qt.QueuedConnection, Q_ARG(tuple, (self.all_products,'')))
                            self.products_for_sale = reply["prod_for_sale"].copy()
                            QMetaObject.invokeMethod(self, "update_my_products", Qt.QueuedConnection, Q_ARG(tuple, (self.products_for_sale,)))
                            self.sold_products = reply["your_sold_products"].copy()
                            QMetaObject.invokeMethod(self, "update_sold_products", Qt.QueuedConnection, Q_ARG(tuple, (self.sold_products,)))
                            QMetaObject.invokeMethod(self, "send_req", Qt.QueuedConnection, Q_ARG(dict, {"action" : "show_users"}))
                            self.bought_products = reply["bought_prods"].copy()
                            QMetaObject.invokeMethod(self, "update_products_I_bought", Qt.QueuedConnection, Q_ARG(tuple, (self.bought_products,)))
                            self.points = int(reply["points"]) 
                            QMetaObject.invokeMethod(self, "update_dashboard_points", Qt.QueuedConnection, Q_ARG(int, self.points))
                            
                            
                            
                            
                        elif action == "your_products":
                            self.products_for_sale = reply["content"].copy()
                            QMetaObject.invokeMethod(self, "update_my_products", Qt.QueuedConnection, Q_ARG(tuple, (self.products_for_sale,)))
                            
                        elif action == "your_sold_products":
                            self.sold_products = reply["content"].copy()
                            QMetaObject.invokeMethod(self, "update_sold_products", Qt.QueuedConnection, Q_ARG(tuple, (self.sold_products,)))
                            
                        elif action == "your_bought_products":
                            self.bought_products = reply["content"].copy()
                            QMetaObject.invokeMethod(self, "update_products_I_bought", Qt.QueuedConnection, Q_ARG(tuple, (self.bought_products,)))
                            
                        elif action == "change_currency":
                            self.preffered_currency_multiplier = reply["multiplier"]
                            # Update the product tables with new prices
                            QMetaObject.invokeMethod(self, "build_product_table", Qt.QueuedConnection, Q_ARG(tuple, (self.all_products, '')))
                            QMetaObject.invokeMethod(self, "update_my_products", Qt.QueuedConnection, Q_ARG(tuple, (self.products_for_sale,)))
                            QMetaObject.invokeMethod(self, "update_sold_products", Qt.QueuedConnection, Q_ARG(tuple, (self.sold_products,)))
                            QMetaObject.invokeMethod(self, "update_products_I_bought", Qt.QueuedConnection, Q_ARG(tuple, (self.bought_products,)))
        
                            QMetaObject.invokeMethod(self,"show_message",Qt.QueuedConnection,Q_ARG(str, f"Currency changed to {reply.get('currency', 'selected currency')} and prices updated!"))
         
                        elif action == "follow" :
                            print("follow")
                        

                    except json.JSONDecodeError as e:
                            print(f"Invalid JSON received: {e}")
                            continue
                            
            except socket.error as e:
                print(f"Socket error: {e}")
                break
            
    
            
                    

app = QApplication(sys.argv)
window = ClientWindow()
window.show()
sys.exit(app.exec_())

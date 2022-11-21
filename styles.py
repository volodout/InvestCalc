style_light = '''
QPushButton{
    background: #ffc800;
    border-radius: 5px;
    color: #000
}
QPushButton#btn_new, QPushButton#btn_forecast, QPushButton#btn_statistic{
    border-radius: 20px;
    color: #000
}
QPushButton:hover{
    background: #fff700;
}
QHeaderView::section{
    padding-left: 4px;
    border: 1px solid #6c6c6c;
    font-size: 20px
}
QComboBox QAbstractItemView{
    border: 2px solid #ffc800;
    selection-background-color: #ffc800;
}
'''


style_dark = '''
QWidget{
    background: #323232;
    color: #fff
}
QLineEdit{
    background-color: #4d4d4d;
    padding: 1px;
    border-style: solid;
    border: 1px solid #1e1e1e;
    border-radius: 5;
}
QComboBox{
    selection-background-color: #ffaa00;
    background-color: #565656;
    border-style: solid;
    border: 1px solid #1e1e1e;
    border-radius: 5;
}
QComboBox QAbstractItemView{
    border: 2px solid darkgray;
    selection-background-color: darkgray;
}
QScrollBar:vertical{
      background: #121212;
      width: 7px;
      margin: 16px 0 16px 0;
      border: 1px solid #222222;
}
QHeaderView::section{
    background-color: #505050
}
QWidget:item:selected{
    background-color: darkgrey;
}
''' + style_light + '''
QComboBox QAbstractItemView{
    border: 2px solid darkgray;
    selection-background-color: darkgray;
}
'''


style_continue = '''
QPushButton#btn_continue{
    color: #000;
    background: gray;
    border-radius: 5px;
}
'''

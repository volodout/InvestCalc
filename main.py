import sys
import sqlite3
import requests
from bs4 import BeautifulSoup
from PyQt5.QtGui import QIcon, QFont
from PyQt5.Qt import Qt
from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget, QApplication, QTableWidgetItem, QMessageBox, QPushButton
from PyQt5.QtWinExtras import QtWin

from wind import Ui_Form
from add_edit import Ui_Form_AddEdit
from forecast import Ui_Form_Forecast
from statistic import Ui_Stat
from styles import style_continue
from styles import style_dark
from styles import style_light

myappid = 'mycompany.myproduct.subproduct.version'
QtWin.setCurrentProcessExplicitAppUserModelID(myappid)

signs = '₽$€'
rate = ('в рублях', 'в долларах', 'в евро')
DOLLAR_RUB = 'https://clck.ru/32bxkY'
EURO_RUB = 'https://clck.ru/32by57'
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
                         ' Chrome/104.0.5112.124 Safari/537.36'}
buttons_edit = []
buttons_del = []
usd0, eur0 = 0., 0.  # значения курса валют
balances = 0
theme = style_dark


class FirstWindow(QWidget, Ui_Form):  # главное окно
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        global usd0, eur0, balances, theme
        self.con = sqlite3.connect('assets.db')
        self.cur = self.con.cursor()
        self.them = theme

        self.btn_new.clicked.connect(self.add_new)
        self.btn_forecast.clicked.connect(self.forecast)
        self.btn_statistic.clicked.connect(self.statistic)
        self.currency_combobox.addItems(rate)
        self.currency_combobox.currentIndexChanged.connect(self.balance)
        self.btn_theme.clicked.connect(self.theme_change)
        self.btn_new.setIcon(QIcon('pictures/icons/add.png'))
        self.btn_forecast.setIcon(QIcon('pictures/icons/forecast.png'))
        self.btn_theme.setIcon(QIcon('pictures/icons/sun.png'))
        self.btn_statistic.setIcon((QIcon('pictures/icons/info.png')))

        self.select_data()
        self.currency()
        self.balance()
        self.setFixedSize(666, 650)

        self.setStyleSheet(theme)

    def theme_change(self):
        global theme
        if theme == style_dark:
            theme = 'Fusion'
            theme = style_light
            self.btn_theme.setIcon(QIcon('pictures/icons/moon.webp'))
            print('light')
        else:
            theme = style_dark
            self.btn_theme.setIcon(QIcon('pictures/icons/sun.png'))
            print('dark')
        self.setStyleSheet(theme)

    def add_new(self):
        self.add_form = AddWindow()
        self.add_form.updateSignal.connect(self.update)
        self.add_form.show()

    def delete(self):  # удаление данных
        name = self.tableWidget.item(buttons_del.index(self.sender().objectName()), 0).text()
        valid = QMessageBox.question(self, 'Удалить',
                                     f'Действительно удалить элемент "{name}"? Отменить это действие будет невозможно.',
                                     QMessageBox.Ok | QMessageBox.Cancel)

        if valid == QMessageBox.Ok:
            self.cur.execute("DELETE FROM asset WHERE title = ?", (name,))
            self.con.commit()
            self.update()

    def edit(self):
        name = self.tableWidget.item(buttons_edit.index(self.sender().objectName()), 0).text()
        query = 'SELECT id FROM asset WHERE title = ?'
        num = self.cur.execute(query, (name,)).fetchone()[0]
        self.edit_form = EditWindow(num)
        self.edit_form.show()
        self.edit_form.updateSignal.connect(self.update)

    def forecast(self):
        self.forecast_form = ForecastWindow()
        self.forecast_form.show()

    def statistic(self):
        self.statistic_form = StatisticWindow()
        self.statistic_form.show()

    def select_data(self):  # заполнение таблицы данными
        res = self.con.cursor().execute("SELECT title, cost, percent, currency FROM asset").fetchall()
        kinds = [' Акция ', ' Вклад ']
        self.tableWidget.setColumnCount(6)
        self.tableWidget.setRowCount(len(res))

        for i, row in enumerate(res):
            self.tableWidget.setItem(i, 0, QTableWidgetItem(str(row[0])))
            rowint = int(row[1]) if float(row[1]) % 1 == 0 else float(row[1])
            self.tableWidget.setItem(i, 1, QTableWidgetItem(str(rowint) + ' ' + signs[row[3] - 1]))
            rowint = int(row[2]) if float(row[2]) % 1 == 0 else float(row[2])
            self.tableWidget.setItem(i, 2, QTableWidgetItem(str(rowint) + '%'))
            q = self.cur.execute(f'SELECT kind FROM asset WHERE title = "{row[0]}"').fetchone()[0]
            self.tableWidget.setItem(i, 3, QTableWidgetItem(str(kinds[q - 1])))
            self.tableWidget.setCellWidget(i, 4,
                                           QPushButton(objectName=f'btn_tabl_{i}', clicked=self.edit))
            self.tableWidget.setCellWidget(i, 5,
                                           QPushButton(objectName=f'btn_tabl_{i}', clicked=self.delete))

            self.tableWidget.cellWidget(i, 4).setIcon(QIcon('pictures/icons/edit.png'))
            self.tableWidget.cellWidget(i, 5).setIcon(QIcon('pictures/icons/delete.png'))

            buttons_edit.append(self.tableWidget.cellWidget(i, 4).objectName())
            buttons_del.append(self.tableWidget.cellWidget(i, 5).objectName())

        self.tableWidget.setHorizontalHeaderLabels(['Название', 'Стоимость', 'Доходность', 'Тип', '', ''])
        self.tableWidget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.tableWidget.resizeColumnToContents(3)
        self.tableWidget.resizeColumnToContents(4)
        self.tableWidget.resizeColumnToContents(5)
        self.tableWidget.horizontalHeader().setFont(QFont('Bahnschrift SemiBold', 15))
        self.setStyleSheet(theme)

    def balance(self):  # итоговый баланс
        global balances
        q = 'SELECT cost FROM asset WHERE currency = (SELECT id FROM currencies WHERE sign = ?)'

        rub = sum([elem[0] for elem in self.cur.execute(q, ('RUB',)).fetchall()])
        usd = sum([elem[0] for elem in self.cur.execute(q, ('USD',)).fetchall()])
        eur = sum([elem[0] for elem in self.cur.execute(q, ('EUR',)).fetchall()])

        balance = rub + usd * float(self.usd_course.text()[:-1]) + eur * float(
            self.eur_course.text()[:-1])
        if self.currency_combobox.currentIndex() == 0:
            value = round(float(balance), 2)
            value1 = int(value) if value % 1 == 0 else value
            self.label_2.setText(str(value1) + ' ₽')
            balances = value1
        elif self.currency_combobox.currentIndex() == 1:
            value = round(balance / float(self.usd_course.text()[:-1]), 2)
            value1 = int(value) if value % 1 == 0 else value
            self.label_2.setText(str(value1) + ' $')
        elif self.currency_combobox.currentIndex() == 2:
            value = round(balance / float(self.eur_course.text()[:-1]), 2)
            value1 = int(value) if value % 1 == 0 else value
            self.label_2.setText(str(value1) + ' €')

    def currency(self):  # курс валют
        global usd0, eur0
        full_page = requests.get(DOLLAR_RUB, headers=headers)
        soup = BeautifulSoup(full_page.content, 'html.parser')
        convert = soup.findAll("span", {"class": 'DFlfde SwHCTb', 'data-precision': 2})
        self.usd_course.setText(str(convert[0].text.replace(',', '.')) + ' ' + '$')
        usd0 = float(convert[0].text.replace(',', '.'))

        full_page = requests.get(EURO_RUB, headers=headers)
        soup = BeautifulSoup(full_page.content, 'html.parser')
        convert = soup.findAll("span", {"class": 'DFlfde SwHCTb', 'data-precision': 2})
        self.eur_course.setText(str(convert[0].text.replace(',', '.')) + ' ' + '€')
        eur0 = float(convert[0].text.replace(',', '.'))

    def update(self):
        buttons_edit.clear()
        buttons_del.clear()
        self.select_data()
        self.balance()
        self.setStyleSheet(theme)


class AddWindow(QWidget, Ui_Form_AddEdit):  # окно добавления данных
    updateSignal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.con = sqlite3.connect('assets.db')
        self.cur = self.con.cursor()
        self.comboBox.addItems(['---', 'RUB', 'USD', 'EUR'])
        self.comboBox_type.addItems(['---', 'Акция', 'Облигация/вклад'])
        self.btn_continue.clicked.connect(self.add_new)

        self.name.textChanged.connect(self.change)
        self.cost.textChanged.connect(self.change)
        self.percent.textChanged.connect(self.change)
        self.comboBox.currentTextChanged.connect(self.change)
        self.comboBox_type.currentTextChanged.connect(self.change)
        self.btn = False

        self.setFixedSize(700, 155)

        self.setStyleSheet(theme)
        self.btn_continue.setStyleSheet(style_continue)

    def add_new(self):
        name = self.name.text()
        cost = self.cost.text().replace(',', '.')
        perc = self.percent.text().replace(',', '.')

        try:
            if self.name.text().isdigit():
                raise TitleError
            float(cost)
            float(perc)
            currency = self.cur.execute('SELECT id FROM currencies WHERE sign = ?',
                                        (self.comboBox.currentText(),)).fetchone()[0]
            type_asset = self.cur.execute('SELECT id FROM types WHERE type = ?',
                                          (self.comboBox_type.currentText(),)).fetchone()[0]
            que = 'INSERT INTO asset(title,cost,percent,currency, kind) VALUES(?,?,?,?,?)'
            self.con.cursor().execute(que, (name, cost, perc, currency, type_asset))
            self.con.commit()
            self.updateSignal.emit()

            self.name.clear()
            self.cost.clear()
            self.percent.clear()

            self.close()
        except TitleError:
            self.label.setText('Ошибка. Название должно включать в себя буквы.')
        except ValueError:
            self.label.setText('Ошибка. Стоимость и доходность должны быть числами.')
        except sqlite3.IntegrityError:
            self.label.setText('Ошибка. Актив с таким названием уже существует.')

    def change(self):  # изменение кнопки
        if self.name.text() and self.cost.text() and self.percent.text():
            if self.comboBox.currentIndex() > 0 and self.comboBox_type.currentIndex() > 0:
                self.btn_continue.setEnabled(True)
                self.btn = True
                self.btn_continue.setStyleSheet(theme)
            else:
                self.btn_continue.setDisabled(True)
                self.btn = False
                self.btn_continue.setStyleSheet(style_continue)
        else:
            self.btn_continue.setDisabled(True)
            self.btn = False
            self.btn_continue.setStyleSheet(style_continue)

    def keyPressEvent(self, event):  # обработка клавиатуры
        if self.btn:
            if event.key() == Qt.Key_Enter or event.key() == Qt.Key_Enter - 1:
                self.add_new()
        if event.key() == Qt.Key_Escape:
            self.close()
        event.accept()


class EditWindow(QWidget, Ui_Form_AddEdit):  # окно изменения данных
    updateSignal = pyqtSignal()

    def __init__(self, num):
        super().__init__()
        self.setupUi(self)
        self.con = sqlite3.connect('assets.db')
        self.cur = self.con.cursor()
        self.setWindowTitle('Изменить')

        self.comboBox.addItems(['RUB', 'USD', 'EUR'])
        self.comboBox_type.addItems(['Акция', 'Облигация/вклад'])

        self.num = num
        self.btn_continue.clicked.connect(self.edit)
        self.name.textChanged.connect(self.change)
        self.cost.textChanged.connect(self.change)
        self.percent.textChanged.connect(self.change)
        self.comboBox.currentTextChanged.connect(self.change)
        self.btn = False

        self.setFixedSize(700, 155)

        title = 'SELECT title FROM asset WHERE id = ?'
        cost = 'SELECT cost FROM asset WHERE id = ?'
        percent = 'SELECT percent FROM asset WHERE id = ?'
        curr = 'SELECT currency FROM asset WHERE id = ?'
        type_asset = 'SELECT kind FROM asset WHERE id = ?'
        self.name.setText(self.cur.execute(title, (num,)).fetchone()[0])
        self.cost.setText(str(self.cur.execute(cost, (num,)).fetchone()[0]))
        self.percent.setText(str(self.cur.execute(percent, (num,)).fetchone()[0]))
        self.comboBox.setCurrentIndex(int(self.cur.execute(curr, (num,)).fetchone()[0]) - 1)
        self.comboBox_type.setCurrentIndex(int(self.cur.execute(type_asset, (num,)).fetchone()[0]) - 1)
        self.change()

        self.setStyleSheet(theme)

    def edit(self):
        name = self.name.text()
        cost = self.cost.text()
        perc = self.percent.text()

        try:
            float(cost)
            float(perc)
            if self.name.text().isdigit():
                raise TitleError
            currency = self.cur.execute('SELECT id FROM currencies WHERE sign = ?',
                                        (self.comboBox.currentText(),)).fetchone()[0]
            type_asset = self.cur.execute('SELECT id FROM types WHERE type = ?',
                                          (self.comboBox_type.currentText(),)).fetchone()[0]
            que = 'UPDATE asset SET title = ?, cost = ?, percent = ?, currency = ?, kind = ? WHERE id = ?'
            self.con.cursor().execute(que, (name, cost, perc, currency, type_asset, self.num))
            self.con.commit()
            self.updateSignal.emit()

            self.name.clear()
            self.cost.clear()
            self.percent.clear()

            self.close()
        except TitleError:
            self.label.setText('Ошибка. Название должно включать в себя буквы.')
        except ValueError:
            self.label.setText('Ошибка. Введены неверные значения.')
        except sqlite3.IntegrityError:
            self.label.setText('Ошибка. Актив с таким названием уже существует.')

    def change(self):  # изменение кнопки
        if self.name.text() and self.cost.text() and self.percent.text():
            self.btn_continue.setEnabled(True)
            self.btn = True
            self.btn_continue.setStyleSheet(theme)
        else:
            self.btn_continue.setDisabled(True)
            self.btn = False
            self.btn_continue.setStyleSheet(style_continue)

    def keyPressEvent(self, event):  # обработка клавиатуры
        if self.btn:
            if event.key() == Qt.Key_Enter or event.key() == Qt.Key_Enter - 1:
                self.edit()
        if event.key() == Qt.Key_Escape:
            self.close()
        event.accept()


class ForecastWindow(QWidget, Ui_Form_Forecast):  # окно прогнозов
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.con = sqlite3.connect('assets.db')
        self.cur = self.con.cursor()

        self.horizontalSlider.valueChanged.connect(self.time)
        self.horizontalSlider.valueChanged.connect(self.change)
        self.horizontalSlider.valueChanged.connect(self.balance)
        self.currency_combobox.currentIndexChanged.connect(self.balance)
        self.currency_combobox.addItems(rate)
        self.allcosts = []
        self.update()
        self.costs()

        self.setFixedSize(500, 600)

        self.setStyleSheet(theme)

    def table(self):  # заполнение таблицы
        res = self.con.cursor().execute("SELECT title, cost, percent, currency FROM asset").fetchall()
        self.tableWidget.setColumnCount(3)
        self.tableWidget.setRowCount(len(res))

        for i, row in enumerate(res):
            self.tableWidget.setItem(i, 0, QTableWidgetItem(str(row[0])))
            self.tableWidget.setItem(i, 1, QTableWidgetItem(str(int(row[1])) + ' ' + signs[row[3] - 1]))
            self.tableWidget.setItem(i, 2, QTableWidgetItem(str(int(row[2])) + '%'))

        self.tableWidget.setHorizontalHeaderLabels(['Название', 'Стоимость', 'Доходность'])
        self.tableWidget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

    def balance(self):  # баланс
        balance = 0.
        try:
            res = self.cur.execute('SELECT * FROM asset').fetchall()
            rubs, usds, eurs = [], [], []

            for i in range(len(res)):
                if self.tableWidget.item(i, 1).text()[-1] == '₽':
                    rubs.append(float(self.tableWidget.item(i, 1).text()[:-2]))
                elif self.tableWidget.item(i, 1).text()[-1] == '$':
                    usds.append(float(self.tableWidget.item(i, 1).text()[:-2]))
                elif self.tableWidget.item(i, 1).text()[-1] == '€':
                    eurs.append(float(self.tableWidget.item(i, 1).text()[:-2]))
            balance = sum(rubs) + sum(usds) * usd0 + sum(eurs) * eur0
            print(balance)
        except UnboundLocalError:
            pass
        except Exception:
            pass

        if self.currency_combobox.currentIndex() == 0:
            value = round(float(balance), 2)
            value1 = int(value) if value % 1 == 0 else value
            self.label.setText(str(value1) + ' ₽')
        elif self.currency_combobox.currentIndex() == 1:
            value = round(balance / usd0, 2)
            value1 = int(value) if value % 1 == 0 else value
            self.label.setText(str(value1) + ' $')
        elif self.currency_combobox.currentIndex() == 2:
            value = round(balance / eur0, 2)
            value1 = int(value) if value % 1 == 0 else value
            self.label.setText(str(value1) + ' €')

    def costs(self):  # заполнение списка начальных стоимостей
        for i in range(self.tableWidget.rowCount()):
            price = float(self.tableWidget.item(i, 1).text()[:-2])
            if price % 1 == 0:
                self.allcosts.append(int(price))
            else:
                self.allcosts.append(price)

    def change(self, value):  # изменение цен в таблице
        for i in range(self.tableWidget.rowCount()):
            sign = self.tableWidget.item(i, 1).text()[-1]
            if value != 0:
                cost = self.allcosts[i]
                perc = float(self.tableWidget.item(i, 2).text()[:-1])
                res = round((cost + (cost * (perc / 100) / 12 * value)), 2)
                resint = int(res) if res % 1 == 0 else res
                self.tableWidget.setItem(i, 1, QTableWidgetItem(str(resint) + ' ' + sign))
            else:
                self.tableWidget.setItem(i, 1, QTableWidgetItem(str(self.allcosts[i]) + ' ' + sign))

    def time(self, value):  # строка времени
        yearmonth = [value // 12, value % 12]
        if value == 0:
            self.label_2.setText('')
        elif value < 12:
            if value == 1:
                m = ' месяц'
            elif value in range(2, 5):
                m = ' месяца'
            else:
                m = ' месяцев'
            self.label_2.setText(str(value) + m)
        else:
            if yearmonth[0] == 1:
                y = ' год '
            elif yearmonth[0] in range(2, 5):
                y = ' года '
            else:
                y = ' лет '

            if yearmonth[1] != 0:
                if yearmonth[1] == 1:
                    m = ' месяц'
                elif yearmonth[1] in range(2, 5):
                    m = ' месяца'
                else:
                    m = ' месяцев'

                self.label_2.setText(str(yearmonth[0]) + y + str(yearmonth[1]) + m)
            else:
                self.label_2.setText(str(yearmonth[0]) + y)

    def update(self):
        self.table()
        self.balance()


class StatisticWindow(QWidget, Ui_Stat):  # окно статистики
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.con = sqlite3.connect('assets.db')
        self.cur = self.con.cursor()
        self.setStyleSheet(theme)

        res = [i[0] for i in self.cur.execute('SELECT kind FROM asset').fetchall()]
        if res.count(1) / len(res) > 0.6:
            self.level.setText('РИСКОВАННЫЙ')
            self.level.setStyleSheet('color:red')
        elif res.count(1) / len(res) < 0.4:
            self.level.setText('КОНСЕРВАТИВНЫЙ')
            self.level.setStyleSheet('color:#ffc800')

        else:
            self.level.setText('УМЕРЕННЫЙ')
            self.level.setStyleSheet('color:lime')

        self.stocks.setText(f'{round(res.count(1) / len(res) * 100, 2)}%  ({res.count(1)}/{len(res)})')
        self.bonds.setText(f'{round(res.count(2) / len(res) * 100, 2)}%  ({res.count(2)}/{len(res)})')

        rubs = sum(i[0] for i in self.cur.execute('SELECT cost FROM asset WHERE currency = 1').fetchall())
        usds = sum(i[0] for i in self.cur.execute('SELECT cost FROM asset WHERE currency = 2').fetchall())
        eurs = sum(i[0] for i in self.cur.execute('SELECT cost FROM asset WHERE currency = 3').fetchall())
        self.rub.setText(f'{round(rubs / balances * 100, 2)}%  ({rubs}₽)')
        self.usd.setText(f'{round(usds * usd0 / balances * 100, 2)}%  ({usds}$)')
        self.eur.setText(f'{round(eurs * eur0 / balances * 100, 2)}%  ({eurs}€)')

        self.setFixedSize(450, 340)


class TitleError(Exception):
    pass


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = FirstWindow()
    app.setWindowIcon(QIcon('icon.jpg'))
    ex.show()
    sys.excepthook = except_hook
    sys.exit(app.exec())

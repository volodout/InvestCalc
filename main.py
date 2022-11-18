import sys
import sqlite3
import requests
from PyQt5.QtGui import QIcon
from PyQt5.Qt import Qt
from bs4 import BeautifulSoup
from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget, QApplication, QTableWidgetItem, QMessageBox, QPushButton
from PyQt5.QtWinExtras import QtWin

from wind import Ui_Form
from add_new import Ui_Form_AddEdit
from forecast import Ui_Form_Forecast
from styles import style_continue
from styles import style

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
usd0, eur0 = 0., 0.  # значения валют


class FirstWindow(QWidget, Ui_Form):  # главное окно
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        global usd0, eur0
        self.con = sqlite3.connect('stocks.db')
        self.cur = self.con.cursor()

        self.btn_new.clicked.connect(self.add_new)
        self.btn_forecast.clicked.connect(self.forecast)
        self.currency_combobox.addItems(rate)
        self.currency_combobox.currentIndexChanged.connect(self.balance)
        self.btn_new.setIcon(QIcon('add.png'))
        self.btn_forecast.setIcon(QIcon('forecast.png'))

        self.select_data()
        self.currency()
        self.balance()
        self.setFixedSize(610, 650)

        self.setStyleSheet(style)

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
            self.cur.execute("DELETE FROM stock WHERE title = ?", (name,))
            self.con.commit()
            self.update()

    def edit(self):
        name = self.tableWidget.item(buttons_edit.index(self.sender().objectName()), 0).text()
        query = 'SELECT id FROM stock WHERE title = ?'
        num = self.cur.execute(query, (name,)).fetchone()[0]
        self.edit_form = EditWindow(num)
        self.edit_form.show()
        self.edit_form.updateSignal.connect(self.update)

    def forecast(self):
        self.forecast_form = ForecastWindow()
        self.forecast_form.show()

    def select_data(self):  # заполнение таблицы данными
        res = self.con.cursor().execute("SELECT title, cost, percent, currency FROM stock").fetchall()
        self.tableWidget.setColumnCount(5)
        self.tableWidget.setRowCount(len(res))

        for i, row in enumerate(res):
            self.tableWidget.setItem(i, 0, QTableWidgetItem(str(row[0])))
            rowint = int(row[1]) if float(row[1]) % 1 == 0 else float(row[1])
            self.tableWidget.setItem(i, 1, QTableWidgetItem(str(rowint) + ' ' + signs[row[3] - 1]))
            rowint = int(row[2]) if float(row[2]) % 1 == 0 else float(row[2])
            self.tableWidget.setItem(i, 2, QTableWidgetItem(str(rowint) + '%'))
            self.tableWidget.setCellWidget(i, 3,
                                           QPushButton(objectName=f'btn_tabl_{i}', clicked=self.edit))
            self.tableWidget.setCellWidget(i, 4,
                                           QPushButton(objectName=f'btn_tabl_{i}', clicked=self.delete))

            self.tableWidget.cellWidget(i, 3).setIcon(QIcon('edit.png'))
            self.tableWidget.cellWidget(i, 4).setIcon(QIcon('delete.png'))

            buttons_edit.append(self.tableWidget.cellWidget(i, 3).objectName())
            buttons_del.append(self.tableWidget.cellWidget(i, 4).objectName())
        print(buttons_edit)

        self.tableWidget.setHorizontalHeaderLabels(['Название', 'Стоимость', 'Доходность', '', ''])
        self.tableWidget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.tableWidget.resizeColumnToContents(3)
        self.tableWidget.resizeColumnToContents(4)

    def balance(self):  # итоговый баланс
        q = 'SELECT cost FROM stock WHERE currency = (SELECT id FROM currencies WHERE sign = ?)'

        rub = sum([elem[0] for elem in self.cur.execute(q, ('RUB',)).fetchall()])
        usd = sum([elem[0] for elem in self.cur.execute(q, ('USD',)).fetchall()])
        eur = sum([elem[0] for elem in self.cur.execute(q, ('EUR',)).fetchall()])

        balance = rub + usd * float(self.usd_course.text()[:-1]) + eur * float(
            self.eur_course.text()[:-1])
        if self.currency_combobox.currentIndex() == 0:
            value = round(float(balance), 2)
            value1 = int(value) if value % 1 == 0 else value
            self.label_2.setText(str(value1) + ' ₽')
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


class AddWindow(QWidget, Ui_Form_AddEdit):  # окно добавления данных
    updateSignal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.con = sqlite3.connect('stocks.db')
        self.cur = self.con.cursor()
        self.comboBox.addItems(['---', 'RUB', 'USD', 'EUR'])
        self.btn_continue.clicked.connect(self.add_new)

        self.name.textChanged.connect(self.change)
        self.cost.textChanged.connect(self.change)
        self.percent.textChanged.connect(self.change)
        self.comboBox.currentTextChanged.connect(self.change)
        self.btn = False

        self.setFixedSize(600, 155)

        self.setStyleSheet(style_continue)

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
            que = 'INSERT INTO stock(title,cost,percent,currency) VALUES(?,?,?,?)'
            self.con.cursor().execute(que, (name, cost, perc, currency))
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
        if self.name.text() and self.cost.text() and self.percent.text() and self.comboBox.currentIndex() > 0:
            self.btn_continue.setEnabled(True)
            self.btn = True
            self.setStyleSheet(style)
        else:
            self.btn_continue.setDisabled(True)
            self.btn = False
            self.setStyleSheet(style_continue)

    def keyPressEvent(self, event):  # обработка клавиатуры
        print(event.key())
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
        self.con = sqlite3.connect('stocks.db')
        self.cur = self.con.cursor()
        self.comboBox.addItems(['RUB', 'USD', 'EUR'])
        self.num = num
        self.btn_continue.clicked.connect(self.edit)
        self.name.textChanged.connect(self.change)
        self.cost.textChanged.connect(self.change)
        self.percent.textChanged.connect(self.change)
        self.comboBox.currentTextChanged.connect(self.change)
        self.btn = False

        self.setFixedSize(560, 144)

        title = 'SELECT title FROM stock WHERE id = ?'
        cost = 'SELECT cost FROM stock WHERE id = ?'
        percent = 'SELECT percent FROM stock WHERE id = ?'

        self.name.setText(self.cur.execute(title, (num,)).fetchone()[0])
        self.cost.setText(str(self.cur.execute(cost, (num,)).fetchone()[0]))
        self.percent.setText(str(self.cur.execute(percent, (num,)).fetchone()[0]))
        q = 'SELECT currency FROM stock WHERE id = ?'
        self.comboBox.setCurrentIndex(int(self.cur.execute(q, (num,)).fetchone()[0]) - 1)
        self.change()

        self.setStyleSheet(style)

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
            que = 'UPDATE stock SET title = ?, cost = ?, percent = ?, currency = ? WHERE id = ?'
            self.con.cursor().execute(que, (name, cost, perc, currency, self.num))
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
        self.setStyleSheet(style)
        if self.name.text() and self.cost.text() and self.percent.text():
            self.btn_continue.setEnabled(True)
            self.btn = True
            self.setStyleSheet(style)
        else:
            self.btn_continue.setEnabled(False)
            self.btn = False
            self.setStyleSheet(style_continue)

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
        self.con = sqlite3.connect('stocks.db')
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

        self.setStyleSheet(style)

    def table(self):  # заполнение таблицы
        res = self.con.cursor().execute("SELECT title, cost, percent, currency FROM stock").fetchall()
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
            res = self.cur.execute('SELECT * FROM stock').fetchall()
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


class TitleError(Exception):
    pass


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = FirstWindow()
    app.setWindowIcon(QIcon('logo.jpg'))
    ex.show()
    sys.excepthook = except_hook
    sys.exit(app.exec())

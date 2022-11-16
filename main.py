import sys
import sqlite3
import requests
from PyQt5.QtGui import QIcon
from bs4 import BeautifulSoup
from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget, QApplication, QTableWidgetItem, QMessageBox, QButtonGroup, QPushButton

from wind import Ui_Form
from add_new import Ui_Form_Add
from forecast import Ui_Form_Forecast

signs = '₽$€'
rate = ('в рублях', 'в долларах', 'в евро')
DOLLAR_RUB = 'https://clck.ru/32bxkY'
EURO_RUB = 'https://clck.ru/32by57'
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
                         ' Chrome/104.0.5112.124 Safari/537.36'}
buttons_edit = []
buttons_del = []
usd0, eur0 = 0., 0.  # значения валют


class FirstWindow(QWidget, Ui_Form):
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
        self.buttons_edit = QButtonGroup()
        self.buttons_delete = QButtonGroup()

        self.select_data()
        self.currency()
        self.balance()
        self.setFixedSize(600, 645)

    def add_new(self):
        self.add_form = AddWindow()
        self.add_form.updateSignal.connect(self.update)
        self.add_form.show()

    def delete(self):
        name = self.tableWidget.item(buttons_del.index(self.sender().objectName()), 0).text()
        self.delete_form = DeleteWindow(name)
        self.delete_form.show()
        self.delete_form.updateSignal.connect(self.update)

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

    def select_data(self):
        res = self.con.cursor().execute("SELECT title, cost, percent, currency FROM stock").fetchall()
        self.tableWidget.setColumnCount(5)
        self.tableWidget.setRowCount(len(res))

        for i, row in enumerate(res):
            self.tableWidget.setItem(i, 0, QTableWidgetItem(str(row[0])))
            self.tableWidget.setItem(i, 1, QTableWidgetItem(str(int(row[1])) + ' ' + signs[row[3] - 1]))
            self.tableWidget.setItem(i, 2, QTableWidgetItem(str(int(row[2])) + '%'))
            self.tableWidget.setCellWidget(i, 3,
                                           QPushButton(text='Изменить', objectName=f'btn_tabl_{i}', clicked=self.edit))
            self.tableWidget.setCellWidget(i, 4,
                                           QPushButton(text='Удалить', objectName=f'btn_tabl_{i}', clicked=self.delete))

            self.tableWidget.cellWidget(i, 3).setIcon(QIcon('edit.png'))
            self.tableWidget.cellWidget(i, 4).setIcon(QIcon('delete.png'))

            self.buttons_edit.addButton(self.tableWidget.cellWidget(i, 3), id=i)
            self.buttons_delete.addButton(self.tableWidget.cellWidget(i, 4), id=i)

            buttons_edit.append(self.tableWidget.cellWidget(i, 3).objectName())
            buttons_del.append(self.tableWidget.cellWidget(i, 4).objectName())

        self.tableWidget.setHorizontalHeaderLabels(['Название', 'Стоимость', 'Доходность', '', ''])
        self.tableWidget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

    def balance(self):
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

    def currency(self):
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
        self.select_data()
        self.balance()


class AddWindow(QWidget, Ui_Form_Add):
    updateSignal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.con = sqlite3.connect('stocks.db')
        self.cur = self.con.cursor()
        self.comboBox.addItems(['RUB', 'USD', 'EUR'])
        self.pushButton.clicked.connect(self.add_new)

    def add_new(self):
        name = self.name.text()
        cost = self.cost.text().replace(',', '.')
        perc = self.percent.text().replace(',', '.')

        try:
            if self.name.text().isdigit():
                assert ValueError
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
        except ValueError:
            self.label.setText('Ошибка. Введены неверные значения.')
        except sqlite3.IntegrityError:
            self.label.setText('Ошибка. Актив с таким названием уже существует.')


class DeleteWindow(QWidget):
    updateSignal = pyqtSignal()

    def __init__(self, name):
        super().__init__()

        self.con = sqlite3.connect('stocks.db')
        self.cur = self.con.cursor()
        self.name = name
        self.delete()

    def delete(self):
        valid = QMessageBox.question(
            self,
            f'Действительно удалить элемент "{self.name}"?',
            ' Отменить это действие будет невозможно.',
            QMessageBox.Yes, QMessageBox.No)
        if valid == QMessageBox.Yes:
            self.cur.execute("DELETE FROM stock WHERE title = ?", (self.name,))
            self.con.commit()
        self.updateSignal.emit()
        self.close()


class EditWindow(QWidget, Ui_Form_Add):
    updateSignal = pyqtSignal()

    def __init__(self, num):
        super().__init__()
        self.setupUi(self)
        self.con = sqlite3.connect('stocks.db')
        self.cur = self.con.cursor()
        self.comboBox.addItems(['RUB', 'USD', 'EUR'])
        self.num = num
        self.pushButton.clicked.connect(self.edit)

        title = 'SELECT title FROM stock WHERE id = ?'
        cost = 'SELECT cost FROM stock WHERE id = ?'
        percent = 'SELECT percent FROM stock WHERE id = ?'

        self.name.setText(self.cur.execute(title, (num,)).fetchone()[0])
        self.cost.setText(str(self.cur.execute(cost, (num,)).fetchone()[0]))
        self.percent.setText(str(self.cur.execute(percent, (num,)).fetchone()[0]))
        q = 'SELECT currency FROM stock WHERE id = ?'
        self.comboBox.setCurrentIndex(int(self.cur.execute(q, (num,)).fetchone()[0]) - 1)

    def edit(self):
        name = self.name.text()
        cost = self.cost.text()
        perc = self.percent.text()

        try:
            float(cost)
            float(perc)
            if self.name.text().isdigit():
                assert ValueError
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
        except ValueError:
            self.label.setText('Ошибка. Введены неверные значения.')
        except sqlite3.IntegrityError:
            self.label.setText('Ошибка. Актив с таким названием уже существует.')


class ForecastWindow(QWidget, Ui_Form_Forecast):
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

    def balance(self):
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
            print(rubs, usds, eurs)
            print(usd0)
            balance = sum(rubs) + sum(usds) * usd0 + sum(eurs) * eur0
            print(balance)
        except AttributeError:
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

    def costs(self):  # список начальных стоимостей
        for i in range(self.tableWidget.rowCount()):
            self.allcosts.append(float(self.tableWidget.item(i, 1).text()[:-2]))

    def change(self, value):
        for i in range(self.tableWidget.rowCount()):
            sign = self.tableWidget.item(i, 1).text()[-1]
            if value != 0:
                cost = self.allcosts[i]
                perc = float(self.tableWidget.item(i, 2).text()[:-1])
                res = round((cost + (cost * (perc / 100) / 12 * value)), 2)
                self.tableWidget.setItem(i, 1, QTableWidgetItem(str(res) + ' ' + sign))
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


def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = FirstWindow()
    ex.show()
    sys.excepthook = except_hook
    sys.exit(app.exec())

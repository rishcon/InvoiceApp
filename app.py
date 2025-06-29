#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import sys
import json
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QSplitter, QWidget, QVBoxLayout, QFormLayout, QHBoxLayout,
    QLineEdit, QTableWidget, QTableWidgetItem, QPushButton, QFileDialog,
    QMessageBox, QLabel, QDateEdit, QSpinBox, QToolBar, QAction, QGroupBox,
    QHeaderView, QAbstractItemView, QStatusBar, QFrame
)
from PyQt5.QtCore import Qt, QDate, QSize
from PyQt5.QtGui import QPalette, QColor, QIcon, QFont
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Image, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Регистрация шрифта для кириллицы
font_path = r"C:\Windows\Fonts\arial.ttf"
pdfmetrics.registerFont(TTFont('ArialUnicode', font_path))

class InvoiceGenerator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Генератор счетов-фактур")
        self.resize(1000, 800)
        self.logo_path = None
        self.next_invoice = 1

        # Статус-бар
        self.status = QStatusBar()
        self.setStatusBar(self.status)

        # Панель инструментов
        self._create_toolbar()

        # Левая часть без предпросмотра PDF
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setSpacing(20)
        left_layout.addWidget(self._create_info_group())
        left_layout.addWidget(self._create_items_group())
        left_layout.addStretch()
        # Устанавливаем только левую часть как центральный виджет
        self.setCentralWidget(left)

    def _create_toolbar(self):
        toolbar = QToolBar("MainToolbar")
        toolbar.setIconSize(QSize(24, 24))
        toolbar.setStyleSheet("""
            QToolBar { background-color: #2C3E50; spacing: 6px; }
            QToolButton { color: #ECF0F1; background-color: transparent; border: none; padding: 4px; }
            QToolButton:hover { background-color: #34495E; border-radius: 4px; }
        """)
        save_act   = QAction(QIcon.fromTheme("document-save"),   "Сохранить",   self)
        load_act   = QAction(QIcon.fromTheme("document-open"),   "Загрузить",   self)
        export_act = QAction(QIcon.fromTheme("document-export"), "Экспорт PDF", self)
        toolbar.addAction(save_act)
        toolbar.addAction(load_act)
        toolbar.addSeparator()
        toolbar.addAction(export_act)
        save_act.triggered.connect(self.save_data)
        load_act.triggered.connect(self.load_data)
        export_act.triggered.connect(self.save_pdf)
        self.addToolBar(toolbar)

    def _create_info_group(self):
        grp = QGroupBox("Данные счета")
        grp.setFont(QFont("Arial", 11, QFont.Bold))
        form = QFormLayout(grp)

        self.company_name    = QLineEdit(); self.company_name.setPlaceholderText("ООО Рога & Копыта")
        self.company_address = QLineEdit(); self.company_address.setPlaceholderText("г. Алматы, ул. Главная, 1")
        self.client_name     = QLineEdit(); self.client_name.setPlaceholderText("Иванов Иван Иванович")
        self.client_address  = QLineEdit(); self.client_address.setPlaceholderText("г. Астана, ул. Примерная, 2")
        self.invoice_number  = QLineEdit(f"{self.next_invoice}"); self.invoice_number.setReadOnly(True)
        self.invoice_date    = QDateEdit(QDate.currentDate()); self.invoice_date.setDisplayFormat("dd.MM.yyyy"); self.invoice_date.setCalendarPopup(True)
        self.vat_rate        = QSpinBox(); self.vat_rate.setRange(0,100); self.vat_rate.setSuffix(" %")

        form.addRow("Название:",      self.company_name)
        form.addRow("Адрес:",         self.company_address)
        form.addRow("Клиент:",        self.client_name)
        form.addRow("Адрес клиента:", self.client_address)
        form.addRow("№ счета:",       self.invoice_number)
        form.addRow("Дата:",          self.invoice_date)
        form.addRow("НДС:",           self.vat_rate)

        # Логотип
        hl = QHBoxLayout()
        btn = QPushButton(QIcon.fromTheme("image"), "Логотип")
        btn.clicked.connect(self.load_logo)
        self.logo_label = QLabel("Не выбран")
        hl.addWidget(btn); hl.addWidget(self.logo_label); hl.addStretch()
        form.addRow("", hl)

        return grp

    def _create_items_group(self):
        grp = QGroupBox("Позиции")
        grp.setFont(QFont("Arial", 11, QFont.Bold))
        vbox = QVBoxLayout(grp)

        self.items_table = QTableWidget(0,4)
        self.items_table.setHorizontalHeaderLabels(["Описание","Кол-во","Цена","Сумма"])
        hdr = self.items_table.horizontalHeader(); hdr.setSectionResizeMode(QHeaderView.Stretch)
        self.items_table.setAlternatingRowColors(True)
        self.items_table.cellChanged.connect(self._update_row_total)

        vbox.addWidget(self.items_table)
        hl = QHBoxLayout()
        add_btn = QPushButton(QIcon.fromTheme("list-add"), "Добавить")
        rem_btn = QPushButton(QIcon.fromTheme("list-remove"), "Удалить")
        add_btn.clicked.connect(self.add_item); rem_btn.clicked.connect(self.remove_item)
        hl.addWidget(add_btn); hl.addWidget(rem_btn); hl.addStretch()
        vbox.addLayout(hl)

        return grp

    def _create_items_group(self):
        grp = QGroupBox("Позиции")
        grp.setFont(QFont("Arial", 11, QFont.Bold))
        vbox = QVBoxLayout(grp)

        self.items_table = QTableWidget(0,4)
        self.items_table.setHorizontalHeaderLabels(["Описание","Кол-во","Цена","Сумма"])
        hdr = self.items_table.horizontalHeader(); hdr.setSectionResizeMode(QHeaderView.Stretch)
        self.items_table.setAlternatingRowColors(True)
        self.items_table.cellChanged.connect(self._update_row_total)

        vbox.addWidget(self.items_table)
        hl = QHBoxLayout()
        add_btn = QPushButton(QIcon.fromTheme("list-add"), "Добавить")
        rem_btn = QPushButton(QIcon.fromTheme("list-remove"), "Удалить")
        add_btn.clicked.connect(self.add_item); rem_btn.clicked.connect(self.remove_item)
        hl.addWidget(add_btn); hl.addWidget(rem_btn); hl.addStretch()
        vbox.addLayout(hl)

        return grp

    def _create_items_group(self):
        grp = QGroupBox("Позиции")
        grp.setFont(QFont("Arial", 11, QFont.Bold))
        vbox = QVBoxLayout(grp)

        self.items_table = QTableWidget(0,4)
        self.items_table.setHorizontalHeaderLabels(["Описание","Кол-во","Цена","Сумма"])
        hdr = self.items_table.horizontalHeader(); hdr.setSectionResizeMode(QHeaderView.Stretch)
        self.items_table.setAlternatingRowColors(True)
        self.items_table.cellChanged.connect(self._update_row_total)

        vbox.addWidget(self.items_table)
        hl = QHBoxLayout()
        add_btn = QPushButton(QIcon.fromTheme("list-add"), "Добавить")
        rem_btn = QPushButton(QIcon.fromTheme("list-remove"), "Удалить")
        add_btn.clicked.connect(self.add_item)
        rem_btn.clicked.connect(self.remove_item)
        hl.addWidget(add_btn); hl.addWidget(rem_btn); hl.addStretch()
        vbox.addLayout(hl)

        return grp


    def _create_preview_tab(self):
        widget = QWidget(); layout = QVBoxLayout(widget)
        label = QLabel('Нажмите «Экспорт в PDF» в меню, чтобы сформировать счет.')
        label.setAlignment(Qt.AlignCenter); layout.addWidget(label)
        return widget

    def load_logo(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Выберите логотип', '', 'Изображения (*.png *.jpg)')
        if path:
            self.logo_path = path; self.logo_label.setText(f"Логотип: {os.path.basename(path)}")
            self.status.showMessage('Логотип загружен', 3000)

    def add_item(self):
        r = self.items_table.rowCount(); self.items_table.insertRow(r)
        for c in range(4): self.items_table.setItem(r, c, QTableWidgetItem(''))
        self.status.showMessage('Добавлена новая позиция', 2000)

    def remove_item(self):
        r = self.items_table.currentRow()
        if r < 0: self.status.showMessage('Выберите строку для удаления', 2000); return
        self.items_table.removeRow(r); self.status.showMessage('Позиция удалена', 2000)

    def _update_row_total(self, row, col):
        if col in (1, 2):
            try:
                qty_text = self.items_table.item(row, 1).text().replace(',', '.')
                price_text = self.items_table.item(row, 2).text().replace(',', '.')
                qty = float(qty_text) if qty_text else 0.0
                price = float(price_text) if price_text else 0.0
                total = qty * price
                self.items_table.blockSignals(True)
                self.items_table.setItem(row, 3, QTableWidgetItem(f"{total:.2f}"))
                self.items_table.blockSignals(False)
            except:
                pass

    def save_data(self):
        path, _ = QFileDialog.getSaveFileName(self, 'Сохранить JSON', 'invoice.json', 'JSON (*.json)')
        if not path: return
        data = {
            'company': self.company_name.text(),
            'address': self.company_address.text(),
            'client': self.client_name.text(),
            'client_address': self.client_address.text(),
            'invoice_no': self.invoice_number.text(),
            'date': self.invoice_date.date().toString('dd.MM.yyyy'),
            'vat': self.vat_rate.value(),
            'logo': self.logo_path,
            'items': []
        }
        for r in range(self.items_table.rowCount()):
            row_data = [self.items_table.item(r, c).text() if self.items_table.item(r, c) else '' for c in range(4)]
            data['items'].append(row_data)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        self.status.showMessage('Данные сохранены', 3000)

    def load_data(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Загрузить JSON', '', 'JSON (*.json)')
        if not path: return
        with open(path, 'r', encoding='utf-8') as f: data = json.load(f)
        self.company_name.setText(data.get('company', ''))
        self.company_address.setText(data.get('address', ''))
        self.client_name.setText(data.get('client', ''))
        self.client_address.setText(data.get('client_address', ''))
        self.invoice_number.setText(data.get('invoice_no', ''))
        d = QDate.fromString(data.get('date', ''), 'dd.MM.yyyy');
        if d.isValid(): self.invoice_date.setDate(d)
        self.vat_rate.setValue(data.get('vat', 0)); self.logo_path = data.get('logo')
        if self.logo_path: self.logo_label.setText(f"Логотип: {os.path.basename(self.logo_path)}")
        self.items_table.setRowCount(0)
        for row_data in data.get('items', []):
            self.add_item(); r = self.items_table.rowCount() - 1
            for c, val in enumerate(row_data): self.items_table.setItem(r, c, QTableWidgetItem(val))
        self.status.showMessage('Данные загружены', 3000)

    def save_pdf(self):
        path, _ = QFileDialog.getSaveFileName(
            self, 'Экспорт в PDF', 'invoice.pdf', 'PDF-файлы (*.pdf)'
        )
        if not path: return
        try:
            doc = SimpleDocTemplate(path, pagesize=A4)
            elems = []
            styles = getSampleStyleSheet()
            styles['Title'].fontName = 'ArialUnicode'
            styles['Normal'].fontName = 'ArialUnicode'
            styles['BodyText'].fontName = 'ArialUnicode'

            if self.logo_path and os.path.exists(self.logo_path):
                img_reader = ImageReader(self.logo_path)
                ow, oh = img_reader.getSize()
                nw = 100; nh = oh * nw / ow
                elems.append(Image(self.logo_path, width=nw, height=nh))
                elems.append(Spacer(1, 12))

            elems.append(Paragraph(f"Счет №<b>{self.invoice_number.text()}</b>", styles['Title']))
            elems.append(Paragraph(
                f"Дата: {self.invoice_date.date().toString('dd.MM.yyyy')}",
                styles['Normal']
            ))
            elems.append(Spacer(1, 12))

            info_data = [
                ['От:', self.company_name.text()],
                ['', self.company_address.text()],
                ['Кому:', self.client_name.text()],
                ['', self.client_address.text()]
            ]
            info_table = Table(info_data, colWidths=[50, 450])
            info_table.setStyle(TableStyle([
                ('FONTNAME',  (0, 0), (-1, -1), 'ArialUnicode'),
                ('FONTSIZE',  (0, 0), (-1, -1), 10),
                ('VALIGN',    (0, 0), (-1, -1), 'TOP'),
                ('ALIGN',     (0, 0), (0, -1), 'LEFT'),
                ('ALIGN',     (1, 0), (1, -1), 'LEFT'),
            ]))
            elems.append(info_table)
            elems.append(Spacer(1, 12))

            table_data = [["Описание", "Кол-во", "Цена", "Итого"]]
            total = 0.0
            for r in range(self.items_table.rowCount()):
                desc = self.items_table.item(r, 0).text() if self.items_table.item(r, 0) else ''
                qty_text = (self.items_table.item(r, 1).text() or '').replace(',', '.')
                price_text = (self.items_table.item(r, 2).text() or '').replace(',', '.')
                try:
                    qty = float(qty_text)
                except:
                    qty = 0.0
                try:
                    price = float(price_text)
                except:
                    price = 0.0
                ln = qty * price
                total += ln
                table_data.append([desc, str(qty), f"{price:.2f}", f"{ln:.2f}"])
            vat_r = self.vat_rate.value() / 100.0; vat_amt = total * vat_r; grand = total + vat_amt
            table_data.extend([
                ['', '', 'Итого:', f"{total:.2f}"],
                ['', '', f"НДС {self.vat_rate.value()}%:", f"{vat_amt:.2f}"],
                ['', '', 'К оплате:', f"{grand:.2f}"],
            ])
            tbl = Table(table_data, colWidths=[300, 80, 80, 80])
            tbl.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'ArialUnicode'),
                ('GRID',     (0, 0), (-1, -1), 0.5, colors.black),
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('ALIGN',    (1, 1), (-1, -1), 'RIGHT'),
                ('VALIGN',   (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            elems.append(tbl)

            doc.build(elems)
            self.status.showMessage('PDF сохранен', 3000)
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', f"Не удалось создать PDF:\n{e}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    pal = QPalette(); pal.setColor(QPalette.Window, QColor(245,245,245))
    pal.setColor(QPalette.Button, QColor(70,130,180)); pal.setColor(QPalette.ButtonText, Qt.white)
    pal.setColor(QPalette.Base, Qt.white); pal.setColor(QPalette.AlternateBase, QColor(230,230,230))
    pal.setColor(QPalette.Highlight, QColor(100,149,237)); pal.setColor(QPalette.HighlightedText, Qt.white)
    app.setPalette(pal)
    app.setStyleSheet(
        """
        /* Синий фон и белый текст для всех QPushButton */
        QPushButton {
            background-color: #4678B4;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 6px 12px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #5A9CEB;
        }

        /* Тёмная тема для тулбара */
        QToolBar {
            background-color: #2C3E50;
            spacing: 6px;
        }
        QToolButton {
            color: #ECF0F1;
            background-color: transparent;
            border: none;
            padding: 4px;
        }
        QToolButton:hover {
            background-color: #34495E;
            border-radius: 4px;
        }
        """
    )

    window = InvoiceGenerator(); window.show(); sys.exit(app.exec_())

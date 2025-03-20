import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import sqlite3
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from tkcalendar import DateEntry
import locale
import os
import subprocess
from tkinter import messagebox as mb

# Imposta la localizzazione italiana per il calendario
try:
    locale.setlocale(locale.LC_TIME, 'it_IT.UTF-8')
except:
    pass
# Fine impostazione localizzazione

class ReportFrame(ttk.Frame):
    def __init__(self, parent, db):
        super().__init__(parent)
        self.db = db
        self.init_ui()
    
    def init_ui(self):
        """Inizializza l'interfaccia per la generazione report"""
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Filtri di ricerca
        filter_frame = ttk.LabelFrame(main_frame, text="Filtri Report", padding=15)
        filter_frame.pack(fill=tk.X, pady=10)
        
        # Selezione fornitore
        ttk.Label(filter_frame, text="Fornitore:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.fornitore_combo = ttk.Combobox(filter_frame, state="readonly")
        self.fornitore_combo.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Tipo movimento
        ttk.Label(filter_frame, text="Tipo Movimento:").grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.tipo_movimento = ttk.Combobox(filter_frame, values=["Tutti", "Uscita", "Rientro"])
        self.tipo_movimento.current(0)
        self.tipo_movimento.grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)
        
        # Date
        ttk.Label(filter_frame, text="Da:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.data_inizio = DateEntry(
            filter_frame,
            date_pattern='dd/mm/yyyy',
            foreground='white',
            background='#0078d7',
            borderwidth=2,
            mindate=datetime(2000, 1, 1),
            maxdate=datetime.today()
        )
        self.data_inizio.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(filter_frame, text="A:").grid(row=1, column=2, padx=5, pady=5, sticky=tk.W)
        self.data_fine = DateEntry(
            filter_frame,
            date_pattern='dd/mm/yyyy',
            foreground='white',
            background='#0078d7',
            borderwidth=2,
            mindate=datetime(2000, 1, 1),
            maxdate=datetime.today()
        )
        self.data_fine.grid(row=1, column=3, padx=5, pady=5, sticky=tk.W)
        
        # Pulsanti filtro
        btn_frame = ttk.Frame(filter_frame)
        btn_frame.grid(row=2, column=0, columnspan=4, pady=10)
        
        ttk.Button(btn_frame, text="Genera Report", command=self.genera_report).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Pulisci Filtri", command=self.pulisci_filtri).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Stampa", command=self.stampa_report).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Esporta Excel", command=self.export_excel).pack(side=tk.LEFT, padx=5)
        
        stats_frame = ttk.LabelFrame(main_frame, text="Statistiche Report", padding=15)
        stats_frame.pack(fill=tk.X, pady=10)
        
        # Etichette per le statistiche
        self.stats_labels = {
                            'fornitore': ttk.Label(stats_frame, text="Fornitore selezionato: -", style="Stats.TLabel"),
                            'totali': ttk.Label(stats_frame, text="Bancali totali: -", style="Stats.TLabel"),
                            'in_magazzino': ttk.Label(stats_frame, text="In magazzino: -", style="Stats.TLabel"),
                            'presso_fornitore': ttk.Label(stats_frame, text="Presso fornitore: -", style="Stats.TLabel")
                        }
        
        # Posizionamento
        self.stats_labels['fornitore'].grid(row=0, column=0, padx=10, pady=5, sticky=tk.W)
        self.stats_labels['totali'].grid(row=0, column=1, padx=10, pady=5, sticky=tk.W)
        self.stats_labels['in_magazzino'].grid(row=0, column=2, padx=10, pady=5, sticky=tk.W)
        self.stats_labels['presso_fornitore'].grid(row=0, column=3, padx=10, pady=5, sticky=tk.W)
        
        # Tabella risultati
        result_frame = ttk.LabelFrame(main_frame, text="Risultati", padding=15)
        result_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        columns = ("Data", "Fornitore", "Tipo", "Codice Bancale", "Note")
        self.tree = ttk.Treeview(result_frame, columns=columns, show='headings')
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120)
        
        scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Pulsanti esportazione
        export_frame = ttk.Frame(main_frame)
        export_frame.pack(fill=tk.X, pady=10)
        
        #ttk.Button(export_frame, text="Stampa", command=self.stampa_report).pack(side=tk.LEFT, padx=5)
        #ttk.Button(export_frame, text="Esporta Excel", command=self.export_excel).pack(side=tk.LEFT, padx=5)
        #ttk.Button(export_frame, text="Esporta PDF", command=self.export_pdf).pack(side=tk.LEFT, padx=5)
        
        self.aggiorna_fornitori()
    
    def aggiorna_fornitori(self):
        """Carica la lista dei fornitori nel combobox"""
        fornitori = self.db.get_fornitori()
        self.fornitore_combo['values'] = [f"{f[0]} - {f[1]}" for f in fornitori]
    
    def pulisci_filtri(self):
        """Resetta tutti i filtri"""
        self.fornitore_combo.set('')
        self.tipo_movimento.current(0)
        self.data_inizio.delete(0, tk.END)
        self.data_fine.delete(0, tk.END)
        self.tree.delete(*self.tree.get_children())
    
    def genera_report(self):
        """Esegue la query con i filtri selezionati"""
        try:
            # Recupera i parametri dai filtri
            fornitore = self.fornitore_combo.get()
            tipo = self.tipo_movimento.get()
            
            # Debug: Stampa i valori delle date prima della conversione
            print("Data inizio (raw):", self.data_inizio.get_date())
            print("Data fine (raw):", self.data_fine.get_date())
            
            # Conversione date
            data_inizio = self.data_inizio.get_date().strftime("%Y-%m-%d") if self.data_inizio.get_date() else ""
            data_fine = self.data_fine.get_date().strftime("%Y-%m-%d") if self.data_fine.get_date() else ""
            
            # Debug: Stampa i valori convertiti
            print("Parametri ricerca:")
            print("Fornitore:", fornitore)
            print("Tipo movimento:", tipo)
            print("Data inizio (DB format):", data_inizio)
            print("Data fine (DB format):", data_fine)
            
            # Costruisci la query
            query = """
                SELECT m.data, f.nome, m.tipo_movimento, b.codice, m.note
                FROM movimenti m
                JOIN fornitori f ON m.fornitore_id = f.id
                JOIN bancali b ON m.bancale_id = b.id
                WHERE 1=1
            """
            params = []
            
            if fornitore:
                fornitore_id = fornitore.split(" - ")[0]
                query += " AND m.fornitore_id = ?"
                params.append(fornitore_id)
            
            if tipo != "Tutti":
                query += " AND m.tipo_movimento = ?"
                params.append(tipo.lower())
            
            if data_inizio:
                query += " AND DATE(m.data) >= ?"  # Considera solo la parte data
                params.append(data_inizio)
            
            if data_fine:
                query += " AND DATE(m.data) <= ?"  # Considera solo la parte data
                params.append(data_fine)
            
            query += " ORDER BY m.data DESC"
            
            # Debug: Stampa la query finale
            print("\nQuery eseguita:")
            print(query)
            print("Parametri:", params)
            
            # Esegui la query
            conn = sqlite3.connect(self.db.db_file)
            cursor = conn.cursor()
            
            # Debug: Verifica l'esistenza delle tabelle
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            print("\nTabelle presenti nel database:", cursor.fetchall())
            
            # Esecuzione query principale
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            # Debug: Stampa i risultati grezzi
            print("\nRisultati ottenuti:", len(results), "righe")
            for row in results[:5]:  # Stampa i primi 5 risultati
                print(row)
            
            conn.close()
            
            # Popola la treeview
            self.tree.delete(*self.tree.get_children())
            for row in results:
                # Formatta la data per la visualizzazione
                formatted_date = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S").strftime("%d/%m/%Y %H:%M")
                self.tree.insert('', 'end', values=(formatted_date, *row[1:]))
                
            self.aggiorna_statistiche(fornitore_id if fornitore else None)
            
            # Debug: Controlla la treeview
            print("\nElementi nella treeview:", len(self.tree.get_children()))
            
        except Exception as e:
            messagebox.showerror("Errore", f"Errore durante la generazione del report:\n{str(e)}")
            # Debug: Stampa l'errore completo
            import traceback
            print("\nTraceback completo:")
            traceback.print_exc()
    
    def aggiorna_statistiche(self, fornitore_id=None):
        """Aggiorna la sezione statistiche con i dati del fornitore"""
        conn = sqlite3.connect(self.db.db_file)
        try:
            cursor = conn.cursor()
            
            # Statistiche generali
            total_bancali = cursor.execute("SELECT COUNT(*) FROM bancali").fetchone()[0]
            in_magazzino = cursor.execute("SELECT COUNT(*) FROM bancali WHERE stato = 'magazzino'").fetchone()[0]
            
            self.stats_labels['totali'].config(text=f"Bancali totali: {total_bancali}")
            self.stats_labels['in_magazzino'].config(text=f"In magazzino: {in_magazzino}")
            
            # Statistiche specifiche per fornitore
            if fornitore_id:
                # Recupera nome fornitore
                nome_fornitore = cursor.execute(
                    "SELECT nome FROM fornitori WHERE id = ?", (fornitore_id,)
                ).fetchone()[0]
                
                # Bancali presso il fornitore
                presso_fornitore = cursor.execute("""
                    SELECT COUNT(*) FROM bancali 
                    WHERE stato = 'fornitore' AND id IN (
                        SELECT bancale_id FROM movimenti 
                        WHERE fornitore_id = ? AND tipo_movimento = 'uscita'
                        EXCEPT
                        SELECT bancale_id FROM movimenti 
                        WHERE fornitore_id = ? AND tipo_movimento = 'rientro'
                    )
                """, (fornitore_id, fornitore_id)).fetchone()[0]
                
                self.stats_labels['fornitore'].config(text=f"Fornitore: {nome_fornitore}")
                self.stats_labels['presso_fornitore'].config(text=f"Presso fornitore: {presso_fornitore}")
            else:
                self.stats_labels['fornitore'].config(text="Fornitore: Tutti i fornitori")
                self.stats_labels['presso_fornitore'].config(text="Presso fornitore: -")
                
        finally:
            conn.close()
    
    def get_report_data(self):
        """Restituisce i dati del report in formato DataFrame"""
        items = [self.tree.item(item)['values'] for item in self.tree.get_children()]
        return pd.DataFrame(items, columns=["Data", "Fornitore", "Tipo", "Codice Bancale", "Note"])
    
    def stampa_report(self):
        """Stampa il report"""
        if len(self.tree.get_children()) == 0:
            messagebox.showwarning("Attenzione", "Nessun dato da stampare")
            return
        
        # Implementa qui la logica di stampa
        messagebox.showinfo("Stampa", "Funzionalità di stampa in esecuzione...")
    
    def export_excel(self):
        """Esporta in formato Excel"""
        df = self.get_report_data()
        if df.empty:
            mb.showwarning("Attenzione", "Nessun dato da esportare")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel Files", "*.xlsx")]
        )
        
        if file_path:
            try:
                df.to_excel(file_path, index=False)
                
                # Mostra la richiesta di apertura
                if mb.askyesno("Successo", "Esportazione Excel completata!\nVuoi aprire il file?"):
                    if os.name == 'nt':  # Windows
                        os.startfile(file_path)
                    elif os.name == 'posix':  # macOS/Linux
                        subprocess.call(('open' if sys.platform == 'darwin' else 'xdg-open', file_path))
                        
            except Exception as e:
                mb.showerror("Errore", f"Errore durante l'esportazione: {str(e)}")
    
    def export_pdf(self):
        """Esporta in formato PDF"""
        df = self.get_report_data()
        if df.empty:
            messagebox.showwarning("Attenzione", "Nessun dato da esportare")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF Files", "*.pdf")]
        )
        
        if file_path:
            try:
                c = canvas.Canvas(file_path, pagesize=A4)
                width, height = A4
                
                # Intestazione
                c.setFont("Helvetica-Bold", 16)
                c.drawString(50, height - 50, "Report Movimentazione Bancali")
                c.setFont("Helvetica", 10)
                c.drawString(50, height - 70, f"Generato il: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
                
                # Dati
                data = [df.columns.tolist()] + df.values.tolist()
                table = Table(data)
                
                # Stile tabella
                style = TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.grey),
                    ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                    ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0,0), (-1,0), 10),
                    ('BOTTOMPADDING', (0,0), (-1,0), 12),
                    ('BACKGROUND', (0,1), (-1,-1), colors.beige),
                    ('GRID', (0,0), (-1,-1), 1, colors.grey)
                ])
                
                table.setStyle(style)
                table.wrapOn(c, width - 100, height)
                table.drawOn(c, 50, height - 120)
                
                c.save()
                messagebox.showinfo("Successo", "Esportazione PDF completata!")
            except Exception as e:
                messagebox.showerror("Errore", f"Errore durante l'esportazione: {str(e)}")
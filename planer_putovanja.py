# 2. Planer putovanja (Naziv app: TravelBuddy)
# Napravio: Luka Šop

#uvoz biblioteka
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, date
import xml.etree.ElementTree as ET
import os

#1. model OOP

#bazna klasa StavkaItinerara
class StavkaItinerara:
    def __init__(self, naziv, lokacija):
        self.naziv = naziv
        self.lokacija = lokacija

    #sortiranje stavki po datumu
    def sortiranje_datum(self):
        # override u dječjim klasama
        return datetime.max

    #pretvaranje u rječnik za spremanje u XML
    def rječnik(self):
        return {"naziv": self.naziv, "lokacija": self.lokacija}

#podklasa smještaj 
class Smjestaj(StavkaItinerara):
    def __init__(self, naziv, lokacija, datum_dolaska, datum_odlaska, ukupni_trosak):
        super().__init__(naziv, lokacija)
        self.datum_dolaska = datum_dolaska #yyyy-mm-dd
        self.datum_odlaska = datum_odlaska
        self.ukupni_trosak = float(ukupni_trosak)

    #izračun broja noćenja
    def broj_nocenja(self):
        return (self.datum_odlaska - self.datum_dolaska).days

    #za sortiranje uzima datum dolaska i vrijeme 00:00
    def sortiranje_datum(self):
        return datetime.combine(self.datum_dolaska, datetime.min.time())

    #proširivanje rječnika s novim atributima
    def rječnik(self):
        d = super().rječnik()
        d.update({
            "datum_dolaska": self.datum_dolaska.isoformat(),
            "datum_odlaska": self.datum_odlaska.isoformat(),
            "ukupni_trosak": str(self.ukupni_trosak)
        })
        return d

#podklasa aktivnost
class Aktivnost(StavkaItinerara):
    def __init__(self, naziv, lokacija, datum, vrijeme, cijena, napomena):
        super().__init__(naziv, lokacija)
        self.datum = datum #yyyy-mm-dd
        self.vrijeme = vrijeme #hh:mm
        self.cijena = float(cijena)
        self.napomena = napomena

    #sortiranje po datumu i vremenu
    def sortiranje_datum(self):
        h, m = map(int, self.vrijeme.split(':'))
        return datetime.combine(self.datum, datetime.min.time()).replace(hour=h, minute=m)

    #proširivanje rječnika s novim atributima
    def rječnik(self):
        d = super().rječnik()
        d.update({
            "datum": self.datum.isoformat(),
            "vrijeme": self.vrijeme,
            "cijena": str(self.cijena),
            "napomena": self.napomena
        })
        return d

# 2. Sučelje GUI

class PlanerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Planer Putovanja - TravelBuddy")
        self.geometry("850x520")
        self.minsize(800,480)

        #paleta boja
        self.bg_color = "#00FFFF"
        self.panel_color = "#00008B"
        self.text_color = "#FFFFFF"
        self.button_color1 = "#00008B"
        self.button_color2 = "#FFA500"
        self.button_color3 = "#FF0000"
        self.button_color4 = "#00FF00"

        self.configure(bg=self.bg_color)

        #lista u koju se spremaju stavke
        self.stavke = []
        # lista objekata koji su trenutno prikazani u listboxu (mapa index -> objekt)
        self.prikaz_stavki = []

        #meni, frameovi i statusna traka
        self.meni_traka()
        self.zaglavlje()
        self.glavni_frame()
        self.statusna_traka()

        #update listboxa
        self.update_listbox()

    #meni traka
        #datoteka -> spremi, učitaj, izlaz
        #pomoć -> o aplikaciji
    def meni_traka(self):
        meni = tk.Menu(self)
        datoteka = tk.Menu(meni, tearoff=0)
        datoteka.add_command(label="Spremi", command=self.save_xml)
        datoteka.add_command(label="Učitaj", command=self.load_xml)
        datoteka.add_separator()
        # koristimo destroy umjesto quit da bi prozor bio pravilno zatvoren
        datoteka.add_command(label="Izlaz", command=self.destroy)
        meni.add_cascade(label="Datoteka", menu=datoteka)

        pomoć = tk.Menu(meni, tearoff=0)
        pomoć.add_command(label="O aplikaciji", command=self.o_aplikaciji)
        meni.add_cascade(label="Pomoć", menu=pomoć)

        self.config(menu=meni)

    #zaglavlje s logotipom
    def zaglavlje(self):
        zaglavlje = tk.Frame(self, bg=self.panel_color, padx=10, pady=8)
        zaglavlje.pack(fill=tk.X, padx=10, pady=(10,5))

        #logotip (tekstualni)
        logo_text = "TravelBuddy"
        logo_label = tk.Label(zaglavlje, text=logo_text, font=("Segoe UI", 18, "bold"),
        bg=self.panel_color, fg=self.text_color)
        logo_label.pack(side=tk.LEFT)

        opis = tk.Label(zaglavlje, text="Planer putovanja - Verzija 1.0", bg=self.panel_color, fg=self.text_color)
        opis.pack(side=tk.LEFT, padx=12)

    #glavni dio, lijevi frame za unos i desni frame za listu, gumbi, filteri
    def glavni_frame(self):
        main = tk.Frame(self, bg=self.bg_color)
        main.pack(fill=tk.BOTH, expand=True, padx=10, pady=6)

        left = tk.Frame(main, bg=self.bg_color)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(0,8))

        right = tk.Frame(main, bg=self.bg_color)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        unos = tk.LabelFrame(left, text="Dodaj stavku", bg=self.bg_color, padx=8, pady=8)
        unos.pack(fill=tk.X)

        #tip stavke (smještaj/aktivnost)
        tk.Label(unos, text="Tip:", bg=self.bg_color).grid(row=0, column=0, sticky="w")
        self.tip = tk.StringVar(value="Smještaj")
        tip_menu = ttk.Combobox(unos, textvariable=self.tip, values=["Smještaj", "Aktivnost"], state="readonly", width=18)
        tip_menu.grid(row=0, column=1, pady=4)
        tip_menu.bind("<<ComboboxSelected>>", lambda e: self.promijeni_polja())

        #unos naziva i lokacije (zajedničko)
        tk.Label(unos, text="Naziv:", bg=self.bg_color).grid(row=1, column=0, sticky="w")
        self.naziv_entry = tk.Entry(unos, width=20)
        self.naziv_entry.grid(row=1, column=1, pady=4)

        tk.Label(unos, text="Lokacija:", bg=self.bg_color).grid(row=2, column=0, sticky="w")
        self.lokacija_entry = tk.Entry(unos, width=20)
        self.lokacija_entry.grid(row=2, column=1, pady=4)

        #unos za smještaj
        tk.Label(unos, text="Datum dolaska (YYYY-MM-DD):", bg=self.bg_color).grid(row=3, column=0, sticky="w")
        self.dolazak_entry = tk.Entry(unos, width=20)
        self.dolazak_entry.grid(row=3, column=1, pady=4)
        tk.Label(unos, text="Datum odlaska (YYYY-MM-DD):", bg=self.bg_color).grid(row=4, column=0, sticky="w")
        self.odlazak_entry = tk.Entry(unos, width=20)
        self.odlazak_entry.grid(row=4, column=1, pady=4)
        tk.Label(unos, text="Ukupni trošak (€):", bg=self.bg_color).grid(row=5, column=0, sticky="w")
        self.trosak_entry = tk.Entry(unos, width=20)
        self.trosak_entry.grid(row=5, column=1, pady=4)

        #unos za aktivnost
        tk.Label(unos, text="Datum (YYYY-MM-DD):", bg=self.bg_color).grid(row=6, column=0, sticky="w")
        self.aktivnost_datum_entry = tk.Entry(unos, width=20)
        self.aktivnost_datum_entry.grid(row=6, column=1, pady=4)
        tk.Label(unos, text="Vrijeme (HH:MM):", bg=self.bg_color).grid(row=7, column=0, sticky="w")
        self.aktivnost_vrijeme_entry = tk.Entry(unos, width=20)
        self.aktivnost_vrijeme_entry.grid(row=7, column=1, pady=4)
        tk.Label(unos, text="Cijena (€):", bg=self.bg_color).grid(row=8, column=0, sticky="w")
        self.aktivnost_cijena_entry = tk.Entry(unos, width=20)
        self.aktivnost_cijena_entry.grid(row=8, column=1, pady=4)
        tk.Label(unos, text="Napomena:", bg=self.bg_color).grid(row=9, column=0, sticky="w")
        self.aktivnost_napomena_entry = tk.Entry(unos, width=20)
        self.aktivnost_napomena_entry.grid(row=9, column=1, pady=4)

        #gumbi
        self.dodaj_gumb = tk.Button(unos, text="Dodaj", command=self.dodaj_stavku, bg=self.button_color1, fg=self.text_color)
        self.dodaj_gumb.grid(row=10, column=0, columnspan=2, pady=8, sticky="we")

        #izmjena polja za unos ovisno o tipu
        self.promijeni_polja()

        #filtriranje, spremanje i učitavanje
        filteri = tk.Frame(left, bg=self.bg_color, pady=6)
        filteri.pack(fill=tk.X)
        tk.Label(filteri, text="Filter:", bg=self.bg_color).pack(side=tk.LEFT)
        self.filter = tk.StringVar(value="Sve")
        tk.Radiobutton(filteri, text="Sve", variable=self.filter, value="Sve", bg=self.bg_color, command=self.update_listbox).pack(side=tk.LEFT)
        tk.Radiobutton(filteri, text="Smještaj", variable=self.filter, value="Smještaj", bg=self.bg_color, command=self.update_listbox).pack(side=tk.LEFT)
        tk.Radiobutton(filteri, text="Aktivnost", variable=self.filter, value="Aktivnost", bg=self.bg_color, command=self.update_listbox).pack(side=tk.LEFT)

        save_gumb = tk.Button(filteri, text="Spremi", bg=self.button_color4, command=self.save_xml)
        save_gumb.pack(side=tk.RIGHT, padx=4)
        load_gumb = tk.Button(filteri, text="Učitaj",bg=self.button_color1, fg=self.text_color, command=self.load_xml)
        load_gumb.pack(side=tk.RIGHT)

        #lista stavki (itinerar)
        listframe = tk.LabelFrame(right, text="Itinerar", bg=self.bg_color, padx=6, pady=6)
        listframe.pack(fill=tk.BOTH, expand=True)

        self.listbox = tk.Listbox(listframe, activestyle='dotbox')
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.listbox.bind('<Double-1>', self.prikazi_detalje) #dupli klik na stavku prikazuje detalje

        scrollbar = tk.Scrollbar(listframe, command=self.listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.config(yscrollcommand=scrollbar.set)

        #gumbi za brisanje, izmjenu i detalje
        dno = tk.Frame(right, bg=self.bg_color)
        dno.pack(fill=tk.X, pady=(6,0))

        tk.Button(dno, text="Uredi odabrano", bg=self.button_color1, fg=self.text_color, command=self.ucitaj).pack(side=tk.RIGHT, padx=4)
        tk.Button(dno, text="Prikaži detalje", bg=self.button_color2, fg=self.text_color, command=self.prikazi_detalje).pack(side=tk.RIGHT, padx=4)
        tk.Button(dno, text="Obriši odabrano", bg=self.button_color3, fg=self.text_color, command=self.obrisi_odabrano).pack(side=tk.RIGHT)

    def promijeni_polja(self):
        tip = self.tip.get()
        #omogućuje polja jednoga tipa, a onemogućuje polja drugog tipa
        if tip == "Smještaj":
            for i in [self.dolazak_entry, self.odlazak_entry, self.trosak_entry]:
                i.config(state='normal')
            for i in [self.aktivnost_datum_entry, self.aktivnost_vrijeme_entry, self.aktivnost_cijena_entry, self.aktivnost_napomena_entry]:
                i.delete(0, tk.END)
                i.config(state='disabled')
        else:
            for i in [self.dolazak_entry, self.odlazak_entry, self.trosak_entry]:
                i.delete(0, tk.END)
                i.config(state='disabled')
            for i in [self.aktivnost_datum_entry, self.aktivnost_vrijeme_entry, self.aktivnost_cijena_entry, self.aktivnost_napomena_entry]:
                i.config(state='normal')

# 3. Logika

    #dodavanje stavke
    def dodaj_stavku(self):
        tip = self.tip.get()
        naziv = self.naziv_entry.get().strip()
        lokacija = self.lokacija_entry.get().strip()

        #provjere grešaka
        if not naziv:
            messagebox.showwarning("Greška", "Naziv ne smije biti prazan.")
            return
        if not lokacija:
            messagebox.showwarning("Greška", "Lokacija ne smije biti prazna.")
            return

        try:
            if tip == "Smještaj":   #za smještaj
                dolazak1 = self.dolazak_entry.get().strip()
                odlazak1 = self.odlazak_entry.get().strip()
                trosak1 = self.trosak_entry.get().strip()

                #provjera popunjenosti
                if not (dolazak1 and odlazak1 and trosak1):
                    messagebox.showwarning("Greška", "Popunite sva polja za smještaj.")
                    return

                #provjera datuma
                d1 = datetime.strptime(dolazak1, "%Y-%m-%d").date()
                d2 = datetime.strptime(odlazak1, "%Y-%m-%d").date()
                if d2 <= d1:
                    messagebox.showwarning("Greška", "Datum odlaska mora biti nakon datuma dolaska.")
                    return

                trosak=float(trosak1)
                
                #nova stavka
                smjestaj = Smjestaj(naziv, lokacija, d1, d2, trosak)
                self.stavke.append(smjestaj)
                
            else:   #za aktivnost
                datum1 = self.aktivnost_datum_entry.get().strip()
                vrijeme1 = self.aktivnost_vrijeme_entry.get().strip()
                cijena1 = self.aktivnost_cijena_entry.get().strip()
                napomena1 = self.aktivnost_napomena_entry.get().strip()

                #provjera popunjenosti
                if not (datum1 and vrijeme1 and cijena1):
                    messagebox.showwarning("Greška", "Popunite datum, vrijeme i cijenu za aktivnost.")
                    return

                try:
                    cijena1 = float(cijena1)
                except ValueError:
                    messagebox.showwarning("Greška", "Cijena mora biti broj.")
                    return

                #provjera vremena i datuma
                try:
                    d = datetime.strptime(datum1, "%Y-%m-%d").date()
                except ValueError:
                    messagebox.showwarning("Greška", "Datum mora biti u formatu YYYY-MM-DD, npr. 2025-12-31.")
                    return

                # zahtijevamo format HH:MM (npr. 09:05). Ako netko upiše '9:5' to neće proći — to smatramo očekivanim
                try:
                    t_parsed = datetime.strptime(vrijeme1, "%H:%M")
                    # normaliziramo vrijeme na format HH:MM
                    vrijeme1 = t_parsed.strftime("%H:%M")
                except ValueError:
                    messagebox.showwarning("Greška", "Vrijeme mora biti u formatu HH:MM, npr. 09:30.")
                    return

                #nova stavka
                aktivnost = Aktivnost(naziv, lokacija, d, vrijeme1, cijena1, napomena1)
                self.stavke.append(aktivnost)

        #greške
        except ValueError as ve:
            messagebox.showerror("Greška pri unosu", f"Neispravan format podataka: {ve}")
            return
        except Exception as e:
            messagebox.showerror("Neočekivana greška", str(e))
            return

        #očisti polja
        self.naziv_entry.delete(0, tk.END)
        self.lokacija_entry.delete(0, tk.END)
        self.dolazak_entry.delete(0, tk.END)
        self.odlazak_entry.delete(0, tk.END)
        self.trosak_entry.delete(0, tk.END)
        self.aktivnost_datum_entry.delete(0, tk.END)
        self.aktivnost_vrijeme_entry.delete(0, tk.END)
        self.aktivnost_cijena_entry.delete(0, tk.END)
        self.aktivnost_napomena_entry.delete(0, tk.END)

        self.update_listbox()
        self.status_set("Dodano: " + naziv)

    # prikaz u listboxu
    def update_listbox(self):
        self.listbox.delete(0, tk.END)
        self.listbox.selection_clear(0, tk.END)
        filt = self.filter.get()
        
        # sortiraj kronološki
        prikaz = []
        
        for s in self.stavke:
            t = "Smještaj" if isinstance(s, Smjestaj) else "Aktivnost"
            if filt == "Sve" or (filt == "Smještaj" and t == "Smještaj") or (filt == "Aktivnost" and t == "Aktivnost"):
                prikaz.append(s)
                
        prikaz.sort(key=lambda x: x.sortiranje_datum())

        # pohrani trenutno prikazane objekte za kasnija mapiranja (odabir/edit/brisanje)
        self.prikaz_stavki = prikaz.copy()
        
        for s in prikaz:
            if isinstance(s, Smjestaj):
                line = f"[Smještaj] {s.datum_dolaska.isoformat()} → {s.datum_odlaska.isoformat()} | {s.naziv} | {s.lokacija} | {s.ukupni_trosak:.2f} €"
            else:
                line = f"[Aktivnost] {s.datum.isoformat()} {s.vrijeme} | {s.naziv} | {s.lokacija} | {s.cijena:.2f} €"
            self.listbox.insert(tk.END, line)

        #statusna traka: broj stavki, ukupni trošak, ukupno noćenja
        ukupni_trosak = sum((s.ukupni_trosak for s in self.stavke if isinstance(s, Smjestaj)), 0.0) + sum((s.cijena for s in self.stavke if isinstance(s, Aktivnost)), 0.0)
        ukupno_nocenja = sum((s.broj_nocenja() for s in self.stavke if isinstance(s, Smjestaj)), 0)
        self.status_set(f"Stavki: {len(self.stavke)} | Ukupni trošak: {ukupni_trosak:.2f} € | Noćenja: {ukupno_nocenja}")

    #prikaži detalje
    def prikazi_detalje(self, event=None):
        sel = self.listbox.curselection()

        if not sel:
            messagebox.showinfo("Info", "Odaberite stavku za prikaz detalja.")
            return

        # koristimo mapu prikzanih stavki umjesto ponovnog filtriranja/sortiranja
        idx = sel[0]
        try:
            obj = self.prikaz_stavki[idx]
        except (IndexError, AttributeError):
            messagebox.showerror("Greška", "Neispravan odabir stavke.")
            return

        if isinstance(obj, Smjestaj):
            tekst = (f"Smještaj: {obj.naziv}\nLokacija: {obj.lokacija}\n"
                     f"Datum dolaska: {obj.datum_dolaska.isoformat()}\nDatum odlaska: {obj.datum_odlaska.isoformat()}\n"
                     f"Broj noćenja: {obj.broj_nocenja()}\nUkupni trošak: {obj.ukupni_trosak:.2f} €")
        else:
            tekst = (f"Aktivnost: {obj.naziv}\nLokacija: {obj.lokacija}\n"
                     f"Datum: {obj.datum.isoformat()}\nVrijeme: {obj.vrijeme}\nCijena: {obj.cijena:.2f} €\nNapomena: {obj.napomena}")
        messagebox.showinfo("Detalji stavke", tekst)

    #brisanje odabrane stavke
    def obrisi_odabrano(self):
        sel = self.listbox.curselection()
        
        if not sel:
            messagebox.showinfo("Info", "Odaberite stavku za brisanje.")
            return
        
        idx = sel[0]
        try:
            obj = self.prikaz_stavki[idx]
        except (IndexError, AttributeError):
            messagebox.showerror("Greška", "Neispravan odabir stavke.")
            return
        
        #brisanj iz liste
        try:
            self.stavke.remove(obj)
            self.update_listbox()
            self.status_set("Obrisano.")
        except ValueError:
            messagebox.showerror("Greška", "Nije moguće obrisati stavku.")

    #učitavanje u entry polja     
    def ucitaj(self):
        sel = self.listbox.curselection()
        
        if not sel:
            messagebox.showinfo("Info", "Odaberite stavku za uređivanje.")
            return

        idx = sel[0]
        try:
            self.odabrani_obj = self.prikaz_stavki[idx]
        except (IndexError, AttributeError):
            messagebox.showerror("Greška", "Neispravan odabir stavke.")
            return
        obj = self.odabrani_obj

        #učitavanje u entry polja
        if isinstance(obj, Smjestaj):
            self.tip.set("Smještaj")
            self.promijeni_polja()
            self.naziv_entry.delete(0, tk.END)
            self.naziv_entry.insert(0, obj.naziv)
            self.lokacija_entry.delete(0, tk.END)
            self.lokacija_entry.insert(0, obj.lokacija)
            self.dolazak_entry.delete(0, tk.END)
            self.dolazak_entry.insert(0, obj.datum_dolaska.isoformat())
            self.odlazak_entry.delete(0, tk.END)
            self.odlazak_entry.insert(0, obj.datum_odlaska.isoformat())
            self.trosak_entry.delete(0, tk.END)
            self.trosak_entry.insert(0, str(obj.ukupni_trosak))
        else:
            self.tip.set("Aktivnost")
            self.promijeni_polja()
            self.naziv_entry.delete(0, tk.END)
            self.naziv_entry.insert(0, obj.naziv)
            self.lokacija_entry.delete(0, tk.END)
            self.lokacija_entry.insert(0, obj.lokacija)
            self.aktivnost_datum_entry.delete(0, tk.END)
            self.aktivnost_datum_entry.insert(0, obj.datum.isoformat())
            self.aktivnost_vrijeme_entry.delete(0, tk.END)
            self.aktivnost_vrijeme_entry.insert(0, obj.vrijeme)
            self.aktivnost_cijena_entry.delete(0, tk.END)
            self.aktivnost_cijena_entry.insert(0, str(obj.cijena))
            self.aktivnost_napomena_entry.delete(0, tk.END)
            self.aktivnost_napomena_entry.insert(0, obj.napomena)

        #promjena gumba "Dodaj" u gumb "Spremi izmjenu"
        self.dodaj_gumb.config(text="Spremi izmjenu", command=self.spremi_izmjenu)

    #spremanje izmjene
    def spremi_izmjenu(self):
        if not hasattr(self, "odabrani_obj") or self.odabrani_obj is None:
            messagebox.showerror("Greška", "Nema odabrane stavke za izmjenu.")
            return

        try:
            tip = self.tip.get()
            naziv = self.naziv_entry.get().strip()
            lokacija = self.lokacija_entry.get().strip()

            #provjere popunjenosti
            if not naziv:
                messagebox.showwarning("Greška", "Naziv ne smije biti prazan.")
                return
            if not lokacija:
                messagebox.showwarning("Greška", "Lokacija ne smije biti prazna.")
                return
            
            if tip == "Smještaj":
                dolazak1 = datetime.strptime(self.dolazak_entry.get().strip(), "%Y-%m-%d").date()
                odlazak1 = datetime.strptime(self.odlazak_entry.get().strip(), "%Y-%m-%d").date()
                if odlazak1 <= dolazak1:
                    messagebox.showwarning("Greška", "Datum odlaska mora biti nakon datuma dolaska.")
                    return
                trosak1 = float(self.trosak_entry.get().strip())
                novi = Smjestaj(naziv, lokacija, dolazak1, odlazak1, trosak1)
            else:
                datum1 = datetime.strptime(self.aktivnost_datum_entry.get().strip(), "%Y-%m-%d").date()
                vrijeme1 = self.aktivnost_vrijeme_entry.get().strip()
                # validiraj vrijeme
                try:
                    t_parsed = datetime.strptime(vrijeme1, "%H:%M")
                    vrijeme1 = t_parsed.strftime("%H:%M")
                except ValueError:
                    messagebox.showwarning("Greška", "Vrijeme mora biti u formatu HH:MM, npr. 09:30.")
                    return
                cijena1 = float(self.aktivnost_cijena_entry.get().strip())
                napomena1 = self.aktivnost_napomena_entry.get().strip()
                novi = Aktivnost(naziv, lokacija, datum1, vrijeme1, cijena1, napomena1)

            #zamjena u glavnoj listi
            if self.odabrani_obj in self.stavke:
                i = self.stavke.index(self.odabrani_obj)
                self.stavke[i] = novi
                # resetiramo odabrani_obj kako bi se spriječile buduće greške
                self.odabrani_obj = None
            else:
                messagebox.showerror("Greška", "Stavka više ne postoji u listi.")
                return
            
            self.update_listbox()
            self.status_set("Stavka izmijenjena.")

            #vraćanje gumba na "Dodaj"
            self.dodaj_gumb.config(text="Dodaj", command=self.dodaj_stavku)

        #greška
        except Exception as e:
            messagebox.showerror("Greška", f"Neuspjelo spremanje izmjene: {e}")

        #čišćenje polja
        for entry in [self.naziv_entry, self.lokacija_entry, self.dolazak_entry,
                      self.odlazak_entry, self.trosak_entry, self.aktivnost_datum_entry,
                      self.aktivnost_vrijeme_entry, self.aktivnost_cijena_entry,
                      self.aktivnost_napomena_entry]:
            entry.delete(0, tk.END)

        self.tip.set("Smještaj")
        self.promijeni_polja()



# 4. Podatci - XML

    #spremanje xml
    def save_xml(self):
        if not self.stavke:
            if not messagebox.askyesno("Spremanje", "Nema stavki. Želite li ipak spremiti praznu datoteku?"):
                return
        path = "planer_putovanja.xml"
        root = ET.Element("itinerar")
        
        for s in self.stavke:
            if isinstance(s, Smjestaj):
                el = ET.SubElement(root, "smjestaj")
                for k,v in s.rječnik().items():
                    ET.SubElement(el, k).text = str(v)
            else:
                el = ET.SubElement(root, "aktivnost")
                for k,v in s.rječnik().items():
                    ET.SubElement(el, k).text = str(v)
                    
        tree = ET.ElementTree(root)
        try:
            tree.write(path, encoding="utf-8", xml_declaration=True)
            self.status_set(f"Spremljeno: {os.path.basename(path)}")
        except Exception as e:
            messagebox.showerror("Greška pri spremanju", str(e))

    #učitavanje XML
    def load_xml(self):
        path = "planer_putovanja.xml"
        
        if not os.path.exists(path):
            messagebox.showinfo("Info", "Datoteka ne postoji.")
            return

        try:
            tree = ET.parse(path)
            root = tree.getroot()
            nova = []

            for el in root:
                # sigurno dohvaćanje teksta (ako je None => prazan string)
                d = {child.tag: (child.text if child.text is not None else "") for child in el}
                if el.tag == "smjestaj":
                    try:
                        # provjera obaveznih polja
                        if not (d.get("datum_dolaska") and d.get("datum_odlaska") and d.get("ukupni_trosak") and d.get("naziv") and d.get("lokacija")):
                            # preskoči neispravnu stavku
                            continue
                        xml_dolazak = datetime.fromisoformat(d["datum_dolaska"]).date()
                        xml_odlazak = datetime.fromisoformat(d["datum_odlaska"]).date()
                        xml_trosak = float(d["ukupni_trosak"])
                        nova.append(Smjestaj(d["naziv"], d["lokacija"], xml_dolazak, xml_odlazak, xml_trosak))
                        
                    except Exception:
                        # preskoči stavku ako parse ne uspije
                        continue
                    
                elif el.tag == "aktivnost":
                    try:
                        if not (d.get("datum") and d.get("vrijeme") and d.get("cijena") and d.get("naziv") and d.get("lokacija")):
                            continue
                        xml_datum = datetime.fromisoformat(d["datum"]).date()
                        xml_vrijeme = d["vrijeme"]
                        # validiraj vrijeme format
                        try:
                            t_parsed = datetime.strptime(xml_vrijeme, "%H:%M")
                            xml_vrijeme = t_parsed.strftime("%H:%M")
                        except Exception:
                            continue
                        xml_cijena = float(d["cijena"])
                        xml_napomena = d.get("napomena", "")
                        nova.append(Aktivnost(d["naziv"], d["lokacija"], xml_datum, xml_vrijeme, xml_cijena, xml_napomena))
                        
                    except Exception:
                        continue

            self.stavke = nova
            self.update_listbox()
            self.status_set(f"Učitano: {os.path.basename(path)}")
            
        except Exception as e:
            messagebox.showerror("Greška pri učitavanju", f"Neuspjelo učitavanje: {e}")

    # statusna traka
    def statusna_traka(self):
        self.status = tk.StringVar()
        st = tk.Label(self, textvariable=self.status, bd=1, relief=tk.SUNKEN, anchor=tk.W, padx=6)
        st.pack(side=tk.BOTTOM, fill=tk.X, anchor="s")
        self.status_set("Spremno.")

    def status_set(self, text):
        self.status.set(text)

    #o aplikaciji prozor
    def o_aplikaciji(self):
        about = tk.Toplevel(self)
        about.title("O aplikaciji")
        about.geometry("380x220")
        about.transient(self)
        about.resizable(False, False)

        #logotip
        logo = tk.Label(about, text="TravelBuddy", font=("Segoe UI", 20, "bold"), fg=self.panel_color)
        logo.pack(pady=(12,4))
        tk.Label(about, text="Verzija: 1.0").pack()
        tk.Label(about, text="Autor: Luka Šop").pack()
        tk.Label(about, text="Kratki opis:\nPlaner putovanja za unos smještaja i aktivnosti.", justify=tk.CENTER).pack(pady=8)
        close = tk.Button(about, text="Zatvori", command=about.destroy)
        close.pack(pady=8)

#pokretanje aplikacije
if __name__ == "__main__":
    app = PlanerApp()
    app.mainloop()

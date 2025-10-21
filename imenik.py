import tkinter as tk
import csv

class Kontakt:
    def __init__(self,ime, email, telefon):
        self.ime=ime
        self.email=email
        self.telefon=telefon

    def __str__(self):
        return f'{self.ime}-{self.email}'

class ImenikApp:
    def __init__(self,root):
        self.root=root
        self.root.title('Jednostavni digitalni imenik')
        self.kontakti=[]

        frame = tk.Frame(self.root, padx=10, pady=10)
        frame.grid(row=0, column=0, sticky='NSEW')

        tk.Label(frame, text='Ime:').grid(row=0, column=0, sticky='E')
        tk.Label(frame, text='Email:').grid(row=1, column=0, sticky='E')
        tk.Label(frame, text='Telefon:').grid(row=2, column=0, sticky='E')

        self.entry_ime = tk.Entry(frame)
        self.entry_email = tk.Entry(frame)
        self.entry_telefon = tk.Entry(frame)

        self.entry_ime.grid(row=0, column=1, padx=5, pady=2)
        self.entry_email.grid(row=1, column=1, padx=5, pady=2)
        self.entry_telefon.grid(row=2, column=1, padx=5, pady=2)

        tk.Button(frame, text='Dodaj kontakt', command=self.dodaj_kontakt).grid(row=3, column=0, columnspan=2, pady=5)

        self.listbox = tk.Listbox(frame, height=10)
        self.scrollbar = tk.Scrollbar(frame, orient='vertical', command=self.listbox.yview)
        self.listbox.config(yscrollcommand=self.scrollbar.set)

        self.listbox.grid(row=4, column=0, columnspan=2, sticky='NSEW', pady=5)
        self.scrollbar.grid(row=4, column=2, sticky='NS')

        tk.Button(frame, text='Spremi kontakte', command=self.spremi_kontakte).grid(row=5, column=0, pady=5)
        tk.Button(frame, text='Učitaj kontakte', command=self.ucitaj_kontakte).grid(row=5, column=1, pady=5)


        tk.Button(frame, text='Obriši kontakt', command=self.obrisi_kontakt).grid(row=6, column=0, columnspan=2, pady=5)        

        frame.rowconfigure(4, weight=1)
        frame.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)

        self.ucitaj_kontakte()

    def dodaj_kontakt(self):
        if len(self.entry_ime.get()) >=3:
            ime = self.entry_ime.get()
        else:
            print('Nedovoljan broj znakova imena!')
            ime=False

        et=0
        for i in self.entry_email.get():
            if i=='@':
                et=et+1

        if et==1:
            email = self.entry_email.get()
        else:
            print('Neispravan oblik emaila')
            email=False

        if len(self.entry_telefon.get()) == 10:
            telefon = self.entry_telefon.get()
        else:
            print('Neispravan broj telefona')
            telefon=False

        if not ime or not email or not telefon:
            print('Sva polja moraju biti popunjena!')
            return

        kontakt = Kontakt(ime, email, telefon)
        self.kontakti.append(kontakt)
        self.osvjezi_listbox()

        self.entry_ime.delete(0, tk.END)
        self.entry_email.delete(0, tk.END)
        self.entry_telefon.delete(0, tk.END)

    def osvjezi_listbox(self):
        self.listbox.delete(0, tk.END)
        for kontakt in self.kontakti:
            self.listbox.insert(tk.END, str(kontakt))

    def spremi_kontakte(self):
        with open('kontakti.csv', 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            for k in self.kontakti:
                writer.writerow([k.ime, k.email, k.telefon])
        print('Kontakti su uspješno spremljeni!')

    def ucitaj_kontakte(self):
        self.kontakti=[]
        try:
            with open('kontakti.csv', 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                for red in reader:
                    if len(red) == 3:
                        ime, email, telefon = red
                        self.kontakti.append(Kontakt(ime, email, telefon))
            self.osvjezi_listbox()
        except FileNotFoundError:
            pass


    def obrisi_kontakt(self):
        try:
            indeks = self.listbox.curselection()[0]
            self.kontakti.pop(indeks)
            self.osvjezi_listbox()
            self.spremi_kontakte()
        except IndexError:
            print('Niste odabrali kontakt za brisanje!')

if __name__ == '__main__':
    root = tk.Tk()
    app = ImenikApp(root)
    root.mainloop()

import tkinter as tk


#Faza 1: Model Podataka (OOP temelj)
class ucenik:
    def __init__ (self,ime,prezime,razred):       #konstruktor

        self.ime=ime
        self.prezime=prezime          #atributi   
        self.razred=razred

    def __str__ (self):
        return f'{self.prezime} {self.ime} ({self.razred})'

ucenik1=ucenik('Pero','Perić','4.a')        #test
print(ucenik1)

#Faza 2: Izrada Sučelja (GUI Layout)
class EvidencijaApp:
    def __init__ (self,root):

#prozor i okviri
        self.root=root
        self.root.title('Evidencija učenika')
        self.root.geometry('500x400')
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        unos_frame = tk.Frame(self.root, padx=10, pady=10, bg='cyan')
        unos_frame.grid(row=0, column=0, sticky='EW')

        prikaz_frame = tk.Frame(self.root, padx=10, pady=10, bg='cyan')
        prikaz_frame.grid(row=1, column=0, sticky='NSEW')

        prikaz_frame.columnconfigure(0, weight=1)
        prikaz_frame.rowconfigure(0, weight=1)

#unos ime, prezime i razred
        tk.Label(unos_frame, text='Ime:',bg='cyan').grid(row=0, column=0, padx=5, pady=5, sticky='W')
        self.ime_entry = tk.Entry(unos_frame)
        self.ime_entry.grid(row=0, column=1, padx=5, pady=5, sticky='EW')

        tk.Label(unos_frame, text='Prezime:', bg='cyan').grid(row=1, column=0, padx=5, pady=5, sticky='W')
        self.prezime_entry = tk.Entry(unos_frame)
        self.prezime_entry.grid(row=1, column=1, padx=5, pady=5, sticky='EW')

        tk.Label(unos_frame, text='Razred:', bg='cyan').grid(row=2, column=0, padx=5, pady=5, sticky='W')
        self.razred_entry = tk.Entry(unos_frame)
        self.razred_entry.grid(row=2, column=1, padx=5, pady=5, sticky='EW')

#gumbi
        self.dodaj_gumb = tk.Button(unos_frame, text='Dodaj učenika',command=self.dodaj_ucenika, bg='green', fg='white')
        self.dodaj_gumb.grid(row=3, column=0, padx=5, pady=10)
        self.spremi_gumb = tk.Button(unos_frame, text='Spremi izmjene',command=self.spremi_izmjene, bg='blue',fg='white')
        self.spremi_gumb.grid(row=3, column=1, padx=5, pady=10, sticky='W')

#prikaz
        self.listbox = tk.Listbox(prikaz_frame)
        self.listbox.grid(row=0, column=0, sticky='NSEW')

        scrollbar = tk.Scrollbar(prikaz_frame, orient='vertical', command=self.listbox.yview)
        scrollbar.grid(row=0, column=1, sticky='NS')
        self.listbox.config(yscrollcommand=scrollbar.set)
        
        self.listbox.bind('<<ListboxSelect>>', self.odaberi_ucenika)


#Faza 3: Implementacija Logike (Funkcionalnost)

        self.ucenici=[]
        self.odabrani_ucenik_index = None

#dodavanje učenika
    def dodaj_ucenika(self):
        ime=self.ime_entry.get()
        prezime=self.prezime_entry.get()
        razred=self.razred_entry.get()

        if not ime or not prezime or not razred:
            print('Nisu sva polja ispunjena')
            return
        
        novi=ucenik(ime,prezime,razred)
        self.ucenici.append(novi)
        self.osvjezi_prikaz()
        self.ime_entry.delete(0, tk.END)
        self.prezime_entry.delete(0, tk.END)
        self.razred_entry.delete(0, tk.END)

#osvježavanje prikaza
    def osvjezi_prikaz(self):
            self.listbox.delete(0, tk.END)
            for ucenik in self.ucenici:
                self.listbox.insert(tk.END, ucenik)

#odabir učenika
    def odaberi_ucenika(self, event):
        odabrani_indeksi = self.listbox.curselection()
        if not odabrani_indeksi:
            return
        
        self.odabrani_ucenik_index = odabrani_indeksi[0]
        ucenik = self.ucenici[self.odabrani_ucenik_index]
        
        self.ime_entry.insert(0,ucenik.ime)
        self.prezime_entry.insert(0,ucenik.prezime)
        self.razred_entry.insert(0,ucenik.razred)

#spremanje izmjena
    def spremi_izmjene(self):
        if self.odabrani_ucenik_index == None:
            print('Nije odabran nijedan učenik')

        ime=self.ime_entry.get()
        prezime=self.prezime_entry.get()
        razred=self.razred_entry.get()

        ucenik=self.ucenici[self.odabrani_ucenik_index]
        ucenik.ime=ime
        ucenik.prezime=prezime
        ucenik.razred=razred

        self.osvjezi_prikaz()
        self.ime_entry.delete(0, tk.END)
        self.prezime_entry.delete(0, tk.END)
        self.razred_entry.delete(0, tk.END)
        self.odabrani_ucenik_index = None

#pokretanje       
if __name__ == '__main__':
    root = tk.Tk()
    app = EvidencijaApp(root)
    root.mainloop()

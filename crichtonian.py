#Maturantski projekt - Luka Šop
#Crichtonian - Bioinformatički sustav za rekonstrukciju DNA izumrlih organizama (dinosaura)

import os
import tkinter as tk
from pathlib import Path
from tkinter import END, LEFT, RIGHT, StringVar, ttk, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

import sqlite3
from datetime import datetime
from dataclasses import dataclass
from math import inf

#BAZA PODATAKA

SCHEMA = [
    """
    CREATE TABLE IF NOT EXISTS dinosauri (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        naziv TEXT NOT NULL,
        latinski_naziv TEXT NOT NULL,
        period TEXT,
        DNA_fragment TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS enzimi (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        naziv TEXT NOT NULL,
        prepoznaje_sekvencu TEXT NOT NULL,
        mjesto_reza INTEGER
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS moderni (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        naziv TEXT NOT NULL,
        latinski_naziv TEXT NOT NULL,
        DNA_sekvenca TEXT NOT NULL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS rekonstrukcije (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_dinosaura INTEGER NOT NULL,
        verzija TEXT NOT NULL,
        DNA_rekonstruirana TEXT NOT NULL,
        id_enzimi TEXT,
        id_donor TEXT,
        stopa_prezivjelih REAL,
        vijabilnost TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY(id_dinosaura) REFERENCES dinosauri(id)
    )
    """,
]

DEFAULT_DB = "crichtonian.db"


def get_connection(db_path: str = DEFAULT_DB):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database(db_path: str = DEFAULT_DB):
    connection = get_connection(db_path)
    cursor = connection.cursor()
    for statement in SCHEMA:
        cursor.execute(statement)

    connection.commit()
    return connection

#PODACI

#klasa dinosauri

@dataclass          #koristio sam dataclass dekorator da pojednostavim definiciju klasa i automatski generiram metode poput __init__ i __repr__
class Dinosaur:
    id: int = None
    naziv: str = ""
    latinski_naziv: str = ""
    period: str = ""
    DNA_fragment: str = ""

    #metode koje omogućuju dohvaćanje podataka iz baze i njihov prikaz
    
    @classmethod
    def from_row(cls, row): 
        return cls(
            id=row["id"],
            naziv=row["naziv"],
            latinski_naziv=row["latinski_naziv"],
            period=row["period"],
            DNA_fragment=row["DNA_fragment"],
        )

    @classmethod
    def create(cls, conn, naziv, latinski_naziv, period, DNA_fragment):
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO dinosauri (naziv, latinski_naziv, period, DNA_fragment) VALUES (?, ?, ?, ?)",
            (
                naziv.strip(),
                latinski_naziv.strip(),
                period.strip(),
                DNA_fragment.strip().upper(),
            ),
        )
        conn.commit()
        return cls(
            id=cursor.lastrowid,
            naziv=naziv.strip(),
            latinski_naziv=latinski_naziv.strip(),
            period=period.strip(),
            DNA_fragment=DNA_fragment.strip().upper(),
        )

    @classmethod
    def get_all(cls, conn):
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM dinosauri ORDER BY id")
        return [cls.from_row(row) for row in cursor.fetchall()]

    @classmethod
    def get_by_code(cls, conn, code):
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM dinosauri WHERE naziv = ?", (code.strip(),))
        row = cursor.fetchone()
        return cls.from_row(row) if row else None

    @classmethod
    def dohvati_po_latinskom_imenu(cls, conn, scientific_name):
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM dinosauri WHERE latinski_naziv = ?",
            (scientific_name.strip(),),
        )
        row = cursor.fetchone()
        return cls.from_row(row) if row else None

#klasa enzimi

@dataclass
class Enzim:
    id: int = None
    naziv: str = ""
    prepoznaje_sekvencu: str = ""
    mjesto_reza: int = None

#metode za dohvaćanje i prikaz podataka

    @classmethod
    def from_row(cls, row):
        return cls(
            id=row["id"],
            naziv=row["naziv"],
            prepoznaje_sekvencu=row["prepoznaje_sekvencu"],
            mjesto_reza=row["mjesto_reza"],
        )

    @classmethod
    def create(cls, conn, naziv, prepoznaje_sekvencu, mjesto_reza=None):
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO enzimi (naziv, prepoznaje_sekvencu, mjesto_reza) VALUES (?, ?, ?)",
            (naziv.strip(), prepoznaje_sekvencu.strip().upper(), mjesto_reza),
        )
        conn.commit()
        return cls(
            id=cursor.lastrowid,
            naziv=naziv.strip(),
            prepoznaje_sekvencu=prepoznaje_sekvencu.strip().upper(),
            mjesto_reza=mjesto_reza,
        )

    @classmethod
    def get_all(cls, conn):
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM enzimi ORDER BY id")
        return [cls.from_row(row) for row in cursor.fetchall()]

    @classmethod
    def get_by_name(cls, conn, name):
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM enzimi WHERE naziv = ?", (name.strip(),))
        row = cursor.fetchone()
        return cls.from_row(row) if row else None

#metoda koja osigurava ispravan format podataka
    def normalize(self):
        site = self.prepoznaje_sekvencu or ""
        try:
            cut_offset = (
                int(self.mjesto_reza)
                if self.mjesto_reza is not None and str(self.mjesto_reza).strip() != ""
                else 0
            )
        except (TypeError, ValueError):
            cut_offset = 0
        return Rekonstrukcija.normaliziraj_dna(site), cut_offset

#klasa moderni organizmi

@dataclass
class ModerniOrganizam:
    id: int = None
    naziv: str = ""
    latinski_naziv: str = ""
    DNA_sekvenca: str = ""

#metode za dohvaćanje i prikaz podataka
    @classmethod
    def from_row(cls, row):
        return cls(
            id=row["id"],
            naziv=row["naziv"],
            latinski_naziv=row["latinski_naziv"],
            DNA_sekvenca=row["DNA_sekvenca"],
        )

    @classmethod
    def create(cls, conn, naziv, latinski_naziv, DNA_sekvenca):
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO moderni (naziv, latinski_naziv, DNA_sekvenca) VALUES (?, ?, ?)",
            (naziv.strip(), latinski_naziv.strip(), DNA_sekvenca.strip().upper()),
        )
        conn.commit()
        return cls(
            id=cursor.lastrowid,
            naziv=naziv.strip(),
            latinski_naziv=latinski_naziv.strip(),
            DNA_sekvenca=DNA_sekvenca.strip().upper(),
        )

    @classmethod
    def get_all(cls, conn):
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM moderni ORDER BY id")
        return [cls.from_row(row) for row in cursor.fetchall()]

    @classmethod
    def dohvati_po_latinskom_imenu(cls, conn, scientific_name):
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM moderni WHERE latinski_naziv = ?", (scientific_name.strip(),)
        )
        row = cursor.fetchone()
        return cls.from_row(row) if row else None

#klasa rekonstrukcija

@dataclass
class Rekonstrukcija:
    id: int = None
    id_dinosaura: int = None
    verzija: str = ""
    DNA_rekonstruirana: str = ""
    id_enzimi: str = None
    id_donor: str = None
    stopa_prezivjelih: float = None
    vijabilnost: str = None
    created_at: str = ""

#metode za dohvaćanje i prikaz podataka

    @classmethod
    def from_row(cls, row):
        return cls(
            id=row["id"],
            id_dinosaura=row["id_dinosaura"],
            verzija=row["verzija"],
            DNA_rekonstruirana=row["DNA_rekonstruirana"],
            id_enzimi=row["id_enzimi"],
            id_donor=row["id_donor"],
            stopa_prezivjelih=row["stopa_prezivjelih"],
            vijabilnost=row["vijabilnost"],
            created_at=row["created_at"],
        )

    @classmethod
    def create(
        cls,
        conn,
        id_dinosaura,
        verzija,
        DNA_rekonstruirana,
        id_enzimi,
        id_donor,
        stopa_prezivjelih=None,
        vijabilnost=None,
    ):
        cursor = conn.cursor()
        enzimi_str = ",".join(str(e) for e in id_enzimi) if id_enzimi else None
        donor_str = ",".join(str(d) for d in id_donor) if id_donor else None
        cursor.execute(
            "INSERT INTO rekonstrukcije (id_dinosaura, verzija, DNA_rekonstruirana, id_enzimi, id_donor, stopa_prezivjelih, vijabilnost, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                id_dinosaura,
                verzija,
                DNA_rekonstruirana.strip().upper(),
                enzimi_str,
                donor_str,
                float(stopa_prezivjelih) if stopa_prezivjelih is not None else None,
                vijabilnost,
                datetime.utcnow().isoformat(),
            ),
        )
        conn.commit()
        return cls(
            id=cursor.lastrowid,
            id_dinosaura=id_dinosaura,
            verzija=verzija,
            DNA_rekonstruirana=DNA_rekonstruirana.strip().upper(),
            id_enzimi=enzimi_str,
            id_donor=donor_str,
            stopa_prezivjelih=(
                float(stopa_prezivjelih) if stopa_prezivjelih is not None else None
            ),
            vijabilnost=vijabilnost,
            created_at=datetime.utcnow().isoformat(),
        )

    @classmethod
    def get_all(cls, conn):
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                r.*,
                d.naziv AS dinosaur_naziv
            FROM rekonstrukcije r
            JOIN dinosauri d ON r.id_dinosaura = d.id
            ORDER BY r.id
            """)
        return [cls.from_row(row) for row in cursor.fetchall()]

    @classmethod
    def get_by_dinosaur_and_version(cls, conn, dinosaur_id, version):
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM rekonstrukcije WHERE id_dinosaura = ? AND verzija = ?",
            (dinosaur_id, version),
        )
        row = cursor.fetchone()
        return cls.from_row(row) if row else None

#metoda za azuriranje vijabilnosti rekonstrukcije
    @classmethod
    def azuriraj_vijabilnost(
        cls, conn, reconstruction_id, stopa_prezivjelih, vijabilnost
    ):
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE rekonstrukcije SET stopa_prezivjelih = ?, vijabilnost = ? WHERE id = ?",
            (float(stopa_prezivjelih), vijabilnost, reconstruction_id),
        )
        conn.commit()

#podaci o donorima i enzimima korišteni u rekonstrukciji

    @property
    def enzyme_ids(self):
        if not self.id_enzimi:
            return []
        return [int(i.strip()) for i in str(self.id_enzimi).split(",") if i.strip()]

    @property
    def donor_ids(self):
        if not self.id_donor:
            return []
        return [int(i.strip()) for i in str(self.id_donor).split(",") if i.strip()]

#osigurava ispravnost formata dna
    @staticmethod
    def normaliziraj_dna(sekvenca: str) -> str:
        return sekvenca.strip().upper()

#pronalaženje rupa u dna
    @classmethod
    def pronadi_rupe(cls, sekvenca: str):
        sekvenca = cls.normaliziraj_dna(sekvenca)
        gaps = []
        start = None
        for indeks, letter in enumerate(sekvenca):
            if letter == "-" and start is None:
                start = indeks
            elif letter != "-" and start is not None:
                gaps.append((start, indeks - 1))
                start = None
        if start is not None:
            gaps.append((start, len(sekvenca) - 1))
        return gaps

#izračun sličnosti između dvije dna sekvence
    @classmethod
    def izracunaj_slicnost(cls, seq1: str, seq2: str) -> float:
        seq1 = cls.normaliziraj_dna(seq1)
        seq2 = cls.normaliziraj_dna(seq2)
        if not seq1 or not seq2:
            return 0.0
        length = min(len(seq1), len(seq2))
        matches = sum(1 for a, b in zip(seq1[:length], seq2[:length]) if a == b)
        normalized = matches / max(len(seq1), len(seq2))
        return round(normalized * 100.0, 2)

#metode za rad enzima
    @staticmethod
    def normalize_enzyme(enzyme):
        if isinstance(enzyme, dict):
            site = enzyme.get("prepoznaje_sekvencu") or enzyme.get(
                "recognition_site", ""
            )
            cut_pos = enzyme.get("mjesto_reza")
        else:
            site = (
                enzyme.prepoznaje_sekvencu
                if hasattr(enzyme, "prepoznaje_sekvencu")
                else enzyme.get("recognition_site", "")
            )
            cut_pos = (
                enzyme.mjesto_reza
                if hasattr(enzyme, "mjesto_reza")
                else enzyme.get("mjesto_reza")
            )
        try:
            cut_offset = (
                int(cut_pos)
                if cut_pos is not None and str(cut_pos).strip() != ""
                else 0
            )
        except (TypeError, ValueError):
            cut_offset = 0
        return Rekonstrukcija.normaliziraj_dna(site), cut_offset

    @classmethod
    def pronadi_sekvencu_enzima(cls, sekvenca: str, site: str) -> list:
        sekvenca = cls.normaliziraj_dna(sekvenca)
        site = cls.normaliziraj_dna(site)
        if not site:
            return []
        pozicije = []
        start = 0
        while True:
            pozicija = sekvenca.find(site, start)
            if pozicija == -1:
                break
            pozicije.append(pozicija)
            start = pozicija + 1
        return pozicije

    @classmethod
    def pronadi_mjesto_reza(cls, sekvenca: str, enzyme) -> list:
        site, cut_offset = cls.normalize_enzyme(enzyme)
        pozicije = []
        if not site:
            return pozicije
        for site_start in cls.pronadi_sekvencu_enzima(sekvenca, site):
            cut_index = site_start + cut_offset
            if 0 <= cut_index <= len(sekvenca):
                pozicije.append(cut_index)
        return pozicije

    @classmethod
    def raspon_enzima(cls, sekvenca: str, raspon_rupe: tuple, enzyme) -> list:
        start, end = raspon_rupe
        site, cut_offset = cls.normalize_enzyme(enzyme)
        if not site:
            return []
        rezovi = []
        for site_start in cls.pronadi_sekvencu_enzima(sekvenca, site):
            site_end = site_start + len(site)
            cut_index = site_start + cut_offset
            if 0 <= cut_index <= len(sekvenca):
                if site_start >= 0 and site_end <= start:
                    pomak = cut_index - start
                    rezovi.append(("left", pomak))
                elif site_start >= end + 1 and site_end <= len(sekvenca):
                    pomak = cut_index - (end + 1)
                    rezovi.append(("right", pomak))
                elif site_start < start and site_end > end:
                    pomak = cut_index - start
                    rezovi.append(("internal", pomak))
        return rezovi

    @classmethod
    def rupa_u_rasponu(cls, sekvenca: str, raspon_rupe: tuple, enzyme) -> bool:
        sides = cls.raspon_enzima(sekvenca, raspon_rupe, enzyme)
        has_left = any(side == "left" for side, _ in sides)
        has_right = any(side == "right" for side, _ in sides)
        return has_left and has_right

    @classmethod
    def is_enzyme_compatible_with_donor(
        cls,
        dna_sekvenca: str,
        raspon_rupe: tuple,
        sekvenca_donora: str,
        enzyme,
        velicina_bocnog_podrucja: int = 15,
    ) -> bool:
        dna = cls.normaliziraj_dna(dna_sekvenca)
        donor = cls.normaliziraj_dna(sekvenca_donora)
        if not cls.rupa_u_rasponu(dna, raspon_rupe, enzyme):
            return False
        start, end = raspon_rupe
        gap_len = end - start + 1
        lijeva_strana = dna[max(0, start - velicina_bocnog_podrucja) : start]
        desna_strana = dna[end + 1 : end + 1 + velicina_bocnog_podrucja]
        velicina_prozora = len(lijeva_strana) + gap_len + len(desna_strana)
        if velicina_prozora > len(donor) or velicina_prozora == 0:
            return False
        enzyme_sides = cls.raspon_enzima(dna, raspon_rupe, enzyme)
        for i in range(0, len(donor) - velicina_prozora + 1):
            if cls.raspon_donor(
                donor,
                i,
                i + velicina_prozora,
                enzyme,
                enzyme_sides,
                len(lijeva_strana),
                gap_len,
            ):
                return True
        return False

    @classmethod
    def pronadi_enzim_kandidat(
        cls, dna_sekvenca: str, enzymes: list, velicina_bocnog_podrucja: int = 15
    ):
        dna_sekvenca = Rekonstrukcija.normaliziraj_dna(dna_sekvenca)
        gaps = cls.pronadi_rupe(dna_sekvenca)
        kandidati = []
        for gap_index, (start, end) in enumerate(gaps, start=1):
            gap_candidates = []
            for enzyme in enzymes:
                if cls.rupa_u_rasponu(dna_sekvenca, (start, end), enzyme):
                    gap_candidates.append(enzyme)
            kandidati.append(
                {
                    "gap_index": gap_index,
                    "range": (start, end),
                    "enzymes": gap_candidates,
                }
            )
        return kandidati

    @classmethod
    def raspon_donor(
        cls,
        sekvenca: str,
        pocetak_prozora: int,
        kraj_prozora: int,
        enzyme,
        gap_cuts: list,
        left_flank_len: int,
        gap_len: int,
    ) -> bool:
        site, cut_offset = cls.normalize_enzyme(enzyme)
        if not site:
            return False
        window_gap_start = pocetak_prozora + left_flank_len
        window_gap_end = window_gap_start + gap_len
        pronadeno_lijevo = False
        pronadeno_desno = False
        for site_start in cls.pronadi_sekvencu_enzima(sekvenca, site):
            if not (pocetak_prozora <= site_start < kraj_prozora):
                continue
            site_end = site_start + len(site)
            cut_index = site_start + cut_offset
            if not (pocetak_prozora <= cut_index <= kraj_prozora):
                continue
            for side, pomak in gap_cuts:
                if (
                    side == "left"
                    and site_start >= pocetak_prozora
                    and site_end <= window_gap_start
                    and cut_index == window_gap_start + pomak
                ):
                    pronadeno_lijevo = True
                if (
                    side == "right"
                    and site_start >= window_gap_end
                    and site_end <= kraj_prozora
                    and cut_index == window_gap_end + pomak
                ):
                    pronadeno_desno = True
        return pronadeno_lijevo and pronadeno_desno

    @classmethod
    def pronadi_donor_kandidat(
        cls,
        sekvenca_dinosaura: str,
        raspon_rupe: tuple,
        modern_organisms: list,
        enzyme=None,
        velicina_bocnog_podrucja: int = 15,
        najvise_kandidata: int = 5,
    ):
        dna = cls.normaliziraj_dna(sekvenca_dinosaura)
        start, end = raspon_rupe
        duljina_rupe = end - start + 1
        lijeva_strana = dna[max(0, start - velicina_bocnog_podrucja) : start]
        desna_strana = dna[end + 1 : end + 1 + velicina_bocnog_podrucja]
        kandidati = []
        enzyme_sides = (
            cls.raspon_enzima(dna, raspon_rupe, enzyme) if enzyme is not None else None
        )
        enzyme_constraints = enzyme is not None and bool(enzyme_sides)
        for organism in modern_organisms:
            sekvenca = (
                cls.normaliziraj_dna(
                    organism.get("DNA_sekvenca")
                    if isinstance(organism, dict)
                    else organism["DNA_sekvenca"]
                )
                if isinstance(organism, dict)
                else cls.normaliziraj_dna(organism["DNA_sekvenca"])
            )
            if not sekvenca and isinstance(organism, dict):
                sekvenca = cls.normaliziraj_dna(organism.get("dna_sequence", ""))
            velicina_prozora = len(lijeva_strana) + duljina_rupe + len(desna_strana)
            if velicina_prozora > len(sekvenca):
                continue
            najbolja_ocjena = 0.0
            najbolji_segment = None
            najbolja_kompatibilnost = False
            for i in range(0, len(sekvenca) - velicina_prozora + 1):
                window = sekvenca[i : i + velicina_prozora]
                window_compatible = True
                if enzyme_constraints:
                    window_compatible = cls.raspon_donor(
                        sekvenca,
                        i,
                        i + velicina_prozora,
                        enzyme,
                        enzyme_sides,
                        len(lijeva_strana),
                        duljina_rupe,
                    )
                    if not window_compatible:
                        continue
                lijevi_prozor = window[: len(lijeva_strana)]
                desni_prozor = window[-len(desna_strana) :] if desna_strana else ""
                score = 0.0
                if lijeva_strana:
                    score += cls.izracunaj_slicnost(lijeva_strana, lijevi_prozor)
                if desna_strana:
                    score += cls.izracunaj_slicnost(desna_strana, desni_prozor)
                score = score / (
                    1
                    if not lijeva_strana and not desna_strana
                    else (2 if lijeva_strana and desna_strana else 1)
                )
                if (
                    najbolji_segment is None
                    or score > najbolja_ocjena
                    or (
                        score == najbolja_ocjena
                        and window_compatible
                        and not najbolja_kompatibilnost
                    )
                ):
                    najbolja_ocjena = score
                    najbolji_segment = window
                    najbolja_kompatibilnost = window_compatible
            if najbolji_segment is not None:
                kandidati.append(
                    {
                        "organism": organism,
                        "score": round(najbolja_ocjena, 2),
                        "segment": najbolji_segment,
                        "gap_fill": najbolji_segment[
                            len(lijeva_strana) : len(lijeva_strana) + duljina_rupe
                        ],
                        "enzyme_compatible": najbolja_kompatibilnost,
                    }
                )
        kandidati.sort(
            key=lambda item: (item["score"], item["enzyme_compatible"]), reverse=True
        )
        return kandidati[:najvise_kandidata]

    @classmethod
    def primijeni_enzim(
        cls,
        sekvenca_dinosaura,
        sekvenca_donora,
        enzyme,
        raspon_rupe,
        velicina_bocnog_podrucja=8,
    ):
        dino = cls.normaliziraj_dna(sekvenca_dinosaura)
        donor = cls.normaliziraj_dna(sekvenca_donora)
        start, end = raspon_rupe
        duljina_rupe = end - start + 1
        lijeva_strana = dino[max(0, start - velicina_bocnog_podrucja) : start]
        desna_strana = dino[end + 1 : end + 1 + velicina_bocnog_podrucja]
        velicina_prozora = len(lijeva_strana) + duljina_rupe + len(desna_strana)
        if velicina_prozora > len(donor) or velicina_prozora <= 0:
            return dino
        najbolja_ocjena = 0.0
        best_window = None
        best_window_start = 0
        najbolja_kompatibilnost = False
        for i in range(len(donor) - velicina_prozora + 1):
            window = donor[i : i + velicina_prozora]
            lijevi_prozor = window[: len(lijeva_strana)]
            desni_prozor = window[-len(desna_strana) :] if desna_strana else ""
            score = 0.0
            if lijeva_strana:
                score += cls.izracunaj_slicnost(lijeva_strana, lijevi_prozor)
            if desna_strana:
                score += cls.izracunaj_slicnost(desna_strana, desni_prozor)
            score = score / (
                1
                if not lijeva_strana and not desna_strana
                else (2 if lijeva_strana and desna_strana else 1)
            )
            window_compatible = True
            if enzyme is not None:
                enzyme_sides = cls.raspon_enzima(dino, raspon_rupe, enzyme)
                if enzyme_sides:
                    window_compatible = cls.raspon_donor(
                        donor,
                        i,
                        i + velicina_prozora,
                        enzyme,
                        enzyme_sides,
                        len(lijeva_strana),
                        duljina_rupe,
                    )
                else:
                    window_compatible = False
            if (
                best_window is None
                or score > najbolja_ocjena
                or (
                    score == najbolja_ocjena
                    and window_compatible
                    and not najbolja_kompatibilnost
                )
            ):
                najbolja_ocjena = score
                best_window = window
                best_window_start = i
                najbolja_kompatibilnost = window_compatible
        if best_window is None:
            return dino
        if enzyme is not None and najbolja_kompatibilnost:
            site, cut_offset = cls.normalize_enzyme(enzyme)
            dino_cuts = []
            for site_start in cls.pronadi_sekvencu_enzima(dino, site):
                cut_index = site_start + cut_offset
                if (
                    max(0, start - velicina_bocnog_podrucja)
                    <= cut_index
                    <= end + 1 + velicina_bocnog_podrucja
                ):
                    dino_cuts.append(cut_index)
            if len(dino_cuts) >= 2:
                pocetak_segmenta = min(dino_cuts)
                kraj_segmenta = max(dino_cuts) + 1
                rezovi_donorovog_prozora = []
                for site_start in cls.pronadi_sekvencu_enzima(donor, site):
                    cut_index = site_start + cut_offset
                    window_cut = cut_index - best_window_start
                    if 0 <= window_cut <= velicina_prozora:
                        rezovi_donorovog_prozora.append(window_cut)
                if len(rezovi_donorovog_prozora) >= 2:
                    pocetak_donorovog_segmenta = min(rezovi_donorovog_prozora)
                    kraj_donorovog_segmenta = max(rezovi_donorovog_prozora) + 1
                    fill_segment = best_window[
                        pocetak_donorovog_segmenta:kraj_donorovog_segmenta
                    ]
                    return dino[:pocetak_segmenta] + fill_segment + dino[kraj_segmenta:]
        fill_segment = best_window[
            len(lijeva_strana) : len(lijeva_strana) + duljina_rupe
        ]
        return cls.popuni_rupu(dino, raspon_rupe, fill_segment)

    @staticmethod
    def popuni_rupu(dna_sekvenca: str, raspon_rupe: tuple, fill_segment: str) -> str:
        sekvenca = Rekonstrukcija.normaliziraj_dna(dna_sekvenca)
        start, end = raspon_rupe
        if len(fill_segment) != end - start + 1:
            raise ValueError("Donor segment length must match gap length.")
        return sekvenca[:start] + fill_segment + sekvenca[end + 1 :]

    @classmethod
    def build_distance_matrix(cls, zapisi):
        oznake = [record["label"] for record in zapisi]
        sequences = [cls.normaliziraj_dna(record["sequence"]) for record in zapisi]
        n = len(sequences)
        matrica = [[0.0] * n for _ in range(n)]
        for i in range(n):
            for j in range(i + 1, n):
                seq1, seq2 = sequences[i], sequences[j]
                length = min(len(seq1), len(seq2))
                if length == 0:
                    distance = 1.0
                else:
                    mismatches = sum(
                        1 for a, b in zip(seq1[:length], seq2[:length]) if a != b
                    )
                    distance = (mismatches + abs(len(seq1) - len(seq2))) / max(
                        len(seq1), len(seq2)
                    )
                matrica[i][j] = matrica[j][i] = round(distance, 4)
        return oznake, matrica

    @classmethod
    def build_upgma_tree(cls, oznake, matrica):
        clusters = [[Filogenetika(label=label)] for label in oznake]
        distances = [row[:] for row in matrica]
        while len(clusters) > 1:
            n = len(distances)
            min_dist = inf
            pair = (0, 1)
            for i in range(n):
                for j in range(i + 1, n):
                    if distances[i][j] < min_dist:
                        min_dist = distances[i][j]
                        pair = (i, j)
            i, j = pair
            lijevi_klaster = clusters[i]
            desni_klaster = clusters[j]
            novi_cvor = Filogenetika(
                left=lijevi_klaster[0],
                right=desni_klaster[0],
                label=f"({lijevi_klaster[0].label},{desni_klaster[0].label})",
                distance=min_dist,
            )
            novi_klaster = [novi_cvor]
            clusters = [clusters[k] for k in range(len(clusters)) if k not in pair]
            clusters.append(novi_klaster)
            nove_udaljenosti = []
            for k in range(len(distances)):
                if k in pair:
                    continue
                d_ik = distances[i][k]
                d_jk = distances[j][k]
                nove_udaljenosti.append(round((d_ik + d_jk) / 2, 4))
            nova_matrica = []
            indeksi = [k for k in range(len(distances)) if k not in pair]
            for p, k in enumerate(indeksi):
                row = [distances[k][q] for q in indeksi]
                row.append(nove_udaljenosti[p])
                nova_matrica.append(row)
            nova_matrica.append(nove_udaljenosti + [0.0])
            distances = nova_matrica
        return clusters[0][0] if clusters else None

#rad sa podacima u bazi podataka
def dodaj_dinosaur(conn, naziv, latinski_naziv, period, DNA_fragment):
    return Dinosaur.create(conn, naziv, latinski_naziv, period, DNA_fragment)


def dodaj_enzim(conn, naziv, prepoznaje_sekvencu, mjesto_reza=None):
    return Enzim.create(conn, naziv, prepoznaje_sekvencu, mjesto_reza)


def dodaj_moderni_organizam(conn, naziv, latinski_naziv, DNA_sekvenca):
    return ModerniOrganizam.create(conn, naziv, latinski_naziv, DNA_sekvenca)


def azuriraj_dinosaur(conn, dinosaur_id, naziv, latinski_naziv, period, DNA_fragment):
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE dinosauri SET naziv = ?, latinski_naziv = ?, period = ?, DNA_fragment = ? WHERE id = ?",
        (naziv, latinski_naziv, period, DNA_fragment, dinosaur_id),
    )
    conn.commit()


def izbrisi_dinosaur(conn, dinosaur_id):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM dinosauri WHERE id = ?", (dinosaur_id,))
    conn.commit()


def azuriraj_enzim(conn, enzyme_id, naziv, prepoznaje_sekvencu, mjesto_reza=None):
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE enzimi SET naziv = ?, prepoznaje_sekvencu = ?, mjesto_reza = ? WHERE id = ?",
        (naziv, prepoznaje_sekvencu, mjesto_reza, enzyme_id),
    )
    conn.commit()


def izbrisi_enzim(conn, enzyme_id):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM enzimi WHERE id = ?", (enzyme_id,))
    conn.commit()


def azuriraj_moderni_organizam(conn, organism_id, naziv, latinski_naziv, DNA_sekvenca):
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE moderni SET naziv = ?, latinski_naziv = ?, DNA_sekvenca = ? WHERE id = ?",
        (naziv, latinski_naziv, DNA_sekvenca, organism_id),
    )
    conn.commit()


def izbrisi_moderni_organizam(conn, organism_id):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM moderni WHERE id = ?", (organism_id,))
    conn.commit()


def dodaj_rekonstrukcija(
    conn,
    id_dinosaura,
    verzija,
    DNA_rekonstruirana,
    id_enzimi,
    id_donor,
    stopa_prezivjelih=None,
    vijabilnost=None,
):
    reconstruction = Rekonstrukcija.create(
        conn,
        id_dinosaura,
        verzija,
        DNA_rekonstruirana,
        id_enzimi,
        id_donor,
        stopa_prezivjelih,
        vijabilnost,
    )
    return reconstruction.id


def azuriraj_vijabilnost(conn, reconstruction_id, stopa_prezivjelih, vijabilnost):
    Rekonstrukcija.azuriraj_vijabilnost(
        conn, reconstruction_id, stopa_prezivjelih, vijabilnost
    )


def get_all_dinosaurs(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM dinosauri ORDER BY id")
    return cursor.fetchall()


def get_all_enzymes(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM enzimi ORDER BY id")
    return cursor.fetchall()


def get_all_modern_organisms(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM moderni ORDER BY id")
    return cursor.fetchall()


def get_all_reconstructions(conn):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            r.*,
            d.naziv AS dinosaur_naziv
        FROM rekonstrukcije r
        JOIN dinosauri d ON r.id_dinosaura = d.id
        ORDER BY r.id
        """)
    rows = cursor.fetchall()
    result = []
    for row in rows:
        row_dict = dict(row)
        enzimi_ids = row_dict.get("id_enzimi", "")
        donor_ids = row_dict.get("id_donor", "")
        enzimi_list = []
        donor_list = []
        if enzimi_ids:
            for eid in str(enzimi_ids).split(","):
                eid = eid.strip()
                if eid:
                    enzyme_row = cursor.execute(
                        "SELECT naziv FROM enzimi WHERE id = ?", (int(eid),)
                    ).fetchone()
                    if enzyme_row:
                        enzimi_list.append(enzyme_row["naziv"])
        if donor_ids:
            for did in str(donor_ids).split(","):
                did = did.strip()
                if did:
                    donor_row = cursor.execute(
                        "SELECT naziv FROM moderni WHERE id = ?", (int(did),)
                    ).fetchone()
                    if donor_row:
                        donor_list.append(donor_row["naziv"])
        row_dict["enzimi_nazivi"] = ", ".join(enzimi_list) if enzimi_list else ""
        row_dict["donor_nazivi"] = ", ".join(donor_list) if donor_list else ""
        result.append(row_dict)
    return result


def get_dinosaur(conn, dinosaur_id):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM dinosauri WHERE id = ?", (dinosaur_id,))
    return cursor.fetchone()


def get_modern_organism(conn, organism_id):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM moderni WHERE id = ?", (organism_id,))
    return cursor.fetchone()


def get_reconstruction_version(conn, dinosaur_id):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT verzija FROM rekonstrukcije WHERE id_dinosaura = ? ORDER BY id DESC LIMIT 1",
        (dinosaur_id,),
    )
    row = cursor.fetchone()
    return row[0] if row else None


def get_dinosaur_by_code(conn, code):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM dinosauri WHERE naziv = ?", (code.strip(),))
    return cursor.fetchone()


def get_dinosaur_by_scientific_name(conn, scientific_name):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM dinosauri WHERE latinski_naziv = ?", (scientific_name.strip(),)
    )
    return cursor.fetchone()


def get_enzyme_by_name(conn, name):
    return Enzim.get_by_name(conn, name)


def get_modern_organism_by_scientific_name(conn, scientific_name):
    return ModerniOrganizam.dohvati_po_latinskom_imenu(conn, scientific_name)

#FILOGENETSKO STABLO
#izrada filogenetskih stabala

@dataclass
class Filogenetika:
    left: object = None
    right: object = None
    label: str = ""
    distance: float = 0.0

    def grananje(self):
        return self.left is None and self.right is None


DB_PATH = os.path.join(Path(__file__).parent, "crichtonian.db")


#KORISNIČKO SUČELJE

class CrichtonianApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Crichtonian - Rekonstrukcija DNA")
        self.geometry("1100x700")
        self.resizable(True, True)
        self.conn = initialize_database(DB_PATH)
        self.selected_dinosaur_id = None
        self.odabrana_rupa = None
        self.id_odabranog_donora = None
        self.selected_reconstruction_id = None
        self.selected_dino_item_id = None
        self.selected_enzyme_item_id = None
        self.selected_modern_item_id = None
        self.enzymes_for_gap = []
        self.kandidati_donora = []
        self.current_reconstructed_sequence = None
        self.used_enzyme_ids = []
        self.used_donor_ids = []

        self.style = ttk.Style(self)
        self.style.theme_use("clam")
        self.style.configure(
            "TNotebook", tabposition="n", background="#0F1419", borderwidth=0
        )
        self.style.configure(
            "TNotebook.Tab",
            background="#1A1A2E",
            foreground="#E0E0E0",
            padding=(12, 8),
            font=("Segoe UI", 10, "bold"),
        )
        self.style.map(
            "TNotebook.Tab",
            background=[("selected", "#00D4FF")],
            foreground=[("selected", "#1A1A2E")],
        )
        self.style.configure("TFrame", background="#0F1419")
        self.style.configure(
            "TLabelframe",
            background="#0F1419",
            foreground="#E0E0E0",
            borderwidth=2,
            relief="groove",
        )
        self.style.configure(
            "TLabelframe.Label",
            background="#0F1419",
            foreground="#00D4FF",
            font=("Segoe UI", 11, "bold"),
        )
        self.style.configure(
            "TLabel",
            background="#0F1419",
            foreground="#E0E0E0",
            font=("Segoe UI", 9, "bold"),
        )
        self.style.configure(
            "TButton",
            background="#4ECDC4",
            foreground="#1A1A2E",
            font=("Segoe UI", 9, "bold"),
            padding=8,
            borderwidth=0,
            relief="flat",
        )
        self.style.map(
            "TButton",
            background=[("active", "#26A69A")],
            foreground=[("active", "#1A1A2E")],
        )
        self.style.configure(
            "TEntry",
            fieldbackground="#2A2A3E",
            foreground="#FFFFFF",
            background="#2A2A3E",
            insertcolor="#00D4FF",
            borderwidth=1,
            relief="flat",
        )
        self.style.configure(
            "TCombobox",
            fieldbackground="#2A2A3E",
            foreground="#FFFFFF",
            background="#2A2A3E",
            borderwidth=1,
            relief="flat",
        )
        self.style.configure(
            "Treeview",
            background="#2A2A3E",
            fieldbackground="#2A2A3E",
            foreground="#E0E0E0",
            rowheight=26,
            bordercolor="#0F1419",
            borderwidth=1,
            relief="flat",
        )
        self.style.configure(
            "Treeview.Heading",
            background="#1A1A2E",
            foreground="#00D4FF",
            font=("Segoe UI", 9, "bold"),
            borderwidth=1,
            relief="raised",
        )
        self.style.map(
            "Treeview",
            background=[("selected", "#FF6B6B")],
            foreground=[("selected", "#FFFFFF")],
        )
        self.configure(bg="#0F1419")

        main_frame = tk.Frame(self, bg="#0F1419")
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        header_frame = tk.Frame(main_frame, bg="#1A1A2E", height=80)
        header_frame.grid(row=0, column=0, sticky="ew")
        header_frame.pack_propagate(False)

        logo_label = tk.Label(
            header_frame, text="🧬", font=("Segoe UI", 36), bg="#1A1A2E", fg="#00D4FF"
        )
        logo_label.pack(side="left", padx=20, pady=10)

        title_label = tk.Label(
            header_frame,
            text="Crichtonian",
            font=("Segoe UI", 24, "bold"),
            bg="#1A1A2E",
            fg="#E0E0E0",
        )
        title_label.pack(side="left", padx=10, pady=10)

        subtitle_label = tk.Label(
            header_frame,
            text="Bioinformatički sustav za rekonstrukciju DNA",
            font=("Segoe UI", 12),
            bg="#1A1A2E",
            fg="#4ECDC4",
        )
        subtitle_label.pack(side="left", padx=10, pady=15)

        about_button = ttk.Button(
            header_frame,
            text="O aplikaciji",
            command=self.show_about_dialog,
        )
        about_button.pack(side="right", padx=20, pady=20)

        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

        self.status_bar = tk.Label(
            main_frame,
            text="Spremno",
            bd=1,
            relief=tk.SUNKEN,
            anchor=tk.W,
            bg="#1A1A2E",
            fg="#E0E0E0",
            font=("Segoe UI", 9),
        )
        self.status_bar.grid(row=2, column=0, sticky="ew", pady=2)

        self.data_tab = ttk.Frame(self.notebook)
        self.reconstruction_tab = ttk.Frame(self.notebook)
        self.phylo_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.data_tab, text="Podaci i unosi")
        self.notebook.add(self.reconstruction_tab, text="Rekonstrukcija")
        self.notebook.add(self.phylo_tab, text="Filogenetsko stablo")

        self.build_data_tab()
        self.build_reconstruction_tab()
        self.build_phylo_tab()
        self.osvjezi_gui()

    def set_status(self, text):
        self.status_bar.config(text=text)
        self.update_idletasks()

#prozor s informacijama o aplikaciji

    def show_about_dialog(self):
        about_window = tk.Toplevel(self)
        about_window.title("O aplikaciji")
        about_window.configure(bg="#1A1A2E")
        about_window.resizable(False, False)
        about_window.transient(self)
        about_window.grab_set()
        about_frame = tk.Frame(about_window, bg="#1A1A2E")
        about_frame.pack(fill="both", expand=True, padx=20, pady=20)

        logo_label = tk.Label(
            about_frame,
            text="🧬",
            font=("Segoe UI", 48),
            bg="#1A1A2E",
            fg="#00D4FF",
        )
        logo_label.pack(anchor="center", pady=(0, 15))

        title_label = tk.Label(
            about_frame,
            text="Crichtonian",
            font=("Segoe UI", 18, "bold"),
            bg="#1A1A2E",
            fg="#00D4FF",
        )
        title_label.pack(anchor="center", pady=(0, 10))

        version_label = tk.Label(
            about_frame,
            text="Verzija: 1.0",
            font=("Segoe UI", 11),
            bg="#1A1A2E",
            fg="#E0E0E0",
        )
        version_label.pack(anchor="center", pady=(0, 10))

        description_label = tk.Label(
            about_frame,
            text="Bioinformatički sustav za rekonstrukciju DNA izumrlih organizama",
            font=("Segoe UI", 10),
            bg="#1A1A2E",
            fg="#E0E0E0",
            justify="center",
            wraplength=360,
        )
        description_label.pack(anchor="center", pady=(0, 10))

        author_label = tk.Label(
            about_frame,
            text="Autor: Luka Šop",
            font=("Segoe UI", 10),
            bg="#1A1A2E",
            fg="#E0E0E0",
        )
        author_label.pack(anchor="center", pady=(0, 16))

        close_button = ttk.Button(
            about_frame,
            text="Zatvori",
            command=about_window.destroy,
        )
        close_button.pack(anchor="center")

#kartica "Podaci i unos"

    def build_data_tab(self):
        selector_frame = ttk.Frame(self.data_tab)
        selector_frame.pack(fill="x", padx=10, pady=10)
        ttk.Label(selector_frame, text="Prikaži:").pack(side=LEFT, padx=(0, 10))
        self.data_selector = ttk.Combobox(selector_frame, state="readonly", width=30)
        self.data_selector["values"] = [
            "Dinosauri",
            "Restrikcijski enzimi",
            "Moderni organizmi",
            "Rekonstrukcije",
        ]
        self.data_selector.current(0)
        self.data_selector.pack(side=LEFT)
        self.data_selector.bind(
            "<<ComboboxSelected>>", lambda _: self.on_data_view_changed()
        )

        self.data_content_frame = ttk.Frame(self.data_tab)
        self.data_content_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.dino_frame = self.create_dino_frame()
        self.enzyme_frame = self.create_enzim_frame()
        self.modern_frame = self.create_moderni_frame()
        self.recon_frame = self.create_rekon_frame()

        self.build_data_entry_panel()
        self.on_data_view_changed()

#Prikaz različitih podataka

    def create_dino_frame(self):
        frame = ttk.LabelFrame(self.data_content_frame, text="Dinosauri")
        self.dino_tree = ttk.Treeview(
            frame,
            columns=("naziv", "latinski_naziv", "period", "DNA_fragment"),
            show="headings",
        )
        for name, width in [
            ("naziv", 140),
            ("latinski_naziv", 220),
            ("period", 120),
            ("DNA_fragment", 360),
        ]:
            heading = "latinski naziv" if name == "latinski_naziv" else name
            self.dino_tree.heading(name, text=heading)
            self.dino_tree.column(name, width=width, anchor="w")
        self.dino_tree.pack(fill="both", expand=True, padx=5, pady=5)
        self.dino_tree.bind(
            "<<TreeviewSelect>>", lambda _: self.on_dino_tree_selected()
        )
        return frame

    def create_enzim_frame(self):
        frame = ttk.LabelFrame(self.data_content_frame, text="Restrikcijski enzimi")
        self.enzyme_tree = ttk.Treeview(
            frame,
            columns=("naziv", "prepoznaje_sekvencu", "mjesto_reza"),
            show="headings",
        )
        self.enzyme_tree.heading("naziv", text="naziv")
        self.enzyme_tree.heading("prepoznaje_sekvencu", text="prepoznaje_sekvencu")
        self.enzyme_tree.heading("mjesto_reza", text="mjesto_reza")
        self.enzyme_tree.column("naziv", width=140)
        self.enzyme_tree.column("prepoznaje_sekvencu", width=180)
        self.enzyme_tree.column("mjesto_reza", width=120)
        self.enzyme_tree.pack(fill="both", expand=True, padx=5, pady=5)
        self.enzyme_tree.bind(
            "<<TreeviewSelect>>", lambda _: self.on_enzyme_tree_selected()
        )
        return frame

    def create_moderni_frame(self):
        frame = ttk.LabelFrame(self.data_content_frame, text="Moderni organizmi")
        self.modern_tree = ttk.Treeview(
            frame, columns=("naziv", "latinski_naziv", "DNA_sekvenca"), show="headings"
        )
        for name, width in [
            ("naziv", 140),
            ("latinski_naziv", 220),
            ("DNA_sekvenca", 260),
        ]:
            heading = "latinski naziv" if name == "latinski_naziv" else name
            self.modern_tree.heading(name, text=heading)
            self.modern_tree.column(name, width=width, anchor="w")
        self.modern_tree.pack(fill="both", expand=True, padx=5, pady=5)
        self.modern_tree.bind(
            "<<TreeviewSelect>>", lambda _: self.on_modern_tree_selected()
        )
        return frame

    def create_rekon_frame(self):
        frame = ttk.LabelFrame(self.data_content_frame, text="Rekonstrukcije")
        self.recon_tree = ttk.Treeview(
            frame,
            columns=(
                "dinosaur_naziv",
                "verzija",
                "DNA_rekonstruirana",
                "enzimi_nazivi",
                "donor_nazivi",
                "stopa_prezivjelih",
                "vijabilnost",
            ),
            show="headings",
        )
        headings = [
            ("dinosaur_naziv", 180),
            ("verzija", 80),
            ("DNA_rekonstruirana", 260),
            ("enzimi_nazivi", 180),
            ("donor_nazivi", 140),
            ("stopa_prezivjelih", 120),
            ("vijabilnost", 100),
        ]
        for name, width in headings:
            heading = (
                "Dinosaur"
                if name == "dinosaur_naziv"
                else (
                    "Enzimi"
                    if name == "enzimi_nazivi"
                    else "Donori"
                    if name == "donor_nazivi"
                    else name
                )
            )
            self.recon_tree.heading(name, text=heading)
            self.recon_tree.column(name, width=width, anchor="w")
        self.recon_tree.pack(fill="both", expand=True, padx=5, pady=5)
        self.recon_tree.bind(
            "<<TreeviewSelect>>", lambda _: self.on_reconstruction_selected()
        )
        return frame

    def on_data_view_changed(self):
        odabir = self.data_selector.get()

        self.dino_frame.pack_forget()
        self.enzyme_frame.pack_forget()
        self.modern_frame.pack_forget()
        self.recon_frame.pack_forget()

        if odabir == "Dinosauri":
            self.dino_frame.pack(fill="both", expand=True)
        elif odabir == "Restrikcijski enzimi":
            self.enzyme_frame.pack(fill="both", expand=True)
        elif odabir == "Moderni organizmi":
            self.modern_frame.pack(fill="both", expand=True)
        elif odabir == "Rekonstrukcije":
            self.recon_frame.pack(fill="both", expand=True)

        self.update_entry_panel(odabir)

#okvir za unos novih podataka i uređivanje postojećih

    def build_data_entry_panel(self):
        self.entry_panel_frame = ttk.Frame(self.data_tab)
        self.entry_panel_frame.pack(fill="x", padx=10, pady=(0, 10))

    def update_entry_panel(self, odabir):
        for widget in self.entry_panel_frame.winfo_children():
            widget.destroy()

        if odabir == "Dinosauri":
            entry_frame = ttk.LabelFrame(
                self.entry_panel_frame, text="Unos novog dinosaura"
            )
            entry_frame.pack(fill="both", pady=8)
            entry_frame.columnconfigure(0, weight=1)
            entry_frame.columnconfigure(1, weight=2)

            left_frame = ttk.Frame(entry_frame)
            left_frame.grid(row=0, column=0, sticky="nsew", padx=(6, 3), pady=6)
            left_frame.columnconfigure(0, weight=1)
            ttk.Label(left_frame, text="Naziv:", width=16, anchor="w").grid(
                row=0, column=0, sticky="ew", pady=4
            )
            self.entry_dino_code = ttk.Entry(left_frame, width=32)
            self.entry_dino_code.grid(row=1, column=0, sticky="ew", pady=4)
            ttk.Label(left_frame, text="Latinski naziv:", width=16, anchor="w").grid(
                row=2, column=0, sticky="ew", pady=4
            )
            self.entry_dino_scientific = ttk.Entry(left_frame, width=32)
            self.entry_dino_scientific.grid(row=3, column=0, sticky="ew", pady=4)
            ttk.Label(left_frame, text="Period:", width=16, anchor="w").grid(
                row=4, column=0, sticky="ew", pady=4
            )
            self.entry_dino_period = ttk.Entry(left_frame, width=32)
            self.entry_dino_period.grid(row=5, column=0, sticky="ew", pady=4)

            right_frame = ttk.Frame(entry_frame)
            right_frame.grid(row=0, column=1, sticky="nsew", padx=(3, 6), pady=6)
            right_frame.columnconfigure(0, weight=1)
            ttk.Label(right_frame, text="DNA:", width=12, anchor="w").grid(
                row=0, column=0, sticky="w", pady=4
            )
            self.entry_dino_dna = tk.Text(
                right_frame,
                height=6,
                wrap="none",
                bg="#2A2A3E",
                fg="#FFFFFF",
                insertbackground="#00D4FF",
                relief="flat",
                borderwidth=1,
                font=("Consolas", 9, "bold"),
            )
            self.entry_dino_dna.grid(row=1, column=0, sticky="nsew", pady=4)

            action_frame = ttk.Frame(right_frame)
            action_frame.grid(row=2, column=0, columnspan=2, pady=8)
            ttk.Button(action_frame, text="Dodaj dinosaura", command=self.dodaj_dinosaur).pack(
                side=LEFT, padx=4
            )
            ttk.Button(
                action_frame, text="Ažuriraj dinosaura", command=self.izmijeni_dinosaur
            ).pack(side=LEFT, padx=4)
            ttk.Button(
                action_frame, text="Obriši dinosaura", command=self.izbrisi_dinosaur
            ).pack(side=LEFT, padx=4)

        elif odabir == "Restrikcijski enzimi":
            entry_frame = ttk.LabelFrame(
                self.entry_panel_frame, text="Unos novog enzima"
            )
            entry_frame.pack(fill="x", pady=8)
            entry_frame.columnconfigure(0, weight=1)
            ttk.Label(entry_frame, text="Naziv:", width=16, anchor="w").grid(
                row=0, column=0, sticky="ew", padx=6, pady=4
            )
            self.entry_enzyme_name = ttk.Entry(entry_frame, width=40)
            self.entry_enzyme_name.grid(row=1, column=0, sticky="ew", padx=6, pady=4)
            ttk.Label(
                entry_frame, text="Prepoznaje sekvencu:", width=16, anchor="w"
            ).grid(row=2, column=0, sticky="ew", padx=6, pady=4)
            self.entry_enzyme_site = ttk.Entry(entry_frame, width=40)
            self.entry_enzyme_site.grid(row=3, column=0, sticky="ew", padx=6, pady=4)
            ttk.Label(entry_frame, text="Mjesto reza:", width=16, anchor="w").grid(
                row=4, column=0, sticky="ew", padx=6, pady=4
            )
            self.entry_enzyme_cut_pos = ttk.Entry(entry_frame, width=40)
            self.entry_enzyme_cut_pos.grid(row=5, column=0, sticky="ew", padx=6, pady=4)
            action_frame = ttk.Frame(entry_frame)
            action_frame.grid(row=6, column=0, pady=2)
            ttk.Button(action_frame, text="Dodaj enzim", command=self.dodaj_enzim).pack(
                side=LEFT, padx=4
            )
            ttk.Button(
                action_frame, text="Ažuriraj enzim", command=self.izmijeni_enzim
            ).pack(side=LEFT, padx=4)
            ttk.Button(
                action_frame, text="Obriši enzim", command=self.izbrisi_enzim
            ).pack(side=LEFT, padx=4)

        elif odabir == "Moderni organizmi":
            entry_frame = ttk.LabelFrame(
                self.entry_panel_frame, text="Unos novog modernog organizma"
            )
            entry_frame.pack(fill="both", pady=8)
            entry_frame.columnconfigure(0, weight=1)
            entry_frame.columnconfigure(1, weight=2)

            left_frame = ttk.Frame(entry_frame)
            left_frame.grid(row=0, column=0, sticky="nsew", padx=(6, 3), pady=6)
            left_frame.columnconfigure(0, weight=1)
            ttk.Label(left_frame, text="Ime:", width=16, anchor="w").grid(
                row=0, column=0, sticky="ew", pady=4
            )
            self.entry_modern_common = ttk.Entry(left_frame, width=32)
            self.entry_modern_common.grid(row=1, column=0, sticky="ew", pady=4)
            ttk.Label(left_frame, text="Latinski:", width=16, anchor="w").grid(
                row=2, column=0, sticky="ew", pady=4
            )
            self.entry_modern_scientific = ttk.Entry(left_frame, width=32)
            self.entry_modern_scientific.grid(row=3, column=0, sticky="ew", pady=4)

            right_frame = ttk.Frame(entry_frame)
            right_frame.grid(row=0, column=1, sticky="nsew", padx=(3, 6), pady=6)
            right_frame.columnconfigure(0, weight=1)
            ttk.Label(right_frame, text="DNA:", width=12, anchor="w").grid(
                row=0, column=0, sticky="w", pady=4
            )
            self.entry_modern_dna = tk.Text(
                right_frame,
                height=6,
                wrap="none",
                bg="#2A2A3E",
                fg="#FFFFFF",
                insertbackground="#00D4FF",
                relief="flat",
                borderwidth=1,
                font=("Consolas", 9, "bold"),
            )
            self.entry_modern_dna.grid(row=1, column=0, sticky="nsew", pady=4)

            action_frame = ttk.Frame(entry_frame)
            action_frame.grid(row=1, column=0, columnspan=2, pady=8)
            ttk.Button(
                action_frame,
                text="Dodaj moderni organizam",
                command=self.dodaj_moderni_organizam,
            ).pack(side=LEFT, padx=4)
            ttk.Button(
                action_frame,
                text="Ažuriraj moderni organizam",
                command=self.izmijeni_moderni_organizam,
            ).pack(side=LEFT, padx=4)
            ttk.Button(
                action_frame,
                text="Obriši moderni organizam",
                command=self.izbrisi_moderni_organizam,
            ).pack(side=LEFT, padx=4)

        elif odabir == "Rekonstrukcije":
            entry_frame = ttk.LabelFrame(
                self.entry_panel_frame, text="Ažuriraj stopu preživjelih"
            )
            entry_frame.pack(fill="x", pady=8)
            entry_frame.columnconfigure(1, weight=0)
            entry_frame.columnconfigure(2, weight=0)
            entry_frame.columnconfigure(3, weight=1)
            ttk.Label(
                entry_frame, text="Stopa preživjelih (%):", width=18, anchor="e"
            ).grid(row=0, column=0, sticky="e", padx=6, pady=4)
            self.entry_survival_rate_data = ttk.Entry(entry_frame, width=8)
            self.entry_survival_rate_data.grid(
                row=0, column=1, sticky="w", padx=6, pady=4
            )
            ttk.Button(
                entry_frame,
                text="Ažuriraj rekonstrukciju",
                command=self.procijeni_vijabilnost,
            ).grid(row=0, column=2, sticky="w", padx=12, pady=4)
            self.label_viability_data = ttk.Label(entry_frame, text="Vijabilnost: -")
            self.label_viability_data.grid(row=0, column=3, sticky="w", padx=12, pady=4)

#odabir u tablici
    def on_dino_tree_selected(self):
        selected = self.dino_tree.selection()
        if not selected:
            self.selected_dino_item_id = None
            return
        self.selected_dino_item_id = int(selected[0])
        values = self.dino_tree.item(selected[0], "values")
        if len(values) >= 4:
            if hasattr(self, "entry_dino_code"):
                self.entry_dino_code.delete(0, END)
                self.entry_dino_code.insert(0, values[0])
            if hasattr(self, "entry_dino_scientific"):
                self.entry_dino_scientific.delete(0, END)
                self.entry_dino_scientific.insert(0, values[1])
            if hasattr(self, "entry_dino_period"):
                self.entry_dino_period.delete(0, END)
                self.entry_dino_period.insert(0, values[2])
            if hasattr(self, "entry_dino_dna"):
                self.entry_dino_dna.delete("1.0", END)
                self.entry_dino_dna.insert(END, values[3])

    def on_enzyme_tree_selected(self):
        selected = self.enzyme_tree.selection()
        if not selected:
            self.selected_enzyme_item_id = None
            return
        self.selected_enzyme_item_id = int(selected[0])
        values = self.enzyme_tree.item(selected[0], "values")
        if len(values) >= 3:
            if hasattr(self, "entry_enzyme_name"):
                self.entry_enzyme_name.delete(0, END)
                self.entry_enzyme_name.insert(0, values[0])
            if hasattr(self, "entry_enzyme_site"):
                self.entry_enzyme_site.delete(0, END)
                self.entry_enzyme_site.insert(0, values[1])
            if hasattr(self, "entry_enzyme_cut_pos"):
                self.entry_enzyme_cut_pos.delete(0, END)
                self.entry_enzyme_cut_pos.insert(0, values[2])

    def on_modern_tree_selected(self):
        selected = self.modern_tree.selection()
        if not selected:
            self.selected_modern_item_id = None
            return
        self.selected_modern_item_id = int(selected[0])
        values = self.modern_tree.item(selected[0], "values")
        if len(values) >= 3:
            if hasattr(self, "entry_modern_common"):
                self.entry_modern_common.delete(0, END)
                self.entry_modern_common.insert(0, values[0])
            if hasattr(self, "entry_modern_scientific"):
                self.entry_modern_scientific.delete(0, END)
                self.entry_modern_scientific.insert(0, values[1])
            if hasattr(self, "entry_modern_dna"):
                self.entry_modern_dna.delete("1.0", END)
                self.entry_modern_dna.insert(END, values[2])

# kartica "Rekonstrukcija"
    def build_reconstruction_tab(self):
        top_frame = ttk.Frame(self.reconstruction_tab)
        top_frame.pack(fill="x", pady=8, padx=10)

        ttk.Label(top_frame, text="Odaberi dinosaura:").pack(side=LEFT, padx=(0, 10))
        self.dino_selector = ttk.Combobox(top_frame, state="readonly", width=40)
        self.dino_selector.pack(side=LEFT)
        self.dino_selector.bind(
            "<<ComboboxSelected>>", lambda _: self.on_dinosaur_selected()
        )
        ttk.Button(top_frame, text="Osvježi", command=self.osvjezi_odabir).pack(
            side=LEFT, padx=10
        )
        ttk.Button(top_frame, text="Pomoć", command=self.pomoc_rekonstrukcija).pack(
            side=LEFT, padx=10
        )

        center_frame = ttk.Frame(self.reconstruction_tab)
        center_frame.pack(fill="both", expand=True, padx=10, pady=8)

        left_frame = ttk.Frame(center_frame)
        left_frame.pack(side=LEFT, fill="both", expand=True, padx=(0, 8))

        right_frame = ttk.Frame(center_frame)
        right_frame.pack(side=RIGHT, fill="both", expand=True)

        dino_box = ttk.LabelFrame(left_frame, text="Originalna DNA dinosaura")
        dino_box.pack(fill="both", expand=True, pady=6)
        self.text_original_dna = tk.Text(
            dino_box,
            height=6,
            wrap="word",
            bg="#2A2A3E",
            fg="#E0E0E0",
            insertbackground="#00D4FF",
            selectbackground="#FF6B6B",
            selectforeground="#FFFFFF",
            relief="flat",
            borderwidth=1,
            font=("Consolas", 9, "bold"),
        )
        self.text_original_dna.pack(fill="both", expand=True, padx=5, pady=5)

        gaps_box = ttk.LabelFrame(left_frame, text="Rupe i enzimi")
        gaps_box.pack(fill="both", expand=True, pady=6)

        gap_status_frame = ttk.Frame(gaps_box)
        gap_status_frame.pack(fill="x", padx=5, pady=4)
        ttk.Label(gap_status_frame, text="Odabrana rupa:").pack(side="left", padx=2)
        self.label_selected_gap = ttk.Label(
            gap_status_frame,
            text="Nema",
            foreground="#FF6B6B",
            font=("Segoe UI", 9, "bold"),
        )
        self.label_selected_gap.pack(side="left", padx=2)

        self.gaps_list = tk.Listbox(
            gaps_box,
            height=6,
            bg="#2A2A3E",
            fg="#E0E0E0",
            selectbackground="#FF6B6B",
            selectforeground="#FFFFFF",
            relief="flat",
            borderwidth=1,
            font=("Segoe UI", 9, "bold"),
            highlightbackground="#0F1419",
        )
        self.gaps_list.pack(fill="both", expand=True, padx=5, pady=5)
        self.gaps_list.bind("<<ListboxSelect>>", lambda _: self.on_gap_selected())
        ttk.Button(gaps_box, text="Detektiraj rupe", command=self.pronadi_rupe).pack(
            pady=4
        )

        enzyme_box = ttk.LabelFrame(right_frame, text="Kandidati enzima")
        enzyme_box.pack(fill="both", expand=True, pady=6)

        enzyme_status_frame = ttk.Frame(enzyme_box)
        enzyme_status_frame.pack(fill="x", padx=5, pady=4)
        ttk.Label(enzyme_status_frame, text="Odabrani enzim:").pack(side="left", padx=2)
        self.label_selected_enzyme = ttk.Label(
            enzyme_status_frame,
            text="Nema",
            foreground="#FF6B6B",
            font=("Segoe UI", 9, "bold"),
        )
        self.label_selected_enzyme.pack(side="left", padx=2)

        self.enzyme_list = tk.Listbox(
            enzyme_box,
            height=6,
            bg="#2A2A3E",
            fg="#E0E0E0",
            selectbackground="#FF6B6B",
            selectforeground="#FFFFFF",
            relief="flat",
            borderwidth=1,
            font=("Segoe UI", 9, "bold"),
            highlightbackground="#0F1419",
        )
        self.enzyme_list.pack(fill="both", expand=True, padx=5, pady=5)
        self.enzyme_list.bind("<<ListboxSelect>>", lambda _: self.update_enzyme_label())

        donor_box = ttk.LabelFrame(right_frame, text="Kandidati donor sekvence")
        donor_box.pack(fill="both", expand=True, pady=6)

        donor_status_frame = ttk.Frame(donor_box)
        donor_status_frame.pack(fill="x", padx=5, pady=4)
        ttk.Label(donor_status_frame, text="Odabrani donor:").pack(side="left", padx=2)
        self.label_selected_donor = ttk.Label(
            donor_status_frame,
            text="Nema",
            foreground="#FF6B6B",
            font=("Segoe UI", 9, "bold"),
        )
        self.label_selected_donor.pack(side="left", padx=2)

        self.donor_list = tk.Listbox(
            donor_box,
            height=6,
            bg="#2A2A3E",
            fg="#E0E0E0",
            selectbackground="#FF6B6B",
            selectforeground="#FFFFFF",
            relief="flat",
            borderwidth=1,
            font=("Segoe UI", 9, "bold"),
            highlightbackground="#0F1419",
        )
        self.donor_list.pack(fill="both", expand=True, padx=5, pady=5)
        self.donor_list.bind("<<ListboxSelect>>", lambda _: self.on_donor_selected())

        buttons_frame = ttk.Frame(self.reconstruction_tab)
        buttons_frame.pack(fill="x", padx=10, pady=8)
        ttk.Button(
            buttons_frame, text="Nađi donora", command=self.pronadi_donor_kandidat
        ).pack(side=LEFT, padx=4)
        ttk.Button(
            buttons_frame, text="Primijeni odabir", command=self.primijeni_donor
        ).pack(side=LEFT, padx=4)
        ttk.Button(
            buttons_frame,
            text="Spremi rekonstrukciju",
            command=self.spremi_rekonstrukciju,
        ).pack(side=RIGHT, padx=4)

        bottom_frame = ttk.LabelFrame(
            self.reconstruction_tab, text="Rekonstruirana DNA"
        )
        bottom_frame.pack(fill="both", expand=True, padx=10, pady=8)
        self.text_reconstructed_dna = tk.Text(
            bottom_frame,
            height=6,
            wrap="word",
            bg="#2A2A3E",
            fg="#E0E0E0",
            insertbackground="#00D4FF",
            selectbackground="#FF6B6B",
            selectforeground="#FFFFFF",
            relief="flat",
            borderwidth=1,
            font=("Consolas", 9, "bold"),
        )
        self.text_reconstructed_dna.pack(fill="both", expand=True, padx=5, pady=5)

#gumb za pomoć
    def pomoc_rekonstrukcija(self):
        help_text = (
            "Koraci za rekonstrukciju DNA:\n\n"
            "1. Odaberite dinosaura iz padajućeg izbornika.\n"
            "2. Kliknite 'Pronađi rupe' za pronalazak rupa u DNA sekvenci.\n"
            "3. U odjeljku 'Rupe i enzimi' odaberite rupu koju želite popraviti.\n"
            "4. U 'Kandidati donor sekvence' odaberite donora.\n"
            "5. Odaberite enzim u 'Kandidati enzima' (prikazuju se samo enzimi kompatibilni s rupom i donorom).\n"
            "6. Kliknite 'Primijeni odabir' da popunite rupu.\n"
            "7. Ponovite postupak za sve rupe.\n"
            "8. Nakon što je rekonstrukcija gotova, kliknite 'Spremi rekonstrukciju'."
        )
        messagebox.showinfo("Pomoć - koraci rekonstrukcije", help_text)

#kartica "Filogenetsko stablo"
    def build_phylo_tab(self):
        top_frame = ttk.Frame(self.phylo_tab)
        top_frame.pack(fill="x", pady=8, padx=10)
        ttk.Label(top_frame, text="Prikaži:").pack(side=LEFT, padx=(0, 10))
        self.phylo_selector = ttk.Combobox(top_frame, state="readonly", width=24)
        self.phylo_selector["values"] = [
            "Dinosauri",
            "Moderni organizmi",
            "Dinosauri i moderni",
        ]
        self.phylo_selector.current(0)
        self.phylo_selector.pack(side=LEFT)
        ttk.Button(
            top_frame, text="Prikaži stablo", command=self.draw_selected_phylo_tree
        ).pack(side=LEFT, padx=10)

        plot_frame = ttk.Frame(self.phylo_tab)
        plot_frame.pack(fill="both", expand=True, padx=10, pady=8)
        self.figure = plt.Figure(figsize=(9, 5), dpi=100, facecolor="#0F1419")
        self.canvas = FigureCanvasTkAgg(self.figure, master=plot_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def osvjezi_gui(self):
        for stablo, rows, columns in [
            (
                self.dino_tree,
                get_all_dinosaurs(self.conn),
                ["naziv", "latinski_naziv", "period", "DNA_fragment"],
            ),
            (
                self.enzyme_tree,
                self.format_enzyme_rows(get_all_enzymes(self.conn)),
                ["naziv", "prepoznaje_sekvencu", "mjesto_reza"],
            ),
            (
                self.modern_tree,
                get_all_modern_organisms(self.conn),
                ["naziv", "latinski_naziv", "DNA_sekvenca"],
            ),
            (
                self.recon_tree,
                get_all_reconstructions(self.conn),
                [
                    "dinosaur_naziv",
                    "verzija",
                    "DNA_rekonstruirana",
                    "enzimi_nazivi",
                    "donor_nazivi",
                    "stopa_prezivjelih",
                    "vijabilnost",
                ],
            ),
        ]:
            stablo.delete(*stablo.get_children())
            for row in rows:
                stablo.insert(
                    "",
                    END,
                    iid=str(row["id"]),
                    values=tuple(row[col] for col in columns),
                )
        self.osvjezi_odabir()

    def format_enzyme_rows(self, enzymes):
        formatted = []
        for enzyme in enzymes:
            formatted_enzyme = dict(enzyme)
            cut_pos = formatted_enzyme.get("mjesto_reza")
            formatted_enzyme["mjesto_reza"] = (
                str(cut_pos) if cut_pos is not None else "-"
            )
            formatted.append(formatted_enzyme)
        return formatted

    def osvjezi_odabir(self):
        dinosauri = get_all_dinosaurs(self.conn)
        items = [
            f"{d['id']} - {d['naziv']} ({d['latinski_naziv']})" for d in dinosauri
        ]
        self.dino_selector["values"] = items
        if items:
            self.dino_selector.current(0)
            self.on_dinosaur_selected()

#provjera ispravnosti podataka

    def validate_dinosaur_inputs(self, period, dna):
        allowed_periods = {"Trijas", "Jura", "Kreda"}
        if period not in allowed_periods:
            messagebox.showwarning(
                "Upozorenje", "Period dinosaura mora biti Trijas, Jura ili Kreda."
            )
            return False
        cleaned_dna = dna.strip().upper()
        allowed_chars = set("ATGC-")
        if not cleaned_dna or any(ch not in allowed_chars for ch in cleaned_dna):
            messagebox.showwarning(
                "Upozorenje",
                "DNA dinosaura može sadržavati samo znakove A, T, G, C i -.",
            )
            return False
        return True

    def validate_enzyme_inputs(self, site, cut_pos):
        cleaned_site = site.strip().upper()
        allowed_chars = set("ATGC")
        if not cleaned_site or any(ch not in allowed_chars for ch in cleaned_site):
            messagebox.showwarning(
                "Upozorenje",
                "Sekvenca koju enzim prepoznaje može sadržavati samo znakove A, T, G, C.",
            )
            return False
        if cut_pos is not None:
            if cut_pos < 0 or cut_pos > len(cleaned_site):
                messagebox.showwarning(
                    "Upozorenje",
                    f"Mjesto reza enzima mora biti između 0 i {len(cleaned_site)}.",
                )
                return False
        return True

    def validate_modern_organism_dna(self, dna):
        cleaned_dna = dna.strip().upper()
        allowed_chars = set("ATGC")
        if not cleaned_dna or any(ch not in allowed_chars for ch in cleaned_dna):
            messagebox.showwarning(
                "Upozorenje",
                "DNA modernog organizma može sadržavati samo znakove A, T, G, C.",
            )
            return False
        return True
    
#metode za dodavanje, ažuriranje i brisanje podataka

    def dodaj_dinosaur(self):
        code = self.entry_dino_code.get().strip()
        scientific_name = self.entry_dino_scientific.get().strip()
        period = self.entry_dino_period.get().strip()
        dna = self.entry_dino_dna.get("1.0", END).strip().upper()
        if not (code and scientific_name and period and dna):
            messagebox.showwarning(
                "Upozorenje", "Unesite kod, vrstu, period i DNA sekvencu za dinosaura."
            )
            return
        if not self.validate_dinosaur_inputs(period, dna):
            return
        if get_dinosaur_by_code(self.conn, code):
            messagebox.showwarning("Upozorenje", "Dinosaur s istim nazivom već postoji.")
            return
        if get_dinosaur_by_scientific_name(self.conn, scientific_name):
            messagebox.showwarning(
                "Upozorenje", "Dinosaur s istim latinskim nazivom već postoji."
            )
            return
        dodaj_dinosaur(self.conn, code, scientific_name, period, dna)
        self.set_status("Dinosaur je dodan u bazu.")
        self.entry_dino_code.delete(0, END)
        self.entry_dino_scientific.delete(0, END)
        self.entry_dino_period.delete(0, END)
        self.entry_dino_dna.delete("1.0", END)
        self.selected_dino_item_id = None
        self.osvjezi_gui()

    def dodaj_enzim(self):
        name = self.entry_enzyme_name.get().strip()
        site = self.entry_enzyme_site.get().strip().upper()
        cut_pos_str = self.entry_enzyme_cut_pos.get().strip()
        if not (name and site):
            messagebox.showwarning(
                "Upozorenje", "Unesite naziv i prepoznavnu sekvencu enzima."
            )
            return
        if not self.validate_enzyme_inputs(site, None):
            return
        if get_enzyme_by_name(self.conn, name):
            messagebox.showwarning("Upozorenje", "Enzim s istim nazivom već postoji.")
            return
        cut_pos = None
        if cut_pos_str:
            try:
                cut_pos = int(cut_pos_str)
                if not self.validate_enzyme_inputs(site, cut_pos):
                    return
            except ValueError:
                messagebox.showwarning(
                    "Upozorenje", "Mjesto reza mora biti cijeli broj."
                )
                return
        dodaj_enzim(self.conn, name, site, cut_pos)
        self.set_status("Enzim je dodan u bazu.")
        self.entry_enzyme_name.delete(0, END)
        self.entry_enzyme_site.delete(0, END)
        self.entry_enzyme_cut_pos.delete(0, END)
        self.selected_enzyme_item_id = None
        self.osvjezi_gui()

    def dodaj_moderni_organizam(self):
        common_name = self.entry_modern_common.get().strip()
        scientific_name = self.entry_modern_scientific.get().strip()
        dna = self.entry_modern_dna.get("1.0", END).strip().upper()
        if not (common_name and scientific_name and dna):
            messagebox.showwarning(
                "Upozorenje",
                "Unesite naziv, latinski naziv i DNA sekvencu za moderni organizam.",
            )
            return
        if not self.validate_modern_organism_dna(dna):
            return
        if get_modern_organism_by_scientific_name(self.conn, scientific_name):
            messagebox.showwarning(
                "Upozorenje", "Moderni organizam s istim latinskim nazivom već postoji."
            )
            return
        dodaj_moderni_organizam(self.conn, common_name, scientific_name, dna)
        self.set_status("Moderni organizam je dodan u bazu.")
        self.entry_modern_common.delete(0, END)
        self.entry_modern_scientific.delete(0, END)
        self.entry_modern_dna.delete("1.0", END)
        self.selected_modern_item_id = None
        self.osvjezi_gui()

    def izmijeni_dinosaur(self):
        if self.selected_dino_item_id is None:
            messagebox.showwarning("Upozorenje", "Odaberite dinosaura za ažuriranje.")
            return
        code = self.entry_dino_code.get().strip()
        scientific_name = self.entry_dino_scientific.get().strip()
        period = self.entry_dino_period.get().strip()
        dna = self.entry_dino_dna.get("1.0", END).strip().upper()
        if not (code and scientific_name and period and dna):
            messagebox.showwarning(
                "Upozorenje", "Unesite kod, vrstu, period i DNA sekvencu za dinosaura."
            )
            return
        if not self.validate_dinosaur_inputs(period, dna):
            return
        existing = get_dinosaur_by_code(self.conn, code)
        if existing and existing["id"] != self.selected_dino_item_id:
            messagebox.showwarning("Upozorenje", "Drugi dinosaur koristi isti naziv.")
            return
        existing = get_dinosaur_by_scientific_name(self.conn, scientific_name)
        if existing and existing["id"] != self.selected_dino_item_id:
            messagebox.showwarning(
                "Upozorenje", "Drugi dinosaur koristi isti latinski naziv."
            )
            return
        azuriraj_dinosaur(
            self.conn, self.selected_dino_item_id, code, scientific_name, period, dna
        )
        self.set_status("Dinosaur je ažuriran.")
        self.selected_dino_item_id = None
        self.entry_dino_code.delete(0, END)
        self.entry_dino_scientific.delete(0, END)
        self.entry_dino_period.delete(0, END)
        self.entry_dino_dna.delete("1.0", END)
        self.osvjezi_gui()

    def izbrisi_dinosaur(self):
        if self.selected_dino_item_id is None:
            messagebox.showwarning("Upozorenje", "Odaberite dinosaura za brisanje.")
            return
        if not messagebox.askyesno(
            "Potvrda", "Jeste li sigurni da želite obrisati odabranog dinosaura?"
        ):
            return
        izbrisi_dinosaur(self.conn, self.selected_dino_item_id)
        self.set_status("Dinosaur je obrisan iz baze.")
        self.selected_dino_item_id = None
        self.entry_dino_code.delete(0, END)
        self.entry_dino_scientific.delete(0, END)
        self.entry_dino_period.delete(0, END)
        self.entry_dino_dna.delete("1.0", END)
        self.osvjezi_gui()

    def izmijeni_enzim(self):
        if self.selected_enzyme_item_id is None:
            messagebox.showwarning("Upozorenje", "Odaberite enzim za ažuriranje.")
            return
        name = self.entry_enzyme_name.get().strip()
        site = self.entry_enzyme_site.get().strip().upper()
        cut_pos_str = self.entry_enzyme_cut_pos.get().strip()
        if not (name and site):
            messagebox.showwarning(
                "Upozorenje", "Unesite naziv i prepoznavnu sekvencu enzima."
            )
            return
        if not self.validate_enzyme_inputs(site, None):
            return
        existing = get_enzyme_by_name(self.conn, name)
        if existing and existing.id != self.selected_enzyme_item_id:
            messagebox.showwarning("Upozorenje", "Drugi enzim koristi isti naziv.")
            return
        cut_pos = None
        if cut_pos_str:
            try:
                cut_pos = int(cut_pos_str)
                if not self.validate_enzyme_inputs(site, cut_pos):
                    return
            except ValueError:
                messagebox.showwarning(
                    "Upozorenje", "Mjesto reza mora biti cijeli broj."
                )
                return
        azuriraj_enzim(self.conn, self.selected_enzyme_item_id, name, site, cut_pos)
        self.set_status("Enzim je ažuriran.")
        self.selected_enzyme_item_id = None
        self.entry_enzyme_name.delete(0, END)
        self.entry_enzyme_site.delete(0, END)
        self.entry_enzyme_cut_pos.delete(0, END)
        self.osvjezi_gui()

    def izbrisi_enzim(self):
        if self.selected_enzyme_item_id is None:
            messagebox.showwarning("Upozorenje", "Odaberite enzim za brisanje.")
            return
        if not messagebox.askyesno(
            "Potvrda", "Jeste li sigurni da želite obrisati odabrani enzim?"
        ):
            return
        izbrisi_enzim(self.conn, self.selected_enzyme_item_id)
        self.set_status("Enzim je obrisan iz baze.")
        self.selected_enzyme_item_id = None
        self.entry_enzyme_name.delete(0, END)
        self.entry_enzyme_site.delete(0, END)
        self.entry_enzyme_cut_pos.delete(0, END)
        self.osvjezi_gui()

    def izmijeni_moderni_organizam(self):
        if self.selected_modern_item_id is None:
            messagebox.showwarning(
                "Upozorenje", "Odaberite moderni organizam za ažuriranje."
            )
            return
        common_name = self.entry_modern_common.get().strip()
        scientific_name = self.entry_modern_scientific.get().strip()
        dna = self.entry_modern_dna.get("1.0", END).strip().upper()
        if not (common_name and scientific_name and dna):
            messagebox.showwarning(
                "Upozorenje", "Unesite naziv, latinski naziv i DNA sekvencu."
            )
            return
        if not self.validate_modern_organism_dna(dna):
            return
        existing = get_modern_organism_by_scientific_name(self.conn, scientific_name)
        if existing and existing.id != self.selected_modern_item_id:
            messagebox.showwarning(
                "Upozorenje", "Drugi organizam koristi isti latinski naziv."
            )
            return
        azuriraj_moderni_organizam(
            self.conn, self.selected_modern_item_id, common_name, scientific_name, dna
        )
        self.set_status("Moderni organizam je ažuriran.")
        self.selected_modern_item_id = None
        self.entry_modern_common.delete(0, END)
        self.entry_modern_scientific.delete(0, END)
        self.entry_modern_dna.delete("1.0", END)
        self.osvjezi_gui()

    def izbrisi_moderni_organizam(self):
        if self.selected_modern_item_id is None:
            messagebox.showwarning(
                "Upozorenje", "Odaberite moderni organizam za brisanje."
            )
            return
        if not messagebox.askyesno(
            "Potvrda", "Jeste li sigurni da želite obrisati odabrani moderni organizam?"
        ):
            return
        izbrisi_moderni_organizam(self.conn, self.selected_modern_item_id)
        self.set_status("Moderni organizam je obrisan iz baze.")
        self.selected_modern_item_id = None
        self.entry_modern_common.delete(0, END)
        self.entry_modern_scientific.delete(0, END)
        self.entry_modern_dna.delete("1.0", END)
        self.osvjezi_gui()

    def on_dinosaur_selected(self):
        odabir = self.dino_selector.get()
        if not odabir:
            return
        dinosaur_id = int(odabir.split(" - ")[0])
        self.selected_dinosaur_id = dinosaur_id
        self.odabrana_rupa = None
        self.id_odabranog_donora = None
        self.used_enzyme_ids = []
        self.used_donor_ids = []
        dinosaur = get_dinosaur(self.conn, dinosaur_id)
        self.text_original_dna.delete("1.0", END)
        self.text_original_dna.insert(END, dinosaur["DNA_fragment"])
        self.text_reconstructed_dna.delete("1.0", END)
        self.text_reconstructed_dna.insert(END, dinosaur["DNA_fragment"])
        self.current_reconstructed_sequence = dinosaur["DNA_fragment"]
        self.gaps_list.delete(0, END)
        self.enzyme_list.delete(0, END)
        self.donor_list.delete(0, END)

    def on_reconstruction_selected(self):
        selected = self.recon_tree.selection()
        if not selected:
            return
        id_rekonstrukcije = selected[0]
        rekonstrukcija = next(
            (
                row
                for row in get_all_reconstructions(self.conn)
                if str(row["id"]) == id_rekonstrukcije
            ),
            None,
        )
        if rekonstrukcija is None:
            return
        stopa = rekonstrukcija["stopa_prezivjelih"]
        if hasattr(self, "entry_survival_rate_data"):
            self.entry_survival_rate_data.delete(0, END)
            if stopa is not None:
                self.entry_survival_rate_data.insert(0, str(stopa))
        if hasattr(self, "label_viability_data"):
            self.label_viability_data.config(
                text=f"Vijabilnost: {rekonstrukcija['vijabilnost'] if rekonstrukcija['vijabilnost'] else '-'}"
            )

#pronalaženje i odabir rupa
    def pronadi_rupe(self):
        if self.selected_dinosaur_id is None:
            messagebox.showwarning("Upozorenje", "Prvo odaberite dinosaura.")
            return
        sekvenca = (
            self.current_reconstructed_sequence
            or self.text_original_dna.get("1.0", END).strip()
        )
        gaps = Rekonstrukcija.pronadi_rupe(sekvenca)
        self.gaps_list.delete(0, END)
        if not gaps:
            self.set_status("Nema rupa u odabranoj DNA sekvenci.")
            return
        for indeks, (start, end) in enumerate(gaps, start=1):
            self.gaps_list.insert(
                END, f"Rupa {indeks}: {start}-{end}, duljina {end - start + 1}"
            )
        enzyme_candidates = Rekonstrukcija.pronadi_enzim_kandidat(
            sekvenca, [dict(row) for row in get_all_enzymes(self.conn)]
        )
        best_gap_index = next(
            (idx for idx, gap in enumerate(enzyme_candidates) if gap["enzymes"]), 0
        )
        self.gaps_list.selection_clear(0, END)
        self.gaps_list.selection_set(best_gap_index)
        self.gaps_list.see(best_gap_index)
        self.odabrana_rupa = gaps[best_gap_index]
        self.on_gap_selected()

    def on_gap_selected(self):
        odabir = self.gaps_list.curselection()
        if not odabir:
            return
        indeks = odabir[0]
        sekvenca = (
            self.current_reconstructed_sequence
            or self.text_original_dna.get("1.0", END).strip()
        )
        gaps = Rekonstrukcija.pronadi_rupe(sekvenca)
        if indeks < len(gaps):
            self.odabrana_rupa = gaps[indeks]
            self.label_selected_gap.config(
                text=f"Rupa {indeks + 1}: ({self.odabrana_rupa[0]}, {self.odabrana_rupa[1]})"
            )
            self.load_gap_enzymes()

#pronalaženje i odabir enzima za odabranu rupu
    def load_gap_enzymes(self):
        sekvenca = (
            self.current_reconstructed_sequence
            or self.text_original_dna.get("1.0", END).strip()
        )
        sekvenca_donora = None
        if self.id_odabranog_donora is not None:
            donor = get_modern_organism(self.conn, self.id_odabranog_donora)
            sekvenca_donora = donor["DNA_sekvenca"] if donor else None
        enzymes = get_all_enzymes(self.conn)
        kandidati = Rekonstrukcija.pronadi_enzim_kandidat(
            sekvenca, [dict(row) for row in enzymes]
        )
        self.enzyme_list.delete(0, END)
        self.enzymes_for_gap = []
        if self.id_odabranog_donora is None:
            self.enzyme_list.insert(
                END, "Odaberite donora da biste vidjeli kompatibilne enzime."
            )
            self.label_selected_enzyme.config(text="Nema")
            return
        for gap in kandidati:
            if gap["range"] == self.odabrana_rupa:
                for enzyme in gap["enzymes"]:
                    if not Rekonstrukcija.is_enzyme_compatible_with_donor(
                        sekvenca, self.odabrana_rupa, sekvenca_donora, enzyme
                    ):
                        continue
                    cut_info = (
                        f", mjesto_reza {enzyme['mjesto_reza']}"
                        if enzyme.get("mjesto_reza") is not None
                        else ""
                    )
                    self.enzyme_list.insert(
                        END,
                        f"{enzyme['id']}: {enzyme['naziv']} ({enzyme['prepoznaje_sekvencu']}{cut_info})",
                    )
                    self.enzymes_for_gap.append(enzyme)
                break
        if not self.enzymes_for_gap:
            self.enzyme_list.insert(
                END, "Nema kompatibilnih enzima za ovu rupu i odabrani donor."
            )
            self.label_selected_enzyme.config(text="Nema")
        else:
            self.enzyme_list.selection_clear(0, END)
            self.enzyme_list.selection_set(0)
            self.enzyme_list.see(0)
            self.get_selected_enzyme()

    def get_selected_enzyme(self):
        odabir = self.enzyme_list.curselection()
        if not odabir or not self.enzymes_for_gap:
            return None
        indeks = odabir[0]
        if indeks < len(self.enzymes_for_gap):
            enzyme = self.enzymes_for_gap[indeks]
            self.label_selected_enzyme.config(text=f"{enzyme['naziv']}")
            return enzyme
        return None

    def update_enzyme_label(self):
        self.get_selected_enzyme()

#pronalaženje i odabir donora za odabranu rupu

    def pronadi_donor_kandidat(self):
        if self.odabrana_rupa is None:
            messagebox.showwarning("Upozorenje", "Prvo detektirajte i odaberite rupu.")
            return
        sekvenca = (
            self.current_reconstructed_sequence
            or self.text_original_dna.get("1.0", END).strip()
        )
        moderni = get_all_modern_organisms(self.conn)
        odabrani_enzim = self.get_selected_enzyme()
        kandidati = Rekonstrukcija.pronadi_donor_kandidat(
            sekvenca,
            self.odabrana_rupa,
            [dict(row) for row in moderni],
            enzyme=odabrani_enzim,
        )
        self.donor_list.delete(0, END)
        self.kandidati_donora = kandidati
        if not kandidati:
            self.donor_list.insert(END, "Nema pogodnih donor sekvenci.")
            self.label_selected_donor.config(text="Nema")
            return
        for entry in kandidati:
            organism = entry["organism"]
            self.donor_list.insert(
                END, f"{organism['id']} - {organism['naziv']} ({entry['score']}%)"
            )
        self.donor_list.selection_clear(0, END)
        self.donor_list.selection_set(0)
        self.donor_list.see(0)
        self.on_donor_selected()

    def on_donor_selected(self):
        odabir = self.donor_list.curselection()
        if not odabir:
            return
        indeks = odabir[0]
        if indeks < len(self.kandidati_donora):
            kandidat = self.kandidati_donora[indeks]
            self.id_odabranog_donora = kandidat["organism"]["id"]
            self.label_selected_donor.config(
                text=f"{kandidat['organism']['naziv']} ({kandidat['score']}%)"
            )
            self.load_gap_enzymes()

    def primijeni_donor(self):
        if self.odabrana_rupa is None or self.id_odabranog_donora is None:
            messagebox.showwarning("Upozorenje", "Odaberite rupu i donor sekvencu.")
            return
        kandidat = next(
            (
                c
                for c in self.kandidati_donora
                if c["organism"]["id"] == self.id_odabranog_donora
            ),
            None,
        )
        if kandidat is None:
            messagebox.showwarning("Upozorenje", "Odabrani donor više nije dostupan.")
            return
        odabrani_enzim = self.get_selected_enzyme()
        if odabrani_enzim is None:
            messagebox.showwarning(
                "Upozorenje", "Za rekonstrukciju morate odabrati kompatibilan enzim."
            )
            return
        sekvenca_donora = kandidat["organism"]["DNA_sekvenca"]
        if self.current_reconstructed_sequence is None:
            self.current_reconstructed_sequence = self.text_original_dna.get(
                "1.0", END
            ).strip()
        new_sequence = Rekonstrukcija.primijeni_enzim(
            self.current_reconstructed_sequence,
            sekvenca_donora,
            odabrani_enzim,
            self.odabrana_rupa,
        )
        if new_sequence == self.current_reconstructed_sequence:
            messagebox.showwarning(
                "Upozorenje",
                "Nije moguće izvršiti rekonstrukciju s odabranim enzimom i donorom.",
            )
            return
        self.current_reconstructed_sequence = new_sequence
        self.text_reconstructed_dna.delete("1.0", END)
        self.text_reconstructed_dna.insert(END, new_sequence)
        if odabrani_enzim is not None and isinstance(odabrani_enzim, dict):
            enzim_id = odabrani_enzim.get("id")
            if enzim_id and enzim_id not in self.used_enzyme_ids:
                self.used_enzyme_ids.append(enzim_id)
        id_donora = kandidat["organism"]["id"]
        if id_donora and id_donora not in self.used_donor_ids:
            self.used_donor_ids.append(id_donora)
        self.pronadi_rupe()
        self.set_status("Rupa je popunjena donor segmentom.")

#spremanje rekonstrukcije

    def spremi_rekonstrukciju(self):
        if self.selected_dinosaur_id is None:
            messagebox.showwarning("Upozorenje", "Odaberite dinosaura prije spremanja.")
            return
        reconstructed = self.text_reconstructed_dna.get("1.0", END).strip()
        if not reconstructed or "-" in reconstructed:
            messagebox.showwarning(
                "Upozorenje", "Rekonstruirana DNA mora biti dovršena i bez rupa."
            )
            return
        if not self.used_enzyme_ids:
            messagebox.showwarning(
                "Upozorenje",
                "Za spremanje rekonstrukcije mora postojati kompatibilan enzim.",
            )
            return
        last_version = get_reconstruction_version(self.conn, self.selected_dinosaur_id)
        version = "1.0" if last_version is None else f"{int(float(last_version)) + 1}.0"
        enzyme_ids = list(self.used_enzyme_ids)
        donor_ids = list(self.used_donor_ids)
        dodaj_rekonstrukcija(
            self.conn,
            self.selected_dinosaur_id,
            version,
            reconstructed,
            enzyme_ids,
            donor_ids,
        )
        self.set_status(f"Rekonstrukcija je spremljena verzijom {version}.")
        self.osvjezi_gui()

#vijabilnost rekonstrukcije

    def procijeni_vijabilnost(self):
        unos_stope = None
        if (
            hasattr(self, "entry_survival_rate_data")
            and self.entry_survival_rate_data.winfo_ismapped()
        ):
            unos_stope = self.entry_survival_rate_data
        if unos_stope is None:
            messagebox.showwarning(
                "Upozorenje", "Nema dostupnog unosa stope preživjelih."
            )
            return
        try:
            stopa = float(unos_stope.get())
        except ValueError:
            messagebox.showwarning("Upozorenje", "Unesite valjani numerički postotak.")
            return
        if stopa < 0 or stopa > 100:
            messagebox.showwarning("Upozorenje", "Postotak mora biti između 0 i 100.")
            return
        selected = self.recon_tree.selection()
        if not selected:
            messagebox.showwarning(
                "Upozorenje", "Prvo odaberite rekonstrukciju u tablici Rekonstrukcije."
            )
            return
        id_rekonstrukcije = selected[0]
        rekonstrukcija = next(
            (
                row
                for row in get_all_reconstructions(self.conn)
                if str(row["id"]) == id_rekonstrukcije
            ),
            None,
        )
        if rekonstrukcija is None:
            messagebox.showwarning(
                "Upozorenje", "Nije pronađena odabrana rekonstrukcija."
            )
            return
        viability = "DA" if stopa > 50 else "NE"
        azuriraj_vijabilnost(self.conn, rekonstrukcija["id"], stopa, viability)
        self.set_status("Stopa preživjelih je ažurirana za odabranu rekonstrukciju.")
        self.osvjezi_gui()

#metode za crtanje filogenetskog stabla

    def draw_selected_phylo_tree(self):
        zapisi, title = self.get_phylo_records_and_title()
        self.nacrtaj_filogenetsko_stablo(zapisi, title=title)

    def get_phylo_records_and_title(self):
        odabir = (
            self.phylo_selector.get() if hasattr(self, "phylo_selector") else "Oboje"
        )
        if odabir == "Dinosauri":
            dinosauri = get_all_dinosaurs(self.conn)
            zapisi = [
                {"label": f"{d['naziv']}", "sequence": d["DNA_fragment"]}
                for d in dinosauri
            ]
            title = "Filogenetsko stablo dinosaura"
        elif odabir == "Moderni organizmi":
            moderni = get_all_modern_organisms(self.conn)
            zapisi = [
                {"label": f"{m['naziv']}", "sequence": m["DNA_sekvenca"]}
                for m in moderni
            ]
            title = "Filogenetsko stablo modernih organizama"
        else:
            dinosauri = get_all_dinosaurs(self.conn)
            moderni = get_all_modern_organisms(self.conn)
            zapisi = [
                {"label": f"D:{d['naziv']}", "sequence": d["DNA_fragment"]}
                for d in dinosauri
            ] + [
                {"label": f"M:{m['naziv']}", "sequence": m["DNA_sekvenca"]}
                for m in moderni
            ]
            title = "Filogenetsko stablo svih organizama"
        return zapisi, title

    def nacrtaj_filogenetsko_stablo(self, zapisi, title="Filogenetsko stablo"):
        if len(zapisi) < 2:
            messagebox.showwarning(
                "Upozorenje", "Treba najmanje dva zapisa za izradu stabla."
            )
            return
        oznake, matrica = Rekonstrukcija.build_distance_matrix(zapisi)
        stablo = Rekonstrukcija.build_upgma_tree(oznake, matrica)
        if stablo is None:
            messagebox.showwarning("Upozorenje", "Pogreška pri izradi stabla.")
            return
        self.figure.clear()
        os = self.figure.add_subplot(111, facecolor="#0F1419")
        os.set_title(title, color="#E0E0E0", fontweight="bold", fontsize=12)
        os.axis("off")
        os.tick_params(colors="#E0E0E0")
        self.nacrtaj_stablo(os, stablo)
        self.canvas.draw()

    def nacrtaj_stablo(self, os, stablo):
        listovi = []
        self.nacrtaj_list(stablo, listovi)
        pozicije = {leaf.label: idx for idx, leaf in enumerate(listovi)}
        # Prvo nacrtaj stablo da dobiješ pozicije
        x_korijena, y_korijena = self.natpis_list(os, stablo, pozicije, x=0.0)
        # Dodaj horizontalnu crtu od lijevog ruba do centra prve vertikalne crte
        os.plot(
            [-2, x_korijena], [y_korijena, y_korijena], color="#00D4FF", linewidth=2
        )
        os.set_ylim(-1, len(listovi))

    def nacrtaj_list(self, node, listovi):
        if node.grananje():
            listovi.append(node)
            return
        self.nacrtaj_list(node.left, listovi)
        self.nacrtaj_list(node.right, listovi)

    def natpis_list(self, os, node, pozicije, x=0.0):
        if node.grananje():
            y = pozicije[node.label]
            os.text(
                x,
                y,
                node.label,
                verticalalignment="center",
                fontsize=10,
                color="#E0E0E0",
                fontweight="bold",
            )
            return x, y
        _, y_lijevo = self.natpis_list(os, node.left, pozicije, x + 1)
        _, y_desno = self.natpis_list(os, node.right, pozicije, x + 1)
        y = (y_lijevo + y_desno) / 2
        os.plot([x, x], [y_lijevo, y_desno], color="#00D4FF", linewidth=2)
        os.plot([x, x + 1], [y_lijevo, y_lijevo], color="#00D4FF", linewidth=2)
        os.plot([x, x + 1], [y_desno, y_desno], color="#00D4FF", linewidth=2)
        os.text(
            x,
            y,
            f"{node.distance:.2f}",
            fontsize=9,
            verticalalignment="center",
            color="#4ECDC4",
            fontweight="bold",
        )
        return x, y

#pokretanje

def main():
    app = CrichtonianApp()
    app.mainloop()


if __name__ == "__main__":
    main()

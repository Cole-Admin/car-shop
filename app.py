from flask import Flask, render_template, request, redirect, session, flash

app = Flask(__name__)
app.secret_key = "tajni_kljuc_2024"

BAZA_AUTA = "baza_auta.txt"
BAZA_KORISNIKA = "korisnici.txt"


# ─────────────────────────────────────────────
#  POMOCNE FUNKCIJE — AUTOMOBILI
# ─────────────────────────────────────────────

def ucitaj_aute():
    auti = []
    try:
        with open(BAZA_AUTA, "r", encoding="utf-8") as f:
            for linija in f:
                d = linija.strip().split(":")
                if len(d) == 7:
                    auto = {
                        "id":     int(d[0]),
                        "marka":  d[1],
                        "model":  d[2],
                        "godiste": int(d[3]),
                        "snaga":  int(d[4]),
                        "brzina": int(d[5]),
                        "cena":   int(d[6]),
                    }
                    auti.append(auto)
    except FileNotFoundError:
        pass
    return auti


def sacuvaj_aute(auti):
    with open(BAZA_AUTA, "w", encoding="utf-8") as f:
        for a in auti:
            f.write(f"{a['id']}:{a['marka']}:{a['model']}:{a['godiste']}:{a['snaga']}:{a['brzina']}:{a['cena']}\n")


def obrisi_auto(auto_id):
    auti = ucitaj_aute()
    auti = [a for a in auti if a["id"] != auto_id]
    sacuvaj_aute(auti)


# ─────────────────────────────────────────────
#  POMOCNE FUNKCIJE — KORISNICI
# ─────────────────────────────────────────────

def ucitaj_korisnike():
    korisnici = []
    try:
        with open(BAZA_KORISNIKA, "r", encoding="utf-8") as f:
            for linija in f:
                d = linija.strip().split(":")
                if len(d) == 3:
                    korisnici.append({
                        "ime":    d[0],
                        "sifra":  d[1],
                        "balans": int(d[2]),
                    })
    except FileNotFoundError:
        pass
    return korisnici


def sacuvaj_korisnike(korisnici):
    with open(BAZA_KORISNIKA, "w", encoding="utf-8") as f:
        for k in korisnici:
            f.write(f"{k['ime']}:{k['sifra']}:{k['balans']}\n")


def pronadji_korisnika(ime):
    for k in ucitaj_korisnike():
        if k["ime"] == ime:
            return k
    return None


def azuriraj_balans(ime, novi_balans):
    korisnici = ucitaj_korisnike()
    for k in korisnici:
        if k["ime"] == ime:
            k["balans"] = novi_balans
            break
    sacuvaj_korisnike(korisnici)


# ─────────────────────────────────────────────
#  CENA REGISTRACIJE
# ─────────────────────────────────────────────

def cena_registracije(snaga):
    if snaga < 100:
        return "150 EUR"
    elif snaga <= 175:
        return "250 EUR"
    elif snaga <= 250:
        return "300 EUR"
    elif snaga <= 425:
        return "500 EUR"
    elif snaga <= 700:
        return "1200 EUR"
    else:
        return "2000 EUR"


# ─────────────────────────────────────────────
#  RUTE
# ─────────────────────────────────────────────

@app.route("/", methods=["GET", "POST"])
def login():
    if "ime" in session:
        return redirect("/market")

    greska = None

    if request.method == "POST":
        ime = request.form.get("ime", "").strip()
        sifra = request.form.get("sifra", "").strip()

        korisnik = pronadji_korisnika(ime)

        if korisnik and korisnik["sifra"] == sifra:
            session["ime"] = korisnik["ime"]
            session["balans"] = korisnik["balans"]
            return redirect("/market")
        else:
            greska = "Pogrešno korisničko ime ili lozinka."

    return render_template("login.html", greska=greska)


@app.route("/register", methods=["GET", "POST"])
def register():
    if "ime" in session:
        return redirect("/market")

    greska = None

    if request.method == "POST":
        ime = request.form.get("ime", "").strip()
        sifra = request.form.get("sifra", "").strip()
        balans_str = request.form.get("balans", "0").strip()

        if not ime or not sifra:
            greska = "Korisničko ime i lozinka su obavezni."
        elif pronadji_korisnika(ime):
            greska = "Korisnik sa tim imenom već postoji."
        else:
            try:
                balans = int(balans_str) if balans_str else 0
            except ValueError:
                balans = 0

            korisnici = ucitaj_korisnike()
            korisnici.append({"ime": ime, "sifra": sifra, "balans": balans})
            sacuvaj_korisnike(korisnici)
            return redirect("/")

    return render_template("register.html", greska=greska)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/market", methods=["GET", "POST"])
def market():
    if "ime" not in session:
        return redirect("/")

    auti = ucitaj_aute()

    search    = request.form.get("search", "").strip()
    min_cena  = request.form.get("min_cena", "").strip()
    max_cena  = request.form.get("max_cena", "").strip()
    min_god   = request.form.get("min_god", "").strip()
    min_snaga = request.form.get("min_snaga", "").strip()

    if search:
        auti = [a for a in auti if search.lower() in a["marka"].lower() or search.lower() in a["model"].lower()]
    if min_cena:
        auti = [a for a in auti if a["cena"] >= int(min_cena)]
    if max_cena:
        auti = [a for a in auti if a["cena"] <= int(max_cena)]
    if min_god:
        auti = [a for a in auti if a["godiste"] >= int(min_god)]
    if min_snaga:
        auti = [a for a in auti if a["snaga"] >= int(min_snaga)]

    poruka = session.pop("poruka", None)

    return render_template(
        "market.html",
        auti=auti,
        ime=session["ime"],
        balans=session["balans"],
        poruka=poruka,
        filters={
            "search": search,
            "min_cena": min_cena,
            "max_cena": max_cena,
            "min_god": min_god,
            "min_snaga": min_snaga,
        }
    )


@app.route("/kupi/<int:auto_id>")
def kupi(auto_id):
    if "ime" not in session:
        return redirect("/")

    auti = ucitaj_aute()
    auto = next((a for a in auti if a["id"] == auto_id), None)

    if auto is None:
        session["poruka"] = ("greska", "Automobil nije pronađen.")
        return redirect("/market")

    balans = session["balans"]

    if balans < auto["cena"]:
        session["poruka"] = ("greska", "Nemate dovoljno sredstava za kupovinu.")
        return redirect("/market")

    novi_balans = balans - auto["cena"]
    azuriraj_balans(session["ime"], novi_balans)
    obrisi_auto(auto_id)

    session["balans"] = novi_balans
    session["poruka"] = ("uspeh", f"{auto['marka']} {auto['model']} je uspešno kupljen!")

    return redirect("/market")


@app.route("/registracija")
def registracija():
    try:
        snaga = int(request.args.get("snaga", 0))
    except ValueError:
        snaga = 0
    return cena_registracije(snaga)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
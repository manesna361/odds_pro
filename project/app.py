from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import login_required

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///final.db")

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
@login_required
def index():
    name = db.execute("SELECT username FROM users WHERE id = ?", session["user_id"])[0]["username"]

    return render_template("index.html", name = name)


@app.route("/expect/<string:build>")
@login_required
def expect(build):
    name = db.execute("SELECT username FROM users WHERE id = ?", session["user_id"])[0]["username"]

    if build == "tansho":
        gain = "単勝"
    elif build == "fukusho":
        gain = "複勝"
    elif build == "wakuren":
        gain = "枠連"
    elif build == "umaren":
        gain = "馬連"
    elif build == "waido":
        gain = "ワイド"
    elif build == "umatan":
        gain = "馬単"
    elif build == "sanrenpuku":
        gain = "3連複"
    elif build == "sanrentan":
        gain = "3連単"

    items_buy = db.execute("SELECT raceid, buy, got, money, odds FROM buylist WHERE id = ? AND buy = ?", session["user_id"], gain)

    if not items_buy:
        flash("登録されていません")
        return render_template("index.html", name=name)

    count = 0
    bought = 0
    hit = 0
    hited = 0

    for i,j in enumerate(items_buy):
        bought += int(items_buy[i]['money'])
        if items_buy[i]['got'] == "不的中":
            count += int(items_buy[i]['money'])
        else:
            count -= round(int(items_buy[i]['money']) * round(float(items_buy[i]['odds']), 1))
            hit += 1
            hited = round(hit / (i + 1) * 100)

        total = -count

        if total > 0:
            score = round(total / bought * 100)
        else:
            score = 0

    return render_template("expect.html", total = total, items = items_buy, name = name, bought = bought, hited = hited, score = score)


@app.route("/analyze/<string:raceids>")
@login_required
def analyze(raceids):
    name = db.execute("SELECT username FROM users WHERE id = ?", session["user_id"])[0]["username"]

    items_buy = db.execute("SELECT buy, odds FROM buylist WHERE id = ? AND raceid = ?", session["user_id"], raceids)

    if items_buy[0]["buy"] == "単勝":
        a = round(float(items_buy[0]["odds"]) / 3.0, 1)
        lists = [{"buy": "複勝", "odds": a}]
    elif items_buy[0]["buy"] == "複勝":
        a = round(float(items_buy[0]["odds"]) * 3.0, 1)
        lists = [{"buy": "単勝", "odds": a}]
    elif items_buy[0]["buy"] == "枠連":
        a = round(float(items_buy[0]["odds"]) * 4.0, 1)
        lists = [{"buy": "馬連", "odds": a}]
    elif items_buy[0]["buy"] == "馬連":
        a = round(float(items_buy[0]["odds"]) / 4.0, 1)
        b = round(float(items_buy[0]["odds"]) / 3.0, 1)
        c = round(float(items_buy[0]["odds"]) * 4.0, 1)
        lists = [{"buy": "枠連", "odds": a}, {"buy": "ワイド", "odds": b}, {"buy": "馬単", "odds": c}]
    elif items_buy[0]["buy"] == "ワイド":
        a = round(float(items_buy[0]["odds"]) * 3.0, 1)
        lists = [{"buy": "馬連", "odds": a}]
    elif items_buy[0]["buy"] == "馬単":
        a = round(float(items_buy[0]["odds"]) / 2.0, 1)
        lists = [{"buy": "馬連", "odds": a}]
    elif items_buy[0]["buy"] == "3連複":
        a = round(float(items_buy[0]["odds"]) * 6.0, 1)
        lists = [{"buy": "3連単", "odds": a}]
    elif items_buy[0]["buy"] == "3連単":
        a = round(float(items_buy[0]["odds"]) / 6.0, 1)
        lists = [{"buy": "3連複", "odds": a}]
        # lists = {"buy":"odds", "複勝", "枠連", "馬連", "ワイド", "馬単", "3連複", "3連単"}

    return render_template("analyze.html", items = items_buy, name = name, raceid = raceids, lists = lists)


@app.route("/input", methods=["GET", "POST"])
@login_required
def input():
    """Show history of transactions"""
    name = db.execute("SELECT username FROM users WHERE id = ?", session["user_id"])[0]["username"]
    # POSTであれば
    if request.method == "POST":

        get_year = request.form.get("year")
        get_place = request.form.get("place")
        get_date = request.form.get("date")
        get_day = request.form.get("day")
        get_race = request.form.get("race")
        get_buy = request.form.get("buy")
        get_raceid = str(get_year) + str(get_place) + str(get_date) + str(get_day) + str(get_race)
        get_odds = request.form.get("odds")
        get_money = request.form.get("money")
        get_got = request.form.get("got")
        get_tankeinumber1 = request.form.get("tankeinumber1")
        get_renkeinumber1li = request.form.getlist("renkeinumber1")
        get_renkeinumber2li = request.form.getlist("renkeinumber2")
        get_sanrenkeinumber1li = request.form.getlist("sanrenkeinumber1")
        get_sanrenkeinumber2li = request.form.getlist("sanrenkeinumber2")
        get_sanrenkeinumber3li = request.form.getlist("sanrenkeinumber3")


        # yearが入力されてるか確認
        if not get_year:
            flash("西暦を入力してください")
            return redirect('input')

        # placeが入力されてるか確認
        elif not get_place:
            flash("競馬場を入力してください")
            return redirect('input')

        # dateが入力されてるか確認
        elif not get_date:
            flash("第何回開催かを入力してください")
            return redirect('input')

        # dayが入力されてるか確認
        elif not get_day:
            flash("開催何日目かを入力してください")
            return redirect('input')

        # raceが入力されてるか確認
        elif not get_race:
            flash("何レース目かを入力してください")
            return redirect('input')

        # buyが入力されてるか確認
        elif not get_buy:
            flash("券種を入力してください")
            return redirect('input')

        # 単系が入力されているか確認
        elif get_buy == "単勝" or get_buy == "複勝":
            if not get_tankeinumber1:
                flash("1頭目の馬番を入力してください")
                return redirect('input')
            get_point = 1

        # 連系が入力されているか確認
        elif get_buy == "枠連" or get_buy == "馬連" or get_buy == "ワイド" or get_buy == "馬単":
            if not get_renkeinumber1li:
                flash("1頭目の馬番を入力してください")
                return redirect('input')
            elif not get_renkeinumber2li:
                flash("2頭目の馬番を入力してください")
                return redirect('input')
            elif len(get_renkeinumber1li) > 1:
                flash("まだフォーメーション対応していません")
                return redirect('input')
            elif len(get_renkeinumber2li) > 1:
                flash("まだフォーメーション対応していません")
                return redirect('input')
            get_point = 1

        # 3連系が入力されているか確認
        elif get_buy == "3連複" or get_buy == "3連単":
            if not get_sanrenkeinumber1li:
                flash("1頭目の馬番を入力してください")
                return redirect('input')
            elif not get_sanrenkeinumber2li:
                flash("2頭目の馬番を入力してください")
                return redirect('input')
            elif not get_sanrenkeinumber3li:
                flash("3頭目の馬番を入力してください")
                return redirect('input')
            elif len(get_sanrenkeinumber1li) > 1:
                flash("まだフォーメーション対応していません")
                return redirect('input')
            elif len(get_sanrenkeinumber2li) > 1:
                flash("まだフォーメーション対応していません")
                return redirect('input')
            elif len(get_sanrenkeinumber3li) > 1:
                flash("まだフォーメーション対応していません")
                return redirect('input')
            get_point = 1

        # oddsが入力されているか確認
        elif not get_odds:
            flash("オッズを入力してください")
            return redirect('input')

        # moneyが入力されているか確認
        elif not get_money:
            flash("購入金額を入力してください")
            return redirect('input')

        # gotが入力されているか確認
        elif not get_got:
            flash("的中したかを入力してください")
            return redirect('input')

        row = db.execute("SELECT * FROM raceid WHERE raceid = ?", get_raceid)
        money = get_money * get_point

        if len(row) == 0:
            db.execute("INSERT INTO raceid (id, raceid, year, place, date, day, race) values(?, ?, ?, ?, ?, ?, ?)", session["user_id"], get_raceid, get_year, get_place, get_date, get_day, get_race)

        db.execute("INSERT INTO buylist (id, raceid, buy, odds, money, got) values(?, ?, ?, ?, ?, ?)", session["user_id"], get_raceid, get_buy, get_odds, money, get_got)

        # 条件分岐を表示する
        flash("登録に成功しました")
        return render_template("input.html", name = name)

    else:
        return render_template("input.html", name = name)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            flash("ユーザーネームを入力してください")
            return redirect('login')

        # Ensure password was submitted
        elif not request.form.get("password"):
            flash("パスワードを入力してください")
            return redirect('login')

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            flash("正しいユーザーネームまたはパスワードを入力してください")
            return redirect('login')

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/history")
@login_required
def history():
    """Get stock quote."""

    name = db.execute("SELECT username FROM users WHERE id = ?", session["user_id"])[0]["username"]
    items_buy = db.execute("SELECT raceid, buy, got, money, odds FROM buylist WHERE id = ?", session["user_id"])

    if not items_buy:
        flash("登録されていません")
        return render_template("index.html", name=name)

    count = 0
    bought = 0
    hit = 0
    num = 0

    for i,j in enumerate(items_buy):
        bought += int(items_buy[i]['money'])
        num += 1
        if items_buy[i]['got'] == "不的中":
            count += int(items_buy[i]['money'])
        else:
            count -= round(int(items_buy[i]['money']) * round(float(items_buy[i]['odds']), 1))
            hit += 1

        hited = round(hit / (num) * 100)

        total = -count

        score = round(total / bought * 100)

    return render_template("history.html", total = total, items = items_buy, name = name, bought = bought, hited = hited, score = score)


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        get_username = request.form.get("username")
        get_password = request.form.get("password")
        get_again = request.form.get("confirmation")

        # Ensure username was submitted
        if not get_username:
            flash("ユーザーネームを入力してください")
            return redirect('register')

        # Ensure password was submitted
        elif not get_password:
            flash("パスワードを入力してください")
            return redirect('register')

        # パスワードの再入力があるか
        elif not get_again:
            flash("パスワードを再入力してください")
            return redirect('register')

        # パスワードと再入力の一致を確認
        elif get_password != get_again:
            flash("パスワードと再入力が異なっています")
            return redirect('register')

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", get_username)

        # ユーザーネームが一つしかないか確認する
        if len(rows) == 1:
            flash("そのユーザーネームはすでに使われています")
            return redirect('register')

        # そのユーザーネームが登録されていなければ
        if len(rows) != 1:

            # パスワードをハッシュ化する
            hash_password = generate_password_hash(get_password)

        # 新規登録処理
        user_id = db.execute("INSERT INTO users(username, hash) values(?, ?)", get_username, hash_password)

        # ログイン状態にする
        session["user_id"] = user_id

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")
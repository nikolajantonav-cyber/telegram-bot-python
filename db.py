# db.py
import sqlite3, json
from pathlib import Path
from typing import List, Dict, Any, Optional

DB_PATH = Path("recipes.db")

def get_conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS recipes(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,                -- NULL = общая база; иначе — личный рецепт
        title TEXT NOT NULL,
        description TEXT NOT NULL,      -- краткое описание (без граммовок)
        ingredients_json TEXT NOT NULL, -- [{"name": str, "grams": float, "kcal": float}]
        steps_json TEXT NOT NULL,       -- [str, ...]
        cook_time_min INTEGER NOT NULL,
        total_kcal INTEGER NOT NULL,
        total_grams INTEGER NOT NULL
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS cook_logs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        recipe_id INTEGER NOT NULL,
        ts DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """)
    conn.commit(); conn.close()

def _insert(conn, user_id, title, desc, ings: List[Dict[str, Any]], steps: List[str], tmin: int):
    total_kcal = int(round(sum(float(i.get("kcal", 0)) for i in ings)))
    total_grams = int(round(sum(float(i.get("grams", 0)) for i in ings)))
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO recipes(user_id,title,description,ingredients_json,steps_json,cook_time_min,total_kcal,total_grams)
    VALUES(?,?,?,?,?,?,?,?)
    """, (user_id, title, desc, json.dumps(ings, ensure_ascii=False),
          json.dumps(steps, ensure_ascii=False), tmin, total_kcal, total_grams))
    conn.commit()

def insert_many(recipes: List[Dict[str, Any]]):
    conn = get_conn()
    for r in recipes:
        _insert(conn, None, r["title"], r["description"], r["ingredients"], r["steps"], r["cook_time_min"])
    conn.close()

def add_user_recipe(user_id: int, title: str, desc: str, ings: List[Dict[str, Any]], steps: List[str], tmin: int):
    conn = get_conn(); _insert(conn, user_id, title, desc, ings, steps, tmin); conn.close()

def search(keyword: str, user_id: int):
    conn = get_conn(); conn.row_factory = sqlite3.Row
    cur = conn.cursor(); like = f"%{keyword.lower()}%"
    cur.execute("""
    SELECT * FROM recipes
    WHERE (user_id IS NULL OR user_id=?)
      AND (LOWER(title) LIKE ? OR LOWER(description) LIKE ? OR LOWER(ingredients_json) LIKE ?)
    ORDER BY id DESC LIMIT 40
    """, (user_id, like, like, like))
    rows = cur.fetchall(); conn.close(); return rows

def all_for_user(user_id: int, quick_only: bool=False):
    conn = get_conn(); conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    if quick_only:
        cur.execute("""SELECT * FROM recipes WHERE (user_id IS NULL OR user_id=?) AND cook_time_min<=15 ORDER BY cook_time_min,id DESC""",(user_id,))
    else:
        cur.execute("""SELECT * FROM recipes WHERE (user_id IS NULL OR user_id=?) ORDER BY id DESC""",(user_id,))
    rows = cur.fetchall(); conn.close(); return rows

def by_id(recipe_id: int, user_id: int) -> Optional[sqlite3.Row]:
    conn = get_conn(); conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""SELECT * FROM recipes WHERE id=? AND (user_id IS NULL OR user_id=?)""",(recipe_id, user_id))
    row = cur.fetchone(); conn.close(); return row

def delete_user_recipe(recipe_id: int, user_id: int) -> bool:
    conn = get_conn(); cur = conn.cursor()
    cur.execute("DELETE FROM recipes WHERE id=? AND user_id=?", (recipe_id, user_id))
    ok = cur.rowcount > 0; conn.commit(); conn.close(); return ok

def random_recipe(user_id: int):
    conn = get_conn(); conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""SELECT * FROM recipes WHERE (user_id IS NULL OR user_id=?) ORDER BY RANDOM() LIMIT 1""", (user_id,))
    row = cur.fetchone(); conn.close(); return row

def by_ingredients(words: List[str], user_id: int):
    conn = get_conn(); conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    like = "%" + "%".join(w.lower() for w in words) + "%"
    cur.execute("""SELECT * FROM recipes WHERE (user_id IS NULL OR user_id=?) AND (LOWER(ingredients_json) LIKE ? OR LOWER(title) LIKE ?) ORDER BY id DESC LIMIT 40""",(user_id, like, like))
    rows = cur.fetchall(); conn.close(); return rows

def log_cook(user_id: int, recipe_id: int):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("INSERT INTO cook_logs(user_id, recipe_id) VALUES (?,?)", (user_id, recipe_id))
    conn.commit(); conn.close()

def stats(user_id: int):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM recipes WHERE user_id IS NULL"); common = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM recipes WHERE user_id=?", (user_id,)); mine = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM cook_logs WHERE user_id=?", (user_id,)); cooked = cur.fetchone()[0]
    conn.close(); return {"common": common, "mine": mine, "cooked": cooked}
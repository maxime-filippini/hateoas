import base64
from ctypes.wintypes import RGB
import io
import sqlite3
from fastapi import FastAPI
from jinja2 import Environment, PackageLoader, select_autoescape
from matplotlib import pyplot as plt
import numpy as np
import pandas as pd
from pydantic import BaseModel
from starlette.responses import FileResponse , HTMLResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI()
app.mount("/static", StaticFiles(directory="public"), name="public")

env = Environment(
    loader=PackageLoader("src"),
    autoescape=select_autoescape()
)

plt.switch_backend("Agg")

@app.get("/")
async def read_index():
    return FileResponse('public/index.html')

def _build_chart_response(fig):
    iobytes = io.BytesIO()
    fig.savefig(iobytes, format="png")
    iobytes.seek(0)
    data = base64.b64encode(iobytes.read())
    return HTMLResponse(f'<img src="data:image/png;base64, {data.decode()}"/>')  


@app.get("/build-random-series/")
def build_random_prices():
    returns = np.random.normal(loc=0, scale=0.01, size=(5000,))
    prices = 100 * np.exp(np.cumsum(returns))

    fig, ax = plt.subplots()
    fig.set_facecolor("#ffffff00")
    ax.plot(np.arange(returns.size), prices)
    return _build_chart_response(fig)


def _make_table_rows(df: pd.DataFrame) -> str:
    template = env.get_template("table.html")
    rows = [row for _, row in df.iterrows()]

    out = template.render(rows=rows, columns=df.columns)
    return out


@app.get("/prices")
def get_prices(symbol: str):
    with sqlite3.connect("price_db.db") as con:
        df = pd.read_sql(
            sql="SELECT date, raw_close_price FROM prices WHERE symbol = :symbol", 
            con=con, 
            params={"symbol": symbol},
            parse_dates=["date"]
        )
        
    table = _make_table_rows(df.tail(10))
    return HTMLResponse(table)

    
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <html>
        <body>
            <h1>🚀 FastAPI 已启动 </h1>
            <p> 访问 <a href="/docs">/docs</a> 查看 API 文档 </p>
        </body>
    </html>
    """

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("demo2:app", host="127.0.0.1", port=8888, reload=True)
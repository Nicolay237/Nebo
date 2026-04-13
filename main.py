from fastapi import FastAPI

app = FastAPI()


@app.get('/req')
def get_req():
    return 'hello world'
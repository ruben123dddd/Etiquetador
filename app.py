import uvicorn
import fastapi
from reportlab.pdfgen import canvas
import qrcode
import barcode
app = fastapi.FastAPI()
@app.get("/")
def read_root():
    return {"Hello": "World"}
@app.get("/generate_pdf")
def generate_pdf():
    c = canvas.Canvas("output.pdf")
    c.drawString(100, 750, "Hello, World!")
    c.save()
    return fastapi.responses.FileResponse("output.pdf", media_type="application/pdf", filename="output.pdf")
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=80)
from barcode import ean
import uvicorn
import fastapi
from reportlab.pdfgen import canvas
import qrcode
import barcode
from fastapi.responses import HTMLResponse
from pathlib import Path
BASE_DIR = Path(__file__).parent
app = fastapi.FastAPI()
def safe_ean13(code):
    if len(code) == 13:
        try:
            ean.get("ean13", code)
            return code
        except barcode.errors.IllegalCharacterError:
            raise ValueError("EAN-13 code must contain only digits")
        except barcode.errors.NumberOfDigitsError:
            raise ValueError("EAN-13 code must be 12 digits long")
        except barcode.errors.InvalidChecksumError:
            raise ValueError("Invalid EAN-13 code")
    if len(code) < 12:
        for i in range(len(code), 12):
            code = "0" + code
    if len(code) == 12:
        # Calculate the EAN-13 checksum
        total = sum(int(digit) * (3 if i % 2 == 0 else 1) for i, digit in enumerate(code))
        checksum = (10 - (total % 10)) % 10
        code += str(checksum)
    else:
        raise ValueError("EAN-13 code must be 12 or 13 digits long")
    if not code.isdigit():
        raise ValueError("EAN-13 code must contain only digits")
    return code

@app.get("/", response_class=HTMLResponse)
def read_root():

    generator_path = BASE_DIR / "generator.html"

    return generator_path.read_text(
        encoding="utf-8"
    )

@app.get("/generate_barcode")
def generate_barcode(code: str,type: str = "ean13"):
    if type == "ean13":
        ean = barcode.get("ean13", safe_ean13(code), writer=barcode.writer.SVGWriter())
        ean.save(
            "barcode",
            {
                "module_height": 6,
                "font_size": 0,
                "text_distance": 0,
                "quiet_zone": 1,
            }
        )
    elif type == "code128":
        code128 = barcode.get("code128", code, writer=barcode.writer.SVGWriter())
        code128.save("barcode", {
            "module_height": 3,
            "font_size": 0,
            "text_distance": 0,
            "quiet_zone": 1
            }
            )
    else:
        raise ValueError("Unsupported barcode type")
    return fastapi.responses.FileResponse("barcode.svg", media_type="image/svg+xml", filename="barcode.svg")

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=80,reload=True)
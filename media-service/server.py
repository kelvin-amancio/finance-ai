import base64
import io
import json
import os
import re
import subprocess
import tempfile
import wave

from flask import Flask, jsonify, request
from PIL import Image, ImageOps
from vosk import KaldiRecognizer, Model

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 30 * 1024 * 1024

MODEL_PATH = os.environ.get("VOSK_MODEL", "/app/model/vosk")
model = None
try:
    if os.path.isdir(MODEL_PATH):
        model = Model(MODEL_PATH)
        print("Vosk: modelo carregado.", flush=True)
except Exception as e:  # noqa: BLE001
    print("Vosk erro:", e, flush=True)


def to_buf(body):
    if not body or not body.get("base64"):
        return None
    return base64.b64decode(body["base64"])


def run(cmd, args, timeout=180):
    subprocess.run([cmd] + args, capture_output=True, timeout=timeout, check=True)


def transcrever(buf):
    if model is None:
        raise RuntimeError("Vosk indisponivel")
    f1 = tempfile.NamedTemporaryFile(suffix=".ogg", delete=False)
    f2 = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    f1.write(buf)
    f1.close()
    f2.close()
    src, wav = f1.name, f2.name
    try:
        run("ffmpeg", ["-y", "-i", src, "-ar", "16000", "-ac", "1", "-f", "wav", wav])
        rec = KaldiRecognizer(model, 16000)
        with wave.open(wav, "rb") as w:
            data = w.readframes(w.getnframes())
        rec.AcceptWaveform(data)
        res = json.loads(rec.FinalResult())
        return res.get("text", "").strip()
    finally:
        for p in (src, wav):
            try:
                os.remove(p)
            except OSError:
                pass


def preprocess(buf):
    """Melhora o OCR em fotos: escala, tons de cinza, contraste e nitidez."""
    img = Image.open(io.BytesIO(buf)).convert("L")
    w, h = img.size
    if max(w, h) < 1600:
        img = img.resize((w * 2, h * 2), Image.LANCZOS)
    img = ImageOps.autocontrast(img, cutoff=2)
    out = io.BytesIO()
    img.save(out, format="PNG")
    return out.getvalue()


def ocr(buf):
    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    tmp.write(preprocess(buf))
    tmp.close()
    base = tmp.name
    try:
        # --psm 6: bloco uniforme (preserva listas de itens/transacoes)
        subprocess.run(
            ["tesseract", base, base + ".out", "-l", "por", "--psm", "6", "--oem", "1"],
            capture_output=True,
            timeout=180,
            check=True,
        )
        out = base + ".out.txt"
        if os.path.exists(out):
            return open(out, encoding="utf-8", errors="ignore").read()
        return ""
    finally:
        for p in (base, base + ".out.txt"):
            try:
                os.remove(p)
            except OSError:
                pass


def cat_from(texto):
    t = (texto or "").lower()
    rules = [
        (("carne", "frango", "arroz", "feijao", "feijão", "cafe", "café", "leite", "acucar", "açúcar", "oleo", "óleo", "detergente", "sabao", "mercado", "supermercado", "padaria", "acai", "hortifruti"), "Mercado"),
        (("restaurante", "almoco", "almoço", "lanche", "pizza", "hamburguer", "ifood", "delivery", "bar", "padaria"), "Alimentação"),
        (("uber", "taxi", "combustivel", "posto", "estacionamento", "transporte", "99 tach"), "Transporte"),
        (("netflix", "spotify", "streaming", "assinatura", "mensalidade"), "Assinaturas"),
        (("cell", "celular", "iphone", "samsung", "notebook", "eletrodom", "casas", "magalu"), "Compras"),
        (("farmacia", "farmácia", "drogaria", "medicamento"), "Saúde"),
        (("aluguel", "condominio", "energia", "internet", "telefone", "agua", "luz", "imposto"), "Contas fixas"),
    ]
    for kws, cat in rules:
        if any(k in t for k in kws):
            return cat
    return "Outros"


_MONEY = re.compile(r"-?\d{1,3}(?:\.\d{3})*,\d{2}(?!\d)")


def money_matches(line):
    return _MONEY.findall(line)


def value_of(text):
    ms = money_matches(text)
    if not ms:
        return None
    return float(ms[-1].replace(".", "").replace(",", "."))


def transacao_tipo(low):
    if re.search(r"(receb(ido|ida)|deposito|salario|rendiment|pix\s*receb|ted\s*receb|transferencia\s*(de|do)*\s*receb)", low):
        return "receita"
    if re.search(r"(compra|debito|tarifa|pagamento|boleto|pix\s*envi|ted\s*envi|transferencia.*envi|saque|carn|mensalidade|imposto|juros|multa)", low):
        return "despesa"
    return "despesa"


def parse_gastos(txt):
    linhas = [re.sub(r"\s{2,}", " ", l).strip() for l in str(txt or "").splitlines() if l.strip()]
    gastos = []
    total = None
    pendente = None  # descricao numa linha, valor na seguinte (OCR separa às vezes)
    for line in linhas:
        low = line.lower()
        if re.search(r"\bsaldo\b", low) and re.search(r"(anterior|atual|final)", low):
            continue
        if re.search(r"^(banco|extrato|conta|agencia|cliente|pagina|documento|data\b|descric|hist\b|valor\b|comprovante|fatura|cartao|cartão|nota|cupom|cnpj|cpf|rua|avenida|av\.|telefone|www|http)", low) and not money_matches(line):
            continue
        if re.search(r"total|soma|geral|valor total", low):
            v = value_of(line)
            if v:
                total = abs(v)
            continue

        ms = money_matches(line)
        if not ms:
            if re.match(r"^[A-Za-zÀ-ÿ0-9]", line) and len(line) > 2:
                pendente = line
            continue

        valor = abs(float(ms[-1].replace(".", "").replace(",", ".")))
        desc = line
        for s in ms:
            desc = desc.replace(s, "")
        desc = re.sub(r"\b\d{1,2}/\d{1,2}\b", "", desc)  # remove data DD/MM
        desc = re.sub(r"R\$\s?", "", desc, flags=re.I).strip(" :;-–—|.")
        if pendente:
            desc = (pendente + " " + desc).strip()
            pendente = None
        if not desc:
            desc = "Transação"

        gi = {
            "descricao": desc[:90],
            "valor": round(valor, 2),
            "categoria": cat_from(desc),
            "tipo": transacao_tipo(low),
            "data": None,
        }
        parc = None
        m_x = re.search(r"\b(\d{1,3})\s*[xX]\b", line)          # "12x"
        m_ab = re.search(r"\b(\d{1,2})\s*/\s*(\d{1,3})\b", line)  # "7/12"
        if m_x:
            total = int(m_x.group(1))
            atual = None
            if m_ab and int(m_ab.group(2)) == total:
                atual = int(m_ab.group(1))
            parc = (atual, total)
        elif re.search(r"parcela", low) and m_ab:
            parc = (int(m_ab.group(1)), int(m_ab.group(2)))
        if parc and 1 < parc[1] <= 48 and (parc[0] is None or parc[0] <= parc[1]):
            gi["parcelas_total"] = parc[1]
            if parc[0]:
                gi["parcela_atual"] = parc[0]
            gi["valor_total"] = round(gi["valor"] * parc[1], 2)
        gastos.append(gi)

    if not gastos and total:
        gastos.append(
            {"descricao": "Compra (total)", "valor": round(total, 2),
             "categoria": "Outros", "tipo": "despesa", "data": None}
        )
    return gastos[:14]


@app.get("/health")
def health():
    return jsonify(status="ok", vosk=model is not None)


@app.post("/transcribe")
def transcribe():
    b = to_buf(request.get_json(silent=True) or {})
    if not b:
        return jsonify(error="base64 obrigatorio"), 400
    try:
        return jsonify(text=transcrever(b), provider="vosk")
    except Exception as e:  # noqa: BLE001
        return jsonify(error=str(e), provider="vosk"), 500


@app.post("/ocr")
def ocr_ep():
    b = to_buf(request.get_json(silent=True) or {})
    if not b:
        return jsonify(error="base64 obrigatorio"), 400
    try:
        return jsonify(text=ocr(b), provider="tesseract")
    except Exception as e:  # noqa: BLE001
        return jsonify(error=str(e), provider="tesseract"), 500


@app.post("/parse-print")
def parse_print():
    b = to_buf(request.get_json(silent=True) or {})
    if not b:
        return jsonify(error="base64 obrigatorio"), 400
    try:
        t = ocr(b)
        gastos = parse_gastos(t)
        if not gastos:
            # tenta com PSM automatico (3) como segunda passada
            tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            tmp.write(preprocess(b))
            tmp.close()
            base = tmp.name
            try:
                subprocess.run(["tesseract", base, base + ".out", "-l", "por", "--psm", "3", "--oem", "1"],
                               capture_output=True, timeout=180, check=True)
                out = base + ".out.txt"
                t2 = open(out, encoding="utf-8", errors="ignore").read() if os.path.exists(out) else ""
                gastos = parse_gastos(t2) or gastos
                if t2:
                    t = t2
            finally:
                for p in (base, base + ".out.txt"):
                    try:
                        os.remove(p)
                    except OSError:
                        pass
        return jsonify(text=t, gastos=gastos, provider="tesseract")
    except Exception as e:  # noqa: BLE001
        return jsonify(error=str(e), provider="tesseract"), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 3000)))
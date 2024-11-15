from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
import edge_tts
import zipfile
import io

app = FastAPI()

class Request(BaseModel):
    text: str = "I will Make your text Speak!"
    voice: str = "en-US-BrianMultilingualNeural"
    rate: str = "+7%"
    word_in_cue: int = 1

async def generator(text: str, voice: str, rate: str, in_cue: int):

    audio_file = io.BytesIO()
    srt_file = io.StringIO()
    zip_file = io.BytesIO()

    communicate = edge_tts.Communicate(text, voice, rate=rate)
    submaker = edge_tts.SubMaker()

    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_file.write(chunk["data"])
        elif chunk["type"] == "WordBoundary":
            submaker.create_sub((chunk["offset"], chunk["duration"]), chunk["text"])

    vtt_file = submaker.generate_subs(in_cue)
    replaced = vtt_file.replace(".", ",")
    lines = replaced.splitlines()

    if len(lines) >= 2:
        text = '\n'.join(lines[1:]).strip()
        srt_file.write(f"{text}\n\n")

    with zipfile.ZipFile(zip_file, 'w') as zipf:
        zipf.writestr("audio.mp3", audio_file.getvalue())
        zipf.writestr("audio.srt", srt_file.getvalue())

    zip_file.seek(0)

    return zip_file

@app.get("/")
async def read_root():
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Edge TTS API</title>
    </head>
    <body>
        <h1>Edge TTS API</h1>
        <p>From: Lakshan De Silva</p>
        <p>To know more, Check out my website at <a href="https://lakshandesilva.com">lakshandeilva.com</a>.</p>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.post("/generate")
async def generate(request: Request):
    try:
        zip_file = await generator(request.text, request.voice, request.rate, request.word_in_cue)
        return StreamingResponse(zip_file, media_type='application/zip', headers={"Content-Disposition": "attachment; filename=Result.zip"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from flask import Flask, render_template, request, send_from_directory
from groq import Groq
from dotenv import load_dotenv
import os
import pandas as pd


load_dotenv()

app = Flask(__name__)

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)


# ============================================================
# HOME PAGE
# ============================================================

@app.route("/")
def home():

    return render_template(
        "index.html",
        translation=None,
        text="",
        from_language="English",
        to_language="Tamil",
        csv_summary=None,
        csv_translation=None,
        csv_language="English",
        download_file=None
    )


# ============================================================
# TEXT TRANSLATION
# ============================================================

@app.route("/translate", methods=["POST"])
def translate():

    text = request.form.get("text", "").strip()

    from_language = request.form.get(
        "from_language",
        "English"
    )

    to_language = request.form.get(
        "to_language",
        "Tamil"
    )


    if not text:

        return render_template(
            "index.html",
            translation="Please enter some text.",
            text=text,
            from_language=from_language,
            to_language=to_language
        )


    prompt = f"""
Translate the following text accurately.

Source language: {from_language}
Target language: {to_language}

Important instructions:
- Keep the original meaning.
- Use natural and grammatically correct {to_language}.
- Do not explain the translation.
- Give only the translated text.

Text:
{text}
"""


    response = client.chat.completions.create(

        model="openai/gpt-oss-20b",

        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )


    translation = response.choices[0].message.content.strip()


    return render_template(
        "index.html",
        translation=translation,
        text=text,
        from_language=from_language,
        to_language=to_language,
        csv_summary=None,
        csv_translation=None,
        csv_language="English",
        download_file=None
    )



# ============================================================
# CSV PROCESSING
# ============================================================

@app.route("/csv-process", methods=["POST"])
def csv_process():

    file = request.files.get("csv_file")

    csv_language = request.form.get(
        "csv_language",
        "English"
    )


    if not file or file.filename == "":

        return render_template(
            "index.html",
            translation=None,
            text="",
            from_language="English",
            to_language="Tamil",
            csv_summary="Please upload a CSV file.",
            csv_translation=None,
            csv_language=csv_language
        )


    try:

        # Read CSV
        df = pd.read_csv(file)


        # Convert CSV data into text
        csv_text = df.to_string(index=False)


        # Limit extremely large files
        csv_text_for_ai = csv_text[:15000]


        # ----------------------------------------------------
        # CSV SUMMARY
        # ----------------------------------------------------

        summary_prompt = f"""
Analyze the following CSV data.

Give a clear and easy-to-understand summary of the
important information contained in the dataset.

Mention:
- Number of rows
- Important columns
- Main patterns or information
- Important observations

CSV data:

{csv_text_for_ai}
"""


        summary_response = client.chat.completions.create(

            model="openai/gpt-oss-20b",

            messages=[
                {
                    "role": "user",
                    "content": summary_prompt
                }
            ]
        )


        csv_summary = (
            summary_response
            .choices[0]
            .message
            .content
            .strip()
        )


        # ----------------------------------------------------
        # CSV TRANSLATION
        # ----------------------------------------------------

        translation_prompt = f"""
Translate the following CSV information into
{csv_language}.

Keep the meaning accurate.

Do not add unnecessary explanations.

CSV information:

{csv_text_for_ai}
"""


        translation_response = client.chat.completions.create(

            model="openai/gpt-oss-20b",

            messages=[
                {
                    "role": "user",
                    "content": translation_prompt
                }
            ]
        )


        csv_translation = (
            translation_response
            .choices[0]
            .message
            .content
            .strip()
        )


        # ----------------------------------------------------
        # SAVE TRANSLATED CSV
        # ----------------------------------------------------

        output_folder = "translated_files"

        os.makedirs(
            output_folder,
            exist_ok=True
        )


        output_file = os.path.join(
            output_folder,
            "translated_result.csv"
        )


        translated_df = pd.DataFrame(
            {
                "Translated Content": [
                    csv_translation
                ]
            }
        )


        translated_df.to_csv(
            output_file,
            index=False
        )


        return render_template(

            "index.html",

            translation=None,

            text="",

            from_language="English",

            to_language="Tamil",

            csv_summary=csv_summary,

            csv_translation=csv_translation,

            csv_language=csv_language,

            download_file="translated_result.csv"
        )


    except Exception as e:

        return render_template(

            "index.html",

            translation=None,

            text="",

            from_language="English",

            to_language="Tamil",

            csv_summary=f"Error processing CSV: {str(e)}",

            csv_translation=None,

            csv_language=csv_language,

            download_file=None
        )



# ============================================================
# DOWNLOAD TRANSLATED CSV
# ============================================================

@app.route("/download/<filename>")
def download_file(filename):

    return send_from_directory(
        "translated_files",
        filename,
        as_attachment=True
    )



# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )
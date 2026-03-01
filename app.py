from flask import Flask, render_template, request, jsonify
from translator import translate, single_dict, phrase_dict, DICT_SIZE

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html", dict_size=DICT_SIZE)


@app.route("/api/translate", methods=["POST"])
def api_translate():
    data = request.get_json(silent=True) or {}
    text = data.get("text", "").strip()

    if not text:
        return jsonify({"translated": "", "translated_count": 0, "total_words": 0})

    translated, translated_count, total_words = translate(text, single_dict, phrase_dict)

    return jsonify({
        "translated": translated,
        "translated_count": translated_count,
        "total_words": total_words,
    })


if __name__ == "__main__":
    app.run(debug=True)

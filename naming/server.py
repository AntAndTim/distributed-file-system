from flask import Flask, send_from_directory

app = Flask(__name__)


@app.route('/<path_to_file>')
def download(path_to_file: str):
    return send_from_directory('./', path_to_file, as_attachment=True)


if __name__ == '__main__':

    app.run()

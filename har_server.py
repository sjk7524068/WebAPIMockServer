import json
from flask import Flask, Response, request
import os
from urllib.parse import urlparse, parse_qs, unquote
import shutil
import base64

app = Flask(__name__)

har_data = None
output_folder = "mock_data"  # Folder to save extracted data


def load_har_data(har_file_path):
    """Loads HAR data from a file."""
    global har_data
    with open(har_file_path, 'r', encoding='utf-8') as f:
        har_data = json.load(f)


def extract_and_save_data(har_file_path, output_folder):
    if os.path.exists(output_folder):
        shutil.rmtree(output_folder)
    os.makedirs(output_folder, exist_ok=True)

    with open(har_file_path, 'r', encoding='utf-8') as f:
        har_data = json.load(f)

    for entry in har_data['log']['entries']:
        url = entry['request']['url']
        response = entry['response']

        if 'content' in response and 'text' in response['content']:
            content = response['content']['text']
            content_encoding = response['content'].get('encoding', None)

            if content_encoding == 'base64':
                content = base64.b64decode(content)
            else:
                content = content.encode('utf-8')

            parsed_url = urlparse(url)
            file_path = parsed_url.path
            query = parsed_url.query
            local_file_path = os.path.join(output_folder, *file_path.split('/')[1:])
            if query:
                local_file_path = os.path.join(local_file_path, query.replace('&','_'))
            if local_file_path.endswith(os.path.sep):
                local_file_path = local_file_path[:-1]

            os.makedirs(os.path.dirname(local_file_path), exist_ok=True)

            try:
                with open(local_file_path, 'wb') as local_file:
                    local_file.write(content)
            except Exception as e:
                print(f"Error writing file {local_file_path}: {e}")


@app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])
@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'])
def mock_response(path):
    if har_data is None:
        return "HAR data not loaded.", 500

    request_url = request.url

    for entry in har_data['log']['entries']:
        har_url = entry['request']['url']

        # Parse URLs
        har_parsed = urlparse(har_url)
        request_parsed = urlparse(request_url)

        # Parse Query Strings
        har_query_dict = parse_qs(har_parsed.query)
        request_query_dict = parse_qs(request_parsed.query)

        # Compare Normalized Paths and Query Strings
        if har_parsed.path == request_parsed.path and har_query_dict == request_query_dict:
            response_data = entry['response']
            status_code = response_data['status']
            headers = {header['name']: header['value'] for header in response_data['headers']}

            content = response_data.get('content', {}).get('text', '')
            content_encoding = response_data.get('content', {}).get('encoding', None)

            if content_encoding == 'base64':
                content = base64.b64decode(content)
            else:
                content = content.encode('utf-8')

            mime_type = response_data.get('content', {}).get('mimeType', 'application/octet-stream')
            return Response(content, status=status_code, headers=headers, mimetype=mime_type)

    local_file_path = os.path.join(output_folder, path)
    query = request.query_string.decode('utf-8')
    if query:
        local_file_path = os.path.join(local_file_path, query.replace('&','_'))

    if os.path.isdir(local_file_path):
        index_html_path = os.path.join(local_file_path, "index.html")
        response_json_path = os.path.join(local_file_path, "response.json")

        if os.path.exists(index_html_path):
            local_file_path = index_html_path
        elif os.path.exists(response_json_path):
            local_file_path = response_json_path

    if os.path.exists(local_file_path):
        try:
            with open(local_file_path, 'rb') as f:
                content = f.read()
                for entry in har_data['log']['entries']:
                    har_url = entry['request']['url']
                    har_parsed = urlparse(har_url)
                    local_parsed = urlparse(request.url)

                    har_query_dict = parse_qs(har_parsed.query)
                    local_query_dict = parse_qs(local_parsed.query)
                    local_query_decoded = parse_qs(unquote(local_parsed.query))

                    if har_parsed.path == local_parsed.path and (har_query_dict == local_query_dict or har_query_dict == local_query_decoded):
                        mime_type = entry['response'].get('content',{}).get('mimeType','application/octet-stream')
                        return Response(content, mimetype=mime_type)
                return Response(content, mimetype='application/octet-stream')
        except Exception as e:
            print(f"Error serving local file: {e}")
            return "File not found or error loading it", 404

    return "Mock response not found.", 404


if __name__ == '__main__':
    # import shutil
    har_file = 'xxx.har'  # Replace with your HAR file path
    extract_and_save_data(har_file, output_folder)
    load_har_data(har_file)

    # print(app.url_map)
    app.run(debug=True, port=5050)

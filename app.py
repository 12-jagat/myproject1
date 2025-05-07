<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Batman File Sharing</title>
  <style>
    body {
      font-family: 'Segoe UI', sans-serif;
      background: linear-gradient(135deg, #0f0f0f, #1a1a1a);
      color: #eee;
      padding: 20px;
      text-align: center;
    }
    h1 {
      color: #ffcc00;
      text-shadow: 0 0 10px #ffcc00aa;
    }
    img.logo {
      width: 100px;
      margin-bottom: 20px;
      animation: float 4s ease-in-out infinite;
    }
    @keyframes float {
      0% { transform: translateY(0); }
      50% { transform: translateY(-8px); }
      100% { transform: translateY(0); }
    }
    form {
      margin-bottom: 30px;
    }
    input[type="file"],
    input[type="submit"],
    input[type="text"] {
      padding: 10px;
      margin: 5px;
      border-radius: 5px;
      border: none;
    }
    input[type="submit"] {
      background-color: #ffcc00;
      color: #000;
      cursor: pointer;
      box-shadow: 0 4px 6px rgba(255, 204, 0, 0.4);
    }
    input[type="submit"]:hover {
      background-color: #e6b800;
    }
    table {
      margin: 0 auto;
      border-collapse: collapse;
      width: 60%;
      background-color: #1a1a1a;
      box-shadow: 0 0 10px #000;
    }
    th, td {
      padding: 12px;
      border: 1px solid #444;
    }
    tr:hover {
      background-color: #222;
    }
    a {
      color: #66ccff;
      text-decoration: none;
    }
    a:hover {
      text-decoration: underline;
    }
  </style>
</head>
<body>
  <img src="static/batman.png" alt="Batman Logo" class="logo">
  <h1>Batman File Sharing</h1>

  <form method="post" enctype="multipart/form-data">
    <input type="file" name="file" required>
    <input type="submit" value="Upload File">
  </form>

  <form method="get" action="/">
    <input type="text" name="search" placeholder="Search files..." value="{{ search_query }}">
    <input type="submit" value="Search">
  </form>

  {% if message %}
    <p>{{ message|safe }}</p>
  {% endif %}

  {% if files %}
    <table>
      <tr><th>File Name</th><th>Download</th></tr>
      {% for file in files %}
        <tr>
          <td>{{ file }}</td>
          <td><a href="{{ url_for('download_file', filename=file) }}" download>Download</a></td>
        </tr>
      {% endfor %}
    </table>
  {% else %}
    <p>No files found.</p>
  {% endif %}
</body>
</html>

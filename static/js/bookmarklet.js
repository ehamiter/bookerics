javascript:(function(){
    const apiURL = "http://localhost:8000/add";
    const title = encodeURIComponent(document.title);
    const metaDescription = document.querySelector("meta[name='description']");
    const description = metaDescription ? encodeURIComponent(metaDescription.content) : '';
    const url = encodeURIComponent(window.location.href);

    const popup = window.open("", "Save Bookeric", "width=666,height=420");
    popup.document.write(`
        <html>
        <head>
            <title>Save Bookeric</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    margin: 20px;
                }
                form {
                    display: flex;
                    flex-direction: column;
                }
                label {
                    margin-top: 10px;
                }
                input, textarea {
                    min-width: 400px;
                    padding: 8px;
                    margin-top: 5px;
                }
                textarea {
                    min-height: 100px;
                }
                button {
                    margin-top: 15px;
                    padding: 10px;
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    cursor: pointer;
                    max-width: 250px;
                }
                button:hover {
                    background-color: #45a049;
                }
            </style>
        </head>
        <body>
            <form id="bookmarkForm">
                <label for="title">Title:</label>
                <input type="text" id="title" name="title" value="${decodeURIComponent(title)}">
                <label for="description">Description:</label>
                <textarea id="description" name="description">${decodeURIComponent(description)}</textarea>
                <label for="url">URL:</label>
                <input type="text" id="url" name="url" value="${decodeURIComponent(url)}">
                <label for="tags">Tags (separate by spaces):</label>
                <input type="text" id="tags" name="tags" value="">
                <button type="button" onclick="saveBookmark()">Save</button>
            </form>
            <script>
                function saveBookmark() {
                    const xhr = new XMLHttpRequest();
                    xhr.open("POST", "${apiURL}", true);
                    xhr.setRequestHeader("Content-Type", "application/json;charset=UTF-8");
                    xhr.onreadystatechange = function () {
                        if (xhr.readyState === 4) {
                            const response = JSON.parse(xhr.responseText);
                            if (xhr.status === 201) {
                                window.close();
                            } else {
                                alert("Error: " + response.message);
                            }
                        }
                    };
                    const data = {
                        title: document.getElementById("title").value,
                        description: document.getElementById("description").value,
                        url: document.getElementById("url").value,
                        tags: document.getElementById("tags").value.split(" ")
                    };
                    xhr.send(JSON.stringify(data));
                }

                document.getElementById("bookmarkForm").addEventListener("keypress", function(event) {
                    if (event.key === "Enter") {
                        event.preventDefault();
                        saveBookmark();
                    }
                });

                document.getElementById("title").focus();
                if (document.getElementById("title").value) {
                    document.getElementById("title").select();
                }
            </script>
        </body>
        </html>
    `);
})();

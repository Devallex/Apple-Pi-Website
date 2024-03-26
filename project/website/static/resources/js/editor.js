Array.prototype.slice.call(document.getElementsByClassName("editor")).forEach((editor) => {
    editor.innerHTML = `
    <label for="title">Title (Required)</label><br>
    <input id="title" placeholder="Unique document name...">
    <br><br>

    <label for="title">Body (Required)</label><br>
    <textarea placeholder="Type text here..."></textarea>
    <br><br>

    <input type="submit" value="Publish">
    `
})

loaded()
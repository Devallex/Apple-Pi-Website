Array.prototype.slice.call(document.getElementsByClassName("editor")).forEach((editor) => {
	editor.innerHTML = `
	<label for="title">Title (Required)</label><br>
	<input name="title" type="text" placeholder="Unique document name...">
	<br><br>

	<label for="body">Body (Required)</label><br>
	<textarea name="body" placeholder="Type text here..."></textarea>
	<br><br>

	<input type="submit" value="Publish">
	`
})

loaded()
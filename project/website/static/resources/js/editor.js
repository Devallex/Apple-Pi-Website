Array.prototype.slice.call(document.getElementsByClassName("editor")).forEach((editor) => {
	editor.innerHTML = `
	<fieldset>
		<legend>Document</legend>

		<label for="title"><b>Title (Required — Unique):</b> What should this document be titled?</label><br>
		<input name="title" id="title" type="text" placeholder="Unique document name..."><br>

		<label for="body"><b>Body (Required):</b> The main body content of this document</label><br>
		<textarea name="body" id="body" placeholder="Type text here..."></textarea><br>

		<input name="is_published" id="is_published" type="checkbox">
		<label for="is_published"><b>Published:</b> If the document can be publicly visible. If not, only those with relevant preview or edit permissions can see it.</label><br>
	</fieldset>

	${editor.innerHTML}

	<input type="submit" value="Publish">
	`
})
const API_URL = window.location.origin + "/api"

function go_back() {
	return document.referrer ? window.location = document.referrer : history.back()
}

function call_api(url, method = "get", callback = () => { }, body = {}) {
	url = API_URL + url

	method = method.toLowerCase()

	if (method == "get") {
		body = null
	} else {
		body = JSON.stringify(body)
	}

	fetch(url, {
		method: method,
		body: body,
		headers: {
			"Content-type": "application/json; charset=UTF-8",
		}
	})
		.then(response => {
			if (!response.ok) {
				throw new Error("API Error:", response)
			}

			return response.json()
		})
		.then(callback)
}

Array.prototype.slice.call(document.getElementsByTagName("form")).forEach((form) => {
	form.addEventListener("submit", (event) => {
		event.preventDefault()

		var formData = new FormData(form);
		var contentType = null;

		const action = form.getAttribute("action")
		const method = form.getAttribute("method").toUpperCase()

		var body = null
		if (method != "get") {
			body = formData

			// contentType = "application/json";
			// body = JSON.stringify(Object.fromEntries(formData));
		}


		fetch("/api" + action, {
			method: method,
			body: body
		})
			.then(response => {
				if (response.redirected) {
					window.location.href = response.url
					return
				}

				const contentType = response.headers.get('Content-Type');

				response.text()
					.then((text) => {
						if (contentType && text) {
							if (contentType.includes("application/json") || contentType.includes("text/html")) {
								alert(text)
							} else {
								alert("ERROR: Unknown response type.")
							}
						}
						onsuccess = form.getAttribute("data-onsuccess")
						if (onsuccess) {
							eval(onsuccess)
						}
					}).catch(error => {
						alert("ERROR: " + error)
						console.error("ERROR: ", error)
					})
			})
			.catch(error => {
				alert("ERROR: " + error)
				console.error("ERROR: ", error)
			});
	})
})
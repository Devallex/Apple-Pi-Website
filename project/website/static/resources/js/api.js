const API_URL = window.location.origin + "/api"

function call_error(code) {
	window.location.replace("/errors/" + code)
}

function call_api(url, method = "GET", callback = () => { }, body = {}) {
	url = API_URL + url

	method = method.toUpperCase()

	if (method == "GET") {
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

		const action = form.getAttribute("action")
		const method = form.getAttribute("method").toUpperCase()

		if (method == "GET") {
			body = null
		} else {
			body = formData
		}

		fetch("/api" + action, {
			method: method,
			body: JSON.stringify(Object.fromEntries(formData))
		})
			.then(response => {
				if (response.redirected) {
					window.location.href = response.url
					return
				}

				const contentType = response.headers.get('Content-Type');

				if (contentType) {
					if (contentType.includes("application/json")) {
						response.text().then((text) => {
							alert(text)
						})
					} else if (contentType.includes("text/html")) {
						response.text().then((html) => {
							alert(html)
						})
					} else {
						alert("ERROR: Unknown response type!")
					}
				} else {
					alert("ERROR: Unspecified response type!")
				}
			})
			.catch(error => {
				console.log("ERROR", error)

				alert("ERROR: " + error)
				console.error("Form error: ", error)
			});

	})
})

loaded()
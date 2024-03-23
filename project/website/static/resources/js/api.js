const API_URL = window.location.origin + "/api"

function call_error(code) {
	window.location.replace("/errors/" + code)
}

function call_api(url, method = "GET", callback = () => { }, body = {}) {
	url = API_URL + url

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

loaded()
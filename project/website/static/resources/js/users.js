function createSession(data) {
	const date = new Date(data.expires)
	document.cookie = `session=${data.id + "." + data.user_id + "." + data.auth}; expires=${date.toUTCString()}; path=/`
}

function getSession() {
	session = getCookie("session")

	if (!session) {
		return
	}

	components = session.split(".")

	return {
		"id": components[0],
		"user_id": components[1],
		"token": components[2]
	}
}

function isLoggedIn() {
	return getSession() != null
}

function getUserInfo(callback) {
	if (!isLoggedIn()) {
		return
	}

	session = getSession()

	call_api("/users/" + session.user_id, method = "get", callback = callback)
}

// Validate
if (getSession()) {
	call_api("/sessions/validate/", method = "get", callback = (valid) => {
		if (valid) {
			return
		}

		deleteCookie("session")

		location.reload()
	})
}
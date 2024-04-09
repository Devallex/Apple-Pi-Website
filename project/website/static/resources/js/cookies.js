function getCookie(cookieName) {
	const value = `; ${document.cookie}`
	const parts = value.split(`; ${cookieName}=`)
	if (parts.length === 2) {
		return parts.pop().split(';').shift()
	}
}

function deleteCookie(cookieName) {
	document.cookie = `${cookieName}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`;
}
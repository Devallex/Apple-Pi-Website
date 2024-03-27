function createHeaderLink(name, url) {
	if (url == window.location.pathname) {
		name = "<b>" + name + "</b>"
	}

	return `
		<a href=${url}>
			<div>
				${name}
			</div>
		</a>
	`
}

function updateHeader(header, variables) {
	editorLink = ""
	if (variables["isLoggedIn"]) {
		editorLink = createHeaderLink("Editor", "/editor")
	}

	header.innerHTML = `
	<div class="background"></div>
	<div class="content">
		${createHeaderLink("Home", "/")}
		${createHeaderLink("About Us", "/about-us")}
		${createHeaderLink("Posts", "/posts")}
		${createHeaderLink("Our Team", "/users")}
		${createHeaderLink("Documents", "/documents")}
		${createHeaderLink(variables["userText"], variables["userLink"])}
	</div>
`
}

Array.prototype.slice.call(document.getElementsByTagName("header")).forEach((header) => {
	if (isLoggedIn()) {
		getUserInfo((userInfo) => {
			updateHeader(header, {
				"isLoggedIn": true,
				"userLink": "/settings",
				"userText": `User: <b>${userInfo["username"]}</b>`
			})
		})
	} else {
		updateHeader(header, {
			"isLoggedIn": false,
			"userLink": "/login",
			"userText": "Log In"
		})
	}
})

loaded()